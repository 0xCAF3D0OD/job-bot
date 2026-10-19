<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import DashTile from "../components/dash/DashTile.vue";
import PeriodChart from "../components/dash/PeriodChart.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import { formatMonth, plural, shiftMonth } from "../format";
import CopyLabel from "../components/CopyLabel.vue";
import IllustratedSide from "../components/IllustratedSide.vue";
import RhythmWeeks from "../components/RhythmWeeks.vue";
import HoverNote from "../components/HoverNote.vue";
import { firstTime } from "../composables/useIntro";
import { usePageReady } from "../composables/usePageTransition";

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

async function load(): Promise<void> {
  error.value = "";
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

const STEPS = [
  { key: "received", label: "Offres reçues", to: "/candidatures/offres" },
  { key: "retained", label: "Retenues", to: "/candidatures/offres" },
  { key: "applications", label: "Candidatures", to: "/candidatures/suivi" },
  { key: "responses", label: "Réponses", to: "/candidatures/suivi" },
  { key: "interviews", label: "Entretiens", to: "/candidatures/suivi" },
  { key: "engagements", label: "Engagement", to: "/candidatures/suivi" },
] as const;

const SUIVI = "/candidatures/suivi";
const ICONS: Record<string, InstanceType<typeof AppIcon>["$props"]["name"]> = {
  source: "globe",
  score: "star",
  contact: "user",
  follow_up: "refresh",
};

// Les barres du parcours, à l'échelle de la plus longue (les offres reçues).
const funnelMax = computed(() => Math.max(1, ...STEPS.map((step) => insights.value?.funnel[step.key] ?? 0)));
function funnelWidth(n: number): string {
  return `${Math.max(n ? 2 : 0, (n / funnelMax.value) * 100)}%`;
}
function rate(responses: number, total: number): string {
  return `${total ? Math.max(responses ? 3 : 0, (responses / total) * 100) : 0}%`;
}

const tiles = computed(() => {
  const r = insights.value;
  if (!r) return null;
  const f = r.funnel;
  const share = f.applications ? `${Math.round((f.responses / f.applications) * 100)} % des envois` : "aucun envoi";
  return {
    applications: `sur ${plural(f.retained, "offre retenue", "offres retenues")}`,
    responses: share,
    interviews: r.interviews_upcoming
      ? `dont ${r.interviews_upcoming} à venir`
      : `sur ${plural(f.responses, "réponse", "réponses")}`,
    delay: r.delay ? `${r.delay.typical} j` : "—",
    delayRange: !r.delay
      ? "pas encore de réponse"
      : r.delay.shortest === r.delay.longest
        ? "de réponse, d'habitude"
        : `de réponse, de ${r.delay.shortest} à ${r.delay.longest} j`,
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
// Les barres montent à la première ouverture (docs/60 §3).
const intro = firstTime("bilan-funnel");
</script>

<template>
  <section class="jobs-body insights">
    <div class="insights-head">
      <div
        class="segmented insights-period"
        role="radiogroup"
        aria-label="Période"
      >
        <button
          type="button"
          role="radio"
          :aria-checked="period === 'recent'"
          data-test="period-recent"
          @click="choose('recent')"
        >
          3 derniers mois
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="period === 'month'"
          data-test="period-month"
          @click="choose('month')"
        >
          Un mois
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="period === 'all'"
          data-test="period-all"
          @click="choose('all')"
        >
          Tout
        </button>
      </div>
      <div
        v-if="period === 'month'"
        class="month-nav"
      >
        <button
          type="button"
          class="secondary small"
          aria-label="Mois précédent"
          data-test="prev-month"
          @click="go(-1)"
        >
          ←
        </button>
        <strong data-test="month">{{ formatMonth(month) }}</strong>
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
      <div
        class="bilan-tiles"
        data-test="bilan-tiles"
      >
        <DashTile
          :to="SUIVI"
          icon="send"
          label="Candidatures"
          :value="String(insights.funnel.applications)"
          :trend="tiles.applications"
          tone="accent"
          data-test="tile-applications"
        />
        <DashTile
          :to="SUIVI"
          icon="reply"
          label="Réponses"
          :value="String(insights.funnel.responses)"
          :trend="tiles.responses"
          data-test="tile-responses"
        />
        <DashTile
          :to="SUIVI"
          icon="calendar"
          label="Entretiens"
          :value="String(insights.funnel.interviews)"
          :trend="tiles.interviews"
          data-test="tile-interviews"
        />
        <DashTile
          icon="clock"
          label="Délai"
          :value="tiles.delay"
          :trend="tiles.delayRange"
          data-test="delay"
        />
      </div>

      <div class="dash-row bilan-mid">
        <section
          class="dash-card"
          data-test="funnel"
        >
          <header class="dash-card-head">
            <h2>Parcours</h2>
          </header>
          <ol
            :class="['bilan-funnel', { intro }]"
            aria-label="Parcours"
          >
            <li
              v-for="step in STEPS"
              :key="step.key"
            >
              <RouterLink
                :to="step.to"
                class="bilan-step"
                :data-test="`funnel-${step.key}`"
              >
                <span class="bilan-step-label">{{ step.label }}</span>
                <span class="bilan-track">
                  <span
                    class="bilan-bar"
                    :style="{ width: funnelWidth(insights.funnel[step.key]) }"
                  />
                </span>
                <strong>{{ insights.funnel[step.key] }}</strong>
              </RouterLink>
            </li>
          </ol>
        </section>
        <PeriodChart
          v-if="insights.buckets.length"
          :buckets="insights.buckets"
          :unit="insights.unit"
        />
      </div>

      <IllustratedSide
        v-if="insights.funnel.applications === 0"
        class="empty-state"
        data-test="insights-empty"
        name="bilan"
        phone="small"
      >
        <p>Pas encore de candidature sur cette période : le bilan se remplit au fil de tes envois.</p>
      </IllustratedSide>
      <template v-else>
        <p
          v-if="insights.headline"
          class="bilan-headline"
          data-test="headline"
        >
          <span class="dash-bubble small"><AppIcon name="trend" /></span>
          <span>{{ insights.headline }}</span>
        </p>

        <div class="bilan-compare">
          <section
            v-for="comparison in insights.comparisons"
            :key="comparison.key"
            class="dash-card"
            :data-test="`comparison-${comparison.key}`"
          >
            <header class="dash-card-head">
              <h2>
                <span class="dash-bubble small"><AppIcon :name="ICONS[comparison.key] ?? 'search'" /></span>
                <HoverNote text="Réponses sur candidatures envoyées. Un refus est une réponse ; « Sans réponse » n'en est pas une.">
                  {{ comparison.title }}
                </HoverNote>
              </h2>
            </header>
            <ul
              v-if="comparison.groups.length"
              class="bilan-groups"
            >
              <li
                v-for="group in comparison.groups"
                :key="group.key"
                :class="{ few: !group.enough }"
                :data-test="`group-${group.key}`"
              >
                <span class="bilan-group-label">{{ group.label }}</span>
                <span
                  class="bilan-track"
                  aria-hidden="true"
                >
                  <span
                    class="bilan-bar"
                    :style="{ width: rate(group.responses, group.total) }"
                  />
                </span>
                <span class="bilan-count">{{ group.responses }} sur {{ group.total }}</span>
                <span
                  v-if="!group.enough"
                  class="bilan-few"
                >trop peu pour conclure</span>
              </li>
            </ul>
            <p
              v-else
              class="hint"
            >
              Rien à comparer pour l'instant.
            </p>
          </section>
        </div>
      </template>

      <RhythmWeeks
        v-if="period !== 'all'"
        :month="month"
      />

      <section
        v-if="period === 'month' && insights.orp_summary"
        class="dash-card bilan-summary"
        data-test="orp-summary"
      >
        <header class="dash-card-head">
          <h2>
            <span class="dash-bubble small"><AppIcon name="file" /></span>
            Résumé pour l'ORP
          </h2>
          <button
            type="button"
            class="secondary small"
            data-test="orp-summary-copy"
            @click="copy"
          >
            <CopyLabel :done="copied" />
          </button>
        </header>
        <p>{{ insights.orp_summary }}</p>
      </section>
    </div>
  </section>
</template>
