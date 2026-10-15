<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type NewsItem, type Offer, type Today, type Training } from "../api/client";
import CompanyLogo from "../components/CompanyLogo.vue";
import DashTile from "../components/dash/DashTile.vue";
import OrpGauge from "../components/dash/OrpGauge.vue";
import WeekChart from "../components/dash/WeekChart.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import Illustration, { type IllustrationName } from "../components/Illustration.vue";
import AppIcon from "../components/AppIcon.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PageHero from "../components/PageHero.vue";
import { sinceText } from "../components/status";
import { useCollect } from "../composables/useCollect";
import { formatMonth, localDate, plural, scoreLevel } from "../format";
import { useDataChanged } from "../composables/useDataChanged";
import { useLoadingGate } from "../composables/useLoadingGate";

// Une étape de démarrage : où aller pour la faire (docs/10 §2 b).
// Chaque étape a son illustration (docs/58 §3.1), montrée en grand pour l'étape à faire.
const STEPS: Record<
  Today["checklist"][number]["key"],
  { label: string; to?: string; hint?: string; illustration: IllustrationName }
> = {
  criteria: { label: "Dire ce que tu cherches (lieux, taux, types d'offres)", to: "/profil", illustration: "settings" },
  profile: { label: "Déposer ton CV et créer tes blocs de profil", to: "/profil?onglet=parcours", illustration: "my-resume" },
  identity: { label: "Saisir tes coordonnées (nom, adresse)", to: "/profil?onglet=coordonnees", illustration: "profile" },
  orp_target: { label: "Indiquer l'objectif mensuel de ton conseiller ORP", to: "/reglages", illustration: "stepping-up" },
  notifications: {
    label: "Recevoir les notifications sur ton téléphone",
    to: "/reglages",
    hint: "réglage d'installation, voir le README",
    illustration: "lock-screen-notifications",
  },
  imap: {
    label: "Brancher la collecte sur ta boîte Gmail",
    hint: "réglage d'installation, voir le README",
    illustration: "online-connection",
  },
};

// « Comment ça marche » (docs/21 §3) : le chemin en cinq étapes, avec où les faire.
const JOURNEY: Record<
  Today["journey"][number]["key"],
  { label: string; to: string; where: string; illustration: IllustrationName }
> = {
  alerts: {
    label: "Créer mes alertes sur les sites d'emploi",
    to: "/candidatures/alertes",
    where: "Candidatures › Alertes",
    illustration: "mailbox",
  },
  triage: { label: "Trier les offres reçues", to: "/candidatures/offres", where: "Candidatures › Offres", illustration: "mobile-inbox" },
  apply: {
    label: "Préparer lettre et CV, puis postuler",
    to: "/candidatures/offres",
    where: "« Préparer ma candidature » sur une offre",
    illustration: "message-sent",
  },
  follow: { label: "Suivre les réponses et relancer", to: "/candidatures/suivi", where: "Candidatures › Suivi", illustration: "date-picker" },
  orp: {
    label: "Remettre les preuves à l'ORP chaque mois",
    to: "/candidatures/suivi",
    where: "Candidatures › Suivi",
    illustration: "certification",
  },
};

const today = ref<Today | null>(null);
const { ready: loadReady, illustrated: loadIllustrated } = useLoadingGate(() => !!today.value);
const best = ref<Offer[]>([]);
// Blocs par catégorie (docs/19 §3).
const preparing = ref<Offer[]>([]);
const news = ref<NewsItem[]>([]);
const trainingsInProgress = ref<Training[]>([]);
const trainingIdea = ref<Training | null>(null);
const { message } = useCollect();

// Tableau « À examiner en priorité » (docs/54 §2) : deux onglets, le choix n'est pas retenu.
const tableTab = ref<"best" | "preparing">("best");
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

// Tuiles : courbes des 7 derniers jours et tendance de la semaine (docs/54 §2).
const offersWeek = computed(() => today.value?.week?.map((d) => d.offers) ?? []);
const sentWeek = computed(() => today.value?.week?.map((d) => d.applications) ?? []);
const sum = (values: number[]): number => values.reduce((n, v) => n + v, 0);

// Comme le menu : retour à la candidature commencée ou à l'onglet quitté.
const router = useRouter();
const offerLink = (id: number) => ({ path: "/candidatures/offres", query: { offre: id } });

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
  return Math.round((localDate(due).getTime() - startOfDay(new Date())) / DAY_MS);
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
const nextStep = computed(() => steps.value.find((s) => !s.done) ?? null);
const nextJourney = computed(() => today.value?.journey.find((s) => !s.done) ?? null);
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
    api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 5 } } }),
    api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 20 } } }),
  ]);
  today.value = day.data ?? null;
  best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
  preparing.value = (current.data?.items ?? []).filter((o) => o.status === "preparing").slice(0, 5);
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
      v-if="today && loadReady"
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
      <p class="dash-meta">
        <span
          class="today-collect"
          data-test="last-collect"
        >{{ message || (today.last_collect_at ? `Collecte ${sinceText(today.last_collect_at)}` : "Pas encore de collecte") }}</span>
      </p>

      <!-- Tableau de bord (docs/54) : quatre tuiles et la semaine, puis les offres et l'ORP. -->
      <div class="dash-row dash-top">
        <div class="dash-tiles">
          <DashTile
            to="/candidatures/offres"
            icon="inbox"
            label="À examiner"
            :value="String(today.to_review)"
            :trend="`+${sum(offersWeek)} cette semaine`"
            :rising="sum(offersWeek) > 0"
            :values="offersWeek"
            tone="accent"
            data-test="stat-review"
          />
          <DashTile
            to="/candidatures/suivi"
            icon="send"
            :label="(formatMonth(today.month).split(' ')[0] ?? '').replace(/^./, (c) => c.toUpperCase())"
            :value="`${today.month_count}${today.month_target ? ` / ${today.month_target}` : ''}`"
            :trend="`+${sum(sentWeek)} cette semaine`"
            :rising="sum(sentWeek) > 0"
            :values="sentWeek"
            data-test="stat-month"
          />
          <DashTile
            to="/candidatures/suivi"
            icon="refresh"
            label="À relancer"
            :value="String(today.to_follow_up)"
            :trend="today.contacts_to_follow_up ? `dont ${plural(today.contacts_to_follow_up, 'contact', 'contacts')}` : 'candidatures'"
            :tone="warn === 'follow-up' ? 'warn' : undefined"
            :class="{ warn: warn === 'follow-up' }"
            data-test="stat-follow-up"
          />
          <DashTile
            :to="today.orp_due_month ? { path: '/candidatures/suivi', query: { mois: today.orp_due_month } } : '/candidatures/suivi'"
            icon="file"
            label="Preuves ORP"
            :value="today.orp_due_month && today.orp_due_date ? longDate.format(new Date(today.orp_due_date)) : 'À jour'"
            :trend="today.orp_due_month ? `${formatMonth(today.orp_due_month).split(' ')[0]} à remettre` : 'rien à remettre'"
            :tone="warn === 'orp' ? 'warn' : 'mint'"
            :class="{ warn: warn === 'orp' }"
            data-test="stat-orp"
          />
        </div>
        <WeekChart :week="today.week ?? []" />
      </div>

      <div class="dash-row dash-mid">
        <section
          class="dash-card dash-table"
          data-test="best"
        >
          <header class="dash-card-head">
            <h2>À examiner en priorité</h2>
            <div
              class="segmented small"
              role="radiogroup"
              aria-label="Offres affichées"
            >
              <button
                type="button"
                role="radio"
                :aria-checked="tableTab === 'best'"
                data-test="tab-best"
                @click="tableTab = 'best'"
              >
                Mieux notées
              </button>
              <button
                type="button"
                role="radio"
                :aria-checked="tableTab === 'preparing'"
                data-test="tab-preparing"
                @click="tableTab = 'preparing'"
              >
                Commencées<span
                  v-if="preparing.length"
                  class="tab-count"
                >{{ preparing.length }}</span>
              </button>
            </div>
          </header>
          <div v-show="tableTab === 'best'">
            <p
              v-if="!best.length"
              class="hint"
            >
              Aucune offre notée en attente.
            </p>
            <table
              v-else
              class="dash-offers"
            >
              <thead>
                <tr>
                  <th>Offre</th>
                  <th>Note</th>
                  <th class="dash-col-place">
                    Lieu
                  </th>
                  <th class="dash-col-date">
                    Reçue
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="offer in best"
                  :key="offer.id"
                  class="row-link"
                  @click="router.push(offerLink(offer.id))"
                >
                  <td>
                    <span class="dash-offer">
                      <CompanyLogo :offer="offer" />
                      <span>
                        <RouterLink
                          :to="offerLink(offer.id)"
                          class="row-link-title"
                          @click.stop
                        ><strong>{{ offer.title }}</strong></RouterLink>
                        <span class="muted">{{ offer.company || "Entreprise non indiquée" }}</span>
                      </span>
                    </span>
                  </td>
                  <td><span :class="['score', scoreLevel(offer.score!)]">{{ offer.score }}</span></td>
                  <td class="dash-col-place muted">
                    {{ offer.location || "—" }}
                  </td>
                  <td class="dash-col-date muted">
                    {{ offer.first_seen_at ? shortDate.format(new Date(offer.first_seen_at)) : "—" }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div
            v-show="tableTab === 'preparing'"
            data-test="preparing"
          >
            <p
              v-if="!preparing.length"
              class="hint"
            >
              Aucune candidature en préparation.
            </p>
            <table
              v-else
              class="dash-offers"
            >
              <tbody>
                <tr
                  v-for="offer in preparing"
                  :key="offer.id"
                  class="row-link"
                  @click="router.push(`/candidatures/offres/${offer.id}/preparer`)"
                >
                  <td>
                    <span class="dash-offer">
                      <CompanyLogo :offer="offer" />
                      <span>
                        <RouterLink
                          :to="`/candidatures/offres/${offer.id}/preparer`"
                          class="row-link-title"
                          @click.stop
                        ><strong>{{ offer.title }}</strong></RouterLink>
                        <span class="muted">{{ offer.company || "Entreprise non indiquée" }}</span>
                      </span>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <OrpGauge
          :count="today.month_count"
          :target="today.month_target ?? null"
          :month="today.month"
          :history="today.orp_history ?? []"
        />
      </div>

      <div class="dash-row dash-bottom">
        <section
          class="dash-card"
          data-test="today-trainings"
        >
          <header class="dash-card-head">
            <h2>
              <RouterLink
                to="/formations"
                class="dash-title-link"
              >
                <span class="dash-bubble small"><AppIcon name="book" /></span>
                Progresser
              </RouterLink>
            </h2>
          </header>
          <ul
            v-if="trainingsInProgress.length || trainingIdea"
            class="today-list"
          >
            <li
              v-for="training in trainingsInProgress"
              :key="training.id"
            >
              <span>
                <RouterLink to="/formations"><strong>{{ training.title }}</strong></RouterLink><br>
                <span class="muted">En cours{{ training.mark?.progress ? ` · ${training.mark.progress}` : "" }} · {{ training.provider }}</span>
              </span>
            </li>
            <li
              v-if="trainingIdea"
              data-test="training-idea"
            >
              <span>
                <a
                  :href="trainingIdea.url"
                  target="_blank"
                  rel="noopener noreferrer"
                ><strong>{{ trainingIdea.title }}</strong></a><br>
                <span class="muted">À découvrir, dans ton domaine · {{ trainingIdea.provider }}</span>
              </span>
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
        </section>
        <section
          v-if="news.length"
          class="dash-card"
          data-test="today-news"
        >
          <header class="dash-card-head">
            <h2>
              <RouterLink
                to="/actualites"
                class="dash-title-link"
              >
                <span class="dash-bubble small"><AppIcon name="news" /></span>
                Comprendre le marché
              </RouterLink>
            </h2>
          </header>
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
        </section>
      </div>

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
        <RouterLink
          v-if="nextJourney"
          :to="JOURNEY[nextJourney.key].to"
          class="onboard-next"
          data-test="journey-next"
        >
          <Illustration :name="JOURNEY[nextJourney.key].illustration" />
          <span class="onboard-next-text">
            <span class="hint">Étape {{ today.journey.indexOf(nextJourney) + 1 }} sur {{ today.journey.length }}</span>
            <strong>{{ JOURNEY[nextJourney.key].label }}</strong>
            <span class="hint">{{ JOURNEY[nextJourney.key].where }}</span>
          </span>
        </RouterLink>
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
        <component
          :is="STEPS[nextStep.key].to ? 'RouterLink' : 'div'"
          v-if="nextStep"
          v-bind="STEPS[nextStep.key].to ? { to: STEPS[nextStep.key].to } : {}"
          class="onboard-next"
          data-test="checklist-next"
        >
          <Illustration :name="STEPS[nextStep.key].illustration" />
          <span class="onboard-next-text">
            <span class="hint">Étape {{ steps.indexOf(nextStep) + 1 }} sur {{ steps.length }}</span>
            <strong>{{ STEPS[nextStep.key].label }}</strong>
            <span
              v-if="STEPS[nextStep.key].hint"
              class="hint"
            >{{ STEPS[nextStep.key].hint }}</span>
          </span>
        </component>
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
      <LoadingBlocks
        :heights="['7rem', '7rem', '12rem']"
        :illustrated="loadIllustrated"
      />
    </div>
  </section>
</template>
