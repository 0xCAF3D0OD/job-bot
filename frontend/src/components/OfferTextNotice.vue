<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import Composer from "./Composer.vue";

// Annonce complète lue automatiquement (prompt du 10 novembre, PR 13 ; maquettes OffreProvisoire et
// CandidaturesOrdinateurB) : l'utilisateur ne va plus chercher le texte lui-même. Une offre venue d'une alerte est lue
// en arrière-plan ; la carte de la note montre où en est la lecture, sans bouton :
// - `reading` : « jobA1 lit l'annonce complète… » avec un petit indicateur (role="status", aria-live="polite") ;
// - `refused` (le site bloque, connexion obligatoire, annonce retirée, pas de lien) : « jobA1 n'a pas pu lire
//   l'annonce », « Coller le texte » en tonal (la feuille de collage) et le lien « Ouvrir l'annonce ».
// Plus de « Lire l'annonce » ni de bande « Il manque l'annonce complète ». `done` est montré par la fiche (« Note
// refaite sur l'annonce complète. »). Si la fiche s'ouvre avant la tâche de fond, la lecture est demandée tout de suite
// (une fois par offre) ; si le site est lent, jobA1 réessaie une fois de lui-même et la fiche se recharge un moment.
const props = defineProps<{ offer: Offer }>();
// `changed` : le texte est enregistré, ou la lecture a abouti ; `refresh` : relire l'offre (la lecture continue).
const emit = defineEmits<{ changed: []; refresh: [] }>();

const MIN_TEXT = 200;
// Le lien d'un texte collé à l'ajout n'est pas une page à lire (manual_offers.NO_LINK).
const NO_LINK = "https://annonce-collee.invalid/";
const readable = computed(() =>
  props.offer.employer_url?.startsWith("https://")
    ? props.offer.employer_url
    : props.offer.links.find((l) => l.url.startsWith("https://") && !l.url.startsWith(NO_LINK))?.url,
);

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
onBeforeUnmount(() => clearTimeout(timer));

const pasting = ref(false);
const text = ref("");
const error = ref("");
const saving = ref(false);
const length = computed(() => text.value.trim().length);
function openPaste(): void {
  error.value = "";
  pasting.value = true;
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
    <div>
      <h4
        id="offer-text-title"
        data-test="refused-title"
      >
        jobA1 n’a pas pu lire l’annonce
      </h4>
      <p data-test="refused-text">
        Ce site bloque la lecture automatique. Colle le texte : la note sera refaite tout de suite.
      </p>
    </div>
    <div class="offer-text-actions">
      <button
        type="button"
        data-test="paste-offer-text"
        @click="openPaste"
      >
        Coller le texte
      </button>
      <a
        v-if="readable"
        :href="readable"
        target="_blank"
        rel="noopener noreferrer"
        class="offer-text-open"
        data-test="open-offer"
      >Ouvrir l’annonce<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
    </div>
  </div>
  <BottomSheet
    :open="pasting"
    title="Coller le texte de l’annonce"
    data-test="paste-sheet"
    @close="pasting = false"
  >
    <p class="hint">
      Ouvre l’annonce, sélectionne tout le texte, copie-le et colle-le ici. jobA1 refait la note tout de suite.
    </p>
    <Composer
      v-model="text"
      placeholder="Colle ici le texte de l’annonce"
      :rows="5"
      :min-chars="MIN_TEXT"
      send-label="Enregistrer et refaire la note"
      :busy="saving"
      counter-hint="la flèche enregistre et refait la note"
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
