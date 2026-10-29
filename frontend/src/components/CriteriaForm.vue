<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, type ContractType, type CriteriaIn, type Keywords, type Language } from "../api/client";
import type { components } from "../api/schema";

type RemotePolicy = components["schemas"]["RemotePolicy"];
import HoverNote from "./HoverNote.vue";
import TagInput from "./TagInput.vue";
import { placeLabel } from "../cantons";

import AppIcon from "./AppIcon.vue";
import FilterOutcome from "./FilterOutcome.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import type { IconName } from "../icons";
import { useNarrow } from "../composables/usePhone";
const CONTRACTS: { value: ContractType; label: string }[] = [
  { value: "stage", label: "Stages" },
  { value: "apprentissage", label: "Apprentissages" },
  { value: "temporaire", label: "Temporaires et CDD" },
  { value: "freelance", label: "Freelance" },
];
const LANGUAGES: { value: Language; label: string }[] = [
  { value: "allemand", label: "Allemand" },
  { value: "italien", label: "Italien" },
  { value: "anglais", label: "Anglais" },
];

// Télétravail complet (docs/26 §3) : trois positions, la phrase reste courte.
const REMOTE_POLICIES: { value: RemotePolicy; label: string; summary: string }[] = [
  { value: "refuse", label: "Refusé", summary: "Télétravail complet : refusé hors de tes lieux" },
  {
    value: "from_switzerland",
    label: "Si ouvert depuis la Suisse",
    summary: "Télétravail complet : accepté s'il est ouvert depuis la Suisse",
  },
  { value: "anywhere", label: "Partout", summary: "Télétravail complet : accepté partout" },
];

// Tous les champs sont présents dans le formulaire, même ceux que l'API rend facultatifs.
type CriteriaForm = Required<CriteriaIn>;

const EMPTY: CriteriaForm = {
  locations: [],
  remote_policy: "refuse",
  min_rate: null,
  excluded_types: [],
  banned_words: [],
  unspoken_languages: [],
};

const form = ref<CriteriaForm>({ ...EMPTY });
const keywords = ref<Keywords | null>(null);
const loaded = ref(false);
const saving = ref(false);
const message = ref("");
const failed = ref(false);
// Saisis une fois au démarrage, puis résumés : le formulaire (pré-rempli) ne s'ouvre que sur
// « Modifier » (docs/10 §2).
const savedAt = ref<string | null>(null);
const editing = ref(false);

// Aides « ? » (docs/32 §1) : les mots-clés réels du filtre, en abrégé.
// La description en une ligne ; les mots-clés au survol (docs/88 règle 5, audit de la 1.1.1).
const contractsHelp = computed(() => {
  if (!keywords.value) return "";
  const k = keywords.value;
  return `${CONTRACTS.map((c) => `${c.label} : ${(k.contract_types[c.value] ?? []).slice(0, 3).join(", ")}…`).join(" ; ")}.`;
});
const languagesHelp = computed(() => {
  const words = keywords.value?.requirement_words.slice(0, 8).join(", ") ?? "";
  return `Son nom à moins de trois mots de ${words}…`;
});

// Résumé en lignes alignées, libellé à gauche, valeur à droite (docs/43 n° 23) ; les cantons
// en toutes lettres (n° 24).
const summary = computed(() => {
  const f = form.value;
  const rows: { key: string; label: string; value: string }[] = [
    { key: "lieux", label: "Lieux", value: f.locations.length ? f.locations.map(placeLabel).join(", ") : "partout" },
  ];
  const remote = REMOTE_POLICIES.find((p) => p.value === f.remote_policy)?.summary ?? "";
  const [remoteLabel, remoteValue] = remote.split(" : ");
  if (remoteLabel && remoteValue) rows.push({ key: "teletravail", label: remoteLabel, value: remoteValue });
  rows.push({ key: "taux", label: "Taux d'activité", value: f.min_rate ? `${f.min_rate} % au moins` : "tous" });
  // Seule l'initiale passe en minuscule : « temporaires et CDD », pas « cdd ».
  const types = CONTRACTS.filter((c) => f.excluded_types.includes(c.value)).map((c) => c.label.charAt(0).toLowerCase() + c.label.slice(1));
  rows.push({ key: "types", label: "Types d'offres exclus", value: types.length ? types.join(", ") : "aucun" });
  if (f.banned_words.length) rows.push({ key: "mots", label: "Mots interdits dans le titre", value: f.banned_words.join(", ") });
  const langs = LANGUAGES.filter((l) => f.unspoken_languages.includes(l.value)).map((l) => l.label.toLowerCase());
  if (langs.length) rows.push({ key: "langues", label: "Langues non parlées", value: langs.join(", ") });
  return rows;
});

// Sous 600 px (planche « Structure téléphone ») : le résumé en liste groupée, une ligne par critère,
// la valeur en phrase grise ; toucher une ligne ouvre le formulaire sur ce critère.
const { phone: narrow } = useNarrow();
const ICONS: Record<string, IconName> = { lieux: "pin", teletravail: "plug", taux: "stats", types: "briefcase", mots: "filter", langues: "globe" };
function sentence(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
async function editAt(key: string): Promise<void> {
  editing.value = true;
  await nextTick();
  const fieldset = document.getElementById(`criteria-${key}`);
  fieldset?.scrollIntoView?.({ block: "start" });
  fieldset?.querySelector<HTMLElement>("input, select, textarea, button")?.focus({ preventScroll: true });
}

// Le taux minimum : vide, ou un nombre de 1 à 100 ; l'erreur sous le champ, en le quittant et à
// l'enregistrement (règles §4, Champ de formulaire).
const rateError = ref("");
function checkRate(): void {
  const rate = form.value.min_rate as number | string | null;
  rateError.value =
    rate === null || rate === "" || (Number.isInteger(rate) && Number(rate) >= 1 && Number(rate) <= 100)
      ? ""
      : "Indique un taux entier de 1 à 100, ou laisse vide.";
}

async function load(): Promise<void> {
  rateError.value = "";
  try {
    const { data } = await api.GET("/api/criteria");
    if (!data) throw new Error("réponse vide");
    form.value = { ...EMPTY, ...data.criteria };
    keywords.value = data.keywords;
    savedAt.value = data.saved_at ?? null;
    editing.value = !savedAt.value;
  } catch {
    failed.value = true;
  } finally {
    loaded.value = true;
  }
}

async function save(): Promise<void> {
  checkRate();
  if (rateError.value) {
    await nextTick();
    document.getElementById("min_rate")?.focus();
    return;
  }
  if ((form.value.min_rate as number | string | null) === "") form.value.min_rate = null;
  saving.value = true;
  message.value = "";
  try {
    const { data, response } = await api.PUT("/api/criteria", { body: form.value });
    if (!data) throw new Error(`HTTP ${response.status}`);
    form.value = { ...EMPTY, ...data.criteria };
    savedAt.value = data.saved_at ?? new Date().toISOString();
    editing.value = false;
    message.value = "Critères enregistrés. Les offres sont refiltrées d'ici une minute.";
  } catch {
    message.value = "L'enregistrement a échoué : vérifie les valeurs saisies.";
  } finally {
    saving.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div class="panel">
    <p
      v-if="loaded && !failed && !form.locations.length"
      class="notice"
      data-test="criteria-missing"
    >
      Aucun lieu indiqué : les offres de toute la Suisse passent le filtre.
    </p>
    <LoadingBlocks
      v-if="!loaded"
      :heights="['14rem']"
    />
    <p
      v-else-if="failed"
      class="notice error"
    >
      Impossible de charger les prérequis.
    </p>
    <div
      v-else-if="!editing && narrow"
      class="criteria-layout"
    >
      <GroupedList
        title="Poste recherché"
        data-test="criteria-summary"
      >
        <GroupedRow
          v-for="row in summary"
          :key="row.key"
          :title="row.label"
          :description="sentence(row.value)"
          :icon="ICONS[row.key]"
          button
          :data-test="`criteria-row-${row.key}`"
          @click="editAt(row.key)"
        />
      </GroupedList>
      <p
        v-if="message"
        role="status"
        class="muted"
      >
        {{ message }}
      </p>
      <FilterOutcome grouped />
    </div>
    <div
      v-else-if="!editing"
      class="criteria-layout"
    >
      <!-- Ce qu'on consulte, comme les CFF (docs/110) : le titre au-dessus, le résumé sur fond
           gris, un crayon rond pour le modifier. -->
      <section class="criteria-summary-section">
        <h2 class="section-title">
          Critères
        </h2>
        <div
          class="info-card criteria-summary"
          data-test="criteria-summary"
        >
          <dl class="summary-rows">
            <div
              v-for="row in summary"
              :key="row.label"
            >
              <dt>{{ row.label }}</dt>
              <dd>{{ row.value }}</dd>
            </div>
          </dl>
          <button
            type="button"
            class="edit-round"
            aria-label="Modifier les prérequis"
            title="Modifier les prérequis"
            data-test="edit-criteria"
            @click="editing = true"
          >
            <AppIcon name="pencil" />
          </button>
        </div>
        <p
          v-if="message"
          role="status"
          class="muted"
        >
          {{ message }}
        </p>
      </section>
      <FilterOutcome />
    </div>
    <form
      v-else
      class="form-card"
      data-test="criteria-form"
      novalidate
      @submit.prevent="save"
    >
      <fieldset id="criteria-lieux">
        <legend>Lieux acceptés</legend>
        <p class="setting-desc">
          Communes (Lausanne) ou cantons (VD). Vide : partout.
        </p>
        <TagInput
          id="locations"
          v-model="form.locations"
          placeholder="Lausanne, VD…"
        />
      </fieldset>

      <fieldset id="criteria-teletravail">
        <legend>Télétravail complet</legend>
        <p class="setting-desc">
          « Si ouvert depuis la Suisse » écarte les postes « US only ».
        </p>
        <div
          class="segmented"
          role="radiogroup"
          aria-label="Télétravail complet"
        >
          <button
            v-for="policy in REMOTE_POLICIES"
            :key="policy.value"
            type="button"
            role="radio"
            :aria-checked="form.remote_policy === policy.value"
            :data-test="`remote-policy-${policy.value}`"
            @click="form.remote_policy = policy.value"
          >
            {{ policy.label }}
          </button>
        </div>
      </fieldset>

      <fieldset id="criteria-taux">
        <legend id="min_rate-legend">
          Taux d'activité minimum
        </legend>
        <p
          id="min_rate-desc"
          class="setting-desc"
        >
          « 60-80 % » passe avec un minimum de 80 ; sans taux, l'offre passe.
        </p>
        <div class="inline-field">
          <input
            id="min_rate"
            v-model.number="form.min_rate"
            type="number"
            min="1"
            max="100"
            placeholder="80"
            aria-labelledby="min_rate-legend"
            :aria-describedby="rateError ? 'min_rate-desc min_rate-error' : 'min_rate-desc'"
            :aria-invalid="rateError ? true : undefined"
            data-test="criteria-min-rate"
            @blur="checkRate"
            @input="rateError && checkRate()"
          >
          <span>%</span>
        </div>
        <p
          v-if="rateError"
          id="min_rate-error"
          class="field-error"
          data-test="field-error"
        >
          {{ rateError }}
        </p>
      </fieldset>

      <fieldset id="criteria-types">
        <legend>Types d'offres exclus</legend>
        <p class="setting-desc">
          <HoverNote
            v-if="contractsHelp"
            :text="contractsHelp"
          >
            Écartée si le titre ou l'extrait contient un mot du type.
          </HoverNote>
          <template v-else>
            Écartée si le titre ou l'extrait contient un mot du type.
          </template>
        </p>
        <label
          v-for="contract in CONTRACTS"
          :key="contract.value"
          class="check"
        >
          <input
            v-model="form.excluded_types"
            type="checkbox"
            :value="contract.value"
          >
          {{ contract.label }}
        </label>
      </fieldset>

      <fieldset id="criteria-mots">
        <legend>Mots interdits dans le titre</legend>
        <p class="setting-desc">
          Une offre dont le titre contient l'un de ces mots est écartée.
        </p>
        <TagInput
          id="banned_words"
          v-model="form.banned_words"
          placeholder="vente, commercial…"
        />
      </fieldset>

      <fieldset id="criteria-langues">
        <legend>Langues non parlées</legend>
        <p class="setting-desc">
          <HoverNote
            v-if="keywords"
            :text="languagesHelp"
          >
            Écartée si le titre ou l'extrait exige l'une de ces langues.
          </HoverNote>
          <template v-else>
            Écartée si le titre ou l'extrait exige l'une de ces langues.
          </template>
        </p>
        <label
          v-for="language in LANGUAGES"
          :key="language.value"
          class="check"
        >
          <input
            v-model="form.unspoken_languages"
            type="checkbox"
            :value="language.value"
          >
          {{ language.label }}
        </label>
      </fieldset>

      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          :disabled="saving"
          data-test="save-criteria"
        >
          Enregistrer et refiltrer
        </button>
        <button
          v-if="savedAt"
          type="button"
          class="secondary"
          data-test="cancel-criteria"
          @click="load"
        >
          Annuler
        </button>
        <span
          v-if="message"
          role="status"
          class="muted"
        >{{ message }}</span>
      </div>
    </form>
  </div>
</template>
