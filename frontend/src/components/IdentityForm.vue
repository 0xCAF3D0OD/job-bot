<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Coordonnées pour l'en-tête des lettres, du CV et du formulaire ORP : base locale seulement,
// jamais envoyées à l'IA.
const IDENTITY_FIELDS = ["name", "street", "postcode", "city", "phone", "email"] as const;
type IdentityForm = Record<(typeof IDENTITY_FIELDS)[number], string>;
const identity = ref<IdentityForm>({ name: "", street: "", postcode: "", city: "", phone: "", email: "" });
const identityMessage = ref("");

async function saveIdentity(): Promise<void> {
  const body = Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, identity.value[f].trim() || null]));
  try {
    const { data, response } = await api.PUT("/api/identity", { body });
    if (data) identityMessage.value = "Coordonnées enregistrées.";
    else if (response.status === 404) identityMessage.value = "La plateforme n'est pas à jour : redémarre-la.";
    else identityMessage.value = "Enregistrement refusé : vérifie le NPA (quatre chiffres).";
  } catch {
    identityMessage.value = "API injoignable.";
  }
}

const loaded = ref(false);

// Ce qui manque pour l'en-tête des lettres et des preuves ORP (docs/21 §6).
const REQUIRED: [keyof IdentityForm, string][] = [
  ["name", "ton nom"],
  ["street", "ta rue"],
  ["postcode", "ton NPA"],
  ["city", "ta localité"],
];
const missing = computed(() => REQUIRED.filter(([key]) => !identity.value[key].trim()).map(([, label]) => label));

onMounted(async () => {
  const who = await api.GET("/api/identity");
  if (who.data) {
    const loadedIdentity = who.data;
    identity.value = Object.fromEntries(
      IDENTITY_FIELDS.map((f) => [f, loadedIdentity[f] ?? ""]),
    ) as IdentityForm;
  }
  loaded.value = true;
});
</script>

<template>
  <form
    v-if="loaded"
    class="form-card"
    data-test="identity-form"
    @submit.prevent="saveIdentity"
  >
    <fieldset>
      <legend>Mes coordonnées</legend>
      <p
        v-if="missing.length"
        class="notice"
        data-test="identity-missing"
      >
        Il manque : {{ missing.join(", ") }}.
      </p>
      <p class="hint">
        Gardées sur ta plateforme, jamais envoyées à l'IA.
      </p>
      <div class="form-grid">
        <label class="wide">Nom et prénom
          <input
            v-model="identity.name"
            type="text"
            autocomplete="name"
            data-test="identity-name"
          >
        </label>
        <label class="wide">Rue et numéro
          <input
            v-model="identity.street"
            type="text"
            autocomplete="address-line1"
            data-test="identity-street"
          >
        </label>
        <label>NPA
          <input
            v-model="identity.postcode"
            type="text"
            inputmode="numeric"
            pattern="[0-9]{4}"
            maxlength="4"
            autocomplete="postal-code"
            title="Quatre chiffres"
            data-test="identity-postcode"
          >
        </label>
        <label>Localité
          <input
            v-model="identity.city"
            type="text"
            autocomplete="address-level2"
            data-test="identity-city"
          >
        </label>
        <label>Téléphone
          <input
            v-model="identity.phone"
            type="tel"
            autocomplete="tel"
          >
        </label>
        <label>E-mail
          <input
            v-model="identity.email"
            type="email"
            autocomplete="email"
          >
        </label>
      </div>
    </fieldset>
    <div class="form-actions">
      <button
        type="submit"
        class="primary"
        data-test="save-identity"
      >
        Enregistrer mes coordonnées <AppIcon name="chevron" />
      </button>
      <span
        v-if="identityMessage"
        role="status"
        class="muted"
      >{{ identityMessage }}</span>
    </div>
  </form>
</template>
