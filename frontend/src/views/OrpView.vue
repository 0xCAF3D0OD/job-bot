<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type OrpMonth, type OrpRow, type Source } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import JournalPanel from "../components/JournalPanel.vue";
import PageHero from "../components/PageHero.vue";
import { applicationUpdateBody } from "../applicationBody";
import { formatMonth, shiftMonth, sourceLabel } from "../format";

const route = useRoute();
const router = useRouter();

const data = ref<OrpMonth | null>(null);
const withSearches = ref(false);
const jobRoom = ref(false);
const editing = ref<{ id: number; value: ApplicationFormValue } | null>(null);
const editError = ref("");
const copied = ref("");
const busy = ref(false);

const month = computed(() => data.value?.month ?? "");
const tab = computed(() => (route.query.onglet === "journal" ? "journal" : "preuves"));
const progress = computed(() =>
  data.value?.target ? Math.min(1, data.value.count / data.value.target) : null,
);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric" });
const stateLabel = computed(() => {
  const d = data.value;
  if (!d) return "";
  if (d.state === "remis" && d.submitted_at) return `Remis le ${longDate.format(new Date(d.submitted_at))}`;
  if (d.state === "a_remettre") return `À remettre avant le ${longDate.format(new Date(d.due_date))}`;
  return `En cours · remise avant le ${longDate.format(new Date(d.due_date))}`;
});

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

async function load(): Promise<void> {
  const wanted = typeof route.query.mois === "string" ? route.query.mois : undefined;
  const { data: result } = await api.GET("/api/orp", { params: { query: { month: wanted } } });
  data.value = result ?? null;
}

function go(delta: number): void {
  void router.push({ query: { mois: shiftMonth(month.value, delta) } });
}

async function printPdf(): Promise<void> {
  window.print();
  await api.POST("/api/orp/{month}/exported", { params: { path: { month: month.value } } });
  await load();
}

async function submit(done: boolean): Promise<void> {
  if (!done && !window.confirm("Annuler la remise de ce mois ?")) return;
  busy.value = true;
  try {
    const params = { params: { path: { month: month.value } } };
    if (done) await api.PUT("/api/orp/{month}/submission", params);
    else await api.DELETE("/api/orp/{month}/submission", params);
    await load();
  } finally {
    busy.value = false;
  }
}

async function edit(row: OrpRow): Promise<void> {
  editError.value = "";
  const { data: list } = await api.GET("/api/applications", { params: { query: { month: month.value } } });
  const application = list?.find((a) => a.id === row.application_id);
  if (application) editing.value = { id: application.id, value: { ...application } };
}

async function save(value: ApplicationFormValue): Promise<void> {
  if (!editing.value) return;
  const { data: saved } = await api.PUT("/api/applications/{application_id}", {
    params: { path: { application_id: editing.value.id } },
    body: applicationUpdateBody(value),
  });
  if (!saved) {
    editError.value = "Vérifie les champs obligatoires (date, entreprise, poste).";
    return;
  }
  editing.value = null;
  await load();
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

watch(
  () => route.query.mois,
  () => void load(),
);
onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="ORP"
    title="Preuves de recherches d'emploi"
    subtitle="Le formulaire du mois, prêt à remettre à ton conseiller ou à recopier dans Job-Room."
  />

  <section class="band">
    <div class="container">
      <nav
        class="prep-tabs"
        aria-label="ORP"
      >
        <RouterLink
          :to="{ query: { ...(route.query.mois ? { mois: route.query.mois } : {}) } }"
          :class="{ active: tab === 'preuves' }"
          data-test="tab-preuves"
        >
          Preuves du mois
        </RouterLink>
        <RouterLink
          :to="{ query: { onglet: 'journal' } }"
          :class="{ active: tab === 'journal' }"
          data-test="tab-journal"
        >
          Journal des recherches
        </RouterLink>
      </nav>
      <JournalPanel v-if="tab === 'journal'" />
      <template v-else-if="data">
        <div class="applications-head">
          <div class="month-nav">
            <button
              type="button"
              class="secondary small"
              aria-label="Mois précédent"
              data-test="prev-month"
              @click="go(-1)"
            >
              ←
            </button>
            <strong data-test="month">{{ formatMonth(data.month) }}</strong>
            <button
              type="button"
              class="secondary small"
              aria-label="Mois suivant"
              @click="go(1)"
            >
              →
            </button>
          </div>
          <div class="month-goal">
            <span><strong>{{ data.count }}</strong>{{ data.target ? ` / ${data.target}` : "" }} candidature(s)</span>
            <div
              v-if="progress !== null"
              class="budget-bar"
              role="progressbar"
              :aria-valuenow="Math.round(progress * 100)"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              <span :style="{ width: `${progress * 100}%` }" />
            </div>
          </div>
          <span
            :class="['badge', data.state === 'remis' ? 'new' : '']"
            data-test="state"
          >{{ stateLabel }}</span>
        </div>

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
                <th>Entreprise, adresse</th>
                <th>Contact</th>
                <th>Poste</th>
                <th>Taux</th>
                <th>Mode</th>
                <th>ORP</th>
                <th>Résultat</th>
                <th>Lien</th>
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
                  <span v-if="row.address">{{ row.address }}</span>
                  <button
                    v-else
                    type="button"
                    class="link danger"
                    data-test="complete"
                    @click="edit(row)"
                  >
                    À compléter
                  </button>
                </td>
                <td>{{ [row.contact, row.phone].filter(Boolean).join(", ") || "—" }}</td>
                <td>{{ row.job_title }}</td>
                <td>{{ row.rate || "—" }}</td>
                <td>{{ row.method }}</td>
                <td>{{ row.assigned }}</td>
                <td>{{ row.result }}</td>
                <td>
                  <a
                    v-if="row.url?.startsWith('http')"
                    :href="row.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="link"
                  >ouvrir</a>
                  <span v-else>{{ row.url || "—" }}</span>
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
      </template>
    </div>
  </section>

  <ApplicationForm
    v-if="editing"
    title="Compléter la candidature"
    :initial="editing.value"
    :with-status="true"
    :error="editError"
    @submit="save"
    @close="editing = null"
  />
</template>
