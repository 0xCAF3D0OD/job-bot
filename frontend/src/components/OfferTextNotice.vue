<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import Composer from "./Composer.vue";

// Note provisoire (offre venue d'une alerte, extrait seulement), maquette OffreProvisoire (6.11.2026) : une bande
// pêche en pleine largeur dans la carte de la note, entre les points forts et « Le détail de la note ». Lire
// l'annonce par son lien, ou coller son texte. Le serveur respecte le robots.txt du site et ne contourne aucune
// connexion. Le contenu de la bande change d'un état à l'autre (rien ne s'empile) : lecture, refus du site (« Coller
// le texte » seul, en pleine largeur, et le lien pour ouvrir l'annonce), pas de lien lisible (« Coller le texte » seul).
// Maquette du 8 novembre (D25) : la feuille « Coller le texte » prend le Composer de 5 lignes ; Envoyer = « Enregistrer
// et refaire la note », désactivé sous 200 caractères ; le compteur sous la zone. Pas de + : aucun fichier ne part à
// l'IA sans règle (I-1, E-5).
// Le texte enregistré, l'offre est renotée et la fiche rechargée : la bande disparaît (`changed`).
const props = defineProps<{ offer: Offer }>();
const emit = defineEmits<{ changed: [] }>();

const MIN_TEXT = 200;
// Le lien d'un texte collé à l'ajout n'est pas une page à lire (manual_offers.NO_LINK).
const NO_LINK = "https://annonce-collee.invalid/";
const readable = computed(() =>
  props.offer.employer_url?.startsWith("https://")
    ? props.offer.employer_url
    : props.offer.links.find((l) => l.url.startsWith("https://") && !l.url.startsWith(NO_LINK))?.url,
);

const reading = ref(false);
// Le site refuse la lecture (robots.txt, connexion, page sans annonce) : le serveur propose de coller (`paste`).
const refused = ref(false);
// Un autre empêchement (trop de lectures, IA indisponible) : la phrase de la bande le dit.
const problem = ref("");
async function readNow(): Promise<void> {
  if (reading.value) return;
  reading.value = true;
  problem.value = "";
  try {
    const { data, error } = await api.POST("/api/offers/{offer_id}/read", { params: { path: { offer_id: props.offer.id } } });
    if (data?.saved) {
      emit("changed");
      return;
    }
    if (data?.paste) {
      refused.value = true;
      return;
    }
    // Trop de lectures (429) : le serveur dit quand réessayer (« Réessaie dans 5 minutes. »).
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    problem.value = data?.problem ?? (typeof detail === "string" ? detail : "Lecture impossible : colle le texte de l'annonce.");
  } catch {
    problem.value = "API injoignable : réessaie dans un moment.";
  } finally {
    reading.value = false;
  }
}
const title = computed(() => (refused.value ? "Ce site bloque la lecture automatique" : "Il manque l’annonce complète"));
const sentence = computed(() => {
  if (reading.value) return "Lecture de l’annonce…";
  if (refused.value) return "Copie le texte de l’annonce et colle-le ici : la note sera refaite tout de suite.";
  return problem.value || "Pour une note sûre, jobA1 doit lire le texte entier de l’annonce.";
});
const canRead = computed(() => !!readable.value && !refused.value);

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
    problem.value = "";
    refused.value = false;
    pasting.value = false;
    text.value = "";
  },
);
</script>

<template>
  <div
    class="offer-text-band"
    role="group"
    aria-labelledby="offer-text-title"
    data-test="partial-notice"
  >
    <div>
      <span class="offer-text-icon"><AppIcon name="file" /></span>
      <div>
        <h4
          id="offer-text-title"
          data-test="partial-title"
        >
          {{ title }}
        </h4>
        <p
          aria-live="polite"
          data-test="partial-text"
        >
          {{ sentence }}
        </p>
      </div>
    </div>
    <div class="offer-text-actions">
      <button
        v-if="canRead"
        type="button"
        :aria-disabled="reading ? 'true' : undefined"
        data-test="read-offer-text"
        @click="readNow"
      >
        {{ reading ? "Lecture…" : "Lire l’annonce" }}
      </button>
      <button
        type="button"
        data-test="paste-offer-text"
        @click="openPaste"
      >
        Coller le texte
      </button>
    </div>
    <a
      v-if="refused && readable"
      :href="readable"
      target="_blank"
      rel="noopener noreferrer"
      class="offer-text-open"
      data-test="open-offer"
    >Ouvrir l’annonce pour la copier<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
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
  </div>
</template>
