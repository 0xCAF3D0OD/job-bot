<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { useJobupCode } from "../composables/useJobupCode";
import { timeOfDay } from "../dates";
import AppIcon from "./AppIcon.vue";

// Premiers pas, « Crée ton alerte sur jobup » (section 41 du paquet du 16.11 ; planches OnboardingOrdinateurAlerte,
// …AlerteCode, …CodeRecu, …CodeExpire et OnboardingAlerteDebut, OnboardingAlerteCode… sur téléphone) : une carte, 4
// étapes, un trait entre deux étapes. L'étape en cours a sa pastille bleue numérotée (aria-current="step"), les étapes
// faites une coche verte, les suivantes une pastille grise.
// Le code de jobup s'affiche dans 6 cases en lecture seule : le serveur le reçoit dans la boîte jobA1, la personne le
// recopie sur jobup. Il n'est jamais saisi ici. Un code périmé relance l'écoute : le nouveau s'affiche tout seul.
const props = defineProps<{ desk: boolean; searchLabel: string; url: string | null; mailbox: string | null }>();
// Le code est arrivé : le bouton principal devient « J'ai validé l'alerte » (section 41).
const received = defineModel<boolean>("received", { default: false });

const { state, code, copied, down, late, restart, copy } = useJobupCode({ relisten: true });
// « Ouvrir jobup avec ma recherche » cliqué : l'étape 1 est faite, l'adresse est copiée, l'écran attend le code.
const opened = ref(false);
const addressCopied = ref(false);
const got = computed(() => state.value === "received" && !!code.value);
watch(got, (value) => (received.value = value), { immediate: true });
const digits = computed(() => (got.value ? code.value!.code.replace(/\D/g, "").padEnd(6, " ").slice(0, 6).split("") : Array(6).fill("")));

function open(): void {
  opened.value = true;
  if (state.value !== "received") restart();
  const address = props.mailbox;
  if (!address) return;
  void navigator.clipboard
    ?.writeText(address)
    .then(() => (addressCopied.value = true))
    .catch(() => undefined);
}
function copyAddress(): void {
  if (!props.mailbox) return;
  void navigator.clipboard
    ?.writeText(props.mailbox)
    .then(() => (addressCopied.value = true))
    .catch(() => undefined);
}

// L'état de chaque étape : faite, en cours ou à venir.
type Mark = "done" | "now" | "next";
const marks = computed<Mark[]>(() => {
  if (got.value) return ["done", "done", "done", "now"];
  if (opened.value || state.value === "expired") return ["done", "done", "now", "next"];
  return ["now", "next", "next", "next"];
});
</script>

<template>
  <ol
    :class="['wa', { 'wa-desk': desk }]"
    data-test="welcome-alert-steps"
  >
    <li
      v-for="(mark, i) in marks"
      :key="i"
      :class="['wa-step', mark]"
      :aria-current="mark === 'now' ? 'step' : undefined"
      :data-test="`welcome-alert-step-${i + 1}`"
    >
      <span
        class="wa-num"
        aria-hidden="true"
      ><AppIcon
        v-if="mark === 'done'"
        name="tick"
      /><template v-else>{{ i + 1 }}</template></span>
      <span class="visually-hidden">{{ mark === "done" ? "Fait : " : mark === "now" ? "En cours : " : "" }}</span>
      <div class="wa-body">
        <template v-if="i === 0">
          <b class="wa-title">Ouvre jobup et crée une alerte</b>
          <span class="wa-help">{{ mark === "done" ? `Recherche : ${searchLabel}.` : `jobA1 a préparé ta recherche : ${searchLabel}.` }}</span>
          <div
            v-if="mark === 'now' && url"
            class="wa-open-row"
          >
            <a
              :href="url"
              target="_blank"
              rel="noopener noreferrer"
              class="button-link wa-open wa-open-jobup"
              data-test="wizard-open"
              @click="open"
            ><AppIcon name="external" />Ouvrir jobup<span class="visually-hidden"> (nouvel onglet)</span></a>
            <svg
              v-if="desk"
              class="wa-laptop"
              width="110"
              height="78"
              viewBox="0 0 110 78"
              aria-hidden="true"
            ><rect
              x="16"
              y="6"
              width="78"
              height="52"
              rx="6"
              class="wa-laptop-screen"
              stroke-width="3"
            /><rect
              x="24"
              y="14"
              width="40"
              height="6"
              rx="3"
              class="wa-laptop-bar"
            /><rect
              x="24"
              y="26"
              width="58"
              height="5"
              rx="2.5"
              class="wa-laptop-line"
            /><rect
              x="24"
              y="36"
              width="48"
              height="5"
              rx="2.5"
              class="wa-laptop-line"
            /><path
              d="M6 64h98l-8 8H14z"
              class="wa-laptop-base"
            /><path
              d="M98 4l6-4M101 12l8-1"
              class="wa-laptop-spark"
              stroke-width="3"
              stroke-linecap="round"
            /></svg>
          </div>
          <a
            v-else-if="mark === 'done' && !got && url"
            :href="url"
            target="_blank"
            rel="noopener noreferrer"
            class="wa-link"
            data-test="wizard-reopen"
            @click="open"
          >Rouvrir jobup<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </template>

        <template v-else-if="i === 1">
          <b class="wa-title">Colle cette adresse dans le champ « E-mail » de l’alerte</b>
          <span class="wa-help">{{ got ? "C’est fait." : "Elle est déjà copiée quand tu ouvres jobup." }}</span>
          <div
            v-if="!got && mailbox"
            class="wa-address"
          >
            <span data-test="wizard-address">{{ mailbox }}</span>
            <button
              type="button"
              class="wa-copy"
              :aria-label="desk ? undefined : 'Copier l’adresse'"
              data-test="alert-site-copy"
              @click="copyAddress"
            >
              <AppIcon :name="addressCopied ? 'tick' : 'copy'" /><template v-if="desk">
                {{ addressCopied ? "Copiée" : "Copier" }}
              </template>
            </button>
          </div>
          <span
            class="visually-hidden"
            role="status"
          >{{ addressCopied ? "Adresse copiée" : "" }}</span>
        </template>

        <template v-else-if="i === 2">
          <b class="wa-title">{{ got ? "Code reçu" : "Le code de confirmation s’affiche ici" }}</b>
          <span class="wa-help">{{ got ? "Recopie-le sur jobup pour valider ton alerte." : "Il s’affiche ici tout seul." }}</span>
          <div class="wa-code-row">
            <div
              :class="['wa-code', { got }]"
              role="group"
              aria-label="Code de jobup"
              data-test="welcome-code"
            >
              <span
                v-for="(digit, d) in digits"
                :key="d"
              >{{ digit }}</span>
            </div>
            <button
              v-if="got"
              type="button"
              class="wa-copy wa-copy-code"
              data-test="code-box-copy"
              @click="copy"
            >
              <AppIcon :name="copied ? 'tick' : 'copy'" />{{ copied ? "Copié" : "Copier le code" }}
            </button>
          </div>
          <span
            v-if="got && code"
            class="wa-received"
            data-test="code-box-received"
          ><AppIcon name="tick" />Reçu à {{ timeOfDay(code.received_at) }} · valable {{ code.valid_minutes }} minutes</span>
          <div
            v-if="state === 'expired'"
            class="wa-status wa-bad"
            role="status"
            data-test="code-expired"
          >
            <AppIcon name="alert-circle" /><span><b>Ce code a expiré.</b> Sur jobup, demande un nouveau code : il s’affichera ici.</span>
          </div>
          <div
            v-else-if="!got && opened && down"
            class="wa-status wa-bad"
            role="status"
            data-test="code-box-down"
          >
            <AppIcon name="alert-circle" /><span>La boîte jobA1 ne répond pas. On réessaie dans 1 minute.</span>
          </div>
          <div
            v-else-if="!got && opened"
            class="wa-status"
            role="status"
            data-test="code-waiting"
          >
            <svg
              class="wa-spinner"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              aria-hidden="true"
            ><circle
              class="wa-track"
              cx="12"
              cy="12"
              r="9"
              fill="none"
              stroke-width="3"
            /><path
              class="wa-arc"
              d="M12 3a9 9 0 0 1 9 9"
              fill="none"
              stroke-width="3"
              stroke-linecap="round"
            /></svg><span><b>En attente du code de jobup.</b> Il s’affiche ici dès qu’il arrive, tu n’as rien à faire.</span>
          </div>
          <p
            v-if="!got && opened && late && !down && state !== 'expired'"
            class="wa-late"
            data-test="code-trail-late"
          >
            Toujours rien ? Vérifie que l’adresse est bien collée dans jobup.
          </p>
        </template>

        <template v-else>
          <b class="wa-title">{{ got ? "Colle le code sur jobup et valide l’alerte" : "Termine l’alerte sur jobup" }}</b>
          <span class="wa-help">Ensuite, jobA1 ajoute tes nouvelles offres ici chaque jour.</span>
        </template>
      </div>
    </li>
  </ol>
</template>

<style>
/* Valeurs des planches de la section 41 (OnboardingOrdinateurAlerte… et OnboardingAlerte…), couleurs en jetons. Sur ordinateur,
   arrondies à la grille de 4 (audit-grille) : 18 → 16, 6 → 8, 5 et 2 → 4. */
.wa { --wa-pad: 16px 14px; --wa-gap: 12px; --wa-num: 32px; --wa-num-font: 15px; --wa-title: 16px; --wa-title-lh: 22px; --wa-help: 14px;
  --wa-help-lh: 20px; --wa-box-w: 36px; --wa-box-h: 46px; --wa-box-r: 9px; --wa-box-font: 20px; --wa-box-gap: 6px; --wa-radius: 20px;
  --wa-address-h: 48px; --wa-address-pad: 1px 2px 1px 14px; --wa-address-font: 14px; --wa-copy-h: 44px; --wa-2: 2px; --wa-5: 5px; --wa-6: 6px;
  --wa-8: 8px; --wa-10: 10px; --wa-15: 15px; --wa-18: 18px;
  margin: 0; padding: 0; list-style: none; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--wa-radius); }
.wa-desk { --wa-pad: 16px; --wa-2: 4px; --wa-5: 4px; --wa-6: 8px; --wa-gap: 16px; --wa-num: 36px; --wa-num-font: 16px; --wa-title: 18px; --wa-title-lh: 24px; --wa-help: 15px;
  --wa-help-lh: 21px; --wa-box-w: 44px; --wa-box-h: 52px; --wa-box-r: 10px; --wa-box-font: 22px; --wa-box-gap: 8px; --wa-radius: 22px;
  --wa-address-h: 52px; --wa-address-pad: 0 6px 0 18px; --wa-address-font: 16px; --wa-copy-h: 40px; --wa-open-h: 52px; --wa-open-pad: 0 28px;
  margin-top: var(--space-6); padding: 0 var(--wa-6); }
.wa-step { display: flex; gap: var(--wa-gap); padding: var(--wa-pad); }
.wa-step + .wa-step { border-top: 1px solid var(--line); }
.wa-num { flex: none; display: flex; align-items: center; justify-content: center; width: var(--wa-num); height: var(--wa-num); border-radius: var(--radius-pill); background: var(--surface-muted); color: var(--text-lead); font-size: var(--wa-num-font); font-weight: var(--weight-heavy); }
.wa-step.now .wa-num { background: var(--primary); color: var(--on-primary); }
.wa-step.done .wa-num { background: var(--success); color: var(--surface); }
.wa-num .icon { width: 18px; height: 18px; stroke-width: 3; }
.wa-body { flex: 1; min-width: 0; }
.wa-title { display: block; padding-top: var(--wa-5); font-size: var(--wa-title); line-height: var(--wa-title-lh); }
.wa-help { display: block; margin-top: var(--wa-2); font-size: var(--wa-help); line-height: var(--wa-help-lh); color: var(--text-secondary); }
.wa-open-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-3); }
.wa-open.button-link { gap: var(--space-2); min-height: var(--wa-copy-h); padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--wa-15); }
.wa-desk .wa-open.button-link { min-height: var(--wa-open-h); padding: var(--wa-open-pad); font-size: var(--font-body); }
.wa-open .icon { width: 16px; height: 16px; stroke-width: 2.2; }
/* Téléphone : le bouton prend la largeur de l'étape, son texte passe sur deux lignes (OnboardingAlerteDebut). */
.wa:not(.wa-desk) .wa-open.button-link:not(.wa-open-jobup) { flex: 1; justify-content: center; padding-block: var(--wa-6); white-space: normal; text-align: center; line-height: var(--wa-18); }
/* §72h (18.11, OnboardingAlerteDebut, OnboardingOrdinateurAlerte et AlerteExt) : « Ouvrir jobup » à contour, 44 px, largeur
   au contenu, aligné à gauche ; contour 1,5 px --primary-graphic, fond --surface, texte --primary-text. Le seul bouton
   plein de l'écran reste « J'ai créé l'alerte ». */
.wa-open.wa-open-jobup { --wa-open-jobup-h: 44px; flex: none; height: var(--wa-open-jobup-h); min-height: var(--wa-open-jobup-h); padding: 0 var(--space-4); border: var(--action-line) solid var(--primary-graphic); background: var(--surface); color: var(--primary-text); font-weight: var(--weight-bold); white-space: nowrap; }
.wa-desk .wa-open.wa-open-jobup { min-height: var(--wa-open-jobup-h); padding: var(--wa-open-pad); font-size: var(--font-body); }
.wa-laptop { flex: none; }
.wa-laptop-screen { fill: var(--surface); stroke: var(--text); }
.wa-laptop-bar { fill: var(--primary-graphic); }
.wa-laptop-line { fill: var(--line-strong); }
.wa-laptop-base { fill: var(--text); }
.wa-laptop-spark { stroke: var(--orange); }
.wa-link { display: inline-flex; align-items: center; gap: var(--wa-6); min-height: var(--target-min); margin-top: var(--space-1); color: var(--primary-text); font-size: var(--wa-15); font-weight: var(--weight-bold); text-decoration: none; }
.wa-link .icon { width: 16px; height: 16px; }
.wa-address { display: flex; align-items: center; gap: var(--wa-6); min-height: var(--wa-address-h); margin-top: var(--space-3); padding: var(--wa-address-pad); box-sizing: border-box; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-pill); }
.wa-address > span { flex: 1; min-width: 0; font-size: var(--wa-address-font); line-height: var(--space-5); font-weight: var(--weight-semibold); overflow-wrap: anywhere; }
.wa-copy { flex: none; display: inline-flex; align-items: center; justify-content: center; gap: var(--wa-6); width: var(--target-min); height: var(--target-min); min-height: var(--target-min); padding: 0; border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font: inherit; font-size: var(--wa-15); font-weight: var(--weight-bold); }
.wa-desk .wa-copy { width: auto; height: var(--wa-copy-h); min-height: var(--wa-copy-h); padding: 0 var(--space-4); }
.wa-copy .icon { width: 16px; height: 16px; }
/* §72f (18.11, OnboardingAlerteCodeRecu) : « Copier le code » en bouton à contour, 1,5 px --primary-graphic, fond --surface, texte --primary-text
   (clair #2445C2, #FFFFFF, #1A3496 ; sombre #7D95FF, #221E1A, #AEBDFF). */
.wa-copy.wa-copy-code { width: auto; height: var(--target-min); min-height: var(--target-min); margin-top: var(--space-3); padding: 0 var(--space-4); }
/* Téléphone seulement : la planche ordinateur (OnboardingOrdinateurAlerteCodeRecu) garde le bouton tonal. */
.wa:not(.wa-desk) .wa-copy.wa-copy-code { border: 1.5px solid var(--primary-graphic); background: var(--surface); color: var(--primary-text); }
.wa-code-row { display: flex; flex-wrap: wrap; align-items: center; column-gap: var(--space-3); }
.wa-code { display: flex; gap: var(--wa-box-gap); margin-top: var(--space-3); }
.wa-code > span { display: flex; align-items: center; justify-content: center; box-sizing: border-box; width: var(--wa-box-w); height: var(--wa-box-h); border: 1.5px solid var(--card-line); border-radius: var(--wa-box-r); background: var(--surface); font-size: var(--wa-box-font); font-weight: var(--weight-heavy); font-variant-numeric: tabular-nums; }
.wa-code.got > span { border-color: var(--success); }
.wa-received { display: inline-flex; align-items: center; gap: var(--wa-6); margin-top: var(--wa-10); padding: var(--space-1) var(--wa-10); border-radius: var(--radius-pill); background: var(--success-soft); color: var(--success); font-size: var(--font-caption); line-height: var(--wa-18); font-weight: var(--weight-semibold); }
.wa-received .icon { width: 14px; height: 14px; stroke-width: 2.8; }
.wa-status { display: flex; align-items: flex-start; gap: var(--wa-8); margin-top: var(--space-3); font-size: var(--wa-help); line-height: var(--wa-help-lh); color: var(--text-lead); }
.wa-desk .wa-status { gap: var(--wa-10); }
.wa-status b { color: var(--text); }
.wa-status.wa-bad, .wa-status.wa-bad b { color: var(--peach-text); }
.wa-status .icon, .wa-spinner { flex: none; width: 18px; height: 18px; margin-top: var(--wa-2); }
.wa-spinner { animation: offer-reading-turn 900ms linear infinite; }
.wa-track { stroke: var(--card-line); }
.wa-arc { stroke: var(--primary-graphic); }
.wa-late { margin: var(--space-2) 0 0; font-size: var(--wa-help); line-height: var(--wa-help-lh); color: var(--text-secondary); }
@media (prefers-reduced-motion: reduce) { .wa-spinner { animation: none; } }
</style>
