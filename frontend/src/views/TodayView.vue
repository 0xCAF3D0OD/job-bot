
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";

import { api, type Highlight, type Offer, type Today } from "../api/client";
import ActionBand from "../components/ActionBand.vue";
import AppIcon from "../components/AppIcon.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import RhythmCard from "../components/RhythmCard.vue";
import FirstSteps from "../components/FirstSteps.vue";
import { useAuth } from "../composables/useAuth";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import Illustration from "../components/Illustration.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import OrpMonth from "../components/OrpMonth.vue";
import ScoreWord from "../components/ScoreWord.vue";
import SuccessCard from "../components/SuccessCard.vue";
import PageHero from "../components/PageHero.vue";
import { sinceText } from "../components/status";
import { useCollect } from "../composables/useCollect";
import { DOSE, DOSE_CATCH_UP, triageDoneToday } from "../composables/useDailyDose";
import { daysBefore, formatMonth, localDate, orpPace, plural } from "../format";
import type { IconName } from "../icons";
import { useDataChanged } from "../composables/useDataChanged";
import { offerUndo } from "../composables/useUndo";
import { usePageReady } from "../composables/usePageTransition";

// Aujourd'hui (1.6.51, docs/interface.md n° 17, planche « Revue 1.6.46 ») : une seule colonne. La
// phrase de conclusion ; le tri du jour dans la bande d'action, seule action principale ; puis
// « À faire aujourd'hui. », « Mois ORP. » et « À retenir. ».
const today = ref<Today | null>(null);
usePageReady("today", () => !!today.value);
const best = ref<Offer[]>([]);
const preparing = ref<Offer[]>([]);
const highlight = ref<Highlight | null>(null);
// Le tri du jour fini sur cet appareil (l'écran de tri le note à la fin de la pile).
const triageDone = ref(false);
// Un jour de repos (docs/86) : aucune liste à traiter.
const restDay = computed(() => today.value?.rhythm?.research_today === false);
// Le mois ORP en retard sur son rythme (format.orpPace).
const monthBehind = computed(() => {
  const t = today.value;
  return !!t && orpPace(t.month_count, t.month_target, t.month)?.state === "behind";
});
const rhythmPaused = computed(() => !!today.value?.rhythm?.pause_until);
const { message } = useCollect();

const DAY_MS = 86_400_000;
// Une remise ORP dans moins de 5 jours passe en tête de « À faire » (docs/43 n° 30).
const URGENT_DAYS = 5;
const time = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit" });
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}
// « Aujourd'hui à 09:30 », « Demain à 14:00 ».
function dayAndTime(iso: string): string {
  const at = new Date(iso);
  const day = startOfDay(at) === startOfDay(new Date()) ? "Aujourd'hui" : "Demain";
  return `${day} à ${time.format(at)}`;
}

// La dose du jour (docs/86) : 3 offres ; 5 quand le mois ORP est à rattraper (docs/124 §D).
const dose = computed(() => best.value.slice(0, monthBehind.value ? DOSE_CATCH_UP : DOSE));
// Les premiers pas (docs/128) : tant qu'il en manque, la carte remplace la phrase et le tri ; le mois
// ORP reste, le reste attend.
const starting = computed(() => {
  const t = today.value;
  return !!t && !t.first_steps_dismissed && t.first_steps.some((s) => !s.done);
});
// Le tri à faire : la bande d'action. Sinon, la carte neutre « Tri terminé · À demain ».
const triagePending = computed(() => !restDay.value && !rhythmPaused.value && dose.value.length > 0 && !triageDone.value);
const showTriage = computed(() => !starting.value && !restDay.value && !rhythmPaused.value);
const triageSummary = computed(() =>
  dose.value.length === 1 ? "1 offre à trier :" : `${dose.value.length} offres, la meilleure d'abord :`,
);

// La phrase du jour (docs/95 §1) : ce qu'il y a à faire, les nombres en avant.
type Part = { text: string; strong?: boolean };
const sentence = computed<Part[]>(() => {
  const t = today.value;
  if (!t) return [];
  const pause = t.rhythm?.pause_until;
  if (pause) return [{ text: `En pause jusqu'au ${longDate.format(localDate(pause))}.` }];
  // Jour de repos (1.6.26) : une seule phrase, qui dit quoi faire si l'on veut avancer.
  if (restDay.value) {
    const rest: Part[] = [{ text: "Jour de repos." }];
    if (t.to_follow_up) rest.push({ text: " Si tu veux avancer : " }, { text: plural(t.to_follow_up, "relance", "relances"), strong: true }, { text: " en attente." });
    else if (t.to_review) rest.push({ text: " Si tu veux avancer : " }, { text: plural(t.to_review, "offre", "offres"), strong: true }, { text: " à examiner." });
    return rest;
  }
  const items: Part[][] = [];
  if (triagePending.value) items.push([{ text: plural(dose.value.length, "offre", "offres"), strong: true }, { text: " à trier" }]);
  if (t.to_follow_up) items.push([{ text: plural(t.to_follow_up, "relance", "relances"), strong: true }]);
  if (!items.length) {
    // « Ta semaine est faite » se tait quand le mois est en retard (1.6.27).
    const weekDone = t.rhythm && t.rhythm.target !== null && t.rhythm.count >= t.rhythm.target && !monthBehind.value;
    return [{ text: weekDone ? "Tout est à jour. Ta semaine est faite." : "Tout est à jour." }];
  }
  // Le tri fini : « Il reste 6 relances. »
  const parts: Part[] = triageDone.value ? [{ text: "Il reste " }] : [];
  items.forEach((item, index) => {
    if (index) parts.push({ text: index === items.length - 1 ? " et " : ", " });
    parts.push(...item);
  });
  parts.push({ text: "." });
  const first = parts[0]!;
  parts[0] = { ...first, text: first.text.charAt(0).toUpperCase() + first.text.slice(1) };
  return parts;
});

// « À faire aujourd'hui. » : des lignes toutes construites pareil (icône, titre avec un verbe, une
// ligne de détail, un bouton à contour) ; seulement ce qui a quelque chose à faire, le daté d'abord.
type Task = { key: string; test: string; icon: IconName; title: string; detail: string; action: string; to: RouteLocationRaw };
const tasks = computed<Task[]>(() => {
  const t = today.value;
  if (!t || starting.value) return [];
  const list: Task[] = [];
  if (t.orp_meeting_at) {
    list.push({ key: "meeting", test: "orp-meeting-soon", icon: "calendar", title: "Préparer le rendez-vous ORP", detail: `${dayAndTime(t.orp_meeting_at)} : ta feuille est prête.`, action: "Voir", to: "/candidatures/rendez-vous-orp" });
  }
  for (const item of t.upcoming_interviews ?? []) {
    list.push({ key: `interview-${item.application_id}`, test: "upcoming-interview", icon: "users", title: "Préparer l'entretien", detail: `${dayAndTime(item.at)} chez ${item.company}.`, action: "Préparer", to: "/candidatures/suivi" });
  }
  const orp = orpTask.value;
  if (orp?.urgent) list.push(orp.task);
  if (t.to_follow_up) {
    const oldest = Math.max(0, ...(t.follow_ups ?? []).map((f) => daysBefore(f.sent_at)));
    list.push({
      key: "follow-ups",
      test: "follow-ups",
      icon: "message",
      title: `Relancer ${plural(t.to_follow_up, "candidature", "candidatures")}`,
      detail: oldest ? (t.to_follow_up === 1 ? `Elle attend depuis ${oldest} jours.` : `La plus ancienne attend depuis ${oldest} jours.`) : "Sans réponse depuis 10 jours.",
      action: "Relancer",
      to: "/candidatures/suivi",
    });
  }
  if (preparing.value.length) {
    const n = preparing.value.length;
    list.push({
      key: "preparing",
      test: "preparing",
      icon: "send",
      title: `Préparer ${plural(n, "candidature", "candidatures")}`,
      detail: n === 1 ? "Une offre gardée attend sa lettre." : `${n} offres gardées attendent leur lettre.`,
      action: "Préparer",
      to: n === 1 ? `/candidatures/offres/${preparing.value[0]!.id}/preparer` : { path: "/candidatures/offres", query: { statut: "in_progress" } },
    });
  }
  if (orp && !orp.urgent) list.push(orp.task);
  for (const item of t.interviews_to_review ?? []) {
    list.push({ key: `review-${item.application_id}-${item.interview_on}`, test: "interview-to-review", icon: "clipboard-check", title: "Faire le point sur l'entretien", detail: `Chez ${item.company} : comment s'est-il passé ?`, action: "Faire le point", to: item.link });
  }
  if (t.alerts_waiting) {
    list.push({
      key: "alerts",
      test: "alerts-waiting",
      icon: "bell",
      title: `Vérifier ${plural(t.alerts_waiting, "alerte", "alertes")}`,
      detail: t.alerts_waiting === 1 ? "Créée hier, elle n'a encore rien envoyé." : "Créées depuis hier, elles n'ont encore rien envoyé.",
      action: "Vérifier",
      to: "/candidatures/alertes",
    });
  }
  return list;
});

// Les preuves ORP à remettre (docs/95 §2) : en tête quand l'échéance approche.
const orpTask = computed<{ urgent: boolean; task: Task } | null>(() => {
  const t = today.value;
  if (!t?.orp_due_month || !t.orp_due_date) return null;
  const due = localDate(t.orp_due_date);
  const days = Math.round((due.getTime() - startOfDay(new Date())) / DAY_MS);
  const urgent = days <= URGENT_DAYS;
  return {
    urgent,
    task: {
      key: "orp",
      test: urgent ? "orp-urgent" : "orp-due",
      icon: "check-circle",
      title: `Remettre les preuves de ${formatMonth(t.orp_due_month)}`,
      detail: days < 0 ? `Échéance passée le ${longDate.format(due)}.` : days === 0 ? "À remettre aujourd'hui." : `À remettre avant le ${longDate.format(due)}.`,
      action: "Compléter",
      to: { path: "/candidatures/suivi", query: { mois: t.orp_due_month } },
    },
  };
});

const dateTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" }).format(
  new Date(),
);
// L'étiquette au-dessus du titre : la date et la dernière collecte.
const eyebrow = computed(() => {
  // La collecte seulement quand elle tourne ou a plus d'un jour de retard (docs/131 §B.6).
  const last = today.value?.last_collect_at;
  const late = !!last && Date.now() - new Date(last).getTime() > DAY_MS;
  const collect = message.value || (late ? `collecte ${sinceText(last!)}` : "");
  return collect ? `${dateTitle} · ${collect}` : dateTitle;
});

// R, l'objectif du mois atteint (docs/123 §2) : une victoire, une fois par mois et par appareil.
const goalWon = ref(false);
// Les cinq premiers pas faits (docs/128 §1) : le serveur le dit une seule fois.
const stepsWon = ref(false);
function firstGoal(t: Today | null): boolean {
  if (!t?.month_target || t.month_count < t.month_target) return false;
  const key = `jobA1.orp-goal.${t.month}`;
  try {
    if (localStorage.getItem(key)) return false;
    localStorage.setItem(key, "1");
    return true;
  } catch {
    return false;
  }
}

// Une panne de réseau au chargement : l'écran « Pas de connexion » (planche « Illustrations »).
const offline = ref(false);
async function load(): Promise<void> {
  try {
    await fetchAll();
    offline.value = false;
  } catch (cause) {
    if (!isNetworkError(cause)) throw cause;
    offline.value = true;
  }
}
async function fetchAll(): Promise<void> {
  const [day, offers, current, report] = await Promise.all([
    api.GET("/api/today"),
    // La dose du jour (docs/86) : les meilleures, pas toute la pile.
    api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: DOSE_CATCH_UP } } }),
    api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 100 } } }),
    // « À retenir. » : l'écart du Bilan sur les 3 derniers mois.
    api.GET("/api/insights", { params: { query: { period: "recent" } } }),
  ]);
  today.value = day.data ?? null;
  triageDone.value = triageDoneToday();
  goalWon.value = firstGoal(today.value);
  // Montrée une fois : on le dit au serveur, elle ne revient plus (docs/128 §1).
  if (today.value?.first_steps_finished && !stepsWon.value) {
    stepsWon.value = true;
    void api.PUT("/api/first-steps", { body: { celebrated: true } });
  }
  best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
  preparing.value = (current.data?.items ?? []).filter((o) => o.status === "preparing");
  highlight.value = report.data?.highlight ?? null;
}

// Masquer les premiers pas : la carte s'en va tout de suite, « Annuler » pendant 6 secondes
// (docs/108) ; ensuite, elle ne revient plus (docs/128 §1).
function dismissSteps(): void {
  if (!today.value) return;
  today.value = { ...today.value, first_steps_dismissed: true };
  void offerUndo({
    message: "Premiers pas masqués.",
    commit: async (keepalive) => {
      const { response } = await api.PUT("/api/first-steps", { body: { dismissed: true }, keepalive });
      return response.ok;
    },
    restore: () => {
      if (today.value) today.value = { ...today.value, first_steps_dismissed: false };
    },
  });
}

onMounted(() => void load());
useDataChanged(load);
const { me } = useAuth();
</script>

<template>
  <PageHero
    title="Aujourd'hui"
    :eyebrow="eyebrow"
  />
  <section class="band">
    <div
      v-if="today"
      class="container today"
    >
      <!-- Accueil remis à plus tard (docs/66 §4) : le reprendre d'un clic. -->
      <RouterLink
        v-if="me?.welcome === 'postponed'"
        to="/bienvenue"
        class="notice today-welcome"
        data-test="finish-welcome"
      >
        <strong>Terminer mon accueil</strong> : quelques questions pour régler ta recherche.
      </RouterLink>

      <!-- Les premiers pas (docs/128) : la seule action tant qu'il en manque. -->
      <FirstSteps
        v-if="starting"
        :steps="today.first_steps"
        :has-offers="today.has_offers ?? true"
        :offer-id="today.first_steps_offer_id ?? null"
        :pick-ready="!restDay && !rhythmPaused && best.length > 0"
        @dismiss="dismissSteps"
      />
      <!-- La phrase de conclusion, en grand (docs/95 §1). -->
      <p
        v-else
        class="today-sentence"
        data-test="today-sentence"
      >
        <template
          v-for="(part, index) in sentence"
          :key="index"
        >
          <strong v-if="part.strong">{{ part.text }}</strong><template v-else>
            {{ part.text }}
          </template>
        </template>
      </p>

      <!-- Le tri du jour : la bande d'action, seule action principale ; ouvre l'écran de tri. -->
      <template v-if="showTriage">
        <ActionBand
          v-if="triagePending"
          title="Tri du jour."
          :summary="triageSummary"
          action="Commencer le tri"
          :to="{ name: 'triage' }"
        >
          <div
            class="today-triage-preview"
            data-test="best"
          >
            <CompanyLogo :offer="dose[0]!" />
            <span class="today-triage-offer">
              <strong>{{ dose[0]!.title }}</strong>
              <span class="muted">{{ [dose[0]!.company || "Entreprise non indiquée", dose[0]!.location].filter(Boolean).join(" · ") }}</span>
            </span>
            <span class="today-triage-why">
              <ScoreWord :score="dose[0]!.score ?? null" />
              <span v-if="dose[0]!.why">{{ dose[0]!.why }}</span>
            </span>
          </div>
        </ActionBand>
        <section
          v-else
          class="today-triage-done"
          aria-labelledby="today-triage-title"
          data-test="triage-done"
        >
          <!-- Le tri fait : l'illustration de la réussite (planche « Illustrations », règle §4). -->
          <Illustration
            v-if="triageDone"
            name="reussite"
            class="spot"
            sizes="(max-width: 820px) 260px, 424px"
          />
          <h2 id="today-triage-title">
            Tri du jour.
          </h2>
          <p>{{ triageDone ? "Tri terminé · À demain" : "Rien à trier · À demain" }}</p>
        </section>
      </template>

      <!-- À faire aujourd'hui : masqué s'il n'y a rien, la conclusion le dit. -->
      <section
        v-if="tasks.length"
        class="today-section"
        aria-labelledby="today-tasks-title"
        data-test="today-tasks"
      >
        <h2 id="today-tasks-title">
          À faire aujourd'hui.
        </h2>
        <ul class="today-tasks">
          <li
            v-for="task in tasks"
            :key="task.key"
          >
            <RouterLink
              :to="task.to"
              class="today-task"
              :data-test="task.test"
            >
              <span
                class="today-task-icon"
                aria-hidden="true"
              ><AppIcon :name="task.icon" /></span>
              <span class="today-task-main">
                <strong>{{ task.title }}</strong>
                <span>{{ task.detail }}</span>
              </span>
              <span class="button-link today-task-action">{{ task.action }}</span>
            </RouterLink>
          </li>
        </ul>
      </section>

      <!-- Mois ORP : le mois puis la semaine, face à face sur ordinateur (docs/95 §4, docs/123 Q). -->
      <section
        class="today-section"
        aria-labelledby="today-orp-title"
      >
        <h2 id="today-orp-title">
          Mois ORP.
        </h2>
        <div
          class="dash-card today-orp"
          data-test="orp-month"
        >
          <OrpMonth
            title="Ce mois"
            :count="today.month_count"
            :target="today.month_target ?? null"
            :month="today.month"
            compact
            no-face
          />
          <RhythmCard
            v-if="today.rhythm && !starting"
            :week="today.rhythm"
            :month-behind="monthBehind"
            nested
          />
        </div>
      </section>

      <!-- À retenir : l'écart du Bilan, un mot en très grand, une phrase. -->
      <section
        v-if="highlight && !starting"
        class="today-section"
        aria-labelledby="today-retain-title"
        data-test="today-retain"
      >
        <h2 id="today-retain-title">
          À retenir.
        </h2>
        <div class="today-retain">
          <p class="today-retain-word">
            {{ highlight.word }}
          </p>
          <p>{{ highlight.sentence }}</p>
          <RouterLink
            to="/bilan"
            class="button-link"
            data-test="today-retain-link"
          >
            Voir le Bilan
          </RouterLink>
        </div>
      </section>
    </div>
    <div
      v-else
      class="container today"
    >
      <NetworkError
        v-if="offline"
        @retry="load()"
      />
      <LoadingBlocks
        v-else
        :heights="['7rem', '7rem', '12rem']"
      />
    </div>
  </section>
  <SuccessCard
    v-if="goalWon && today"
    name="reussite"
    keep-focus
    title="Objectif du mois atteint"
    test-id="goal-moment"
    @close="goalWon = false"
  >
    <p>{{ today.month_count }} candidatures sur {{ today.month_target }}.</p>
  </SuccessCard>
  <SuccessCard
    v-else-if="stepsWon"
    face
    wink
    keep-focus
    title="Première candidature notée"
    test-id="first-steps-done"
    @close="stepsWon = false"
  >
    <p>Elle compte pour ton mois ORP.</p>
  </SuccessCard>
</template>
