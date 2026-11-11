<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import { usePhone } from "../composables/usePhone";
import { sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import Composer from "./Composer.vue";
import FormField from "./FormField.vue";

// Annonce complète lue automatiquement (prompt du 10 novembre, PR 13 ; maquettes OffreProvisoire et
// CandidaturesOrdinateurB) : l'utilisateur ne va plus chercher le texte lui-même. Une offre venue d'une alerte est lue
// en arrière-plan ; la carte de la note montre où en est la lecture, sans bouton :
// - `reading` : « jobA1 lit l'annonce complète… » avec un petit indicateur (role="status", aria-live="polite") ;
// - `refused` (le site bloque, connexion obligatoire, annonce retirée, pas de lien) : une seule ligne « Annonce
//   illisible · Indeed bloque la lecture. » et le bouton teinté « Donner l'annonce » (prompt du 10 novembre au soir,
//   PR 25). Sur téléphone, il ouvre la fenêtre du bas « Donner l'annonce à jobA1 » ; sur ordinateur, la carte se
//   déplie sur place (`aria-expanded`). On y donne le lien de l'annonce chez l'employeur, que jobA1 lit, ou on colle le
//   texte. Pas de lien vers le site ici : le seul est « Voir l'annonce sur [source] » de la fiche.
// Plus de « Lire l'annonce » ni de bande « Il manque l'annonce complète ». `done` est montré par la fiche (« Note
// refaite sur l'annonce complète. »). Si la fiche s'ouvre avant la tâche de fond, la lecture est demandée tout de suite
// (une fois par offre) ; si le site est lent, jobA1 réessaie une fois de lui-même et la fiche se recharge un moment.
const props = defineProps<{ offer: Offer }>();
// `changed` : le texte est enregistré, ou la lecture a abouti ; `refresh` : relire l'offre (la lecture continue).
const emit = defineEmits<{ changed: []; refresh: [] }>();

const MIN_TEXT = 200;

// Le serveur dit l'état ; la réponse d'une lecture demandée d'ici peut le devancer (refus).
const refusedHere = ref(false);
const state = computed(() => (refusedHere.value || props.offer.text_reading === "refused" ? "refused" : "reading"));

// La phrase de l'indicateur entre dans la région vivante après son ouverture : un lecteur d'écran l'annonce.
const announce = ref("");
const READING = "jobA1 lit l’annonce complète…";

// Une seule lecture demandée par offre et par visite de l'application ; la fiche se recharge ensuite toutes les
// 20 secondes, 6 fois au plus, le temps que la tâche de fond finisse.
const REFRESH_MS = 20_000;
const REFRESH_MAX = 6;
let refreshes = 0;
let timer: ReturnType<typeof setTimeout> | undefined;
function later(): void {
  if (refreshes >= REFRESH_MAX) return;
  clearTimeout(timer);
  timer = setTimeout(() => {
    refreshes += 1;
    emit("refresh");
  }, REFRESH_MS);
}
async function readNow(): Promise<void> {
  const id = props.offer.id;
  if (requested.has(id)) {
    later();
    return;
  }
  requested.add(id);
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/read", { params: { path: { offer_id: id } } });
    if (id !== props.offer.id) return;
    if (data?.saved) {
      emit("changed");
      return;
    }
    if (data?.paste) {
      refusedHere.value = true;
      return;
    }
  } catch {
    // API injoignable : la tâche de fond lira l'annonce ; la fiche se recharge.
  }
  later();
}
function start(): void {
  announce.value = "";
  if (state.value !== "reading") return;
  setTimeout(() => {
    announce.value = READING;
  }, 50);
  void readNow();
}
onMounted(start);
onBeforeUnmount(() => {
  clearTimeout(timer);
  clearTimeout(pasteTimer);
  window.removeEventListener("popstate", showPaste);
});

const { phone } = usePhone();

// Le nom réel du site d'où vient l'offre (« Indeed bloque la lecture. ») ; inconnu : « Ce site ».
const blocker = computed(() => {
  const link = props.offer.links.find((l) => l.source !== "manual" && !l.url.startsWith("https://annonce-collee.invalid/"));
  return `${link ? (sourceLabel[link.source] ?? "Ce site") : "Ce site"} bloque la lecture.`;
});

// « Donner l'annonce » : le lien chez l'employeur, lu par le serveur (le lien n'est pas gardé).
const giving = ref(false);
const url = ref("");
const problem = ref("");
const reading = ref(false);
const zoneId = "offer-give-zone";
const problemId = "offer-give-problem";
function toggleGive(): void {
  giving.value = !giving.value;
  problem.value = "";
}
async function readLink(): Promise<void> {
  if (reading.value) return;
  const link = url.value.trim();
  if (!/^https:\/\/\S+\.\S+$/.test(link)) {
    problem.value = "Colle un lien complet, qui commence par https://";
    return;
  }
  reading.value = true;
  problem.value = "";
  try {
    const { data, error: refused } = await api.POST("/api/offers/{offer_id}/read-link", {
      params: { path: { offer_id: props.offer.id } },
      body: { url: link },
    });
    if (data?.saved) {
      giving.value = false;
      url.value = "";
      emit("changed");
      return;
    }
    const detail = (refused as { detail?: unknown } | undefined)?.detail;
    problem.value = data?.problem ?? (typeof detail === "string" ? detail : "Cette page ne contient pas d’annonce lisible.");
  } catch {
    problem.value = "API injoignable : réessaie dans un moment.";
  } finally {
    reading.value = false;
  }
}

const pasting = ref(false);
const text = ref("");
const error = ref("");
const saving = ref(false);
const length = computed(() => text.value.trim().length);
// Sur téléphone, la fenêtre « Donner l'annonce » se ferme d'abord : elle rend son entrée d'historique (le bouton
// retour), et la fenêtre de collage ne s'ouvre qu'après, sinon ce retour la refermerait aussitôt. Sur ordinateur, la
// carte reste dépliée derrière le panneau.
let pasteTimer: ReturnType<typeof setTimeout> | undefined;
function showPaste(): void {
  clearTimeout(pasteTimer);
  window.removeEventListener("popstate", showPaste);
  pasting.value = true;
}
function openPaste(): void {
  error.value = "";
  if (!phone.value || !giving.value) {
    pasting.value = true;
    return;
  }
  giving.value = false;
  window.addEventListener("popstate", showPaste, { once: true });
  pasteTimer = setTimeout(showPaste, 300);
}
async function save(): Promise<void> {
  if (length.value < MIN_TEXT || saving.value) return;
  saving.value = true;
  error.value = "";
  try {
    const { data } = await api.PUT("/api/offers/{offer_id}/description", {
      params: { path: { offer_id: props.offer.id } },
      body: { text: text.value },
    });
    if (!data?.saved) {
      error.value = "Enregistrement impossible : vérifie le texte et réessaie.";
      return;
    }
    pasting.value = false;
    text.value = "";
    emit("changed");
  } catch {
    error.value = "API injoignable : réessaie dans un moment.";
  } finally {
    saving.value = false;
  }
}
watch(
  () => props.offer.id,
  () => {
    clearTimeout(timer);
    refreshes = 0;
    refusedHere.value = false;
    pasting.value = false;
    giving.value = false;
    url.value = "";
    problem.value = "";
    text.value = "";
    start();
  },
);
</script>

<script lang="ts">
// Les offres dont la lecture a déjà été demandée depuis une fiche (le serveur limite à une toutes les 5 minutes).
const requested = new Set<number>();
export function resetRequested(): void {
  requested.clear();
}
</script>

<template>
  <p
    v-if="state === 'reading'"
    class="offer-reading"
    role="status"
    aria-live="polite"
    data-test="text-reading"
  >
    <svg
      class="offer-reading-spinner"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke-width="2.6"
      stroke-linecap="round"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        class="offer-reading-track"
      />
      <path
        d="M12 3a9 9 0 0 1 9 9"
        class="offer-reading-arc"
      />
    </svg>
    <span>{{ announce }}</span>
  </p>
  <div
    v-else
    class="offer-text-refused"
    role="group"
    aria-labelledby="offer-text-title"
    data-test="text-refused"
  >
    <div class="offer-text-head">
      <div class="offer-text-what">
        <h4
          id="offer-text-title"
          data-test="refused-title"
        >
          Annonce illisible
        </h4>
        <p data-test="refused-text">
          {{ blocker }}
        </p>
      </div>
      <button
        v-if="phone"
        type="button"
        class="offer-give"
        aria-haspopup="dialog"
        data-test="give-offer"
        @click="toggleGive"
      >
        Donner l’annonce
      </button>
      <button
        v-else
        type="button"
        class="offer-give offer-give-fold"
        :aria-expanded="giving"
        :aria-controls="zoneId"
        data-test="give-offer"
        @click="toggleGive"
      >
        Donner l’annonce<AppIcon :name="giving ? 'chevron-up' : 'chevron-down'" />
      </button>
    </div>
    <div
      v-if="!phone"
      v-show="giving"
      :id="zoneId"
      class="offer-give-zone"
      data-test="give-zone"
    >
      <form
        class="offer-give-row"
        novalidate
        @submit.prevent="readLink"
      >
        <FormField
          v-slot="{ id, describedby }"
          label="Lien de l’annonce chez l’employeur"
          hint="Astuce : cherche le titre du poste sur le site carrière de l’entreprise."
        >
          <input
            :id="id"
            v-model="url"
            type="url"
            autocomplete="url"
            :aria-describedby="`${describedby} ${problemId}`"
            :aria-invalid="problem ? true : undefined"
            data-test="give-url"
          >
        </FormField>
        <button
          type="submit"
          class="offer-give-read"
          :aria-disabled="reading ? 'true' : undefined"
          data-test="give-read"
        >
          {{ reading ? "Lecture…" : "Lire" }}
        </button>
      </form>
      <p
        :id="problemId"
        class="offer-give-problem"
        aria-live="polite"
        data-test="give-problem"
      >
        <span
          v-if="problem"
          class="field-error"
        >{{ problem }}</span>
      </p>
      <button
        type="button"
        class="offer-give-paste"
        data-test="paste-offer-text"
        @click="openPaste"
      >
        Pas de lien ? Colle le texte
      </button>
    </div>
  </div>
  <BottomSheet
    v-if="phone"
    :open="giving"
    title="Donner l’annonce à jobA1"
    data-test="give-sheet"
    @close="giving = false"
  >
    <form
      class="offer-give-form"
      novalidate
      @submit.prevent="readLink"
    >
      <p class="offer-give-lead">
        Colle le lien de l’annonce chez l’employeur : jobA1 la lira directement.
      </p>
      <FormField
        v-slot="{ id, describedby }"
        label="Lien chez l’employeur"
        hint="Astuce : cherche le titre du poste sur le site carrière de l’entreprise."
      >
        <input
          :id="id"
          v-model="url"
          type="url"
          autocomplete="url"
          :aria-describedby="`${describedby} ${problemId}`"
          :aria-invalid="problem ? true : undefined"
          data-test="give-url"
        >
      </FormField>
      <p
        :id="problemId"
        class="offer-give-problem"
        aria-live="polite"
        data-test="give-problem"
      >
        <span
          v-if="problem"
          class="field-error"
        >{{ problem }}</span>
      </p>
      <button
        type="submit"
        class="primary offer-give-submit"
        :aria-disabled="reading ? 'true' : undefined"
        data-test="give-read"
      >
        {{ reading ? "Lecture de l’annonce…" : "Lire l’annonce" }}
      </button>
      <div
        class="offer-give-or"
        aria-hidden="true"
      >
        <span />ou<span />
      </div>
      <button
        type="button"
        class="offer-give-paste"
        data-test="paste-offer-text"
        @click="openPaste"
      >
        Coller le texte de l’annonce
      </button>
    </form>
  </BottomSheet>
  <BottomSheet
    :open="pasting"
    title="Coller le texte de l’annonce"
    data-test="paste-sheet"
    @close="pasting = false"
  >
    <p class="hint">
      Sur la page de l’annonce, sélectionne tout le texte, copie-le et colle-le ici. Tout le texte est accepté, même très long.
    </p>
    <Composer
      v-model="text"
      class="offer-paste"
      placeholder="Colle ici le texte de l’annonce"
      :rows="5"
      :min-chars="MIN_TEXT"
      send-text="Refaire la note"
      enough="assez pour noter"
      :busy="saving"
      data-test="paste-text"
      @send="save"
    />
    <p
      v-if="error"
      class="field-error"
      role="alert"
      data-test="paste-error"
    >
      {{ error }}
    </p>
  </BottomSheet>
</template>
