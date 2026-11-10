<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, type ContractType, type CriteriaIn, type Keywords, type Language } from "../api/client";
import type { components } from "../api/schema";

type RemotePolicy = components["schemas"]["RemotePolicy"];
import HoverNote from "./HoverNote.vue";
import TagInput from "./TagInput.vue";
import { placeLabel } from "../cantons";
import { plural } from "../format";

import AppIcon from "./AppIcon.vue";
import FilterOutcome from "./FilterOutcome.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import LoadingBlocks from "./LoadingBlocks.vue";
import type { IconName } from "../icons";
import { useNarrow } from "../composables/usePhone";
// Le titre du résumé : « Critères » ; « Ce que je cherche » dans le Profil ordinateur (maquette ProfilOrdinateur).
withDefaults(defineProps<{ heading?: string }>(), { heading: "Critères" });
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
// `pill` : l'aperçu court dans la ligne du résumé sur téléphone.
const REMOTE_POLICIES: { value: RemotePolicy; label: string; summary: string; pill: string }[] = [
  { value: "refuse", label: "Refusé", summary: "Télétravail complet : refusé hors de tes lieux", pill: "Refusé" },
  {
    value: "from_switzerland",
    label: "Si ouvert depuis la Suisse",
    summary: "Télétravail complet : accepté s'il est ouvert depuis la Suisse",
    pill: "Depuis la Suisse",
  },
  { value: "anywhere", label: "Partout", summary: "Télétravail complet : accepté partout", pill: "Partout" },
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
// Chaque critère : sa valeur en phrase (le résumé sur ordinateur, les lecteurs d'écran) et ses éléments, montrés
// en pastilles sur téléphone (le premier, puis « +N »), sous un titre court qui tient sur une ligne (`short`).
const summary = computed(() => {
  const f = form.value;
  const places = f.locations.map(placeLabel);
  const rows: { key: string; label: string; value: string; items: string[]; short?: string }[] = [
    { key: "lieux", label: "Lieux", value: places.length ? places.join(", ") : "partout", items: places.length ? places : ["Partout"] },
  ];
  const policy = REMOTE_POLICIES.find((p) => p.value === f.remote_policy);
  const [remoteLabel, remoteValue] = (policy?.summary ?? "").split(" : ");
  if (policy && remoteLabel && remoteValue) rows.push({ key: "teletravail", label: remoteLabel, value: remoteValue, items: [policy.pill] });
  const rate = f.min_rate ? `${f.min_rate} % au moins` : "tous";
  rows.push({ key: "taux", label: "Taux d'activité", value: rate, items: [f.min_rate ? `${f.min_rate} % et +` : "Tous"] });
  // Seule l'initiale passe en minuscule : « temporaires et CDD », pas « cdd ».
  const types = CONTRACTS.filter((c) => f.excluded_types.includes(c.value)).map((c) => c.label.charAt(0).toLowerCase() + c.label.slice(1));
  rows.push({ key: "types", label: "Types d'offres exclus", short: "Offres exclues", value: types.length ? types.join(", ") : "aucun", items: types.length ? types.map(sentence) : ["Aucun"] });
  if (f.banned_words.length) rows.push({ key: "mots", label: "Mots interdits dans le titre", short: "Mots interdits", value: f.banned_words.join(", "), items: f.banned_words });
  const langs = LANGUAGES.filter((l) => f.unspoken_languages.includes(l.value)).map((l) => l.label.toLowerCase());
  if (langs.length) rows.push({ key: "langues", label: "Langues non parlées", value: langs.join(", "), items: langs.map(sentence) });
  return rows;
});

// Sous 600 px (planche « Structure téléphone ») : le résumé en liste groupée, une ligne par critère, d'une seule
// hauteur, la valeur en pastilles (D14, 2026-11-05) ; toucher une ligne ouvre le formulaire sur ce critère.
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
    // Les offres écartées sont réévaluées tout de suite : dire combien reviennent.
    const back = data.returned ?? 0;
    message.value = back
      ? `Critères enregistrés. ${plural(back, "offre revient", "offres reviennent")} dans À examiner.`
      : "Critères enregistrés. Aucune offre écartée ne revient.";
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
          :title="row.short ?? row.label"
          :icon="ICONS[row.key]"
          button
          :data-test="`criteria-row-${row.key}`"
          @click="editAt(row.key)"
        >
          <template #end>
            <span
              class="grouped-value"
              aria-hidden="true"
            >{{ row.items[0] }}</span>
            <span
              v-if="row.items.length > 1"
              class="grouped-value"
              aria-hidden="true"
            >+{{ row.items.length - 1 }}</span>
            <span class="visually-hidden">: {{ row.value }}</span>
          </template>
        </GroupedRow>
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
          {{ heading }}
        </h2>
        <!-- Une ligne cliquable par critère (MODIFICATIONS du 8 novembre au soir, lot 13.2) : le libellé au-dessus de
             la valeur, alignés à gauche, 68 px, chevron à droite ; la ligne ouvre le formulaire sur son critère. -->
        <ul
          class="criteria-rows"
          data-test="criteria-summary"
        >
          <li
            v-for="row in summary"
            :key="row.label"
          >
            <button
              type="button"
              class="criteria-row"
              :data-test="`criteria-row-${row.key}`"
              @click="editAt(row.key)"
            >
              <span class="criteria-row-text">
                <span class="criteria-row-label">{{ row.label }}</span>
                <span class="criteria-row-value">{{ sentence(row.value) }}</span>
              </span>
              <span
                class="arrow-circle small"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </button>
          </li>
        </ul>
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

<style>
/* Profil › Critères sur ordinateur (MODIFICATIONS du 8 novembre au soir, lot 13.2 ; HTML de ProfilOrdinateur) : carte
   blanche aux coins de 18, lignes de 68 (12/20), libellé de 14 en --text-secondary au-dessus de la valeur de 16 en
   700, 2 px entre eux, cercle D29 de 36 à droite (version finale), trait entre les lignes. */
.criteria-rows { --crit-68: 68px; --crit-14: 14px; --crit-20: 20px; --crit-22: 22px; --crit-2: 2px; margin: 0; padding: 0; list-style: none; overflow: hidden; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); }
.narrow-block:has(.criteria-rows) { max-width: none; }
.criteria-rows > li + li { border-top: 1px solid var(--surface-muted); }
.criteria-row { display: flex; align-items: center; gap: var(--crit-14); box-sizing: border-box; width: 100%; min-height: var(--crit-68); padding: var(--space-3) var(--crit-20); border: 0; border-radius: 0; background: transparent; color: var(--text); font-weight: var(--weight-regular); text-align: left; white-space: normal; }
.criteria-row:hover { background: var(--band); }
.criteria-row-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--crit-2); }
.criteria-row-label { font-size: var(--font-small); line-height: var(--leading-normal); color: var(--text-secondary); }
.criteria-row-value { font-size: var(--font-body); line-height: var(--crit-22); font-weight: var(--weight-bold); }
/* Ordinateur (MODIFICATIONS du 9 novembre, §2.9 ; HTML de ProfilOrdinateur) : une carte par préférence, 8 px entre les
   cartes, 72 px de haut au moins, bordure de 1,5 px, rayon 18. Sur la grille de 4 (décision de Kevin du 10 novembre) :
   16 / 20 px de marge trait compris (12,5 de la maquette → 14,5), 16 px entre le texte et le cercle, 4 px entre les lignes. */
@media (min-width: 821px) {
  .criteria-rows .criteria-row { gap: var(--space-4); }
  .criteria-rows .criteria-row-text { gap: var(--space-1); }
  .criteria-rows { --crit-pad-y: 14.5px; --crit-pad-x: 18.5px; --crit-72: 72px; display: flex; flex-direction: column; gap: var(--space-2); overflow: visible; background: none; border: 0; border-radius: 0; }
  .criteria-rows > li + li { border-top: 0; }
  .page-blocks-wide .criteria-rows .criteria-row, .criteria-rows .criteria-row { min-height: var(--crit-72); padding: var(--crit-pad-y) var(--crit-pad-x); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
  .criteria-rows .criteria-row:hover { border-color: var(--primary-graphic); background: var(--surface); }
}
</style>
