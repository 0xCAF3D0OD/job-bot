<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Today } from "../api/client";
import type { components } from "../api/schema";
import ActionBand from "../components/ActionBand.vue";
import AppIcon from "../components/AppIcon.vue";
import BilanCompare from "../components/bilan/BilanCompare.vue";
import BilanFunnel from "../components/bilan/BilanFunnel.vue";
import BilanInterviews from "../components/bilan/BilanInterviews.vue";
import BilanMonths from "../components/bilan/BilanMonths.vue";
import DashTile from "../components/dash/DashTile.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import { formatMonth, plural, shiftMonth } from "../format";
import CopyLabel from "../components/CopyLabel.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import FaceState from "../components/FaceState.vue";
import OrpGauge from "../components/dash/OrpGauge.vue";
import IconButton from "../components/IconButton.vue";
import { usePageReady } from "../composables/usePageTransition";
import {
  bestComparison,
  bestSite,
  conclusion,
  interviewsLine,
  monthLine,
  monthName,
  weakStep,
} from "../bilanText";

// Ce qui marche dans ta recherche (docs/42) : parcours, comparaisons, résumé pour l'ORP ;
// présenté comme le tableau d'Aujourd'hui (docs/55) : tuiles, barres, cartes à bulles.
type Insights = components["schemas"]["SearchReportOut"];
type Period = "recent" | "month" | "all";

const route = useRoute();
const router = useRouter();
const insights = ref<Insights | null>(null);
const error = ref("");
usePageReady("insights", () => !!insights.value || !!error.value);
const copied = ref(false);

function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

// Période et mois dans l'adresse : le mois suit d'un onglet à l'autre (Suivi, Bilan).
const period = computed<Period>(() => {
  if (route.query.periode === "tout") return "all";
  return typeof route.query.mois === "string" ? "month" : "recent";
});
const month = computed(() => (typeof route.query.mois === "string" ? route.query.mois : currentMonth()));

function choose(next: Period): void {
  const query: Record<string, string> = {};
  if (next === "month") query.mois = month.value;
  if (next === "all") query.periode = "tout";
  void router.push({ query });
}

function go(delta: number): void {
  void router.push({ query: { mois: shiftMonth(month.value, delta) } });
}

// L'objectif ORP du mois en cours et les trois mois précédents (docs/95) : la jauge quittée
// d'Aujourd'hui, montrée quand on regarde le mois en cours ou les dernières semaines.
const orp = ref<{ count: number; target: number | null; month: string; history: Today["orp_history"] } | null>(null);
// Un compte sans aucune candidature (docs/128 §3) : la jauge à zéro n'apprend rien.
const gaugeUseful = computed(
  () => !!orp.value && ((insights.value?.funnel.applications ?? 0) > 0 || orp.value.count > 0 || orp.value.history.some((m) => m.count > 0)),
);
const showGauge = computed(() => period.value === "recent" || (period.value === "month" && month.value === currentMonth()));

async function loadOrp(): Promise<void> {
  const { data } = await api.GET("/api/today");
  if (data?.month) orp.value = { count: data.month_count, target: data.month_target ?? null, month: data.month, history: data.orp_history ?? [] };
}

async function load(): Promise<void> {
  error.value = "";
  if (!orp.value) void loadOrp().catch(() => undefined);
  try {
    const { data } = await api.GET("/api/insights", {
      params: { query: period.value === "month" ? { period: "month", month: month.value } : { period: period.value } },
    });
    if (!data) throw new Error();
    insights.value = data;
  } catch {
    error.value = "Bilan indisponible pour l'instant.";
  }
}

const SUIVI = "/candidatures/suivi";

const tiles = computed(() => {
  const r = insights.value;
  if (!r) return null;
  const f = r.funnel;
  const share = f.applications ? `${Math.round((f.responses / f.applications) * 100)} % des envois` : "aucun envoi";
  return {
    applications: `sur ${plural(f.retained, "offre gardée", "offres gardées")}`,
    responses: share,
    interviews: r.interviews_upcoming
      ? `dont ${r.interviews_upcoming} à venir`
      : `sur ${plural(f.responses, "réponse", "réponses")}`,
    delay: r.delay ? `${r.delay.typical} j` : "—",
    delayRange: !r.delay
      ? "pas encore de réponse"
      : r.delay.shortest === r.delay.longest
        ? "d'habitude"
        : `de ${r.delay.shortest} à ${r.delay.longest} j`,
  };
});

async function copy(): Promise<void> {
  if (!insights.value?.orp_summary) return;
  try {
    await navigator.clipboard.writeText(insights.value.orp_summary);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    copied.value = false;
  }
}

watch(() => route.query, () => void load());
onMounted(() => void load());

// La conclusion, la bande et la phrase de chaque repliable (1.6.62, planche « 3 et 4. Bilan »).
const summary = computed(() => (insights.value ? conclusion(insights.value, period.value) : null));
const site = computed(() => (insights.value ? bestSite(insights.value.comparisons) : null));
const weak = computed(() => (insights.value ? weakStep(insights.value.funnel) : null));
// « Le résumé d'octobre à copier », « Le résumé de mai à copier ».
const orpDescription = computed(() => {
  const name = monthName(month.value);
  return `Le résumé ${/^[aeiou]/.test(name) ? "d'" : "de "}${name} à copier`;
});
const PERIODS: { key: Period; label: string }[] = [
  { key: "month", label: "Un mois" },
  { key: "recent", label: "3 mois" },
  { key: "all", label: "Tout" },
];
</script>

<template>
  <section class="jobs-body insights">
    <!-- La conclusion (règles §3.2) : l'état général, comparé à la période d'avant ; elle ne redit pas
         la bande (1.6.62). -->
    <p
      v-if="insights && summary && insights.funnel.applications > 0"
      class="today-sentence bilan-sentence"
      data-test="headline"
    >
      Ta recherche <strong>{{ summary.word }}</strong>{{ summary.rest }}
    </p>
    <!-- La bande d'action (§3) : le site qui répond le plus, et le cibler dans les alertes. Sans site
         qui se détache, pas de bande. -->
    <ActionBand
      v-if="insights && site && insights.funnel.applications > 0"
      :title="site.title"
      :summary="site.summary"
      :action="`Cibler ${site.label} dans mes alertes`"
      to="/candidatures/alertes"
    />
    <div class="insights-head">
      <!-- La période (1.6.62) : le choix actif dans la pastille teintée de l'en-tête, sans rail. -->
      <div
        class="bilan-period"
        role="radiogroup"
        aria-label="Période"
      >
        <button
          v-for="choice in PERIODS"
          :key="choice.key"
          type="button"
          role="radio"
          :aria-checked="period === choice.key"
          :data-test="`period-${choice.key}`"
          @click="choose(choice.key)"
        >
          {{ choice.label }}
        </button>
      </div>
      <div
        v-if="period === 'month'"
        class="month-nav"
      >
        <IconButton
          icon="arrow-left"
          label="Mois précédent"
          data-test="prev-month"
          @click="go(-1)"
        />
        <strong data-test="month">{{ formatMonth(month) }}</strong>
        <IconButton
          icon="arrow-right"
          label="Mois suivant"
          data-test="next-month"
          @click="go(1)"
        />
      </div>
    </div>

    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>

    <LoadingBlocks
      v-if="!insights && !error"
      :heights="['11rem', '16rem', '12rem']"
    />
    <div
      v-if="insights && tiles"
      class="bilan"
    >
      <!-- La conclusion d'abord, puis les trois chiffres et l'objectif ORP ; le détail sur
           demande (docs/126 §2 : « une page, une question »). -->
      <FaceState
        v-if="insights.funnel.applications === 0"
        title="Pas encore de candidature"
        data-test="insights-empty"
      >
        <p>Le bilan commence après tes premières candidatures.</p>
        <div class="face-state-actions">
          <RouterLink
            to="/candidatures/offres"
            class="button-link primary-link"
          >
            <span class="with-icon"><AppIcon name="briefcase" />Voir les offres</span>
          </RouterLink>
        </div>
      </FaceState>
      <!-- Les quatre tuiles en carrés, les mois précédents à côté (docs/133 §3) : le mois en
           cours est sur Aujourd'hui. -->
      <div
        v-if="insights.funnel.applications > 0"
        :class="['bilan-top', { single: !(showGauge && orp && gaugeUseful) }]"
      >
        <div
          v-if="insights.funnel.applications > 0"
          class="bilan-tiles"
          data-test="bilan-tiles"
        >
          <DashTile
            :to="SUIVI"
            icon="send"
            :label="insights.funnel.applications === 1 ? 'candidature' : 'candidatures'"
            :value="String(insights.funnel.applications)"
            :trend="tiles.applications"
            tone="accent"
            data-test="tile-applications"
          />
          <DashTile
            :to="SUIVI"
            icon="reply"
            :label="insights.funnel.responses === 1 ? 'réponse' : 'réponses'"
            :value="String(insights.funnel.responses)"
            :trend="tiles.responses"
            data-test="tile-responses"
          />
          <DashTile
            :to="SUIVI"
            icon="calendar"
            :label="insights.funnel.interviews === 1 ? 'entretien' : 'entretiens'"
            :value="String(insights.funnel.interviews)"
            :trend="tiles.interviews"
            data-test="tile-interviews"
          />
          <DashTile
            icon="clock"
            label="délai de réponse"
            :value="tiles.delay"
            :trend="tiles.delayRange"
            data-test="delay"
          />
        </div>
        <OrpGauge
          v-if="showGauge && orp && gaugeUseful"
          :count="orp.count"
          :target="orp.target"
          :month="orp.month"
          :history="orp.history"
          past
        />
      </div>
      <!-- Le détail replié (règles §3.4, 1.6.62) : chaque ligne dit déjà l'essentiel ; on déplie pour
           le graphique (NN/g, divulgation progressive). -->
      <section
        v-if="insights.funnel.applications > 0"
        class="bilan-detail"
        data-test="bilan-detail"
      >
        <DisclosureRow
          title="Parcours"
          icon="trend"
          :description="weak ? `Le plus de pertes : ${weak.between}` : 'Les six étapes de ta recherche'"
          data-test="detail-funnel"
        >
          <BilanFunnel :funnel="insights.funnel" />
        </DisclosureRow>
        <DisclosureRow
          title="Ce qui marche"
          icon="star"
          :description="bestComparison(insights.comparisons, !!site)"
          data-test="detail-compare"
        >
          <BilanCompare :comparisons="insights.comparisons" />
        </DisclosureRow>
        <DisclosureRow
          v-if="insights.months.length"
          title="Par mois"
          icon="calendar"
          :description="monthLine(insights.months, insights.month_target, new Date())"
          data-test="detail-months"
        >
          <BilanMonths
            :months="insights.months"
            :target="insights.month_target"
          />
        </DisclosureRow>
        <DisclosureRow
          title="Entretiens"
          icon="user"
          :description="interviewsLine(insights.interviews)"
          data-test="detail-interviews"
        >
          <BilanInterviews :lines="insights.interviews" />
        </DisclosureRow>
        <!-- « Pour l'ORP » (période « Un mois ») : le résumé du mois à copier pour le rendez-vous. -->
        <DisclosureRow
          v-if="period === 'month' && insights.orp_summary"
          title="Pour l'ORP"
          icon="file"
          :description="orpDescription"
          data-test="detail-orp"
        >
          <div
            class="bilan-summary"
            data-test="orp-summary"
          >
            <p>{{ insights.orp_summary }}</p>
            <button
              type="button"
              class="secondary small"
              data-test="orp-summary-copy"
              @click="copy"
            >
              <CopyLabel :done="copied" />
            </button>
          </div>
        </DisclosureRow>
      </section>
    </div>
  </section>
</template>
