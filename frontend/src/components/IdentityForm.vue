<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import { email, postcode, webAddress, type Check } from "../validators";
import DisclosureRow from "./DisclosureRow.vue";
import HelpTip from "./HelpTip.vue";

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

// Vérification en quittant chaque champ (docs/29 §4) ; à l'enregistrement, tout est revérifié
// et le premier champ en erreur reçoit le curseur.
const CHECKS: Partial<Record<keyof IdentityForm, Check>> = {
  postcode,
  email,
  linkedin: webAddress,
  website: webAddress,
};
const errors = ref<Partial<Record<keyof IdentityForm, string>>>({});

function check(field: keyof IdentityForm): void {
  const message = CHECKS[field]?.(identity.value[field]) ?? null;
  const next = { ...errors.value };
  if (message) next[field] = message;
  else delete next[field];
  errors.value = next;
}

function clearIfFixed(field: keyof IdentityForm): void {
  if (errors.value[field]) check(field);
}

async function saveIdentity(): Promise<void> {
  (Object.keys(CHECKS) as (keyof IdentityForm)[]).forEach(check);
  const first = (Object.keys(CHECKS) as (keyof IdentityForm)[]).find((f) => errors.value[f]);
  if (first) {
    document.getElementById(`identity-${first}`)?.focus();
    identityMessage.value = "Corrige le champ signalé.";
    return;
  }
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
      <legend>
        Mes coordonnées
        <HelpTip
          text="Gardées sur ta plateforme, jamais envoyées à l'IA."
          label="Aide : mes coordonnées"
        />
      </legend>
      <p
        v-if="missing.length"
        class="notice"
        data-test="identity-missing"
      >
        Il manque : {{ missing.join(", ") }}.
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
            id="identity-postcode"
            v-model="identity.postcode"
            type="text"
            inputmode="numeric"
            maxlength="4"
            autocomplete="postal-code"
            data-test="identity-postcode"
            :aria-invalid="Boolean(errors.postcode)"
            :aria-describedby="errors.postcode ? 'identity-postcode-error' : undefined"
            @blur="check('postcode')"
            @input="clearIfFixed('postcode')"
          >
          <span
            v-if="errors.postcode"
            id="identity-postcode-error"
            class="field-error"
            data-test="error-postcode"
          >{{ errors.postcode }}</span>
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
            id="identity-email"
            v-model="identity.email"
            type="email"
            autocomplete="email"
            :aria-invalid="Boolean(errors.email)"
            :aria-describedby="errors.email ? 'identity-email-error' : undefined"
            @blur="check('email')"
            @input="clearIfFixed('email')"
          >
          <span
            v-if="errors.email"
            id="identity-email-error"
            class="field-error"
            data-test="error-email"
          >{{ errors.email }}</span>
        </label>
      </div>
      <DisclosureRow
        class="identity-more"
        title="Pour les formulaires de candidature"
        :value="formFilled ? `facultatif · ${formFilled} / 5` : 'facultatif'"
        data-test="identity-more"
      >
        <div class="form-grid">
          <label>LinkedIn
            <input
              id="identity-linkedin"
              v-model="identity.linkedin"
              type="text"
              inputmode="url"
              placeholder="linkedin.com/in/…"
              data-test="identity-linkedin"
              :aria-invalid="Boolean(errors.linkedin)"
              :aria-describedby="errors.linkedin ? 'identity-linkedin-error' : undefined"
              @blur="check('linkedin')"
              @input="clearIfFixed('linkedin')"
            >
            <span
              v-if="errors.linkedin"
              id="identity-linkedin-error"
              class="field-error"
              data-test="error-linkedin"
            >{{ errors.linkedin }}</span>
          </label>
          <label>Site personnel
            <input
              id="identity-website"
              v-model="identity.website"
              type="text"
              inputmode="url"
              placeholder="facultatif"
              :aria-invalid="Boolean(errors.website)"
              :aria-describedby="errors.website ? 'identity-website-error' : undefined"
              @blur="check('website')"
              @input="clearIfFixed('website')"
            >
            <span
              v-if="errors.website"
              id="identity-website-error"
              class="field-error"
              data-test="error-website"
            >{{ errors.website }}</span>
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
      </DisclosureRow>
    </fieldset>
    <div class="form-actions">
      <button
        type="submit"
        class="primary"
        data-test="save-identity"
      >
        Enregistrer mes coordonnées
      </button>
      <span
        v-if="identityMessage"
        role="status"
        class="muted"
      >{{ identityMessage }}</span>
    </div>
  </form>
</template>
