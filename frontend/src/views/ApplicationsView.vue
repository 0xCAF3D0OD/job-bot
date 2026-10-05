<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import {
  api,
  type Application,
  type ApplicationStatus,
  type MonthSummary,
} from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import PageHero from "../components/PageHero.vue";
import { applicationStatusLabel, formatMonth, methodLabel, shiftMonth } from "../format";

function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

const month = ref(currentMonth());
const items = ref<Application[]>([]);
const summary = ref<MonthSummary | null>(null);
const editing = ref<{ id: number | null; value: ApplicationFormValue } | null>(null);
const error = ref("");
const loaded = ref(false);

const progress = computed(() => {
  if (!summary.value?.target) return null;
  return Math.min(1, summary.value.count / summary.value.target);
});

function today(): string {
  const now = new Date();
  return `${currentMonth()}-${String(now.getDate()).padStart(2, "0")}`;
}

async function load(): Promise<void> {
  const [list, sum] = await Promise.all([
    api.GET("/api/applications", { params: { query: { month: month.value } } }),
    api.GET("/api/applications/summary", { params: { query: { month: month.value } } }),
  ]);
  items.value = list.data ?? [];
  summary.value = sum.data ?? null;
  loaded.value = true;
}

function edit(application: Application): void {
  error.value = "";
  editing.value = { id: application.id, value: { ...application } };
}

function addManual(): void {
  error.value = "";
  editing.value = {
    id: null,
    value: {
      sent_at: today(),
      method: "electronique",
      assigned_by_orp: false,
      company: "",
      job_title: "",
      status: "en_attente",
    },
  };
}

function body(value: ApplicationFormValue) {
  return {
    sent_at: value.sent_at,
    method: value.method,
    assigned_by_orp: value.assigned_by_orp,
    company: value.company,
    company_address: value.company_address || null,
    contact_name: value.contact_name || null,
    contact_phone: value.contact_phone || null,
    job_title: value.job_title,
    location: value.location || null,
    rate_text: value.rate_text || null,
  };
}

async function save(value: ApplicationFormValue): Promise<void> {
  if (!editing.value) return;
  const result =
    editing.value.id === null
      ? await api.POST("/api/applications", { body: { ...body(value), offer_id: null } })
      : await api.PUT("/api/applications/{application_id}", {
          params: { path: { application_id: editing.value.id } },
          body: {
            ...body(value),
            status: value.status ?? "en_attente",
            status_reason: value.status_reason || null,
            status_at: value.status_at ?? null,
            interview_at: value.interview_at ?? null,
          },
        });
  if (!result.data) {
    error.value = "Vérifie les champs obligatoires (date, entreprise, poste).";
    return;
  }
  editing.value = null;
  await load();
}

async function setStatus(application: Application, status: ApplicationStatus): Promise<void> {
  await api.PUT("/api/applications/{application_id}", {
    params: { path: { application_id: application.id } },
    body: {
      ...body(application),
      status,
      status_reason: application.status_reason ?? null,
      interview_at: application.interview_at ?? null,
    },
  });
  await load();
}

async function remove(application: Application): Promise<void> {
  if (!window.confirm(`Supprimer la candidature chez ${application.company} ? L'offre revient « en préparation ».`)) {
    return;
  }
  await api.DELETE("/api/applications/{application_id}", {
    params: { path: { application_id: application.id } },
  });
  await load();
}

watch(month, () => void load());
onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Candidatures"
    title="Tes candidatures envoyées"
    subtitle="Le suivi de chaque candidature, et le décompte du mois pour l'ORP."
  />

  <section class="band">
    <div class="container">
      <div class="applications-head">
        <div class="month-nav">
          <button
            type="button"
            class="secondary small"
            aria-label="Mois précédent"
            data-test="prev-month"
            @click="month = shiftMonth(month, -1)"
          >
            ←
          </button>
          <strong data-test="month">{{ formatMonth(month) }}</strong>
          <button
            type="button"
            class="secondary small"
            aria-label="Mois suivant"
            @click="month = shiftMonth(month, 1)"
          >
            →
          </button>
        </div>
        <div
          v-if="summary"
          class="month-goal"
          data-test="goal"
        >
          <span><strong>{{ summary.count }}</strong>{{ summary.target ? ` / ${summary.target}` : "" }} candidature(s)</span>
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
          <span
            v-else
            class="hint"
          >Objectif ORP à saisir dans les Réglages.</span>
        </div>
        <button
          type="button"
          class="primary small"
          data-test="add-application"
          @click="addManual"
        >
          Ajouter une candidature <AppIcon name="chevron" />
        </button>
      </div>

      <p
        v-if="loaded && !items.length"
        class="muted empty"
      >
        Aucune candidature en {{ formatMonth(month) }}. Depuis une offre, « Marquer comme envoyée » l'ajoute ici.
      </p>
      <table
        v-else-if="items.length"
        class="runs"
      >
        <thead>
          <tr>
            <th>Envoyée</th>
            <th>Entreprise</th>
            <th>Poste</th>
            <th>Mode</th>
            <th>Statut</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="application in items"
            :key="application.id"
            data-test="application"
          >
            <td>{{ new Date(application.sent_at).toLocaleDateString("fr-CH") }}</td>
            <td>
              {{ application.company }}
              <span
                v-if="application.assigned_by_orp"
                class="badge"
              >ORP</span>
            </td>
            <td>{{ application.job_title }}</td>
            <td>{{ methodLabel[application.method ?? "electronique"] }}</td>
            <td>
              <select
                :value="application.status"
                :class="['status-select', application.status]"
                :aria-label="`Statut de la candidature chez ${application.company}`"
                data-test="status-select"
                @change="setStatus(application, ($event.target as HTMLSelectElement).value as ApplicationStatus)"
              >
                <option
                  v-for="(label, value) in applicationStatusLabel"
                  :key="value"
                  :value="value"
                >
                  {{ label }}
                </option>
              </select>
            </td>
            <td class="row-actions">
              <a
                v-if="application.letter_draft_id"
                class="link"
                :href="`/api/letters/${application.letter_draft_id}/docx`"
                download
                data-test="letter-docx"
              >Lettre</a>
              <a
                v-if="application.cv_draft_id"
                class="link"
                :href="`/api/cvs/${application.cv_draft_id}/docx`"
                download
                data-test="cv-docx"
              >CV</a>
              <button
                type="button"
                class="link"
                @click="edit(application)"
              >
                Modifier
              </button>
              <button
                type="button"
                class="link danger"
                @click="remove(application)"
              >
                Supprimer
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <ApplicationForm
    v-if="editing"
    :title="editing.id === null ? 'Ajouter une candidature' : 'Modifier la candidature'"
    :initial="editing.value"
    :with-status="editing.id !== null"
    :error="error"
    @submit="save"
    @close="editing = null"
  />
</template>
