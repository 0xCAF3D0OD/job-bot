<script lang="ts">
import { SCENES, sceneFile, type Scene } from "../troupe";

// Les trois scènes sont chargées d'avance au premier moment libre et gardées en mémoire : pendant la
// maintenance, le serveur ne répond peut-être plus ; hors ligne, plus rien n'arrive (docs/80 §2). Dans
// l'apparence du moment (Réglages, ou le système en Auto), à la taille de l'écran.
const held: HTMLImageElement[] = [];
const idle = globalThis.requestIdleCallback ?? ((run: () => void) => setTimeout(run, 1500));
if (typeof Image !== "undefined") {
  idle(() => {
    const root = document.documentElement.dataset.theme;
    const dark = root === "dark" || (root !== "light" && !!globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches);
    const wide = !!globalThis.matchMedia?.("(min-width: 1024px)").matches;
    for (const scene of ["hors-ligne", "maintenance", "mise-a-jour"] as Scene[]) {
      const img = new Image();
      img.src = sceneFile(scene, wide ? SCENES[scene].desk : SCENES[scene].phone, dark);
      held.push(img);
    }
  });
}
</script>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import BrandMark from "./BrandMark.vue";
import TroupeScene from "./TroupeScene.vue";
import { usePhone } from "../composables/usePhone";

// La page d'attente (docs/79) : par-dessus tout, sans recharger ; le reste de l'écran est
// inerte tant qu'elle est là, et retrouvé tel quel ensuite. Mise en page (maquettes MaintenanceMaj,
// MaintenanceAnnoncee et MaintenanceHorsLigne, scènes du 9 novembre, §15) : les 4 personnages du logo, 340 px sur
// téléphone ; « mise-a-jour » pour la mise à jour, « maintenance » pour la maintenance annoncée, « hors-ligne »
// (l'équipe rebranche la prise) quand le réseau manque ; un titre
// selon le cas, ce qui se passe, puis en bas le prochain essai et « Réessayer maintenant ».
// Trois cas : hors ligne (le navigateur le sait), une maintenance annoncée avec son message, sinon
// une mise à jour.
const props = defineProps<{ waiting: boolean; message: string | null; nextAt?: number | null }>();
// Ordinateur dès 1 024 px (maquettes du 8 novembre, MaintenanceOrdinateur et HorsLigneOrdinateur) : le logo seul en
// haut, la scène (409 px pour la mise à jour, 612 hors ligne), le titre de 34, le prochain essai en toutes lettres et le bouton plein dessous.
const { phone: wide } = usePhone("(min-width: 1024px)");
const emit = defineEmits<{ retry: [] }>();
const panel = ref<HTMLElement | null>(null);
const now = ref(Date.now());
const retrying = ref(false);
let clock: ReturnType<typeof setInterval> | undefined;
const offline = ref(globalThis.navigator?.onLine === false);
const network = () => (offline.value = globalThis.navigator?.onLine === false);
onMounted(() => {
  globalThis.addEventListener?.("online", network);
  globalThis.addEventListener?.("offline", network);
});
onUnmounted(() => {
  globalThis.removeEventListener?.("online", network);
  globalThis.removeEventListener?.("offline", network);
});
const scene = computed<Scene>(() => {
  if (offline.value) return "hors-ligne";
  return props.message ? "maintenance" : "mise-a-jour";
});
const title = computed(() => {
  if (offline.value) return "Pas de connexion";
  return props.message ? "Maintenance en cours" : "jobA1 se met à jour";
});
const line = computed(() => {
  if (offline.value) {
    return wide.value
      ? "Vérifie le Wi‑Fi ou le câble réseau. Ce que tu écrivais est gardé."
      : "Vérifie le Wi‑Fi ou les données mobiles. Ce que tu écrivais est gardé.";
  }
  return props.message || "Ça revient dans un instant. Ce que tu écrivais est gardé.";
});

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
  const left = Math.max(1, seconds.value);
  return wide.value ? `Nouvel essai automatique dans ${left} ${left > 1 ? "secondes" : "seconde"}` : `Nouvel essai dans ${left} s`;
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
      <header
        v-if="wide"
        class="maintenance-brand"
      >
        <BrandMark :size="30" />
        <span>jobA1</span>
      </header>
      <div class="maintenance-body">
        <TroupeScene
          :scene="scene"
          full
          class="maintenance-person"
          data-test="maintenance-person"
        />
        <h1 id="maintenance-title">
          {{ title }}
        </h1>
        <p
          class="maintenance-message"
          aria-live="polite"
        >
          {{ line }}
        </p>
      </div>
      <div class="maintenance-status">
        <p
          class="maintenance-next"
          data-test="maintenance-next"
        >
          {{ status }}
        </p>
        <button
          type="button"
          class="maintenance-retry"
          :disabled="retrying"
          data-test="maintenance-retry"
          @click="retry"
        >
          Réessayer maintenant
        </button>
      </div>
    </div>
  </Teleport>
</template>
