
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Offer, type Today } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import DailyPick from "../components/DailyPick.vue";
import RhythmCard from "../components/RhythmCard.vue";
import FirstSteps from "../components/FirstSteps.vue";
import { useAuth } from "../composables/useAuth";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import FaceMark from "../components/FaceMark.vue";
import FaceState from "../components/FaceState.vue";
import OrpMonth from "../components/OrpMonth.vue";
import SuccessCard from "../components/SuccessCard.vue";
import { usePhone } from "../composables/usePhone";
import PageHero from "../components/PageHero.vue";
import { sinceText } from "../components/status";
import { useCollect } from "../composables/useCollect";
import { colorIndex, formatMonth, localDate, orpPace, plural, scoreWord } from "../format";
import { useDataChanged } from "../composables/useDataChanged";
import { offerUndo } from "../composables/useUndo";
import { usePageReady } from "../composables/usePageTransition";

const today = ref<Today | null>(null);
usePageReady("today", () => !!today.value);
// La dose du jour (docs/86) : 3 offres ; 5 quand le mois ORP est à rattraper (docs/124 §D).
const DOSE = 3;
const DOSE_CATCH_UP = 5;
const best = ref<Offer[]>([]);
// Un jour de repos (docs/86) : aucune liste à traiter.
const restDay = computed(() => today.value?.rhythm?.research_today === false);
// Le mois ORP en retard sur son rythme (format.orpPace).
const monthBehind = computed(() => {
  const t = today.value;
  return !!t && orpPace(t.month_count, t.month_target, t.month)?.state === "behind";
});
const rhythmPaused = computed(() => !!today.value?.rhythm?.pause_until);
const preparing = ref<Offer[]>([]);
const { message } = useCollect();

// Au plus 3 lignes par carte (docs/129 §3) ; « Tout voir » pour le reste.
const ROWS = 3;
// « 1 sur 5 » de l'offre du jour, sur la ligne du titre de sa carte (docs/129 §2).
const pick = ref<{ position: string } | null>(null);
const pickPosition = computed(() => pick.value?.position ?? "");

// Le plus urgent en tête (docs/43 n° 30) : entretien aujourd'hui ou demain, remise ORP dans
// moins de 5 jours.
const URGENT_DAYS = 5;
const DAY_MS = 86_400_000;
const time = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit" });

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

// Rendez-vous ORP aujourd'hui ou demain (docs/83) : sa feuille est prête.
function meetingText(iso: string): string {
  const at = new Date(iso);
  const day = startOfDay(at) === startOfDay(new Date()) ? "aujourd'hui" : "demain";
  return `Rendez-vous ORP ${day} à ${time.format(at)} : ta feuille est prête.`;
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

// La phrase du jour (docs/95 §1) : ce qu'il y a à faire, les nombres en avant.
type Part = { text: string; strong?: boolean };
const sentence = computed<Part[]>(() => {
  const t = today.value;
  if (!t) return [];
  const pause = t.rhythm?.pause_until;
  if (pause) return [{ text: `En pause jusqu'au ${longDate.format(localDate(pause))}.` }];
  // Jour de repos (1.6.26) : une seule phrase, qui dit quoi faire si l'on veut avancer ; les
  // cartes ne le répètent plus.
  if (restDay.value) {
    const rest: Part[] = [{ text: "Jour de repos." }];
    if (t.to_follow_up) rest.push({ text: " Si tu veux avancer : " }, { text: plural(t.to_follow_up, "relance", "relances"), strong: true }, { text: " en attente." });
    else if (t.to_review) rest.push({ text: " Si tu veux avancer : " }, { text: plural(t.to_review, "offre", "offres"), strong: true }, { text: " à examiner." });
    return rest;
  }
  const items: Part[][] = [];
  if (t.to_review) items.push([{ text: plural(t.to_review, "offre", "offres"), strong: true }, { text: " à examiner" }]);
  if (t.to_follow_up) items.push([{ text: plural(t.to_follow_up, "relance", "relances"), strong: true }]);
  // La semaine est dans le mois ORP, juste dessous (docs/131 §A.2) : la phrase n'en parle plus.
  if (!items.length) {
    // « Ta semaine est faite » se tait quand le mois est en retard (1.6.27).
    const weekDone = t.rhythm && t.rhythm.target !== null && t.rhythm.count >= t.rhythm.target && !monthBehind.value;
    return [{ text: weekDone ? "Tout est à jour. Ta semaine est faite." : "Tout est à jour." }];
  }
  const parts: Part[] = [];
  items.forEach((item, index) => {
    if (index) parts.push({ text: index === items.length - 1 ? " et " : ", " });
    parts.push(...item);
  });
  parts.push({ text: "." });
  const first = parts[0]!;
  parts[0] = { ...first, text: first.text.charAt(0).toUpperCase() + first.text.slice(1) };
  return parts;
});
// Une seule action, la plus utile (docs/95 §1).
const cta = computed(() => {
  const t = today.value;
  if (!t || restDay.value || t.rhythm?.pause_until) return null;
  // Seulement quand sa carte n'est pas sur la page (docs/131 §A.1) : des offres à examiner pas
  // encore notées, des relances au-delà de celles affichées.
  if (t.to_review && !best.value.length) return { label: "Examiner les offres", to: "/candidatures/offres", icon: "briefcase" as const };
  return null;
});

// Ce qui a une date, trois au plus (docs/95 §2) : le plus proche d'abord.
const banners = computed(() => {
  const t = today.value;
  if (!t) return [];
  const list: { key: string; test: string; text: string; action: string; to: string | Record<string, unknown> }[] = [];
  if (t.orp_meeting_at) {
    list.push({ key: "meeting", test: "orp-meeting-soon", text: meetingText(t.orp_meeting_at), action: "Voir la feuille", to: "/candidatures/rendez-vous-orp" });
  }
  for (const item of t.upcoming_interviews ?? []) {
    list.push({ key: `interview-${item.application_id}`, test: "upcoming-interview", text: `${interviewText(item.at, item.company)}.`, action: "Préparer", to: "/candidatures/suivi" });
  }
  if (t.orp_due_month) {
    list.push({
      key: "orp",
      test: orpUrgent.value ? "orp-urgent" : "orp-due",
      text: orpText.value,
      action: "Préparer la remise",
      to: { path: "/candidatures/suivi", query: { mois: t.orp_due_month } },
    });
  }
  for (const item of t.interviews_to_review ?? []) {
    list.push({ key: `review-${item.application_id}-${item.interview_on}`, test: "interview-to-review", text: `Comment s'est passé ton entretien chez ${item.company} ?`, action: "Faire le point", to: item.link });
  }
  if (t.alerts_waiting) {
    list.push({
      key: "alerts",
      test: "alerts-waiting",
      text: t.alerts_waiting === 1 ? "1 alerte créée hier n'a encore rien envoyé." : `${t.alerts_waiting} alertes créées depuis hier n'ont encore rien envoyé.`,
      action: "Vérifier mes alertes",
      to: "/candidatures/alertes",
    });
  }
  return list.slice(0, 3);
});

// Les premiers pas (docs/128) : tant qu'il en manque, la carte remplace la phrase du jour et
// son action, et Aujourd'hui s'allège (pas de rythme, pas d'onglet vide, pas de jour calme).
const starting = computed(() => {
  const t = today.value;
  return !!t && !t.first_steps_dismissed && t.first_steps.some((s) => !s.done);
});
const dateTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" }).format(
  new Date(),
);
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
// L'étiquette au-dessus du titre : la date et la dernière collecte.
const eyebrow = computed(() => {
  // La collecte seulement quand elle tourne ou a plus d'un jour de retard (docs/131 §B.6).
  const last = today.value?.last_collect_at;
  const late = !!last && Date.now() - new Date(last).getTime() > DAY_MS;
  const collect = message.value || (late ? `collecte ${sinceText(last!)}` : "");
  return collect ? `${dateTitle} · ${collect}` : dateTitle;
});

// S, « Rien d'urgent aujourd'hui » (docs/123 §2) : un jour de recherche sans offre à examiner,
// sans relance ni rien de daté. Le visage ravi, la devise, le mois ORP en une ligne.
const calm = computed(() => {
  const t = today.value;
  return !!t && !starting.value && !restDay.value && !rhythmPaused.value && !t.to_review && !t.to_follow_up && !banners.value.length;
});
// U, Aujourd'hui en compact (docs/123 §2) : sur téléphone, le mois ORP en une ligne.
const { phone } = usePhone();
// Pendant les premiers pas, la carte des offres seulement quand il y en a (docs/128 §2).
// Un jour de repos, pas d'offre du jour : la phrase du haut le dit (1.6.26).
const showPick = computed(() => !restDay.value && (!starting.value || best.value.length > 0));

// « Voir les offres à préparer », une fois le tri fini : la carte voisine prend le focus.
function showPreparingCard(): void {
  const card = document.getElementById("a-preparer");
  card?.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
  card?.focus({ preventScroll: true });
}

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

const dose = computed(() => {
  const t = today.value;
  const behind = !!t && orpPace(t.month_count, t.month_target, t.month)?.state === "behind";
  return best.value.slice(0, behind ? DOSE_CATCH_UP : DOSE);
});

// Une offre gardée passe dans « À préparer » : la liste se recharge. Toutes sont gardées pour
// le compte du titre ; 3 lignes s'affichent.
async function reloadPreparing(): Promise<void> {
  const { data } = await api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 100 } } });
  preparing.value = (data?.items ?? []).filter((o) => o.status === "preparing");
}

async function load(): Promise<void> {
  const [day, offers, current] = await Promise.all([
    api.GET("/api/today"),
    // La dose du jour (docs/86) : les 3 meilleures, pas toute la pile.
    api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: DOSE_CATCH_UP } } }),
    api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 100 } } }),
  ]);
  today.value = day.data ?? null;
  goalWon.value = firstGoal(today.value);
  // Montrée une fois : on le dit au serveur, elle ne revient plus (docs/128 §1).
  if (today.value?.first_steps_finished && !stepsWon.value) {
    stepsWon.value = true;
    void api.PUT("/api/first-steps", { body: { celebrated: true } });
  }
  best.value = (offers.data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined);
  preparing.value = (current.data?.items ?? []).filter((o) => o.status === "preparing");
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

      <!-- S, rien d'urgent (docs/123 §2) : le visage ravi, pourquoi, la devise, le mois en une
           ligne, et les offres quand même. -->
      <section
        v-if="calm"
        class="today-calm"
        data-test="today-calm"
      >
        <FaceState
          mood="ravi"
          title="Rien d'urgent aujourd'hui"
        >
          <p>Aucune offre à examiner, aucune relance, rien de daté.</p>
          <div class="face-state-actions">
            <RouterLink
              to="/candidatures/offres"
              class="button-link primary-link"
              data-test="today-calm-offers"
            >
              Voir les offres quand même
            </RouterLink>
          </div>
        </FaceState>
        <div class="dash-card today-calm-month">
          <OrpMonth
            title="Mois ORP"
            :count="today.month_count"
            :target="today.month_target ?? null"
            :month="today.month"
            compact
          />
        </div>
      </section>
      <template v-else>
        <!-- Les premiers pas (docs/128) : la seule action tant qu'il en manque. -->
        <FirstSteps
          v-if="starting"
          :steps="today.first_steps"
          :has-offers="today.has_offers ?? true"
          :offer-id="today.first_steps_offer_id ?? null"
          :pick-ready="!restDay && !rhythmPaused && best.length > 0"
          @dismiss="dismissSteps"
        />
        <!-- La phrase du jour, en grand, et une seule action (docs/95 §1, d'après Sphere). -->
        <div
          v-else
          class="today-lead"
        >
          <p
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
          <RouterLink
            v-if="cta"
            :to="cta.to"
            class="button-link primary-link today-cta"
            data-test="today-cta"
          >
            <span class="with-icon"><AppIcon :name="cta.icon" />{{ cta.label }}</span>
          </RouterLink>
        </div>

        <!-- Ce qui a une date, trois au plus (docs/95 §2). -->
        <ul
          v-if="banners.length"
          class="today-banners"
        >
          <li
            v-for="banner in banners"
            :key="banner.key"
            class="today-banner"
            :data-test="banner.test"
          >
            <span>{{ banner.text }}</span>
            <RouterLink :to="banner.to">
              {{ banner.action }}
            </RouterLink>
          </li>
        </ul>

        <!-- Rangée 1 (docs/129 §1) : les offres du jour et le mois ORP. -->
        <div
          class="today-grid"
          :class="{ single: !showPick }"
        >
          <section
            v-if="showPick"
            class="dash-card today-pick"
            aria-labelledby="today-pick-title"
            data-test="best"
          >
            <header class="today-card-head">
              <h2 id="today-pick-title">
                Offres du jour
              </h2>
              <span
                v-if="pickPosition"
                class="today-card-side"
                data-test="pick-count"
              >{{ pickPosition }}</span>
            </header>
            <p
              v-if="rhythmPaused"
              class="hint"
              data-test="paused-day"
            >
              En pause : pas d'offre du jour.
            </p>
            <p
              v-else-if="!best.length"
              class="hint today-empty-line"
            >
              <FaceMark mood="neutre" />Aucune offre notée en attente.
            </p>
            <DailyPick
              v-else
              id="offres-du-jour"
              ref="pick"
              :offers="dose"
              @changed="reloadPreparing"
              @show-preparing="showPreparingCard"
            />
          </section>

          <!-- Mois ORP (docs/95 §4, docs/123 Q) : le compte du mois et son humeur, puis la semaine. -->
          <section
            class="dash-card today-month"
            data-test="orp-month"
          >
            <OrpMonth
              title="Mois ORP"
              :count="today.month_count"
              :target="today.month_target ?? null"
              :month="today.month"
              :compact="phone"
            />
            <RhythmCard
              v-if="today.rhythm && !starting"
              :week="today.rhythm"
              :month-behind="monthBehind"
              nested
            />
          </section>
        </div>

        <!-- Rangée 2 (docs/129 §1, §3) : à préparer et à relancer, la même forme de ligne ; une
             carte vide ne s'affiche pas, sa voisine prend toute la largeur. -->
        <div
          v-if="preparing.length || today.follow_ups?.length"
          class="today-grid halves"
          :class="{ single: !preparing.length || !today.follow_ups?.length }"
        >
          <section
            v-if="preparing.length"
            id="a-preparer"
            class="dash-card today-list"
            aria-labelledby="today-preparing-title"
            data-test="preparing"
            tabindex="-1"
          >
            <header class="today-card-head">
              <h2 id="today-preparing-title">
                À préparer · {{ preparing.length }}
              </h2>
              <RouterLink
                :to="{ path: '/candidatures/offres', query: { statut: 'in_progress' } }"
                class="today-card-link"
                data-test="preparing-all"
              >
                Tout voir
              </RouterLink>
            </header>
            <ul class="today-rows">
              <li
                v-for="offer in preparing.slice(0, ROWS)"
                :key="offer.id"
              >
                <RouterLink
                  :to="`/candidatures/offres/${offer.id}/preparer`"
                  class="today-row"
                  :title="`${offer.company || 'Entreprise non indiquée'} · ${offer.title}`"
                >
                  <CompanyLogo :offer="offer" />
                  <span class="today-row-main">
                    <strong>{{ offer.company || "Entreprise non indiquée" }}</strong>
                    <span class="today-row-line">{{ offer.title }}</span>
                    <span
                      v-if="offer.score !== null && offer.score !== undefined"
                      class="today-row-line"
                    >{{ scoreWord(offer.score).word }}</span>
                  </span>
                  <span class="today-row-action">Préparer</span>
                </RouterLink>
              </li>
            </ul>
          </section>

          <section
            v-if="today.follow_ups?.length"
            class="dash-card today-list"
            aria-labelledby="today-follow-title"
            data-test="follow-ups"
          >
            <header class="today-card-head">
              <h2 id="today-follow-title">
                À relancer · {{ today.to_follow_up }}
              </h2>
              <RouterLink
                to="/candidatures/suivi"
                class="today-card-link"
                data-test="follow-ups-all"
              >
                Tout voir
              </RouterLink>
            </header>
            <ul class="today-rows">
              <li
                v-for="item in today.follow_ups.slice(0, ROWS)"
                :key="item.application_id"
              >
                <RouterLink
                  :to="{ path: '/candidatures/suivi', query: { mois: item.orp_month, candidature: String(item.application_id) } }"
                  class="today-row"
                  :title="`${item.company} · ${item.job_title}`"
                >
                  <span
                    class="logo"
                    :class="`c${colorIndex(item.company)}`"
                  >{{ item.company.trim().charAt(0).toUpperCase() }}</span>
                  <span class="today-row-main">
                    <strong>{{ item.company }}</strong>
                    <span class="today-row-line">{{ item.job_title }}</span>
                    <span class="today-row-line">{{ item.status === "relancee" ? "relancée, sans réponse" : `envoyée le ${longDate.format(localDate(item.sent_at))}` }}</span>
                  </span>
                  <span class="today-row-action">Relancer</span>
                </RouterLink>
              </li>
            </ul>
          </section>
        </div>
      </template>
    </div>
    <div
      v-else
      class="container today"
    >
      <LoadingBlocks :heights="['7rem', '7rem', '12rem']" />
    </div>
  </section>
  <SuccessCard
    v-if="goalWon && today"
    face
    wink
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
