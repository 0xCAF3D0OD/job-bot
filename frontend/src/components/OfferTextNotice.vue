<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import BottomSheet from "./BottomSheet.vue";
import BusyButton from "./BusyButton.vue";
import FormField from "./FormField.vue";

// Note provisoire (offre venue d'une alerte, extrait seulement) : lire l'annonce par son lien, ou coller
// son texte. Le serveur respecte le robots.txt du site et ne contourne aucune connexion ; en cas d'échec,
// le message propose de coller le texte. Le texte enregistré, l'offre est renotée et la fiche rechargée.
const props = defineProps<{ offer: Offer }>();
const emit = defineEmits<{ changed: [] }>();

const MIN_TEXT = 200;
// Le lien d'un texte collé à l'ajout n'est pas une page à lire (manual_offers.NO_LINK).
const NO_LINK = "https://annonce-collee.invalid/";
const canRead = computed(
  () =>
    !!props.offer.employer_url?.startsWith("https://") ||
    props.offer.links.some((l) => l.url.startsWith("https://") && !l.url.startsWith(NO_LINK)),
);

const reading = ref(false);
const problem = ref("");
async function readNow(): Promise<void> {
  reading.value = true;
  problem.value = "";
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/read", { params: { path: { offer_id: props.offer.id } } });
    if (data?.saved) {
      emit("changed");
      return;
    }
    problem.value = data?.problem ?? "Lecture impossible : colle le texte de l'annonce.";
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
const length = computed(() => text.value.split(/\s+/).filter(Boolean).join(" ").length);
const hint = computed(() => `${MIN_TEXT} caractères au moins (${Math.min(length.value, MIN_TEXT)}/${MIN_TEXT}).`);
function openPaste(): void {
  error.value = "";
  pasting.value = true;
}
async function save(): Promise<void> {
  if (length.value < MIN_TEXT) {
    error.value = `Le texte est trop court : colle toute l'annonce (${MIN_TEXT} caractères au moins).`;
    return;
  }
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
    pasting.value = false;
    text.value = "";
  },
);
</script>

<template>
  <div
    class="notice offer-text-notice"
    data-test="partial-notice"
  >
    <p>Note provisoire : l'annonce complète n'a pas pu être lue.</p>
    <div class="offer-text-actions">
      <BusyButton
        v-if="canRead"
        class="secondary small"
        :busy="reading"
        busy-label="Lecture…"
        data-test="read-offer-text"
        @click="readNow"
      >
        Lire l'annonce maintenant
      </BusyButton>
      <button
        type="button"
        :class="canRead ? 'link' : 'secondary small'"
        data-test="paste-offer-text"
        @click="openPaste"
      >
        Coller le texte de l'annonce
      </button>
    </div>
    <p
      v-if="problem"
      class="hint offer-text-problem"
      role="alert"
      data-test="read-problem"
    >
      {{ problem }}
    </p>
    <BottomSheet
      :open="pasting"
      title="Coller le texte de l'annonce"
      data-test="paste-sheet"
      @close="pasting = false"
    >
      <FormField
        v-slot="{ id, describedby, invalid }"
        label="Texte de l'annonce"
        :hint="hint"
        :error="error"
      >
        <textarea
          :id="id"
          v-model="text"
          rows="8"
          maxlength="40000"
          :aria-describedby="describedby"
          :aria-invalid="invalid"
          data-test="paste-text"
        />
      </FormField>
      <template #actions>
        <BusyButton
          class="primary"
          :busy="saving"
          busy-label="Enregistrement…"
          data-test="paste-save"
          @click="save"
        >
          Enregistrer
        </BusyButton>
      </template>
    </BottomSheet>
  </div>
</template>
