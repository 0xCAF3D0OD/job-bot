<script setup lang="ts">
import { ref, watch } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import BottomSheet from "./BottomSheet.vue";
import FormField from "./FormField.vue";
import { useProfiles } from "../composables/useProfiles";

// « Modifier » de l'en-tête du Profil ordinateur (PR 9b, décision de Kevin du 10 novembre) : le nom, le poste et le
// lieu, rien d'autre ; les coordonnées complètes restent dans « Mon parcours › Coordonnées ». Le poste est celui du
// profil de recherche choisi ; le lieu, le NPA et la localité des coordonnées (le NPA donne le canton de l'ORP).
type Identity = components["schemas"]["Identity"];

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: []; saved: [] }>();
const profiles = useProfiles();

const identity = ref<Identity | null>(null);
const name = ref("");
const occupation = ref("");
const postcode = ref("");
const city = ref("");
const error = ref("");
const saving = ref(false);

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    error.value = "";
    const [who] = await Promise.all([api.GET("/api/identity"), profiles.list.value ? Promise.resolve() : profiles.load()]);
    identity.value = who.data ?? null;
    name.value = who.data?.name ?? "";
    postcode.value = who.data?.postcode ?? "";
    city.value = who.data?.city ?? "";
    occupation.value = profiles.current.value?.occupation ?? "";
  },
  { immediate: true },
);

async function save(): Promise<void> {
  if (saving.value) return;
  if (postcode.value.trim() && !/^\d{4}$/.test(postcode.value.trim())) {
    error.value = "Le NPA a quatre chiffres.";
    return;
  }
  saving.value = true;
  error.value = "";
  try {
    // Les autres coordonnées sont renvoyées telles quelles : « Modifier » ne change que ces trois champs.
    const body = {
      ...(identity.value ?? {}),
      name: name.value.trim() || null,
      postcode: postcode.value.trim() || null,
      city: city.value.trim() || null,
    } as Identity;
    const saved = await api.PUT("/api/identity", { body });
    const profile = profiles.current.value;
    const wanted = occupation.value.trim();
    let profileOk = true;
    if (profile && wanted !== (profile.occupation ?? "")) {
      const { data } = await api.PATCH("/api/profiles/{profile_id}", { params: { path: { profile_id: profile.id } }, body: { occupation: wanted || null } });
      profileOk = !!data;
      if (data) await profiles.load();
    }
    if (!saved.data || !profileOk) {
      error.value = "Enregistrement refusé : vérifie les champs et réessaie.";
      return;
    }
    emit("saved");
    emit("close");
  } catch {
    error.value = "API injoignable : réessaie dans un moment.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Modifier le profil"
    subtitle="Ton nom, le poste que tu cherches et ton lieu."
    @close="emit('close')"
  >
    <form
      id="profile-edit-form"
      class="profile-edit-form"
      data-test="profile-edit-form"
      @submit.prevent="save"
    >
      <FormField
        v-slot="{ id }"
        label="Nom"
      >
        <input
          :id="id"
          v-model="name"
          type="text"
          autocomplete="name"
          data-test="profile-edit-name"
        >
      </FormField>
      <FormField
        v-slot="{ id }"
        label="Poste"
      >
        <input
          :id="id"
          v-model="occupation"
          type="text"
          placeholder="Ex.&#8239;: Junior DevOps"
          data-test="profile-edit-occupation"
        >
      </FormField>
      <div class="profile-edit-place">
        <FormField
          v-slot="{ id }"
          label="NPA"
        >
          <input
            :id="id"
            v-model="postcode"
            type="text"
            inputmode="numeric"
            maxlength="4"
            autocomplete="postal-code"
            data-test="profile-edit-postcode"
          >
        </FormField>
        <FormField
          v-slot="{ id }"
          label="Lieu"
        >
          <input
            :id="id"
            v-model="city"
            type="text"
            autocomplete="address-level2"
            data-test="profile-edit-city"
          >
        </FormField>
      </div>
      <p
        v-if="error"
        class="notice error"
        role="alert"
        data-test="profile-edit-error"
      >
        {{ error }}
      </p>
    </form>
    <template #actions>
      <button
        type="button"
        class="secondary"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="submit"
        class="primary"
        form="profile-edit-form"
        :aria-busy="saving ? 'true' : undefined"
        data-test="profile-edit-save"
      >
        Enregistrer
      </button>
    </template>
  </BottomSheet>
</template>

<style>
.profile-edit-form { display: flex; flex-direction: column; gap: var(--space-4); }
.profile-edit-place { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 3fr); gap: var(--space-3); }
</style>
