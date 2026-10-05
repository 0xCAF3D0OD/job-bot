<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type ContractType, type CriteriaIn, type Keywords, type Language } from "../api/client";
import AppIcon from "./AppIcon.vue";
import TagInput from "./TagInput.vue";

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

// Tous les champs sont présents dans le formulaire, même ceux que l'API rend facultatifs.
type CriteriaForm = Required<CriteriaIn>;

const EMPTY: CriteriaForm = {
  locations: [],
  remote_ok: false,
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

const summary = computed(() => {
  const f = form.value;
  const lines: string[] = [];
  lines.push(
    f.locations.length
      ? `Lieux : ${f.locations.join(", ")}${f.remote_ok ? ", ou télétravail complet" : ""}`
      : "Lieux : partout",
  );
  lines.push(f.min_rate ? `Taux d'activité : ${f.min_rate} % au moins` : "Taux d'activité : tous");
  const types = CONTRACTS.filter((c) => f.excluded_types.includes(c.value)).map((c) => c.label.toLowerCase());
  lines.push(types.length ? `Exclus : ${types.join(", ")}` : "Aucun type d'offre exclu");
  if (f.banned_words.length) lines.push(`Mots interdits dans le titre : ${f.banned_words.join(", ")}`);
  const langs = LANGUAGES.filter((l) => f.unspoken_languages.includes(l.value)).map((l) => l.label.toLowerCase());
  if (langs.length) lines.push(`Langues que tu ne parles pas : ${langs.join(", ")}`);
  return lines;
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
      v-if="failed"
      class="notice error"
    >
      Impossible de charger les prérequis.
    </p>
    <div
      v-else-if="loaded && !editing"
      class="form-card criteria-summary"
      data-test="criteria-summary"
    >
      <ul>
        <li
          v-for="line in summary"
          :key="line"
        >
          {{ line }}
        </li>
      </ul>
      <div class="form-actions">
        <button
          type="button"
          class="secondary"
          data-test="edit-criteria"
          @click="editing = true"
        >
          Modifier ce que je cherche
        </button>
        <span
          v-if="message"
          role="status"
          class="muted"
        >{{ message }}</span>
      </div>
    </div>
    <form
      v-else-if="loaded"
      class="form-card"
      data-test="criteria-form"
      @submit.prevent="save"
    >
      <fieldset>
        <legend>Lieux acceptés</legend>
        <p class="hint">
          Communes (Lausanne, Genève) ou cantons en deux lettres (VD, GE). Vide : pas de règle de lieu.
        </p>
        <TagInput
          id="locations"
          v-model="form.locations"
          placeholder="Lausanne, VD…"
        />
        <label class="check">
          <input
            v-model="form.remote_ok"
            type="checkbox"
          >
          Accepter le télétravail complet, même hors de ces lieux
        </label>
      </fieldset>

      <fieldset>
        <legend>Taux d'activité minimum</legend>
        <p class="hint">
          Une offre « 60-80 % » passe avec un minimum de 80. Sans taux indiqué, elle passe toujours.
        </p>
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
        <legend>Types d'offres exclus</legend>
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
          <span>
            {{ contract.label }}
            <small
              v-if="keywords"
              class="hint"
            >Cherche : {{ keywords.contract_types[contract.value]?.join(", ") }}</small>
          </span>
        </label>
      </fieldset>

      <fieldset>
        <legend>Mots interdits dans le titre</legend>
        <p class="hint">
          Sans tenir compte des majuscules ni des accents.
        </p>
        <TagInput
          id="banned_words"
          v-model="form.banned_words"
          placeholder="vente, commercial…"
        />
      </fieldset>

      <fieldset>
        <legend>Langues que tu ne parles pas</legend>
        <p
          v-if="keywords"
          class="hint"
        >
          Écartée si le titre ou l'extrait exige la langue : son nom à moins de trois mots de
          {{ keywords.requirement_words.slice(0, 8).join(", ") }}…
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
          Enregistrer et refiltrer <AppIcon name="chevron" />
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
