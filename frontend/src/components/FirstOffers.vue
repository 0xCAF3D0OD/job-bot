<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { api } from "../api/client";
import { plural } from "../format";

// Les premières offres (docs/104, 0.80.0) : à la fin de l'accueil, jobA1 lit la recherche
// publique de jobup pour le métier et les lieux du compte. Sur la page Offres, une ligne dit
// ce qui se passe ; sur la page Alertes, une carte permet de relancer la recherche.
const props = defineProps<{ where: "offers" | "alerts" }>();
const emit = defineEmits<{ arrived: [] }>();

type State = { status: "none" | "queued" | "done" | "failed" | "no_trade" | "disabled"; at?: string | null; found: number; new: number; queries: string[] };
const state = ref<State | null>(null);
const message = ref("");
const busy = ref(false);
const DISMISS_KEY = "jobA1.firstOffers.dismissed";
const dismissed = ref(readDismissed());
// L'annonce « premières offres » reste trois jours sur la page Offres.
const RECENT_MS = 3 * 86_400_000;
let timer: ReturnType<typeof setTimeout> | undefined;

function readDismissed(): string | null {
  try {
    return localStorage.getItem(DISMISS_KEY);
  } catch {
    return null;
  }
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches/first-offers");
  if (!data || typeof data.status !== "string") return;
  const before = state.value?.status;
  state.value = data;
  if (before === "queued" && data.status !== "queued") emit("arrived");
  poll();
}

// En file : on regarde toutes les 8 secondes, jusqu'au résultat.
function poll(): void {
  clearTimeout(timer);
  if (state.value?.status === "queued") timer = setTimeout(() => void load(), 8000);
}

const searched = computed(() => state.value?.queries?.join(", ") ?? "");
const recent = computed(() => {
  const at = state.value?.at;
  return !!at && Date.now() - new Date(at).getTime() < RECENT_MS && dismissed.value !== at;
});
const offersLine = computed(() => {
  const s = state.value;
  if (!s) return null;
  if (s.status === "queued") return "Je cherche tes premières offres sur jobup… Elles arrivent dans une minute.";
  if (s.status === "done" && s.new > 0 && recent.value) {
    return `${plural(s.new, "première offre trouvée", "premières offres trouvées")} sur jobup (${searched.value}). Tes alertes prennent le relais dès qu'elles arrivent.`;
  }
  return null;
});
const alertsText = computed(() => {
  const s = state.value;
  if (!s || s.status === "none") return "jobA1 peut chercher tout de suite sur jobup, avec ton métier et tes lieux, sans attendre tes alertes.";
  if (s.status === "queued") return "Recherche en cours sur jobup…";
  if (s.status === "no_trade") return "Indique d'abord ton métier : c'est lui que jobA1 cherche.";
  if (s.status === "failed") return "jobup n'a pas répondu à la dernière recherche. Réessaie plus tard.";
  return `Dernière recherche (${searched.value}) : ${plural(s.found, "offre trouvée", "offres trouvées")}, dont ${plural(s.new, "nouvelle", "nouvelles")}.`;
});

async function start(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data } = await api.POST("/api/alert-searches/first-offers");
    if (!data) {
      message.value = "Recherche impossible pour l'instant.";
      return;
    }
    state.value = data;
    if (data.result === "too_soon") message.value = "Déjà cherché il y a moins d'une heure : réessaie un peu plus tard.";
    else if (data.result === "already_queued") message.value = "La recherche est déjà en route.";
    poll();
  } finally {
    busy.value = false;
  }
}

function dismiss(): void {
  const at = state.value?.at ?? "";
  dismissed.value = at;
  try {
    localStorage.setItem(DISMISS_KEY, at);
  } catch {
    // Sans stockage, la ligne revient au prochain passage : sans gravité.
  }
}

onMounted(() => void load());
onUnmounted(() => clearTimeout(timer));
</script>

<template>
  <p
    v-if="props.where === 'offers' && offersLine"
    class="notice first-offers-line"
    role="status"
    data-test="first-offers-line"
  >
    <span>{{ offersLine }}</span>
    <button
      v-if="state?.status === 'done'"
      type="button"
      class="link"
      data-test="first-offers-dismiss"
      @click="dismiss"
    >
      OK
    </button>
  </p>
  <section
    v-else-if="props.where === 'alerts' && state && state.status !== 'disabled'"
    class="first-offers"
    data-test="first-offers"
  >
    <h2 class="section-title first">
      Sans attendre tes alertes
    </h2>
    <div class="settings-card">
      <div class="first-offers-body">
        <p class="setting-desc">
          {{ alertsText }}
        </p>
        <p
          v-if="message"
          class="hint"
          role="status"
          data-test="first-offers-message"
        >
          {{ message }}
        </p>
        <button
          type="button"
          class="pill"
          :disabled="busy || state.status === 'queued'"
          data-test="first-offers-start"
          @click="start"
        >
          {{ state.status === "queued" ? "Recherche en cours…" : "Chercher sur jobup maintenant" }}
        </button>
      </div>
    </div>
  </section>
</template>
