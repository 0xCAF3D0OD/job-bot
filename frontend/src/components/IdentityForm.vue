<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, QUIET } from "../api/client";
import { email, postcode, webAddress, type Check } from "../validators";
import DisclosureRow from "./DisclosureRow.vue";
import FormField from "./FormField.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import { useAuth } from "../composables/useAuth";

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
  fromCv.value = [];
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
      fromCv.value = [];
    } else if (response.status === 404) identityMessage.value = "La plateforme n’est pas à jour : redémarre-la.";
    else identityMessage.value = "Enregistrement refusé : vérifie le NPA (quatre chiffres) et les adresses web.";
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
    await fillFromCv();
  } finally {
    loaded.value = true;
  }
});

// Les coordonnées repérées en tête du CV (test du 10 novembre) remplissent les champs encore vides : une proposition,
// rien n'est enregistré avant « Enregistrer », et « Annuler » revient aux valeurs enregistrées. Le CV est le dernier
// document lisible qui n'est pas un certificat ; sans CV ou en cas d'erreur, le formulaire reste tel quel. Le repérage
// se fait sur le serveur, sans IA (PR #623). L'e-mail vide prend d'abord celui du compte, sans marque « Du CV »
// (maquette CoordonneesOrdinateur du 10 novembre au soir, PR 23).
const FROM_CV = ["name", "street", "postcode", "city", "phone", "email"] as const;
type CvField = (typeof FROM_CV)[number];
const fromCv = ref<CvField[]>([]);
const { me } = useAuth();
async function fillFromCv(): Promise<void> {
  const next = { ...identity.value };
  const account = me.value?.username ?? "";
  if (!next.email.trim() && account.includes("@")) next.email = account;
  identity.value = next;
  if (!FROM_CV.some((f) => !identity.value[f].trim())) return;
  try {
    const docs = await api.GET("/api/documents", QUIET);
    const cv = Array.isArray(docs.data) ? docs.data.find((d) => d.kind !== "certificate" && d.text_status === "ok") : undefined;
    if (!cv) return;
    const { data } = await api.GET("/api/identity/from-document/{document_id}", { params: { path: { document_id: cv.id } }, ...QUIET });
    if (!data) return;
    const filled = { ...identity.value };
    const marked: CvField[] = [];
    for (const f of FROM_CV) {
      const value = data[f];
      if (!filled[f].trim() && value) {
        filled[f] = value;
        marked.push(f);
      }
    }
    identity.value = filled;
    fromCv.value = marked;
  } catch {
    // Le CV reste à relire plus tard ; la saisie à la main suffit.
  }
}
// La marque « Du CV » reste tant que la valeur proposée n'est ni enregistrée ni changée.
const marked = (field: CvField): boolean => fromCv.value.includes(field) && identity.value[field].trim() !== "";
const markedCount = computed(() => FROM_CV.filter(marked).length);
</script>

<template>
  <!-- Profil › Coordonnées (maquettes CoordonneesOrdinateur et CoordonneesTel du 10 novembre au soir, PR 23) : une
       carte de 640 au plus, 20 de marge et 16 entre les blocs ; le bloc « n champs repris de ton CV » en tête, la
       marque « Du CV » à côté du libellé de chaque champ pré-rempli, la phrase sur l’IA sous les champs, puis
       « Annuler » et « Enregistrer » à droite (sur téléphone, pleine largeur, « Enregistrer » au-dessus). -->
  <section
    class="identity-section"
    aria-labelledby="identity-title"
  >
    <h2
      id="identity-title"
      class="visually-hidden"
    >
      Coordonnées
    </h2>
    <LoadingBlocks
      v-if="!loaded"
      :heights="['30rem']"
    />
    <form
      v-else
      ref="formEl"
      class="identity-card"
      data-test="identity-form"
      novalidate
      @submit.prevent="saveIdentity"
    >
      <div
        class="identity-live"
        role="status"
      >
        <div
          v-if="markedCount"
          class="identity-from-cv"
          data-test="identity-from-cv"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          ><circle
            cx="12"
            cy="12"
            r="9"
          /><path d="M12 11v5.5M12 7.5h.01" /></svg>
          <div>
            <p class="identity-from-cv-title">
              {{ markedCount }} {{ markedCount > 1 ? "champs repris" : "champ repris" }} de ton CV
            </p>
            <p class="identity-from-cv-text">
              Vérifie-les puis enregistre. Rien n’est enregistré avant.
            </p>
          </div>
        </div>
        <p
          v-else-if="missing.length"
          class="notice"
          data-test="identity-missing"
        >
          Il manque&#8239;: {{ missing.join(", ") }}.
        </p>
      </div>
      <div class="identity-grid">
        <div class="identity-pair">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Prénom et nom"
            :badge="marked('name') ? 'Du CV' : ''"
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
            label="E-mail"
            :badge="marked('email') ? 'Du CV' : ''"
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
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Rue et numéro"
          :badge="marked('street') ? 'Du CV' : ''"
        >
          <input
            :id="id"
            v-model="identity.street"
            type="text"
            autocomplete="street-address"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="identity-street"
          >
        </FormField>
        <div class="identity-place">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="NPA"
            :badge="marked('postcode') ? 'Du CV' : ''"
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
            :badge="marked('city') ? 'Du CV' : ''"
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
        </div>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Téléphone"
          :badge="marked('phone') ? 'Du CV' : ''"
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
      </div>
      <!-- Pas dans la maquette : les cinq champs des formulaires en ligne des employeurs (docs/25), gardés en
           attendant la décision de Kevin. -->
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
      <p class="identity-ai">
        Tes coordonnées servent seulement à l’en-tête de tes lettres. Elles ne sont jamais envoyées à l’IA.
      </p>
      <div class="identity-actions">
        <button
          v-if="changed"
          type="button"
          class="identity-button identity-cancel"
          data-test="cancel-identity"
          @click="cancel"
        >
          Annuler
        </button>
        <button
          type="submit"
          class="identity-button identity-save"
          data-test="save-identity"
        >
          Enregistrer
        </button>
      </div>
      <p
        v-if="identityMessage"
        role="status"
        class="identity-message"
      >
        {{ identityMessage }}
      </p>
    </form>
  </section>
</template>

<style>
/* Maquettes CoordonneesOrdinateur / CoordonneesTel (10 novembre au soir) : carte 640, contour 1,5 et coins de 18 ; bloc
   info sur --primary-soft, coins de 14, 16 de marge ; libellés 14 gras, à 8 du champ ; champs de 48, coins de 12 ;
   marque « Du CV » 22 de haut, 12 gras, --primary-soft / --primary-text ; phrase 13/18 en --text-secondary. */
.identity-card { max-width: 40rem; box-sizing: border-box; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); padding: var(--space-5); display: flex; flex-direction: column; gap: var(--space-4); }
.identity-live:empty { display: none; }
.identity-from-cv { display: flex; gap: var(--space-3); padding: var(--space-4); border-radius: 0.875em; background: var(--primary-soft); color: var(--primary-text); }
.identity-from-cv svg { flex: none; }
.identity-from-cv-title { margin: 0; font-size: var(--font-label); line-height: 1.4667em; font-weight: var(--weight-bold); color: var(--text); }
.identity-from-cv-text { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); }
.identity-grid { display: flex; flex-direction: column; gap: var(--space-4); }
.identity-pair { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); }
.identity-place { display: grid; grid-template-columns: 6rem 1fr; gap: var(--space-4); }
.identity-card .identity-grid .form-field { display: flex; flex-direction: column; gap: var(--space-2); min-width: 0; max-width: none; }
.identity-card .identity-grid .form-field-label { display: flex; align-items: center; gap: var(--space-2); min-height: calc(var(--space-5) + 0.125rem); font-size: var(--font-small); font-weight: var(--weight-bold); }
.identity-card .identity-grid input { height: var(--space-12); width: 100%; max-width: none; padding: 0 0.90625em; border: 1.5px solid var(--field-border); border-radius: var(--space-3); background: var(--surface); font-size: var(--font-body); color: var(--text); box-sizing: border-box; }
.form-field-badge { display: inline-flex; align-items: center; height: calc(var(--space-5) + 0.125rem); padding: 0 var(--space-2); border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-caption); font-weight: var(--weight-bold); }
.identity-card .identity-more { margin-top: 0; }
.identity-ai { margin: 0; font-size: 0.8125em; line-height: 1.3846em; color: var(--text-secondary); }
.identity-actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.identity-button { display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; height: 2.75rem; border-radius: var(--radius-pill); font-family: inherit; font-size: var(--font-label); white-space: nowrap; cursor: pointer; }
.identity-save { padding: 0 var(--space-5); border: 0; background: var(--primary); color: var(--on-primary); font-weight: var(--weight-bold); }
.identity-cancel { padding: 0 var(--space-5); border: 1.5px solid var(--primary); background: var(--surface); color: var(--primary-text); font-weight: var(--weight-semibold); }
.identity-message { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
@media (max-width: 599px) {
  .identity-pair { grid-template-columns: 1fr; }
  .identity-actions { flex-direction: column-reverse; }
  .identity-button { width: 100%; }
}
</style>
