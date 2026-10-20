<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type ContractType, type CriteriaIn, type Keywords, type Language } from "../api/client";
import type { components } from "../api/schema";

type RemotePolicy = components["schemas"]["RemotePolicy"];
import TagInput from "./TagInput.vue";
import { placeLabel } from "../cantons";

import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";
import FilterOutcome from "./FilterOutcome.vue";
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
const contractsHelp = computed(() => {
  const intro = "Écartée si le titre ou l'extrait contient un mot du type.";
  if (!keywords.value) return intro;
  const k = keywords.value;
  const lines = CONTRACTS.map((c) => `${c.label} : ${(k.contract_types[c.value] ?? []).slice(0, 3).join(", ")}…`);
  return `${intro} ${lines.join(" ; ")}.`;
});
const languagesHelp = computed(() => {
  const words = keywords.value?.requirement_words.slice(0, 8).join(", ") ?? "";
  return `Écartée si le titre ou l'extrait exige la langue : son nom à moins de trois mots de ${words}…`;
});

// Résumé en lignes alignées, libellé à gauche, valeur à droite (docs/43 n° 23) ; les cantons
// en toutes lettres (n° 24).
const summary = computed(() => {
  const f = form.value;
  const rows: { label: string; value: string }[] = [
    { label: "Lieux", value: f.locations.length ? f.locations.map(placeLabel).join(", ") : "partout" },
  ];
  const remote = REMOTE_POLICIES.find((p) => p.value === f.remote_policy)?.summary ?? "";
  const [remoteLabel, remoteValue] = remote.split(" : ");
  if (remoteLabel && remoteValue) rows.push({ label: remoteLabel, value: remoteValue });
  rows.push({ label: "Taux d'activité", value: f.min_rate ? `${f.min_rate} % au moins` : "tous" });
  const types = CONTRACTS.filter((c) => f.excluded_types.includes(c.value)).map((c) => c.label.toLowerCase());
  rows.push({ label: "Types d'offres exclus", value: types.length ? types.join(", ") : "aucun" });
  if (f.banned_words.length) rows.push({ label: "Mots interdits dans le titre", value: f.banned_words.join(", ") });
  const langs = LANGUAGES.filter((l) => f.unspoken_languages.includes(l.value)).map((l) => l.label.toLowerCase());
  if (langs.length) rows.push({ label: "Langues que tu ne parles pas", value: langs.join(", ") });
  return rows;
});

async function load(): Promise<void> {
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
  saving.value = true;
  message.value = "";
  try {
    const { data, response } = await api.PUT("/api/criteria", { body: form.value });
    if (!data) throw new Error(`HTTP ${response.status}`);
    form.value = { ...EMPTY, ...data.criteria };
    savedAt.value = data.saved_at ?? new Date().toISOString();
    editing.value = false;
    message.value = "Prérequis enregistrés. Les offres sont refiltrées d'ici une minute.";
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
    <p
      v-if="failed"
      class="notice error"
    >
      Impossible de charger les prérequis.
    </p>
    <div
      v-else-if="loaded && !editing"
      class="criteria-layout"
    >
      <div
        class="form-card criteria-summary"
        data-test="criteria-summary"
      >
        <h2 class="criteria-summary-title">
          Prérequis
        </h2>
        <dl class="summary-rows">
          <div
            v-for="row in summary"
            :key="row.label"
          >
            <dt>{{ row.label }}</dt>
            <dd>{{ row.value }}</dd>
          </div>
        </dl>
        <div class="form-actions">
          <button
            type="button"
            class="secondary"
            data-test="edit-criteria"
            @click="editing = true"
          >
            <span class="with-icon"><AppIcon name="pencil" />Modifier les prérequis</span>
          </button>
          <span
            v-if="message"
            role="status"
            class="muted"
          >{{ message }}</span>
        </div>
      </div>
      <FilterOutcome />
    </div>
    <form
      v-else-if="loaded"
      class="form-card"
      data-test="criteria-form"
      @submit.prevent="save"
    >
      <fieldset>
        <legend>
          <HoverNote text="Communes (Lausanne, Genève) ou cantons en deux lettres (VD, GE). Vide : pas de règle de lieu.">
            Lieux acceptés
          </HoverNote>
        </legend>
        <TagInput
          id="locations"
          v-model="form.locations"
          placeholder="Lausanne, VD…"
        />
      </fieldset>

      <fieldset>
        <legend>
          <HoverNote text="« Si ouvert depuis la Suisse » écarte les postes réservés à d'autres pays (« US only »).">
            Télétravail complet
          </HoverNote>
        </legend>
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

      <fieldset>
        <legend>
          <HoverNote text="Une offre « 60-80 % » passe avec un minimum de 80. Sans taux indiqué, elle passe toujours.">
            Taux d'activité minimum
          </HoverNote>
        </legend>
        <div class="inline-field">
          <input
            id="min_rate"
            v-model.number="form.min_rate"
            type="number"
            min="1"
            max="100"
            placeholder="80"
          >
          <span>%</span>
        </div>
      </fieldset>

      <fieldset>
        <legend>
          <HoverNote :text="contractsHelp">
            Types d'offres exclus
          </HoverNote>
        </legend>
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

      <fieldset>
        <legend>
          Mots interdits dans le titre
        </legend>
        <TagInput
          id="banned_words"
          v-model="form.banned_words"
          placeholder="vente, commercial…"
        />
      </fieldset>

      <fieldset>
        <legend>
          <HoverNote :text="keywords ? languagesHelp : ''">
            Langues que tu ne parles pas
          </HoverNote>
        </legend>
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
          class="link"
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
