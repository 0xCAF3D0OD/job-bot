<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type NewsItem, type Offer, type Today, type Training } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import { sinceText } from "../components/status";
import { useCollect } from "../composables/useCollect";
import { useJobsMemory } from "../composables/useJobsMemory";
import { formatMonth, scoreLevel } from "../format";

// Une étape de démarrage : où aller pour la faire (docs/10 §2 b).
const STEPS: Record<Today["checklist"][number]["key"], { label: string; to?: string; hint?: string }> = {
  criteria: { label: "Dire ce que tu cherches (lieux, taux, types d'offres)", to: "/profil" },
  profile: { label: "Déposer ton CV et créer tes blocs de profil", to: "/profil?onglet=parcours" },
  identity: { label: "Saisir tes coordonnées (nom, adresse)", to: "/profil?onglet=coordonnees" },
  orp_target: { label: "Indiquer l'objectif mensuel de ton conseiller ORP", to: "/reglages" },
  notifications: {
    label: "Recevoir les notifications sur ton téléphone",
    to: "/reglages",
    hint: "JOBBOT_NTFY_TOPIC dans .env",
  },
  imap: {
    label: "Brancher la collecte sur ta boîte Gmail",
    hint: "JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD dans .env",
  },
};

const today = ref<Today | null>(null);
const best = ref<Offer[]>([]);
// Blocs par catégorie (docs/19 §3).
const preparing = ref<Offer[]>([]);
const news = ref<NewsItem[]>([]);
const trainingsInProgress = ref<Training[]>([]);
const trainingIdea = ref<Training | null>(null);
const { message, running, collectNow } = useCollect();
// Comme le menu : retour à la candidature commencée ou à l'onglet quitté.
const { last: lastJobsPage } = useJobsMemory();

const steps = computed(() => today.value?.checklist ?? []);
const doneCount = computed(() => steps.value.filter((s) => s.done).length);
const showChecklist = computed(
  () => !!today.value && !today.value.checklist_dismissed && doneCount.value < steps.value.length,
);
const dateTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" }).format(
  new Date(),
);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

async function loadNews(): Promise<void> {
  // Les dernières de « Mon domaine » ; à défaut (domaine vide ou rien de neuf), les dernières tout court.
  const mine = await api.GET("/api/news", { params: { query: { limit: 3, domain_only: true } } });
  const items = (mine.data?.items ?? []).filter((i) => i.matched.length);
  if (items.length) {
    news.value = items;
    return;
  }
  const all = await api.GET("/api/news", { params: { query: { limit: 3 } } });
  news.value = all.data?.items ?? [];
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

async function dismiss(): Promise<void> {
  await api.PUT("/api/onboarding", { body: { dismissed: true } });
  await load();
}

onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Aujourd'hui"
    :title="dateTitle.charAt(0).toUpperCase() + dateTitle.slice(1)"
    subtitle="Le point sur ta recherche, et ce qu'il reste à faire."
  />
  <section class="band">
    <div
      v-if="today"
      class="container today"
    >
      <article
        v-if="showChecklist"
        class="side-card checklist"
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
            >· {{ STEPS[step.key].hint }}</span>
          </li>
        </ul>
      </article>

      <div class="today-section-head">
        <h2>Candidatures</h2>
        <RouterLink
          :to="lastJobsPage"
          class="link"
        >
          Ouvrir les candidatures
        </RouterLink>
      </div>
      <p
        v-if="today.alerts_waiting"
        class="notice"
        data-test="alerts-waiting"
      >
        {{ today.alerts_waiting }} alerte(s) créée(s) depuis 3 jours n'ont encore rien envoyé.
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
          <span>offre(s) à examiner</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          class="stat"
          data-test="stat-month"
        >
          <strong>{{ today.month_count }}{{ today.month_target ? ` / ${today.month_target}` : "" }}</strong>
          <span>candidature(s) en {{ formatMonth(today.month) }}</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          :class="['stat', { warn: today.to_follow_up }]"
          data-test="stat-follow-up"
        >
          <strong>{{ today.to_follow_up }}</strong>
          <span>à relancer (sans réponse depuis 10 jours)</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/preuves"
          :class="['stat', { warn: today.orp_due_month }]"
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

      <div class="today-grid">
        <article
          v-if="preparing.length"
          class="side-card"
          data-test="preparing"
        >
          <h2>Candidatures commencées</h2>
          <ul class="today-list">
            <li
              v-for="offer in preparing"
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
          </ul>
        </article>
        <article class="side-card">
          <h2>Les mieux notées à examiner</h2>
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
              v-for="offer in best"
              :key="offer.id"
            >
              <span :class="['score', scoreLevel(offer.score!)]">{{ offer.score }}</span>
              <span>
                <strong>{{ offer.title }}</strong><br>
                <span class="muted">{{ [offer.company, offer.location].filter(Boolean).join(" · ") }}</span>
              </span>
            </li>
          </ul>
          <RouterLink
            :to="{ path: '/candidatures/offres', query: { tri: 'score' } }"
            class="link"
          >
            Voir toutes les offres
          </RouterLink>
        </article>
        <article class="side-card">
          <h2>Collecte</h2>
          <p class="hint">
            {{
              today.last_collect_at
                ? `Dernière collecte réussie ${sinceText(today.last_collect_at)}.`
                : "Aucune collecte réussie pour l'instant."
            }}
            Automatique toutes les 2 heures en journée.
          </p>
          <button
            type="button"
            class="primary small"
            :disabled="running"
            data-test="collect-today"
            @click="collectNow"
          >
            Collecter maintenant <AppIcon name="chevron" />
          </button>
          <span
            v-if="message"
            class="hint"
            role="status"
          >{{ message }}</span>
        </article>
      </div>

      <div class="today-section-head">
        <h2>Comprendre le marché</h2>
        <RouterLink
          to="/actualites"
          class="link"
        >
          Toutes les actualités
        </RouterLink>
      </div>
      <article
        class="side-card"
        data-test="today-news"
      >
        <p
          v-if="!news.length"
          class="hint"
        >
          Pas encore d'actualités : elles sont relevées toutes les 6 heures.
        </p>
        <ul
          v-else
          class="today-list"
        >
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
    </div>
  </section>
</template>
