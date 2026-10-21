<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from "vue";

import BrandMark from "./BrandMark.vue";
import LoadingDrawing from "./LoadingDrawing.vue";

// La page d'attente (docs/79) : par-dessus tout, sans recharger ; le reste de l'écran est
// inerte tant qu'elle est là, et retrouvé tel quel ensuite. Mise en page (0.82.1) : l'en-tête
// de jobA1, puis une carte : le dessin, ce qui se passe, le prochain essai et « Réessayer
// maintenant », et la note qui rassure sur ce qui était en cours.
const props = defineProps<{ waiting: boolean; message: string | null; nextAt?: number | null }>();
const emit = defineEmits<{ retry: [] }>();
const panel = ref<HTMLElement | null>(null);
const now = ref(Date.now());
const retrying = ref(false);
let clock: ReturnType<typeof setInterval> | undefined;

function setInert(on: boolean): void {
  const app = document.getElementById("app");
  if (!app) return;
  if (on) app.setAttribute("inert", "");
  else app.removeAttribute("inert");
}

// L'élément où l'on était (la lettre en cours…) retrouve le curseur au retour (docs/81 §2).
let before: HTMLElement | null = null;

watch(
  () => props.waiting,
  async (on) => {
    if (on) before = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setInert(on);
    clearInterval(clock);
    if (on) {
      clock = setInterval(() => (now.value = Date.now()), 1000);
      await nextTick();
      panel.value?.focus();
    } else if (before?.isConnected) {
      before.focus();
      before = null;
    }
  },
  { immediate: true },
);
onUnmounted(() => clearInterval(clock));

const seconds = computed(() => (props.nextAt ? Math.max(0, Math.ceil((props.nextAt - now.value) / 1000)) : null));
const status = computed(() => {
  if (retrying.value || seconds.value === null) return "Nouvel essai en cours…";
  return seconds.value <= 1 ? "Nouvel essai dans 1 seconde" : `Nouvel essai dans ${seconds.value} secondes`;
});

async function retry(): Promise<void> {
  retrying.value = true;
  emit("retry");
  // Le bouton reste « en cours » le temps de la réponse, au moins un instant.
  setTimeout(() => (retrying.value = false), 1200);
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="waiting"
      ref="panel"
      class="maintenance"
      role="dialog"
      aria-modal="true"
      aria-labelledby="maintenance-title"
      tabindex="-1"
      data-test="maintenance"
    >
      <header class="topbar maintenance-top">
        <div class="topbar-inner">
          <span class="brand">
            <BrandMark :size="32" />
            jobA1
          </span>
        </div>
      </header>
      <div class="maintenance-body">
        <section class="maintenance-card">
          <!-- Le dessin unDraw de la maintenance : il bouge tant que l'attente dure (docs/80 §2). -->
          <div class="maintenance-drawing">
            <LoadingDrawing name="maintenance" />
          </div>
          <h1 id="maintenance-title">
            jobA1 revient dans un instant
          </h1>
          <p
            class="maintenance-message"
            aria-live="polite"
          >
            {{ message || "La plateforme se met à jour, ou la connexion est coupée." }}
          </p>
          <div class="maintenance-status">
            <span
              class="maintenance-pulse"
              aria-hidden="true"
            />
            <span
              class="maintenance-next"
              data-test="maintenance-next"
            >{{ status }}</span>
            <button
              type="button"
              class="pill"
              :disabled="retrying"
              data-test="maintenance-retry"
              @click="retry"
            >
              Réessayer maintenant
            </button>
          </div>
          <p class="maintenance-note">
            Ce que tu écrivais n'est pas perdu : tout reprend là où tu en étais.
          </p>
        </section>
      </div>
    </div>
  </Teleport>
</template>
