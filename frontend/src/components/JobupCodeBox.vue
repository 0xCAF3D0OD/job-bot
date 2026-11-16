<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { api } from "../api/client";
import { timeOfDay } from "../dates";
import AppIcon from "./AppIcon.vue";

// « Recopie le code de jobup » (section 15 du paquet du 15.11, planches OnboardingOrdinateurAlerteCode…,
// OnboardingAlerteCode…, AlertesOrdinateurSite) : jobup envoie un code à l'adresse jobA1 quand la personne valide
// son alerte ; il s'affiche ici. Trois états : attente (cadre pointillé, roue), reçu (le code, Copier, « Reçu à … ·
// valable … ») et expiré (« Code expiré », « Renvoyer » qui rouvre jobup).
// Décisions de Kevin du 15.11 : la relecture toutes les 5 s ne tourne que pendant l'attente et seulement quand l'écran
// est visible ; elle s'arrête dès que le code arrive, ou au bout de 10 minutes sans code (état expiré). La durée de
// validité vient de l'e-mail de jobup (10 minutes sinon). Un nouveau code remplace l'ancien.
// Le serveur ne relève la boîte que si on le lui demande : dès l'affichage, puis chaque minute tant que l'étape attend
// et que l'onglet est visible (« watch-code »), il la relève toutes les 15 s. Sans relance, il s'arrête de lui-même.
const props = defineProps<{ siteUrl: string | null }>();

type Code = { code: string; received_at: string; valid_minutes: number };
const state = ref<"waiting" | "received" | "expired">("waiting");
const code = ref<Code | null>(null);
const copied = ref(false);
// La boîte jobA1 a raté ses 3 dernières lectures (décision de Kevin du 15.11, 19 h 02) : la ligne d'attente le dit, et
// la relance part à chaque relecture pour revenir à l'attente dès qu'une lecture réussit.
const down = ref(false);
// Début de l'attente, dernier code déjà vu (seul un code plus récent compte), minuteurs.
let since = 0;
let seen = "";
let timer = 0;
let expiry = 0;
let asked = 0;
const ends = (c: Code): number => Date.parse(c.received_at) + c.valid_minutes * 60_000;

function stop(next: "waiting" | "received" | "expired"): void {
  clearInterval(timer);
  state.value = next;
}

async function watch(): Promise<void> {
  try {
    down.value = !!(await api.POST("/api/alert-searches/watch-code"))?.data?.mailbox_down;
  } catch {
    // Hors ligne : la ligne reste telle quelle, la relecture suivante réessaie.
  }
}

async function tick(): Promise<void> {
  if (Date.now() - since >= 10 * 60_000) return stop("expired");
  if (document.visibilityState !== "visible") return;
  // La relance du relevé rapide côté serveur, une fois par minute au plus (à chaque relecture si la boîte est muette).
  if (down.value || Date.now() - asked >= 60_000) {
    asked = Date.now();
    void watch();
  }
  const { data } = await api.GET("/api/alert-searches/codes/last", { params: { query: { site: "jobup" } } });
  if (state.value !== "waiting" || !data || data.received_at === seen) return;
  seen = data.received_at;
  if (!(ends(data) > Date.now())) return;
  code.value = data;
  stop("received");
  expiry = window.setTimeout(() => (state.value = "expired"), ends(data) - Date.now());
}

function wait(): void {
  clearTimeout(expiry);
  stop("waiting");
  since = Date.now();
  timer = window.setInterval(tick, 5000);
  void tick();
}

const onVisible = (): void => void (state.value === "waiting" && tick());

function copy(): void {
  void navigator.clipboard?.writeText(code.value?.code ?? "").then(() => {
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  }, () => undefined);
}

onMounted(() => {
  document.addEventListener("visibilitychange", onVisible);
  wait();
});
onUnmounted(() => {
  document.removeEventListener("visibilitychange", onVisible);
  stop(state.value);
  clearTimeout(expiry);
});

// « Ouvrir jobup » ou « Renvoyer » : l'écran attend le nouveau code, et la boîte est relevée vite dès maintenant.
defineExpose({ restart: wait });
</script>

<template>
  <div
    class="code-box"
    :class="state"
    role="status"
    aria-live="polite"
    data-test="code-box"
  >
    <template v-if="state === 'waiting' && down">
      <AppIcon
        name="alert"
        class="code-box-down"
      />
      <span data-test="code-box-down">La boîte jobA1 ne répond pas. On réessaie dans 1 minute.</span>
    </template>
    <template v-else-if="state === 'waiting'">
      <svg
        class="code-box-spinner"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        aria-hidden="true"
      ><circle
        class="code-box-track"
        cx="12"
        cy="12"
        r="9"
        fill="none"
        stroke-width="3"
      /><path
        class="code-box-arc"
        d="M12 3a9 9 0 0 1 9 9"
        fill="none"
        stroke-width="3"
        stroke-linecap="round"
      /></svg>
      En attente du code de jobup…
    </template>
    <template v-else-if="state === 'received' && code">
      <span
        class="code-box-value"
        data-test="code-box-value"
      >{{ code.code.replace(/^(\d{3})(\d{3})$/, "$1 $2") }}</span>
      <button
        type="button"
        class="code-box-copy"
        aria-label="Copier le code"
        data-test="code-box-copy"
        @click="copy"
      >
        <AppIcon :name="copied ? 'tick' : 'copy'" />{{ copied ? "Copié" : "Copier" }}
      </button>
    </template>
    <template v-else>
      <svg
        class="code-box-bang"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.2"
        stroke-linecap="round"
        aria-hidden="true"
      ><circle
        cx="12"
        cy="12"
        r="9"
      /><path d="M12 7v5M12 16v.5" /></svg>
      <span class="code-box-expired">Code expiré</span>
      <a
        v-if="props.siteUrl"
        :href="props.siteUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="code-box-resend"
        aria-label="Renvoyer le code depuis jobup"
        data-test="code-box-resend"
        @click="wait"
      >Renvoyer<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
    </template>
  </div>
  <span
    v-if="state === 'received' && code"
    class="code-box-received"
    data-test="code-box-received"
  ><AppIcon name="tick" />Reçu à {{ timeOfDay(code.received_at) }} · valable {{ code.valid_minutes }} minutes</span>
</template>

<style>
/* Valeurs du HTML des planches OnboardingOrdinateurAlerteCode… (section 15), couleurs en jetons. L'état expiré reprend
   --peach-soft / --peach-text (les valeurs claires de la planche, décision de Kevin : réutiliser un jeton existant). */
.code-box { --code-5: 5px; --code-6: 6px; --code-56: 56px; --code-26: 26px; --code-32: 32px; --code-radius: 16px; display: flex; align-items: center; gap: var(--space-3); min-height: var(--code-56); box-sizing: border-box; border-radius: var(--code-radius); font-size: var(--font-label); }
.code-box.waiting { padding: 0 var(--space-5); border: 1.5px dashed var(--card-line); color: var(--text-secondary); }
.code-box.received { padding: 0 var(--code-5) 0 var(--space-5); background: var(--surface); border: 1.5px solid var(--primary-graphic); }
.code-box.expired { padding: var(--code-6) var(--code-5) var(--code-6) var(--space-4); background: var(--peach-soft); color: var(--peach-text); }
.code-box-spinner { flex: none; animation: offer-reading-turn 900ms linear infinite; }
.code-box-track { stroke: var(--line); }
.code-box-arc { stroke: var(--primary); }
.code-box-bang { flex: none; }
.code-box-down { flex: none; width: 20px; height: 20px; color: var(--orange); }
.code-box-value { flex: 1; min-width: 0; font-size: var(--code-26); line-height: var(--code-32); font-weight: var(--weight-heavy); letter-spacing: .14em; font-variant-numeric: tabular-nums; color: var(--text); }
.code-box-copy, .code-box-resend { flex: none; display: inline-flex; align-items: center; gap: var(--code-6); height: var(--target-min); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill); font-family: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.code-box-copy { background: var(--primary-soft); }
.code-box-resend { background: var(--surface); }
.code-box-copy .icon { width: 18px; height: 18px; }
.code-box-expired { flex: 1; min-width: 0; line-height: var(--space-5); font-weight: var(--weight-bold); white-space: nowrap; }
.code-box-received { --code-6: 6px; --code-10: 10px; --code-18: 18px; display: inline-flex; align-items: center; gap: var(--code-6); margin-top: var(--code-10); padding: var(--space-1) var(--code-10); border-radius: var(--radius-pill); background: var(--success-soft); color: var(--success); font-size: calc(var(--font-caption) + 1px); line-height: var(--code-18); font-weight: var(--weight-semibold); }
.code-box-received .icon { width: 14px; height: 14px; stroke-width: 2.8; }
@media (prefers-reduced-motion: reduce) { .code-box-spinner { animation: none; } }
</style>
