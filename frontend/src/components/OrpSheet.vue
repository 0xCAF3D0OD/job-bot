<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type OrpMonth, type OrpRow, type Source } from "../api/client";
import AppIcon from "./AppIcon.vue";
import { printSheet } from "../composables/usePrint";
import { formatMonth, sourceLabel } from "../format";

// Preuves ORP du mois (docs/09), onglet de la page Candidatures (docs/18 §2).
const props = defineProps<{ data: OrpMonth }>();
const emit = defineEmits<{ reload: []; edit: [applicationId: number] }>();

const withSearches = ref(false);
const jobRoom = ref(false);
const copied = ref("");
const busy = ref(false);

// Champs dans l'ordre du formulaire de saisie, pour les recopier un à un dans Job-Room.
const FIELDS: [keyof OrpRow, string][] = [
  ["date", "Date"],
  ["company", "Entreprise"],
  ["address", "Adresse"],
  ["contact", "Personne de contact"],
  ["phone", "Téléphone"],
  ["job_title", "Poste"],
  ["rate", "Taux"],
  ["method", "Mode"],
  ["assigned", "Assignée par l'ORP"],
  ["result", "Résultat"],
  ["url", "Lien de la candidature"],
];

async function printPdf(): Promise<void> {
  const sheet = document.querySelector<HTMLElement>(".orp-sheet");
  if (sheet) printSheet(sheet, { title: `Preuves ORP - ${props.data.month}`, landscape: true });
  await api.POST("/api/orp/{month}/exported", { params: { path: { month: props.data.month } } });
  emit("reload");
}

async function submit(done: boolean): Promise<void> {
  if (!done && !window.confirm("Annuler la remise de ce mois ?")) return;
  busy.value = true;
  try {
    const params = { params: { path: { month: props.data.month } } };
    if (done) await api.PUT("/api/orp/{month}/submission", params);
    else await api.DELETE("/api/orp/{month}/submission", params);
    emit("reload");
  } finally {
    busy.value = false;
  }
}

function edit(row: OrpRow): void {
  emit("edit", row.application_id);
}

async function copy(value: string, key: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    copied.value = key;
    setTimeout(() => {
      if (copied.value === key) copied.value = "";
    }, 1500);
  } catch {
    copied.value = "";
  }
}

const today = new Intl.DateTimeFormat("fr-CH").format(new Date());

// Colonnes affichées à l'écran, enregistrées en base (le PDF et le CSV gardent tout).
type OrpColumn = "address" | "contact" | "rate" | "method" | "assigned" | "result" | "url";
const COLUMNS: { key: OrpColumn; label: string }[] = [
  { key: "address", label: "Adresse de l'entreprise" },
  { key: "contact", label: "Contact" },
  { key: "rate", label: "Taux" },
  { key: "method", label: "Mode" },
  { key: "assigned", label: "Assignée par l'ORP" },
  { key: "result", label: "Résultat" },
  { key: "url", label: "Lien de la candidature" },
];
const visibleColumns = ref<OrpColumn[]>(COLUMNS.map((c) => c.key));
const pickingColumns = ref(false);

function show(column: OrpColumn): boolean {
  return visibleColumns.value.includes(column);
}

async function toggleColumn(column: OrpColumn): Promise<void> {
  visibleColumns.value = show(column)
    ? visibleColumns.value.filter((c) => c !== column)
    : COLUMNS.map((c) => c.key).filter((c) => c === column || show(c));
  await api.PUT("/api/orp-columns", { body: { visible: visibleColumns.value } });
}

onMounted(async () => {
  try {
    const { data: saved } = await api.GET("/api/orp-columns");
    if (Array.isArray(saved?.visible)) visibleColumns.value = saved.visible;
  } catch {
    // Toutes les colonnes si l'API ne répond pas.
  }
});
</script>

<template>
  <div class="orp-sheet-tab">
    <p
      v-if="data.changed_after_submit"
      class="notice"
      data-test="changed"
    >
      Des candidatures de ce mois ont changé après la remise : renvoie une version corrigée si besoin.
    </p>
    <p
      v-if="data.incomplete"
      class="notice"
      data-test="incomplete"
    >
      {{ data.incomplete }} ligne(s) à compléter : il manque l'adresse de l'entreprise.
    </p>
    <p
      v-if="!data.holder.name"
      class="notice"
    >
      Ton nom n'est pas saisi : <RouterLink to="/reglages">
        complète tes coordonnées
      </RouterLink> pour l'en-tête du PDF.
    </p>

    <div class="orp-actions">
      <button
        type="button"
        class="primary small"
        :disabled="!data.count"
        data-test="pdf"
        @click="printPdf"
      >
        Télécharger en PDF <AppIcon name="chevron" />
      </button>
      <div class="actions">
        <a
          v-if="data.count"
          class="secondary"
          :href="`/api/orp/${data.month}/csv`"
          download
          data-test="csv"
        >CSV (Excel)</a>
      </div>
      <label class="check">
        <input
          v-model="withSearches"
          type="checkbox"
          data-test="with-searches"
        > Joindre le journal des recherches ({{ data.searches.length }})
      </label>
      <div class="columns-picker">
        <button
          type="button"
          class="link"
          :aria-expanded="pickingColumns"
          data-test="columns"
          @click="pickingColumns = !pickingColumns"
        >
          Colonnes ({{ visibleColumns.length + 3 }} / {{ COLUMNS.length + 3 }})
        </button>
        <fieldset
          v-if="pickingColumns"
          class="customize-list columns-list"
          data-test="columns-list"
        >
          <legend class="hint">
            Date, entreprise et poste toujours affichés ; le PDF et le CSV gardent tout.
          </legend>
          <label
            v-for="column in COLUMNS"
            :key="column.key"
            class="check"
          >
            <input
              type="checkbox"
              :checked="show(column.key)"
              :data-test="`column-${column.key}`"
              @change="toggleColumn(column.key)"
            >
            {{ column.label }}
          </label>
        </fieldset>
      </div>
      <label class="check">
        <input
          v-model="jobRoom"
          type="checkbox"
          data-test="job-room"
        > Saisie Job-Room
      </label>
      <span class="spacer" />
      <button
        v-if="data.state !== 'remis'"
        type="button"
        class="secondary small"
        :disabled="busy || !data.count"
        data-test="submit"
        @click="submit(true)"
      >
        Marquer comme remis
      </button>
      <button
        v-else
        type="button"
        class="link"
        :disabled="busy"
        data-test="cancel-submit"
        @click="submit(false)"
      >
        Annuler la remise
      </button>
    </div>

    <p
      v-if="!data.count"
      class="muted empty"
    >
      Aucune candidature en {{ formatMonth(data.month) }}.
    </p>

    <div
      v-else-if="jobRoom"
      class="job-room"
    >
      <article
        v-for="(row, index) in data.rows"
        :key="row.application_id"
        class="job-room-card"
        data-test="job-room-row"
      >
        <h3>{{ index + 1 }}. {{ row.company }} — {{ row.job_title }}</h3>
        <dl>
          <template
            v-for="[key, label] in FIELDS"
            :key="key"
          >
            <dt>{{ label }}</dt>
            <dd>
              <span>{{ row[key] || "—" }}</span>
              <button
                v-if="row[key]"
                type="button"
                class="link"
                data-test="copy"
                @click="copy(String(row[key]), `${row.application_id}-${key}`)"
              >
                {{ copied === `${row.application_id}-${key}` ? "Copié" : "Copier" }}
              </button>
            </dd>
          </template>
        </dl>
      </article>
    </div>

    <div
      v-else
      class="table-scroll"
    >
      <table class="runs orp-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>{{ show("address") ? "Entreprise, adresse" : "Entreprise" }}</th>
            <th v-if="show('contact')">
              Contact
            </th>
            <th>Poste</th>
            <th v-if="show('rate')">
              Taux
            </th>
            <th v-if="show('method')">
              Mode
            </th>
            <th v-if="show('assigned')">
              ORP
            </th>
            <th v-if="show('result')">
              Résultat
            </th>
            <th v-if="show('url')">
              Lien
            </th>
            <th><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in data.rows"
            :key="row.application_id"
            :class="{ incomplete: row.missing.length }"
            data-test="orp-row"
          >
            <td>{{ row.date }}</td>
            <td>
              <strong>{{ row.company }}</strong><br>
              <span v-if="row.address && show('address')">{{ row.address }}</span>
              <button
                v-else-if="!row.address"
                type="button"
                class="link danger"
                data-test="complete"
                @click="edit(row)"
              >
                À compléter
              </button>
            </td>
            <td v-if="show('contact')">
              {{ [row.contact, row.phone].filter(Boolean).join(", ") || "—" }}
            </td>
            <td>{{ row.job_title }}</td>
            <td v-if="show('rate')">
              {{ row.rate || "—" }}
            </td>
            <td v-if="show('method')">
              {{ row.method }}
            </td>
            <td v-if="show('assigned')">
              {{ row.assigned }}
            </td>
            <td v-if="show('result')">
              {{ row.result }}
            </td>
            <td v-if="show('url')">
              <a
                v-if="row.url?.startsWith('http')"
                :href="row.url"
                target="_blank"
                rel="noopener noreferrer"
                class="link"
              >ouvrir</a>
              <span v-else>{{ row.url || "—" }}</span>
            </td>
            <td>
              <button
                type="button"
                class="link"
                data-test="edit-row"
                @click="edit(row)"
              >
                Modifier
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Version imprimée : A4 paysage, proche du formulaire officiel. -->
    <article
      class="orp-sheet print-sheet"
      aria-hidden="true"
    >
      <h1>Preuves des recherches personnelles effectuées en vue de trouver un emploi</h1>
      <div class="orp-holder">
        <span>Nom et prénom : <strong>{{ data.holder.name }}</strong></span>
        <span>Adresse : {{ data.holder.address }}</span>
        <span>N° AVS : ______________________</span>
        <span>Période : <strong>{{ formatMonth(data.month) }}</strong></span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Entreprise, adresse</th>
            <th>Personne de contact, téléphone</th>
            <th>Poste</th>
            <th>Taux</th>
            <th>Mode</th>
            <th>Assignée ORP</th>
            <th>Résultat</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in data.rows"
            :key="row.application_id"
          >
            <td>{{ row.date }}</td>
            <td>{{ [row.company, row.address].filter(Boolean).join(", ") }}</td>
            <td>{{ [row.contact, row.phone].filter(Boolean).join(", ") }}</td>
            <td>
              {{ row.job_title }}
              <span
                v-if="row.url"
                class="orp-url"
              >{{ row.url }}</span>
            </td>
            <td>{{ row.rate }}</td>
            <td>{{ row.method }}</td>
            <td>{{ row.assigned }}</td>
            <td>{{ row.result }}</td>
          </tr>
        </tbody>
      </table>
      <div class="orp-sign">
        <span>Lieu et date : ______________________ (imprimé le {{ today }})</span>
        <span>Signature : ______________________</span>
      </div>
      <section
        v-if="withSearches && data.searches.length"
        class="orp-annex"
      >
        <h2>Annexe : journal des recherches ({{ formatMonth(data.month) }})</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Site</th>
              <th>Alerte</th>
              <th>Offres</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(search, index) in data.searches"
              :key="index"
            >
              <td>{{ new Date(search.received_at).toLocaleDateString("fr-CH") }}</td>
              <td>{{ sourceLabel[search.source as Source] ?? search.source }}</td>
              <td>{{ search.label }}</td>
              <td>{{ search.results_count }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </article>
  </div>
</template>
