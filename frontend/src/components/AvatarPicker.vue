<script setup lang="ts">
import { ref, watch } from "vue";

import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import ProfileImage from "./ProfileImage.vue";
import { AVATARS, cropPhoto, useProfileImage, type ImageChoice } from "../composables/useProfileImage";
import { usePhone } from "../composables/usePhone";

// La fenêtre « Ton image » (maquette du 8 novembre : ProfilOrdinateur état pick, CompteImage) : une grille
// (initiales, 8 avatars, photo), aria-pressed et anneau bleu de 3 px sur le choix ; Annuler ou Enregistrer. Feuille du
// bas sur téléphone, fenêtre au centre sur ordinateur (BottomSheet). La photo reste dans le navigateur (docs/143 §6).
const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const { choice, initials, save } = useProfileImage();
const { phone } = usePhone();
const pending = ref<ImageChoice>(choice.value);
const photoSrc = ref<string | null>(choice.value.kind === "photo" ? choice.value.src : null);
const error = ref("");
const saving = ref(false);
const input = ref<HTMLInputElement | null>(null);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    pending.value = choice.value;
    photoSrc.value = choice.value.kind === "photo" ? choice.value.src : null;
    error.value = "";
  },
);

function key(value: ImageChoice): string {
  return value.kind === "avatar" ? `avatar-${value.avatar}` : value.kind;
}

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0];
  (event.target as HTMLInputElement).value = "";
  if (!file) return;
  try {
    photoSrc.value = await cropPhoto(file);
    pending.value = { kind: "photo", src: photoSrc.value };
    error.value = "";
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : "Impossible de lire cette image.";
  }
}

function pickPhoto(): void {
  if (photoSrc.value) pending.value = { kind: "photo", src: photoSrc.value };
  else input.value?.click();
}

async function confirm(): Promise<void> {
  saving.value = true;
  try {
    await save(pending.value);
    emit("close");
  } catch {
    error.value = "L’image n’a pas pu être enregistrée. Réessaie.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Ton image"
    subtitle="Elle s’affiche seulement dans jobA1. Elle n’est jamais envoyée aux employeurs."
    @close="emit('close')"
  >
    <ul
      class="avatar-grid"
      aria-label="Images"
      data-test="avatar-grid"
    >
      <li>
        <button
          type="button"
          class="avatar-option"
          :aria-pressed="key(pending) === 'initials'"
          data-test="avatar-initials"
          @click="pending = { kind: 'initials' }"
        >
          <ProfileImage
            :choice="{ kind: 'initials' }"
            :initials="initials"
            :size="64"
          />
          <span>Initiales</span>
        </button>
      </li>
      <li
        v-for="(name, index) in AVATARS"
        :key="name"
      >
        <button
          type="button"
          class="avatar-option"
          :aria-pressed="key(pending) === `avatar-${index + 1}`"
          :data-test="`avatar-${index + 1}`"
          @click="pending = { kind: 'avatar', avatar: index + 1 }"
        >
          <ProfileImage
            :choice="{ kind: 'avatar', avatar: index + 1 }"
            :initials="initials"
            :size="64"
          />
          <span>{{ name }}</span>
        </button>
      </li>
      <li>
        <button
          type="button"
          class="avatar-option"
          :aria-pressed="key(pending) === 'photo'"
          data-test="avatar-photo"
          @click="pickPhoto"
        >
          <ProfileImage
            v-if="photoSrc"
            :choice="{ kind: 'photo', src: photoSrc }"
            :initials="initials"
            :size="64"
          />
          <span
            v-else
            class="avatar-upload"
            aria-hidden="true"
          ><AppIcon name="upload" /></span>
          <span>Ma photo</span>
        </button>
        <input
          ref="input"
          type="file"
          accept="image/jpeg,image/png"
          class="visually-hidden"
          tabindex="-1"
          aria-hidden="true"
          data-test="avatar-file"
          @change="onFile"
        >
      </li>
    </ul>
    <p
      v-if="!phone"
      class="avatar-hint"
    >
      Photo : JPG ou PNG, 5 Mo maximum. Elle est recadrée en cercle, au centre.
    </p>
    <p
      v-if="error"
      class="field-error"
      role="alert"
    >
      {{ error }}
    </p>
    <template #actions>
      <button
        v-if="!phone"
        type="button"
        class="secondary"
        data-test="avatar-cancel"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="primary"
        :aria-disabled="saving ? 'true' : undefined"
        data-test="avatar-save"
        @click="!saving && confirm()"
      >
        {{ saving ? "Enregistrement…" : "Enregistrer" }}
      </button>
    </template>
  </BottomSheet>
</template>
