<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Coordonnées pour l'en-tête des lettres, du CV et du formulaire ORP : base locale seulement,
// jamais envoyées à l'IA.
// Les cinq derniers servent aux formulaires en ligne des employeurs (docs/25), facultatifs.
const IDENTITY_FIELDS = [
  "name", "street", "postcode", "city", "phone", "email",
  "linkedin", "website", "availability", "salary", "permit",
] as const;
type IdentityForm = Record<(typeof IDENTITY_FIELDS)[number], string>;
const identity = ref<IdentityForm>(Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, ""])) as IdentityForm);
const formFilled = computed(() =>
  (["linkedin", "website", "availability", "salary", "permit"] as const).filter((f) => identity.value[f].trim()).length,
);
const identityMessage = ref("");

async function saveIdentity(): Promise<void> {
  const body = Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, identity.value[f].trim() || null]));
  try {
    const { data, response } = await api.PUT("/api/identity", { body });
    if (data) identityMessage.value = "Coordonnées enregistrées.";
    else if (response.status === 404) identityMessage.value = "La plateforme n'est pas à jour : redémarre-la.";
    else identityMessage.value = "Enregistrement refusé : vérifie le NPA (quatre chiffres) et les adresses web.";
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
      <details
        class="identity-more"
        data-test="identity-more"
      >
        <summary>
          Pour les formulaires en ligne
          <span class="muted">· facultatif{{ formFilled ? ` · ${formFilled} / 5` : "" }}</span>
        </summary>
        <div class="form-grid">
          <label>LinkedIn
            <input
              v-model="identity.linkedin"
              type="text"
              inputmode="url"
              placeholder="linkedin.com/in/…"
              data-test="identity-linkedin"
            >
          </label>
          <label>Site personnel
            <input
              v-model="identity.website"
              type="text"
              inputmode="url"
              placeholder="facultatif"
            >
          </label>
          <label>Disponibilité
            <input
              v-model="identity.availability"
              type="text"
              placeholder="dès le 1er novembre, 1 mois de préavis…"
            >
          </label>
          <label>Prétentions salariales
            <input
              v-model="identity.salary"
              type="text"
              placeholder="CHF 90'000 par an"
            >
          </label>
          <label>Permis de travail
            <input
              v-model="identity.permit"
              type="text"
              list="identity-permits"
              placeholder="Suisse, permis C, B…"
            >
          </label>
          <datalist id="identity-permits">
            <option value="Nationalité suisse" />
            <option value="Permis C" />
            <option value="Permis B" />
            <option value="Permis G (frontalier)" />
          </datalist>
        </div>
      </details>
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
