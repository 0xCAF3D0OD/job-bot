<script lang="ts">
export type CompletionSection = "experiences" | "languages" | "identity";
export type Level = "unknown" | "notions" | "fluent" | "native";

export const LEVELS: { value: Level; label: string }[] = [
  { value: "unknown", label: "Non renseigné" },
  { value: "notions", label: "Notions" },
  { value: "fluent", label: "Courant" },
  { value: "native", label: "Langue maternelle" },
];
export const BASE_LANGUAGES: { name: string; label: string }[] = [
  { name: "francais", label: "Français" },
  { name: "allemand", label: "Allemand" },
  { name: "italien", label: "Italien" },
  { name: "anglais", label: "Anglais" },
];
export const languageLabel = (name: string): string =>
  BASE_LANGUAGES.find((l) => l.name === name)?.label ?? name.charAt(0).toUpperCase() + name.slice(1);

// Les exemples de tâches suivent le poste cherché (prompt du 10 novembre, PR 17 : « exemples adaptés aux postes
// recherchés ») ; sans poste reconnu, une phrase qui parle à tous les métiers.
const TASK_EXAMPLES: [RegExp, string][] = [
  [/vent|vend|commerc|caiss|magasin|boutique|retail/i, "accueil des clients, caisse, commandes, inventaire"],
  [/soin|soign|infirm|aide|accompagn|asspe|socio/i, "soins de base, accompagnement, transmissions, hygiène"],
  [/cuisin|restaur|serv|barman|h[oô]tel|r[ée]ception/i, "mise en place, service, encaissement, hygiène"],
  [/logisti|magasinier|entrep[oô]t|chauffeur|livreu|cariste/i, "réception des marchandises, préparation des commandes, inventaire"],
  [/bureau|administr|secr[ée]tar|comptab|employ[ée]e? de commerce|assistant/i, "accueil téléphonique, courrier, saisie, classement"],
  [/nettoy|entretien|concierg/i, "nettoyage des locaux, produits, horaires, contrôle qualité"],
  [/[ée]lectric|m[ée]can|chantier|ma[cç]on|menuis|peint|install/i, "montage, dépannage, lecture de plans, sécurité"],
];
export function taskExample(roles: string[]): string {
  for (const role of roles) {
    const found = TASK_EXAMPLES.find(([pattern]) => pattern.test(role));
    if (found) return found[1];
  }
  return "ce que tu faisais chaque jour, avec tes mots";
}
</script>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, QUIET, type CriteriaIn, type Identity } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { postcode as checkPostcode } from "../validators";
import AppIcon from "./AppIcon.vue";
import FormField from "./FormField.vue";

// « Complétons ton profil » (prompt du 10 novembre, PR 17 ; maquettes OnboardingProfil et OnboardingOrdinateurProfil) :
// les expériences (blocs « expérience » du profil), les langues et leur niveau (prérequis `language_levels`), les
// coordonnées de l'en-tête des lettres. Le même formulaire sert aux premiers pas et au panneau ouvert depuis une
// offre ou depuis Préparer. Rien n'est enregistré avant `save()`.
const props = withDefaults(
  defineProps<{
    sections?: CompletionSection[];
    desk?: boolean;
    roles?: string[];
    // Le CV importé : ses coordonnées repérées sur le serveur, sans IA, remplissent les champs encore vides.
    documentId?: number | null;
    // Les langues que le CV mentionne (lecture réussie) : « Courant », à corriger.
    cvLanguages?: string[];
    // Les niveaux partent avec les autres critères (étape 2 des premiers pas) : `save()` ne les envoie pas.
    languagesOnly?: boolean;
  }>(),
  {
    sections: () => ["experiences", "languages", "identity"],
    desk: false,
    roles: () => [],
    documentId: null,
    cvLanguages: () => [],
    languagesOnly: false,
  },
);

type Experience = { title: string; employer: string; start: string; end: string; current: boolean; tasks: string };
type LanguageRow = { name: string; level: Level; added: boolean };
type IdentityFields = { name: string; street: string; postcode: string; city: string; phone: string; email: string };

const { me } = useAuth();
const blank = (): Experience => ({ title: "", employer: "", start: "", end: "", current: false, tasks: "" });
const experiences = ref<Experience[]>([blank()]);
const languages = ref<LanguageRow[]>(BASE_LANGUAGES.map((l) => ({ name: l.name, level: "unknown", added: false })));
const identity = ref<IdentityFields>({ name: "", street: "", postcode: "", city: "", phone: "", email: "" });
const savedIdentity = ref<Identity>({});
const criteria = ref<CriteriaIn | null>(null);
const errors = ref<{ name?: string; postcode?: string }>({});
const message = ref("");
const saving = ref(false);

const has = (section: CompletionSection): boolean => props.sections.includes(section);
// Le poste saisi d’abord (« Employée de commerce » → caisse, commandes…), puis les postes cherchés.
const example = (title: string): string => taskExample([title, ...props.roles]);
const titlePlaceholder = computed(() => props.roles[0] ?? "Vendeuse, électricien, aide-soignante…");

onMounted(async () => {
  const [found, who] = await Promise.all([
    has("languages") ? api.GET("/api/criteria") : Promise.resolve(null),
    has("identity") ? api.GET("/api/identity") : Promise.resolve(null),
  ]);
  if (found?.data?.criteria) {
    criteria.value = found.data.criteria;
    const levels = (found.data.criteria.language_levels ?? {}) as Record<string, Level>;
    const rows = languages.value.map((row) => ({ ...row, level: levels[row.name] ?? row.level }));
    for (const [name, level] of Object.entries(levels)) {
      if (!rows.some((r) => r.name === name)) rows.push({ name, level, added: false });
    }
    for (const name of props.cvLanguages) {
      const row = rows.find((r) => r.name === name);
      if (row && row.level === "unknown") row.level = "fluent";
    }
    languages.value = rows;
  }
  if (who?.data) {
    savedIdentity.value = who.data;
    for (const key of Object.keys(identity.value) as (keyof IdentityFields)[]) identity.value[key] = who.data[key] ?? "";
  }
  if (has("identity") && props.documentId !== null) {
    const { data } = await api.GET("/api/identity/from-document/{document_id}", {
      params: { path: { document_id: props.documentId } },
      ...QUIET,
    });
    for (const key of Object.keys(identity.value) as (keyof IdentityFields)[]) {
      if (!identity.value[key] && data?.[key]) identity.value[key] = data[key]!;
    }
  }
  if (has("identity") && !identity.value.email && me.value?.username?.includes("@")) identity.value.email = me.value.username;
});

function addExperience(): void {
  experiences.value = [...experiences.value, blank()];
}

function addLanguage(): void {
  languages.value = [...languages.value, { name: "", level: "unknown", added: true }];
}

// Une expérience devient un bloc « expérience » du profil : « Poste, employeur », puis les dates et les tâches.
function chunkOf(experience: Experience): { title: string; content: string } | null {
  const title = experience.title.trim();
  if (!title) return null;
  const employer = experience.employer.trim();
  const end = experience.current ? "aujourd’hui" : experience.end.trim();
  const dates = [experience.start.trim(), end].filter(Boolean).join(" à ");
  const tasks = experience.tasks.trim();
  const content = [dates ? `${dates.charAt(0).toUpperCase()}${dates.slice(1)}.` : "", tasks].filter(Boolean).join("\n") || title;
  return { title: employer ? `${title}, ${employer}` : title, content };
}

function validate(): boolean {
  const next: typeof errors.value = {};
  if (has("identity")) {
    if (!identity.value.name.trim()) next.name = "Indique ton prénom et ton nom.";
    const postcodeError = checkPostcode(identity.value.postcode);
    if (postcodeError) next.postcode = postcodeError;
  }
  errors.value = next;
  return !Object.keys(next).length;
}

// Enregistre ce qui a été rempli. Rend vrai si tout est parti ; sinon le message dit quoi corriger.
async function save(): Promise<boolean> {
  message.value = "";
  if (!validate()) {
    message.value = errors.value.name ?? errors.value.postcode ?? "";
    return false;
  }
  saving.value = true;
  try {
    const calls: Promise<{ response: Response }>[] = [];
    if (has("experiences")) {
      for (const chunk of experiences.value.map(chunkOf).filter((c) => c !== null)) {
        calls.push(api.POST("/api/profile-chunks", { body: { kind: "experience", ...chunk, tags: [], active: true } }));
      }
    }
    if (has("languages") && criteria.value && !props.languagesOnly) {
      calls.push(api.PUT("/api/criteria", { body: { ...criteria.value, language_levels: levels.value } }));
    }
    if (has("identity")) {
      const body: Identity = { ...savedIdentity.value };
      for (const key of Object.keys(identity.value) as (keyof IdentityFields)[]) body[key] = identity.value[key].trim() || null;
      calls.push(api.PUT("/api/identity", { body }));
    }
    const results = await Promise.all(calls);
    if (results.some((r) => !r.response.ok)) {
      message.value = "Une partie n’a pas pu être enregistrée. Vérifie les champs et réessaie.";
      return false;
    }
    return true;
  } catch {
    message.value = "jobA1 est injoignable. Réessaie dans un instant.";
    return false;
  } finally {
    saving.value = false;
  }
}

const levels = computed(
  () =>
    Object.fromEntries(
      languages.value.filter((l) => l.name.trim()).map((l) => [l.name.trim().toLowerCase(), l.level]),
    ) as Record<string, Level>,
);

// Ce qui manque à une lettre (Préparer) : le nom, l'adresse.
const missingForLetter = computed(() => !identity.value.name.trim() || !identity.value.street.trim());

defineExpose({ save, saving, missingForLetter, levels });
</script>

<template>
  <div :class="['pc', { 'pc-desk': desk }]">
    <section
      v-if="has('experiences')"
      class="pc-sec"
      data-test="completion-experiences"
    >
      <h2>Expériences</h2>
      <p class="pc-hint">
        Commence par la plus récente. Ta lettre ne parlera que de ce que tu écris ici.
      </p>
      <div
        v-for="(experience, index) in experiences"
        :key="index"
        class="pc-card pc-stack"
        data-test="completion-experience"
      >
        <div class="pc-pair">
          <FormField
            v-slot="f"
            :field-id="`pc-title-${index}`"
            label="Poste"
            :hint="`Ex. : ${titlePlaceholder}`"
          >
            <input
              :id="f.id"
              v-model="experience.title"
              :aria-describedby="f.describedby"
              type="text"
              maxlength="120"
              data-test="completion-title"
            >
          </FormField>
          <FormField
            v-slot="f"
            :field-id="`pc-employer-${index}`"
            label="Employeur"
          >
            <input
              :id="f.id"
              v-model="experience.employer"
              :aria-describedby="f.describedby"
              type="text"
              maxlength="80"
              data-test="completion-employer"
            >
          </FormField>
        </div>
        <div class="pc-pair pc-pair-always">
          <FormField
            v-slot="f"
            :field-id="`pc-start-${index}`"
            label="Début"
            hint="Ex. : Mars 2021"
          >
            <input
              :id="f.id"
              v-model="experience.start"
              :aria-describedby="f.describedby"
              type="text"
              maxlength="30"
              data-test="completion-start"
            >
          </FormField>
          <FormField
            v-slot="f"
            :field-id="`pc-end-${index}`"
            label="Fin"
          >
            <input
              :id="f.id"
              :aria-describedby="f.describedby"
              :value="experience.current ? 'Aujourd’hui' : experience.end"
              type="text"
              maxlength="30"
              :disabled="experience.current"
              data-test="completion-end"
              @input="experience.end = ($event.target as HTMLInputElement).value"
            >
          </FormField>
        </div>
        <label class="pc-check">
          <input
            v-model="experience.current"
            type="checkbox"
            data-test="completion-current"
          ><span
            class="pc-box"
            aria-hidden="true"
          ><AppIcon name="done" /></span>J’y travaille encore
        </label>
        <div class="pc-field">
          <label :for="`pc-tasks-${index}`">Tâches principales</label>
          <textarea
            :id="`pc-tasks-${index}`"
            v-model="experience.tasks"
            maxlength="2000"
            :aria-describedby="`pc-tasks-hint-${index}`"
            data-test="completion-tasks"
          />
          <span
            :id="`pc-tasks-hint-${index}`"
            class="pc-small"
          >Ex.&#8239;: {{ example(experience.title) }}.</span>
        </div>
      </div>
      <button
        type="button"
        class="pc-link"
        data-test="completion-add-experience"
        @click="addExperience"
      >
        <AppIcon name="plus" />Ajouter une expérience
      </button>
    </section>

    <section
      v-if="has('languages')"
      class="pc-sec"
      data-test="completion-languages"
    >
      <h2>Langues</h2>
      <p class="pc-hint">
        Une langue non renseignée n’écarte aucune offre.
      </p>
      <div class="pc-card pc-langs">
        <div
          v-for="(language, index) in languages"
          :key="index"
          class="pc-lang"
          data-test="completion-language"
        >
          <input
            v-if="language.added"
            v-model="language.name"
            type="text"
            maxlength="40"
            class="pc-lang-name-input"
            placeholder="Espagnol"
            aria-label="Langue"
            data-test="completion-language-name"
          >
          <b v-else>{{ languageLabel(language.name) }}</b>
          <select
            v-model="language.level"
            :class="['pc-level', { 'pc-placeholder': language.level === 'unknown' }]"
            :aria-label="`Niveau en ${language.added ? language.name || 'cette langue' : languageLabel(language.name).toLowerCase()}`"
            :data-test="`completion-level-${language.name || index}`"
          >
            <option
              v-for="level in LEVELS"
              :key="level.value"
              :value="level.value"
            >
              {{ level.label }}
            </option>
          </select>
        </div>
      </div>
      <button
        type="button"
        class="pc-link"
        data-test="completion-add-language"
        @click="addLanguage"
      >
        <AppIcon name="plus" />Ajouter une langue
      </button>
    </section>

    <section
      v-if="has('identity')"
      class="pc-sec"
      data-test="completion-identity"
    >
      <h2>Coordonnées</h2>
      <p class="pc-hint">
        Pour l’en-tête de tes lettres. Jamais envoyées sans ton accord.
      </p>
      <div class="pc-card pc-stack">
        <FormField
          v-slot="f"
          field-id="pc-name"
          label="Prénom et nom (obligatoire)"
        >
          <input
            :id="f.id"
            v-model="identity.name"
            :aria-describedby="f.describedby"
            type="text"
            autocomplete="name"
            maxlength="80"
            required
            :aria-invalid="errors.name ? 'true' : undefined"
            data-test="completion-name"
          >
        </FormField>
        <FormField
          v-slot="f"
          field-id="pc-street"
          label="Adresse"
        >
          <input
            :id="f.id"
            v-model="identity.street"
            :aria-describedby="f.describedby"
            type="text"
            autocomplete="street-address"
            maxlength="80"
            data-test="completion-street"
          >
        </FormField>
        <div class="pc-npa">
          <FormField
            v-slot="f"
            field-id="pc-postcode"
            label="NPA"
          >
            <input
              :id="f.id"
              v-model="identity.postcode"
              :aria-describedby="f.describedby"
              type="text"
              inputmode="numeric"
              autocomplete="postal-code"
              maxlength="4"
              :aria-invalid="errors.postcode ? 'true' : undefined"
              data-test="completion-postcode"
            >
          </FormField>
          <FormField
            v-slot="f"
            field-id="pc-city"
            label="Localité"
          >
            <input
              :id="f.id"
              v-model="identity.city"
              :aria-describedby="f.describedby"
              type="text"
              autocomplete="address-level2"
              maxlength="80"
              data-test="completion-city"
            >
          </FormField>
        </div>
        <div class="pc-pair">
          <FormField
            v-slot="f"
            field-id="pc-phone"
            label="Téléphone"
          >
            <input
              :id="f.id"
              v-model="identity.phone"
              :aria-describedby="f.describedby"
              type="tel"
              autocomplete="tel"
              maxlength="80"
              data-test="completion-phone"
            >
          </FormField>
          <FormField
            v-slot="f"
            field-id="pc-email"
            label="E-mail"
            hint="Celui de ton compte"
          >
            <input
              :id="f.id"
              v-model="identity.email"
              :aria-describedby="f.describedby"
              type="email"
              autocomplete="email"
              maxlength="80"
              data-test="completion-email"
            >
          </FormField>
        </div>
      </div>
    </section>
    <p
      v-if="message"
      class="notice pc-message"
      role="alert"
      data-test="completion-message"
    >
      {{ message }}
    </p>
  </div>
</template>

<style>
/* Valeurs des maquettes OnboardingProfil (téléphone) et OnboardingOrdinateurProfil (ordinateur) du 10 novembre. */
.pc {
  --pc-sec-gap: 36px; --pc-hint-gap: var(--space-1); --pc-card-gap: var(--space-4); --pc-field-gap: var(--space-2); --pc-pair-gap: var(--space-3);
  --pc-card-pad: 14.5px; --pc-input-pad: var(--space-4); --pc-input-radius: var(--space-3); --pc-link-gap: var(--space-2);
  --pc-h2: 20px; --pc-h2-lh: 26px; --pc-hint: 15px; --pc-hint-lh: 22px; --pc-label-lh: 18px; --pc-small-lh: 18px;
  --pc-lead-lh: 24px; --pc-box: 22px; --pc-box-radius: 6px; --pc-lang-h: 64px; --pc-level-w: 210px; --pc-npa: 96px;
  --pc-ta-h: 96px; --pc-ta-pad: var(--space-3); --pc-medium: 500; --pc-small: 13px;
}
.pc-desk { --pc-h2: 22px; --pc-h2-lh: 28px; --pc-card-pad: 18.5px; }
.pc-sec { margin-top: var(--pc-sec-gap); }
.pc-sec:first-child { margin-top: 0; }
.pc-sec h2 { margin: 0; font-size: var(--pc-h2); line-height: var(--pc-h2-lh); font-weight: var(--weight-heavy); }
.pc-hint { margin: var(--pc-hint-gap) 0 0; font-size: var(--pc-hint); line-height: var(--pc-hint-lh); color: var(--text-secondary); }
.pc-card { margin-top: var(--pc-card-gap); padding: var(--pc-card-pad); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.pc-stack { display: flex; flex-direction: column; gap: var(--pc-card-gap); }
.pc-pair { display: flex; flex-direction: column; gap: var(--pc-card-gap); }
.pc-pair-always, .pc-desk .pc-pair { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--pc-pair-gap); }
.pc-npa { display: grid; grid-template-columns: var(--pc-npa) minmax(0, 1fr); gap: var(--pc-pair-gap); }
.pc-field { display: flex; flex-direction: column; gap: var(--pc-field-gap); min-width: 0; }
.pc-field > label { font-size: var(--font-small); line-height: var(--pc-label-lh); font-weight: var(--weight-bold); color: var(--text); }
.pc :is(.pc-lang input[type="text"], select) { width: 100%; padding: 0 var(--pc-input-pad); border-radius: var(--pc-input-radius); }
.pc :is(input[type="text"], input[type="tel"], input[type="email"]):disabled { background-color: var(--field-disabled-bg); border-color: var(--line-strong); color: var(--text-placeholder); -webkit-text-fill-color: var(--text-placeholder); }
.pc textarea { min-height: var(--pc-ta-h); padding: var(--pc-ta-pad) var(--pc-input-pad); border-radius: var(--pc-input-radius); line-height: var(--pc-lead-lh); }
.pc ::placeholder { color: var(--text-placeholder); }
.pc-small { font-size: var(--font-caption); line-height: var(--pc-small-lh); color: var(--text-secondary); }
.pc-field .pc-small { font-size: var(--pc-small); }
.pc-check { position: relative; display: flex; align-items: center; gap: var(--space-2); min-height: var(--target-min); font-size: var(--pc-hint); cursor: pointer; }
.pc-check input { position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }
.pc-box { flex: none; display: grid; place-items: center; width: var(--pc-box); height: var(--pc-box); box-sizing: border-box; border: 1.5px solid var(--field-border); border-radius: var(--pc-box-radius); background: var(--surface); color: var(--on-primary); }
.pc-box .icon { width: 14px; height: 14px; stroke-width: 3.2; visibility: hidden; }
.pc-check input:checked + .pc-box { background: var(--primary-graphic); border-color: var(--primary-graphic); }
.pc-check input:checked + .pc-box .icon { visibility: visible; }
.pc-check input:focus-visible + .pc-box { outline: 2px solid var(--accent); outline-offset: 2px; }
.pc-langs { padding-block: var(--space-1); }
.pc-lang { display: flex; align-items: center; gap: var(--space-4); min-height: var(--pc-lang-h); border-top: 1px solid var(--line); }
.pc-lang:first-child { border-top: 0; }
.pc-lang b { flex: 1; min-width: 0; font-size: var(--font-body); }
.pc-lang .pc-lang-name-input { flex: 1; min-width: 0; }
.pc select.pc-level { flex: none; width: var(--pc-level-w); max-width: calc(100% - 6rem); }
.pc .pc-level.pc-placeholder { color: var(--text-placeholder); }
.pc-link { display: inline-flex; align-items: center; gap: var(--pc-link-gap); min-height: var(--target-min); margin-top: var(--pc-link-gap); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--pc-hint); font-weight: var(--weight-bold); cursor: pointer; }
.pc-link .icon { width: 18px; height: 18px; }
.pc-message { margin-top: var(--space-6); }
</style>
