<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api } from "../api/client";
import { email, postcode, webAddress, type Check } from "../validators";
import DisclosureRow from "./DisclosureRow.vue";
import FormField from "./FormField.vue";
import HoverNote from "./HoverNote.vue";
import LoadingBlocks from "./LoadingBlocks.vue";

// Coordonnées pour l'en-tête des lettres, du CV et du formulaire ORP : base locale seulement,
// jamais envoyées à l'IA.
// Les cinq derniers servent aux formulaires en ligne des employeurs (docs/25), facultatifs.
const IDENTITY_FIELDS = [
  "name", "street", "postcode", "city", "phone", "email",
  "linkedin", "website", "availability", "salary", "permit",
] as const;
type IdentityForm = Record<(typeof IDENTITY_FIELDS)[number], string>;
const blank = (): IdentityForm => Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, ""])) as IdentityForm;
const identity = ref<IdentityForm>(blank());
// Les valeurs enregistrées : « Annuler » y revient.
const saved = ref<IdentityForm>(blank());
const changed = computed(() => IDENTITY_FIELDS.some((f) => identity.value[f] !== saved.value[f]));
const formFilled = computed(() =>
  (["linkedin", "website", "availability", "salary", "permit"] as const).filter((f) => identity.value[f].trim()).length,
);
const identityMessage = ref("");
const formEl = ref<HTMLFormElement | null>(null);

// Vérification en quittant chaque champ (docs/29 §4) ; à l'enregistrement, tout est revérifié
// et le premier champ en erreur reçoit le curseur. L'erreur s'affiche sous le champ (FormField).
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

function cancel(): void {
  identity.value = { ...saved.value };
  errors.value = {};
  identityMessage.value = "";
}

async function saveIdentity(): Promise<void> {
  identityMessage.value = "";
  (Object.keys(CHECKS) as (keyof IdentityForm)[]).forEach(check);
  if (Object.keys(errors.value).length) {
    await nextTick();
    formEl.value?.querySelector<HTMLElement>("[aria-invalid=true]")?.focus();
    return;
  }
  const body = Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, identity.value[f].trim() || null]));
  try {
    const { data, response } = await api.PUT("/api/identity", { body });
    if (data) {
      identityMessage.value = "Coordonnées enregistrées.";
      saved.value = { ...identity.value };
    } else if (response.status === 404) identityMessage.value = "La plateforme n'est pas à jour : redémarre-la.";
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
  try {
    const who = await api.GET("/api/identity");
    if (who.data) {
      const loadedIdentity = who.data;
      identity.value = Object.fromEntries(
        IDENTITY_FIELDS.map((f) => [f, loadedIdentity[f] ?? ""]),
      ) as IdentityForm;
      saved.value = { ...identity.value };
    }
  } finally {
    loaded.value = true;
  }
});
</script>

<template>
  <!-- Comme les CFF (docs/110) : le titre au-dessus de la carte, ce qu'elle sert à faire dessous. -->
  <section class="identity-section">
    <h2 class="section-title">
      Coordonnées
    </h2>
    <LoadingBlocks
      v-if="!loaded"
      :heights="['30rem']"
    />
    <form
      v-else
      ref="formEl"
      class="form-card"
      data-test="identity-form"
      novalidate
      @submit.prevent="saveIdentity"
    >
      <fieldset>
        <p class="setting-desc">
          <HoverNote text="Ajoutées par la plateforme à tes lettres et à ton CV.">
            Elles ne partent jamais à l'IA.
          </HoverNote>
        </p>
        <p
          v-if="missing.length"
          class="notice"
          data-test="identity-missing"
        >
          Il manque : {{ missing.join(", ") }}.
        </p>
        <div class="identity-fields">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Nom et prénom"
            :width="20"
          >
            <input
              :id="id"
              v-model="identity.name"
              type="text"
              autocomplete="name"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-name"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Rue et numéro"
          >
            <input
              :id="id"
              v-model="identity.street"
              type="text"
              autocomplete="address-line1"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-street"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="NPA"
            :width="5"
            :error="errors.postcode"
          >
            <input
              :id="id"
              v-model="identity.postcode"
              type="text"
              inputmode="numeric"
              maxlength="4"
              autocomplete="postal-code"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-postcode"
              @blur="check('postcode')"
              @input="clearIfFixed('postcode')"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Localité"
            :width="30"
          >
            <input
              :id="id"
              v-model="identity.city"
              type="text"
              autocomplete="address-level2"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-city"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Téléphone"
            optional
            :width="20"
          >
            <input
              :id="id"
              v-model="identity.phone"
              type="tel"
              autocomplete="tel"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-phone"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="E-mail"
            optional
            :width="30"
            :error="errors.email"
          >
            <input
              :id="id"
              v-model="identity.email"
              type="email"
              autocomplete="email"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="identity-email"
              @blur="check('email')"
              @input="clearIfFixed('email')"
            >
          </FormField>
        </div>
        <DisclosureRow
          class="identity-more"
          title="Pour les formulaires de candidature"
          :value="formFilled ? `facultatif · ${formFilled} / 5` : 'facultatif'"
          data-test="identity-more"
        >
          <div class="identity-fields">
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="LinkedIn"
              optional
              :error="errors.linkedin"
            >
              <input
                :id="id"
                v-model="identity.linkedin"
                type="text"
                inputmode="url"
                placeholder="linkedin.com/in/…"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
                data-test="identity-linkedin"
                @blur="check('linkedin')"
                @input="clearIfFixed('linkedin')"
              >
            </FormField>
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="Site personnel"
              optional
              :error="errors.website"
            >
              <input
                :id="id"
                v-model="identity.website"
                type="text"
                inputmode="url"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
                data-test="identity-website"
                @blur="check('website')"
                @input="clearIfFixed('website')"
              >
            </FormField>
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="Disponibilité"
              optional
            >
              <input
                :id="id"
                v-model="identity.availability"
                type="text"
                placeholder="dès le 1er novembre, 1 mois de préavis…"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
              >
            </FormField>
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="Prétentions salariales"
              optional
              :width="20"
            >
              <input
                :id="id"
                v-model="identity.salary"
                type="text"
                placeholder="CHF 90'000 par an"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
              >
            </FormField>
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="Permis de travail"
              optional
              :width="20"
            >
              <input
                :id="id"
                v-model="identity.permit"
                type="text"
                list="identity-permits"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
              >
            </FormField>
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
          Enregistrer
        </button>
        <button
          v-if="changed"
          type="button"
          class="secondary"
          data-test="cancel-identity"
          @click="cancel"
        >
          Annuler
        </button>
        <span
          v-if="identityMessage"
          role="status"
          class="muted"
        >{{ identityMessage }}</span>
      </div>
    </form>
  </section>
</template>
