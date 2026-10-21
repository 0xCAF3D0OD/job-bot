<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";

import { api } from "../api/client";
import { sourceLabel } from "../format";

// Les codes des sites (docs/112) : le code de vérification qu'un site envoie à l'adresse
// jobA1 de la personne, en haut de la page Alertes, 30 minutes ; et « J'attends un code »,
// qui fait relever la boîte toutes les 15 secondes pendant 5 minutes.
type SiteCode = { search_id: number; site: string; code: string; received_at: string };
const props = defineProps<{ codes: SiteCode[] }>();
const emit = defineEmits<{ refresh: [] }>();

const waiting = ref(false);
const message = ref("");
const copied = ref<number | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;
let stopAt = 0;
const WAIT_MS = 5 * 60_000;

const time = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Zurich" });
const shown = computed(() =>
  props.codes.map((c) => ({
    ...c,
    name: c.site === "unknown" ? "Un site" : sourceLabel[c.site],
    spaced: c.code.length === 6 ? `${c.code.slice(0, 3)} ${c.code.slice(3)}` : c.code,
  })),
);

function stop(): void {
  clearInterval(timer);
  timer = undefined;
  waiting.value = false;
}

async function expect(): Promise<void> {
  message.value = "";
  const { data } = await api.POST("/api/alert-searches/expect-code");
  if (!data?.queued) {
    message.value = "Déjà six relevés rapides cette heure-ci : le code arrivera au prochain relevé.";
    return;
  }
  waiting.value = true;
  stopAt = Date.now() + WAIT_MS;
  // La page se met à jour seule : un code arrivé s'affiche en haut.
  timer = setInterval(() => {
    if (Date.now() > stopAt) stop();
    else emit("refresh");
  }, 10_000);
}

// Un nouveau code est là : on arrête d'attendre.
watch(
  () => props.codes.length,
  (now, before) => {
    if (waiting.value && now > (before ?? 0)) stop();
  },
);

async function copy(code: SiteCode): Promise<void> {
  try {
    await navigator.clipboard.writeText(code.code);
    copied.value = code.search_id;
    setTimeout(() => (copied.value = null), 2000);
  } catch {
    copied.value = null;
  }
}

onUnmounted(stop);
</script>

<template>
  <section
    class="site-codes"
    data-test="site-codes"
  >
    <ul
      v-if="shown.length"
      class="site-code-list"
    >
      <li
        v-for="item in shown"
        :key="item.search_id"
        class="site-code"
        data-test="site-code"
      >
        <span class="site-code-text">
          <span class="site-code-label">Code {{ item.name }} · reçu à {{ time.format(new Date(item.received_at)) }}</span>
          <strong
            class="site-code-value"
            data-test="site-code-value"
          >{{ item.spaced }}</strong>
        </span>
        <button
          type="button"
          class="pill"
          data-test="site-code-copy"
          @click="copy(item)"
        >
          {{ copied === item.search_id ? "Copié" : "Copier le code" }}
        </button>
      </li>
    </ul>
    <p class="site-code-wait">
      <span v-if="waiting">J'attends le code : je regarde ta boîte toutes les 15 secondes, pendant 5 minutes.</span>
      <span v-else>Un site t'envoie un code de vérification ? Il s'affiche ici dès qu'il arrive.</span>
      <button
        v-if="!waiting"
        type="button"
        class="link"
        data-test="site-code-expect"
        @click="expect"
      >
        J'attends un code
      </button>
    </p>
    <p
      v-if="message"
      class="hint"
      role="status"
    >
      {{ message }}
    </p>
  </section>
</template>
