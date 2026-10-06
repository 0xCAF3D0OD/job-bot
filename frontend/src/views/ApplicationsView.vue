<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Application, type ApplicationStatus, type OrpMonth } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import ApplicationsTable from "../components/ApplicationsTable.vue";
import JournalPanel from "../components/JournalPanel.vue";
import OrpSheet from "../components/OrpSheet.vue";
import PageHero from "../components/PageHero.vue";
import { applicationBody, applicationUpdateBody } from "../applicationBody";
import { formatMonth, shiftMonth } from "../format";

// Candidatures et preuves ORP réunies (docs/18 §2) : un en-tête commun pour le mois,
// puis Suivi, Preuves ORP et Journal des recherches.
type View = "suivi" | "orp" | "journal";
const REMIND_AFTER_DAYS = 10;

const route = useRoute();
const router = useRouter();
const view = computed<View>(() =>
  route.query.vue === "orp" ? "orp" : route.query.vue === "journal" ? "journal" : "suivi",
);
const orp = ref<OrpMonth | null>(null);
const all = ref<Application[]>([]);
const allMonths = ref(false);
const editing = ref<{ id: number | null; value: ApplicationFormValue } | null>(null);
const error = ref("");
const loaded = ref(false);

const month = computed(() => orp.value?.month ?? "");
const items = computed(() =>
  allMonths.value ? all.value : all.value.filter((a) => a.orp_month === month.value),
);
const progress = computed(() =>
  orp.value?.target ? Math.min(1, orp.value.count / orp.value.target) : null,
);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric" });
const stateLabel = computed(() => {
  const d = orp.value;
  if (!d) return "";
  if (d.state === "remis" && d.submitted_at) return `Preuves remises le ${longDate.format(new Date(d.submitted_at))}`;
  if (d.state === "a_remettre") return `Preuves à remettre avant le ${longDate.format(new Date(d.due_date))}`;
  return `En cours · remise avant le ${longDate.format(new Date(d.due_date))}`;
});
// Sans réponse depuis 10 jours : à relancer (comme la page Aujourd'hui et ntfy).
const toFollowUp = computed(() => {
  const limit = new Date();
  limit.setDate(limit.getDate() - REMIND_AFTER_DAYS);
  const day = limit.toISOString().slice(0, 10);
  return all.value.filter((a) => a.status === "en_attente" && a.sent_at <= day);
});

async function load(): Promise<void> {
  const wanted = typeof route.query.mois === "string" ? route.query.mois : undefined;
  const [sheet, list] = await Promise.all([
    api.GET("/api/orp", { params: { query: { month: wanted } } }),
    api.GET("/api/applications"),
  ]);
  orp.value = sheet.data ?? null;
  all.value = list.data ?? [];
  loaded.value = true;
}

function go(delta: number): void {
  void router.push({ query: { ...route.query, mois: shiftMonth(month.value, delta) } });
}

function tabLink(target: View) {
  const query: Record<string, string> = {};
  if (target !== "suivi") query.vue = target;
  if (typeof route.query.mois === "string") query.mois = route.query.mois;
  return { query };
}

function today(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function edit(application: Application): void {
  error.value = "";
  editing.value = { id: application.id, value: { ...application } };
}

function editById(id: number): void {
  const application = all.value.find((a) => a.id === id);
  if (application) edit(application);
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

async function save(value: ApplicationFormValue): Promise<void> {
  if (!editing.value) return;
  const result =
    editing.value.id === null
      ? await api.POST("/api/applications", { body: { ...applicationBody(value), offer_id: null } })
      : await api.PUT("/api/applications/{application_id}", {
          params: { path: { application_id: editing.value.id } },
          body: applicationUpdateBody(value),
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
      ...applicationBody(application),
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

watch(
  () => route.query.mois,
  () => void load(),
);
onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Candidatures"
    title="Tes candidatures et tes preuves ORP"
    subtitle="Le suivi de chaque candidature et le formulaire du mois, prêt à remettre à ton conseiller ou à recopier dans Job-Room."
  />

  <section class="band">
    <div class="container">
      <nav
        class="prep-tabs"
        aria-label="Candidatures"
      >
        <RouterLink
          :to="tabLink('suivi')"
          :class="{ active: view === 'suivi' }"
          data-test="tab-suivi"
        >
          Suivi
        </RouterLink>
        <RouterLink
          :to="tabLink('orp')"
          :class="{ active: view === 'orp' }"
          data-test="tab-orp"
        >
          Preuves ORP
          <span
            v-if="orp?.incomplete"
            class="tab-count"
            :title="`${orp.incomplete} ligne(s) à compléter`"
          >{{ orp.incomplete }}</span>
        </RouterLink>
        <RouterLink
          :to="tabLink('journal')"
          :class="{ active: view === 'journal' }"
          data-test="tab-journal"
        >
          Journal des recherches
        </RouterLink>
      </nav>

      <JournalPanel v-if="view === 'journal'" />
      <template v-else-if="orp">
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
            <strong data-test="month">{{ formatMonth(orp.month) }}</strong>
            <button
              type="button"
              class="secondary small"
              aria-label="Mois suivant"
              data-test="next-month"
              @click="go(1)"
            >
              →
            </button>
          </div>
          <div
            class="month-goal"
            data-test="goal"
          >
            <span><strong>{{ orp.count }}</strong>{{ orp.target ? ` / ${orp.target}` : "" }} candidature(s)</span>
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
          <span
            :class="['badge', orp.state === 'remis' ? 'new' : '']"
            data-test="state"
          >{{ stateLabel }}</span>
          <button
            type="button"
            class="primary small"
            data-test="add-application"
            @click="addManual"
          >
            Ajouter une candidature <AppIcon name="chevron" />
          </button>
        </div>

        <aside
          v-if="toFollowUp.length"
          class="follow-up"
          data-test="follow-up"
        >
          <strong>À relancer ({{ toFollowUp.length }})</strong> : sans réponse depuis {{ REMIND_AFTER_DAYS }} jours ou plus.
          <span class="follow-up-list">
            <button
              v-for="application in toFollowUp"
              :key="application.id"
              type="button"
              class="link"
              @click="edit(application)"
            >
              {{ application.company }}
            </button>
          </span>
        </aside>

        <template v-if="view === 'suivi'">
          <label class="check all-months">
            <input
              v-model="allMonths"
              type="checkbox"
              data-test="all-months"
            > Tous les mois
          </label>
          <p
            v-if="loaded && !items.length"
            class="muted empty"
          >
            Aucune candidature en {{ formatMonth(orp.month) }}. Depuis une offre, « Marquer comme envoyée » l'ajoute ici.
          </p>
          <ApplicationsTable
            v-else
            :items="items"
            :show-month="allMonths"
            @edit="edit"
            @status="setStatus"
            @remove="remove"
          />
        </template>
        <OrpSheet
          v-else
          :data="orp"
          @reload="load"
          @edit="editById"
        />
      </template>
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
