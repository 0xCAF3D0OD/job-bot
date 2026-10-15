<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type NewsItem, type Offer, type Today, type Training } from "../api/client";
import DisclosureRow from "../components/DisclosureRow.vue";
import HelpTip from "../components/HelpTip.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PageHero from "../components/PageHero.vue";
import { sinceText } from "../components/status";
import { useCollect } from "../composables/useCollect";
import { useJobsMemory } from "../composables/useJobsMemory";
import { formatMonth, plural, scoreLevel } from "../format";
import { useDataChanged } from "../composables/useDataChanged";

// Une étape de démarrage : où aller pour la faire (docs/10 §2 b).
const STEPS: Record<Today["checklist"][number]["key"], { label: string; to?: string; hint?: string }> = {
  criteria: { label: "Dire ce que tu cherches (lieux, taux, types d'offres)", to: "/profil" },
  profile: { label: "Déposer ton CV et créer tes blocs de profil", to: "/profil?onglet=parcours" },
  identity: { label: "Saisir tes coordonnées (nom, adresse)", to: "/profil?onglet=coordonnees" },
  orp_target: { label: "Indiquer l'objectif mensuel de ton conseiller ORP", to: "/reglages" },
  notifications: {
    label: "Recevoir les notifications sur ton téléphone",
    to: "/reglages",
    hint: "réglage d'installation, voir le README",
  },
  imap: {
    label: "Brancher la collecte sur ta boîte Gmail",
    hint: "réglage d'installation, voir le README",
  },
};

// « Comment ça marche » (docs/21 §3) : le chemin en cinq étapes, avec où les faire.
const JOURNEY: Record<Today["journey"][number]["key"], { label: string; to: string; where: string }> = {
  alerts: { label: "Créer mes alertes sur les sites d'emploi", to: "/candidatures/alertes", where: "Candidatures › Alertes" },
  triage: { label: "Trier les offres reçues", to: "/candidatures/offres", where: "Candidatures › Offres" },
  apply: {
    label: "Préparer lettre et CV, puis postuler",
    to: "/candidatures/offres",
    where: "« Préparer ma candidature » sur une offre",
  },
  follow: { label: "Suivre les réponses et relancer", to: "/candidatures/suivi", where: "Candidatures › Suivi" },
  orp: { label: "Remettre les preuves à l'ORP chaque mois", to: "/candidatures/suivi", where: "Candidatures › Suivi" },
};

const today = ref<Today | null>(null);
const best = ref<Offer[]>([]);
// Blocs par catégorie (docs/19 §3).
const preparing = ref<Offer[]>([]);
const news = ref<NewsItem[]>([]);
const trainingsInProgress = ref<Training[]>([]);
const trainingIdea = ref<Training | null>(null);
const { message } = useCollect();

// Les deux menus déroulants s'ouvrent et se ferment ensemble (même hauteur), choix retenu.
const FOLDS_KEY = "jobbot-today-folds";
function readFolds(): boolean {
  try {
    return globalThis.localStorage?.getItem(FOLDS_KEY) !== "closed";
  } catch {
    return true;
  }
}
const foldsOpen = ref(readFolds());
function toggleFolds(): void {
  foldsOpen.value = !foldsOpen.value;
  try {
    globalThis.localStorage?.setItem(FOLDS_KEY, foldsOpen.value ? "open" : "closed");
  } catch {
    // Stockage indisponible : le choix vaut pour cette visite.
  }
}

// Comme le menu : retour à la candidature commencée ou à l'onglet quitté.
const { last: lastJobsPage } = useJobsMemory();

// Le plus urgent en tête (docs/43 n° 30) : entretien aujourd'hui ou demain, remise ORP dans
// moins de 5 jours.
const URGENT_DAYS = 5;
const DAY_MS = 86_400_000;
const time = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit" });

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function interviewText(iso: string, company: string): string {
  const at = new Date(iso);
  const day = startOfDay(at) === startOfDay(new Date()) ? "aujourd'hui" : "demain";
  return `Entretien ${day} à ${time.format(at)} chez ${company}`;
}

const orpDays = computed(() => {
  const due = today.value?.orp_due_date;
  if (!due) return null;
  const [y, m, d] = due.split("-").map(Number);
  return Math.round((new Date(y!, m! - 1, d!).getTime() - startOfDay(new Date())) / DAY_MS);
});
const orpUrgent = computed(() => orpDays.value !== null && orpDays.value <= URGENT_DAYS);
const orpText = computed(() => {
  const days = orpDays.value ?? 0;
  const month = formatMonth(today.value?.orp_due_month ?? "");
  if (days < 0) return `Preuves de ${month} à remettre : échéance passée le ${longDate.format(new Date(today.value!.orp_due_date!))}.`;
  const when = days === 0 ? "aujourd'hui" : days === 1 ? "demain" : `dans ${days} jours`;
  return `Preuves de ${month} à remettre ${when}.`;
});

// Une seule chose en orange (docs/43 n° 31) : la plus urgente.
const warn = computed<"orp" | "follow-up" | null>(() => {
  if (!today.value) return null;
  if (orpUrgent.value) return "orp";
  if (today.value.to_follow_up || today.value.contacts_to_follow_up) return "follow-up";
  return today.value.orp_due_month ? "orp" : null;
});

const steps = computed(() => today.value?.checklist ?? []);
const journeyDone = computed(() => today.value?.journey.filter((s) => s.done).length ?? 0);
const doneCount = computed(() => steps.value.filter((s) => s.done).length);
const showChecklist = computed(
  () => !!today.value && !today.value.checklist_dismissed && doneCount.value < steps.value.length,
);
const dateTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" }).format(
  new Date(),
);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

async function loadNews(): Promise<void> {
  // Les dernières de « Mon domaine » ; à défaut, celles qui parlent d'emploi. Rien d'autre :
  // sans actualité utile, la section disparaît (docs/43 n° 9).
  const mine = await api.GET("/api/news", { params: { query: { kind: "articles", limit: 3, domain_only: true } } });
  const items = (mine.data?.items ?? []).filter((i) => i.matched.length);
  if (items.length) {
    news.value = items;
    return;
  }
  const jobs = await api.GET("/api/news", { params: { query: { kind: "articles", limit: 3, topic: "jobs" } } });
  news.value = jobs.data?.items ?? [];
}

async function loadTrainings(): Promise<void> {
  const { data } = await api.GET("/api/trainings", { params: { query: { domain_only: true } } });
  const items = data?.items ?? [];
  trainingsInProgress.value = items.filter((t) => t.mark?.status === "in_progress").slice(0, 3);
  trainingIdea.value = items.find((t) => !t.mark && t.verified) ?? null;
}

async function load(): Promise<void> {
  const [day, offers, current] = await Promise.all([
    api.GET("/api/today"),
    api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 3 } } }),
    api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 20 } } }),
  ]);
  today.value = day.data ?? null;
  best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
  preparing.value = (current.data?.items ?? []).filter((o) => o.status === "preparing").slice(0, 3);
  // Actualités et formations : chargées à part, une panne n'empêche pas le reste.
  void loadNews().catch(() => undefined);
  void loadTrainings().catch(() => undefined);
}

async function dismissJourney(): Promise<void> {
  await api.PUT("/api/journey", { body: { dismissed: true } });
  await load();
}

async function dismiss(): Promise<void> {
  await api.PUT("/api/onboarding", { body: { dismissed: true } });
  await load();
}

onMounted(() => void load());
useDataChanged(load);
</script>

<template>
  <PageHero
    :title="dateTitle.charAt(0).toUpperCase() + dateTitle.slice(1)"
    subtitle="Le point sur ta recherche, et ce qu'il reste à faire."
  />
  <section class="band">
    <div
      v-if="today"
      class="container today"
    >
      <!-- Le plus urgent en tête (docs/43 n° 30). -->
      <p
        v-for="item in today.upcoming_interviews"
        :key="item.application_id"
        class="notice today-urgent"
        data-test="upcoming-interview"
      >
        {{ interviewText(item.at, item.company) }}.
        <RouterLink to="/candidatures/suivi">
          Préparer
        </RouterLink>
      </p>
      <p
        v-if="orpUrgent && today.orp_due_month"
        class="notice today-urgent"
        data-test="orp-urgent"
      >
        {{ orpText }}
        <RouterLink :to="{ path: '/candidatures/suivi', query: { mois: today.orp_due_month } }">
          Préparer la remise
        </RouterLink>
      </p>

      <div class="today-section-head">
        <h2>Candidatures</h2>
        <span
          class="today-collect"
          data-test="last-collect"
        >{{ message || (today.last_collect_at ? `Collecte ${sinceText(today.last_collect_at)}` : "Pas encore de collecte") }}</span>
        <RouterLink
          :to="lastJobsPage"
          class="link"
        >
          Ouvrir les candidatures
        </RouterLink>
      </div>
      <p
        v-for="item in today.interviews_to_review"
        :key="`${item.application_id}-${item.interview_on}`"
        class="notice"
        data-test="interview-to-review"
      >
        Comment s'est passé ton entretien chez {{ item.company }} ?
        <RouterLink :to="item.link">
          Faire le point
        </RouterLink>
      </p>
      <p
        v-if="today.alerts_waiting"
        class="notice"
        data-test="alerts-waiting"
      >
        {{ today.alerts_waiting === 1 ? "1 alerte créée depuis 3 jours n'a encore rien envoyé." : `${today.alerts_waiting} alertes créées depuis 3 jours n'ont encore rien envoyé.` }}
        <RouterLink to="/candidatures/alertes">
          Vérifier mes alertes
        </RouterLink>
      </p>
      <div class="today-stats">
        <RouterLink
          to="/candidatures/offres"
          class="stat"
          data-test="stat-review"
        >
          <strong>{{ today.to_review }}</strong>
          <span>{{ today.to_review === 1 ? "offre à examiner" : "offres à examiner" }}</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          class="stat"
          data-test="stat-month"
        >
          <strong>{{ today.month_count }}{{ today.month_target ? ` / ${today.month_target}` : "" }}</strong>
          <span>{{ today.month_count === 1 ? "candidature" : "candidatures" }} en {{ formatMonth(today.month) }}</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          :class="['stat', { warn: warn === 'follow-up' }]"
          data-test="stat-follow-up"
        >
          <strong>{{ today.to_follow_up }}</strong>
          <!-- Les contacts sans réponse rejoignent cette case (docs/43 n° 8). -->
          <span>à relancer<template v-if="today.contacts_to_follow_up"> · {{ plural(today.contacts_to_follow_up, "contact", "contacts") }}</template></span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          :class="['stat', { warn: warn === 'orp' }]"
          data-test="stat-orp"
        >
          <template v-if="today.orp_due_month && today.orp_due_date">
            <strong>{{ longDate.format(new Date(today.orp_due_date)) }}</strong>
            <span>preuves de {{ formatMonth(today.orp_due_month) }} à remettre</span>
          </template>
          <template v-else>
            <strong>À jour</strong>
            <span>aucune preuve ORP à remettre</span>
          </template>
        </RouterLink>
      </div>

      <!-- Deux menus déroulants côte à côte, de même hauteur, ouverts ou fermés ensemble
           (retour du 2026-10-14) ; le choix est retenu par le navigateur. -->
      <div class="today-pair">
        <section
          :class="['side-card', 'today-fold', { open: foldsOpen }]"
          data-test="preparing"
        >
          <button
            type="button"
            class="today-fold-head"
            :aria-expanded="foldsOpen"
            @click="toggleFolds"
          >
            <h2>Candidatures commencées</h2>
            <span class="today-fold-count">{{ preparing.length }}</span>
          </button>
          <template v-if="foldsOpen">
            <p
              v-if="!preparing.length"
              class="hint"
            >
              Aucune candidature en préparation.
            </p>
            <ul
              v-else
              class="today-list"
            >
              <li
                v-for="offer in preparing.slice(0, 3)"
                :key="offer.id"
              >
                <span>
                  <strong>{{ offer.title }}</strong><br>
                  <span class="muted">{{ offer.company || "Entreprise non indiquée" }}</span>
                </span>
                <RouterLink
                  :to="`/candidatures/offres/${offer.id}/preparer`"
                  class="link"
                >
                  Continuer
                </RouterLink>
              </li>
              <li
                v-if="preparing.length < Math.min(best.length, 3)"
                class="today-list-rest"
              >
                Rien d'autre en cours.
              </li>
            </ul>
            <RouterLink
              :to="{ path: '/candidatures/offres', query: { statut: 'in_progress' } }"
              class="link today-fold-more"
            >
              Voir les candidatures en cours
            </RouterLink>
          </template>
        </section>
        <section
          :class="['side-card', 'today-fold', { open: foldsOpen }]"
          data-test="best"
        >
          <button
            type="button"
            class="today-fold-head"
            :aria-expanded="foldsOpen"
            @click="toggleFolds"
          >
            <h2>Les mieux notées à examiner</h2>
            <span class="today-fold-count">{{ best.length }}</span>
          </button>
          <template v-if="foldsOpen">
            <p
              v-if="!best.length"
              class="hint"
            >
              Aucune offre notée en attente.
            </p>
            <ul
              v-else
              class="best-offers"
            >
              <li
                v-for="offer in best.slice(0, 3)"
                :key="offer.id"
              >
                <span :class="['score', scoreLevel(offer.score!)]">{{ offer.score }}</span>
                <span>
                  <strong>{{ offer.title }}</strong><br>
                  <span class="muted">{{ [offer.company, offer.location].filter(Boolean).join(" · ") }}</span>
                </span>
              </li>
              <li
                v-if="best.length < Math.min(preparing.length, 3)"
                class="today-list-rest"
              >
                Rien d'autre à examiner.
              </li>
            </ul>
            <RouterLink
              :to="{ path: '/candidatures/offres', query: { tri: 'score' } }"
              class="link today-fold-more"
            >
              Voir toutes les offres
            </RouterLink>
          </template>
        </section>
      </div>

      <div
        v-if="news.length"
        class="today-section-head"
      >
        <h2>
          Comprendre le marché
          <HelpTip
            label="Aide : actualités"
            text="Les actualités de ton domaine, sinon celles qui parlent d'emploi ; relevées toutes les 6 heures."
          />
        </h2>
        <RouterLink
          to="/actualites"
          class="link"
        >
          Toutes les actualités
        </RouterLink>
      </div>
      <article
        v-if="news.length"
        class="side-card"
        data-test="today-news"
      >
        <ul class="today-list">
          <li
            v-for="item in news"
            :key="item.id"
          >
            <span>
              <a
                :href="item.url"
                target="_blank"
                rel="noopener noreferrer"
              ><strong>{{ item.title }}</strong></a><br>
              <span class="muted">{{ item.source }} · {{ longDate.format(new Date(item.published_at)) }}</span>
            </span>
          </li>
        </ul>
      </article>

      <div class="today-section-head">
        <h2>Progresser</h2>
        <RouterLink
          to="/formations"
          class="link"
        >
          Toutes les formations
        </RouterLink>
      </div>
      <article
        class="side-card"
        data-test="today-trainings"
      >
        <ul
          v-if="trainingsInProgress.length || trainingIdea"
          class="today-list"
        >
          <li
            v-for="training in trainingsInProgress"
            :key="training.id"
          >
            <span>
              <strong>{{ training.title }}</strong><br>
              <span class="muted">En cours{{ training.mark?.progress ? ` · ${training.mark.progress}` : "" }} · {{ training.provider }}</span>
            </span>
          </li>
          <li
            v-if="trainingIdea"
            data-test="training-idea"
          >
            <span>
              <strong>{{ trainingIdea.title }}</strong><br>
              <span class="muted">À découvrir, dans ton domaine · {{ trainingIdea.provider }}</span>
            </span>
            <a
              :href="trainingIdea.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link"
            >Voir</a>
          </li>
        </ul>
        <p
          v-else
          class="hint"
        >
          Aucune formation suivie : marque celles qui t'intéressent dans <RouterLink to="/formations">
            Formations
          </RouterLink>.
        </p>
      </article>

      <!-- Les deux guides, repliés sous l'essentiel du jour, sur ordinateur comme sur téléphone
           (docs/34 §4, docs/43 n° 6). -->
      <component
        :is="DisclosureRow"
        v-if="!today.journey_dismissed && today.journey.length"
        class="journey today-help-row"
        title="Comment ça marche"
        :value="`${journeyDone} / ${today.journey.length}`"
        group="today-help"
        data-test="journey"
      >
        <div class="checklist-head">
          <h2>Comment ça marche</h2>
          <button
            type="button"
            class="link"
            data-test="dismiss-journey"
            @click="dismissJourney"
          >
            Masquer
          </button>
        </div>
        <ol>
          <li
            v-for="step in today.journey"
            :key="step.key"
            :class="{ done: step.done }"
            :data-test="`journey-${step.key}`"
          >
            <span
              class="tick"
              aria-hidden="true"
            />
            <span
              v-if="step.done"
              class="visually-hidden"
            >Fait : </span>
            <RouterLink :to="JOURNEY[step.key].to">
              {{ JOURNEY[step.key].label }}
            </RouterLink>
            <span class="hint journey-where">{{ JOURNEY[step.key].where }}</span>
          </li>
        </ol>
      </component>
      <component
        :is="DisclosureRow"
        v-if="showChecklist"
        class="checklist today-help-row"
        title="Pour bien démarrer"
        :value="`${doneCount} / ${steps.length}`"
        group="today-help"
        data-test="checklist"
      >
        <div class="checklist-head">
          <h2>Pour bien démarrer · {{ doneCount }} / {{ steps.length }}</h2>
          <button
            type="button"
            class="link"
            data-test="dismiss"
            @click="dismiss"
          >
            Masquer
          </button>
        </div>
        <ul>
          <li
            v-for="step in steps"
            :key="step.key"
            :class="{ done: step.done }"
            :data-test="`step-${step.key}`"
          >
            <span
              class="tick"
              aria-hidden="true"
            >{{ step.done ? "✓" : "" }}</span>
            <RouterLink
              v-if="!step.done && STEPS[step.key].to"
              :to="STEPS[step.key].to!"
            >
              {{ STEPS[step.key].label }}
            </RouterLink>
            <span v-else>{{ STEPS[step.key].label }}</span>
            <span
              v-if="!step.done && STEPS[step.key].hint"
              class="hint"
            >{{ STEPS[step.key].hint }}</span>
          </li>
        </ul>
      </component>
    </div>
    <div
      v-else
      class="container today"
    >
      <LoadingBlocks :heights="['7rem', '7rem', '12rem']" />
    </div>
  </section>
</template>
