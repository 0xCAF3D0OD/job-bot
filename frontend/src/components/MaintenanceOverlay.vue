<script lang="ts">
import { KIT } from "../personnage";

// Adresses écrites en clair : la page d'attente est dans le premier écran, sans la table des poses.
const cables = `/personnage/perso-09-cables-400.webp?v=${KIT}`;
const CABLES_SRCSET = `${cables} 1x, /personnage/perso-09-cables-800.webp?v=${KIT} 2x`;
// Le personnage est chargé d'avance au premier moment libre et gardé en mémoire : pendant la
// maintenance, le serveur ne répond peut-être plus (docs/80 §2).
let held: HTMLImageElement | null = null;
const idle = globalThis.requestIdleCallback ?? ((run: () => void) => setTimeout(run, 1500));
if (typeof Image !== "undefined") {
  idle(() => {
    held = new Image();
    held.srcset = CABLES_SRCSET;
    held.src = cables;
  });
}
</script>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

// La page d'attente (docs/79) : par-dessus tout, sans recharger ; le reste de l'écran est
// inerte tant qu'elle est là, et retrouvé tel quel ensuite. Mise en page (maquettes MaintenanceMaj,
// MaintenanceAnnoncee et MaintenanceHorsLigne du 2026-11-05) : le personnage aux câbles du kit, un titre
// selon le cas, ce qui se passe, puis en bas le prochain essai et « Réessayer maintenant ».
// Trois cas : hors ligne (le navigateur le sait), une maintenance annoncée avec son message, sinon
// une mise à jour.
const props = defineProps<{ waiting: boolean; message: string | null; nextAt?: number | null }>();
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
const title = computed(() => {
  if (offline.value) return "Pas de connexion";
  return props.message ? "Maintenance en cours" : "jobA1 se met à jour";
});
const line = computed(() => {
  if (offline.value) return "Vérifie le Wi‑Fi ou les données mobiles. Ce que tu écrivais est gardé.";
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
  return `Nouvel essai dans ${Math.max(1, seconds.value)} s`;
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
      <div class="maintenance-body">
        <img
          class="maintenance-person"
          :src="cables"
          :srcset="CABLES_SRCSET"
          alt=""
          aria-hidden="true"
          width="203"
          height="400"
          data-test="maintenance-person"
        >
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
