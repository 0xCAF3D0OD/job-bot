<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, QUIET } from "../api/client";
import { COUNTED, answerText, type AnswerKey, type SalaryMode } from "../formAnswers";
import type { IconName } from "../icons";
import { email, postcode, type Check } from "../validators";
import AppIcon from "./AppIcon.vue";
import FormAnswerSheet from "./FormAnswerSheet.vue";
import FormField from "./FormField.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import { useAuth } from "../composables/useAuth";

// Coordonnées pour l'en-tête des lettres, du CV et du formulaire ORP : base locale seulement,
// jamais envoyées à l'IA.
// Les réponses pour les formulaires en ligne des employeurs (docs/25) ont leur rubrique, plus bas : chacune
// s'enregistre seule, depuis son panneau (récapitulatif du 11 novembre, PR 44).
const IDENTITY_FIELDS = ["name", "street", "postcode", "city", "phone", "email"] as const;
type IdentityForm = Record<(typeof IDENTITY_FIELDS)[number], string>;
const blank = (): IdentityForm => Object.fromEntries(IDENTITY_FIELDS.map((f) => [f, ""])) as IdentityForm;
const identity = ref<IdentityForm>(blank());
// Les valeurs enregistrées : « Annuler » y revient.
const saved = ref<IdentityForm>(blank());
const changed = computed(() => IDENTITY_FIELDS.some((f) => identity.value[f] !== saved.value[f]));

// « Pour les formulaires de candidature » (maquettes CoordonneesOrdinateur et CoordonneesTel du 11 novembre) : cinq
// réponses comptées, et « Site ou portfolio », facultatif, qui ne compte pas (décision de Kevin du 11 novembre).
const ANSWERS: { key: AnswerKey; label: string; icon: IconName }[] = [
  { key: "linkedin", label: "Profil LinkedIn", icon: "linkedin" },
  { key: "permit", label: "Permis de travail", icon: "id-card" },
  { key: "availability", label: "Disponible dès", icon: "calendar" },
  { key: "notice", label: "Délai de préavis", icon: "timer" },
  { key: "salary", label: "Prétentions salariales", icon: "banknote" },
  { key: "website", label: "Site ou portfolio", icon: "globe" },
];
const answers = ref<Record<AnswerKey, string>>({ linkedin: "", permit: "", availability: "", notice: "", salary: "", website: "" });
const salaryMode = ref<SalaryMode>("auto");
const shown = computed(() => Object.fromEntries(ANSWERS.map((a) => [a.key, answerText(a.key, answers.value[a.key])])) as Record<AnswerKey, string>);
const answered = computed(() => COUNTED.filter((key) => shown.value[key]).length);
const editing = ref<AnswerKey | null>(null);
function answerSaved(changes: Partial<Record<AnswerKey, string>> & { salary_mode?: SalaryMode }): void {
  const { salary_mode: mode, ...values } = changes;
  answers.value = { ...answers.value, ...values };
  if (mode) salaryMode.value = mode;
}
const identityMessage = ref("");
const formEl = ref<HTMLFormElement | null>(null);

// Vérification en quittant chaque champ (docs/29 §4) ; à l'enregistrement, tout est revérifié
// et le premier champ en erreur reçoit le curseur. L'erreur s'affiche sous le champ (FormField).
const CHECKS: Partial<Record<keyof IdentityForm, Check>> = {
  postcode,
  email,
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
      answers.value = Object.fromEntries(ANSWERS.map((a) => [a.key, loadedIdentity[a.key] ?? ""])) as Record<AnswerKey, string>;
      salaryMode.value = loadedIdentity.salary_mode ?? "auto";
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
      <section
        class="identity-answers"
        aria-labelledby="identity-answers-title"
        data-test="identity-answers"
      >
        <h2 id="identity-answers-title">
          Pour les formulaires de candidature
        </h2>
        <template v-if="answered < COUNTED.length">
          <p class="identity-answers-count">
            <strong data-test="answers-count">{{ answered }} {{ answered > 1 ? "réponses" : "réponse" }} sur {{ COUNTED.length }}</strong>
            <span data-test="answers-missing">Il en manque {{ COUNTED.length - answered }}</span>
          </p>
          <div
            class="identity-answers-bar"
            role="progressbar"
            :aria-valuenow="answered"
            aria-valuemin="0"
            :aria-valuemax="COUNTED.length"
            :aria-label="`${answered} ${answered > 1 ? 'réponses' : 'réponse'} sur ${COUNTED.length}`"
          >
            <span
              v-for="n in COUNTED.length"
              :key="n"
              :class="{ on: n <= answered }"
            />
          </div>
        </template>
        <p class="identity-answers-lead">
          jobA1 les remplit à ta place dans les formulaires des employeurs.
        </p>
        <ul class="identity-answers-list">
          <li
            v-for="row in ANSWERS"
            :key="row.key"
          >
            <button
              type="button"
              aria-haspopup="dialog"
              :data-test="`answer-${row.key}`"
              @click="editing = row.key"
            >
              <AppIcon :name="row.icon" />
              <span class="identity-answer-text">
                <span class="identity-answer-label">{{ row.label }}</span>
                <span
                  v-if="shown[row.key]"
                  class="identity-answer-value"
                >{{ shown[row.key] }}<AppIcon
                  v-if="row.key === 'salary'"
                  name="lock"
                  class="identity-answer-lock"
                /><span
                  v-if="row.key === 'salary'"
                  class="visually-hidden"
                > (visible seulement par toi)</span></span>
                <span
                  v-else-if="row.key === 'website'"
                  class="identity-answer-optional"
                >Facultatif</span>
                <span
                  v-else
                  class="identity-answer-todo"
                >À compléter</span>
              </span>
              <AppIcon
                name="chevron"
                class="identity-answer-arrow"
              />
            </button>
          </li>
        </ul>
      </section>
      <p class="identity-ai">
        Ces informations servent à l’en-tête de tes lettres et aux formulaires de candidature. Elles ne sont jamais envoyées à l’IA.
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
    <FormAnswerSheet
      :field="editing"
      :value="editing ? answers[editing] : ''"
      :salary-mode="salaryMode"
      @saved="answerSaved"
      @close="editing = null"
    />
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
/* « Pour les formulaires de candidature » (maquette du 11 novembre) : trait, titre 13/16 en capitales, progression en
   5 segments de 6 px, puis des lignes de 64 px au moins : icône 24, libellé 13 gras gris, valeur 15/20, flèche. */
.identity-answers { --ia-13: 0.8125rem; --ia-15: 0.9375rem; --ia-seg: 6px; --ia-row: 64px; margin-top: var(--space-2); padding-top: var(--space-5); border-top: 1px solid var(--surface-muted); }
.identity-answers h2 { margin: 0; font-size: var(--ia-13); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-secondary); }
.identity-answers-count { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); margin: var(--space-3) 0 0; }
.identity-answers-count strong { font-size: var(--ia-15); font-weight: var(--weight-bold); }
.identity-answers-count span { font-size: var(--font-small); color: var(--text-secondary); }
.identity-answers-bar { display: flex; gap: var(--space-1); margin-top: var(--space-2); }
.identity-answers-bar span { flex: 1; height: var(--ia-seg); border-radius: var(--ia-seg); background: var(--line-strong); }
.identity-answers-bar span.on { background: var(--ok-text); }
.identity-answers-lead { margin: var(--space-2) 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.identity-answers-list { list-style: none; margin: 0; padding: 0; }
.identity-answers-list li + li { border-top: 1px solid var(--surface-muted); }
.identity-answers-list button {
  display: flex; align-items: center; gap: var(--space-4); width: calc(100% + 2 * var(--space-3)); min-height: var(--ia-row); box-sizing: border-box; margin: 0 calc(-1 * var(--space-3)); padding: var(--space-3);
  border: 0; border-radius: var(--space-3); background: transparent; color: var(--text); font: inherit; text-align: left; cursor: pointer;
}
.identity-answers-list button > svg { flex: none; width: var(--space-6); height: var(--space-6); color: var(--row-icon); }
.identity-answers-list button > .identity-answer-arrow { width: var(--space-5); height: var(--space-5); color: var(--text-secondary); }
.identity-answer-text { flex: 1; min-width: 0; white-space: normal; }
.identity-answer-label { display: block; font-size: var(--ia-13); line-height: var(--space-4); font-weight: var(--weight-bold); color: var(--text-secondary); }
.identity-answer-value { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-1); font-size: var(--ia-15); line-height: var(--space-5); overflow-wrap: anywhere; }
.identity-answer-lock { flex: none; width: var(--font-small); height: var(--font-small); color: var(--text-secondary); }
.identity-answer-todo, .identity-answer-optional { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); }
.identity-answer-todo { font-weight: var(--weight-bold); color: var(--orange-text); }
.identity-answer-optional { color: var(--text-secondary); }
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
