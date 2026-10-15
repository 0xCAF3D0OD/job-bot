<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import type { components } from "../api/schema";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PushTransition from "../components/PushTransition.vue";
import { formatMonth, shiftMonth } from "../format";

// Ce qui marche dans ta recherche (docs/42) : parcours, comparaisons, résumé pour l'ORP.
type Insights = components["schemas"]["SearchReportOut"];
type Period = "recent" | "month" | "all";

const route = useRoute();
const router = useRouter();
const insights = ref<Insights | null>(null);
const error = ref("");
const summaryOpen = ref(false);
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
  summaryOpen.value = false;
  void router.push({ query });
}

function go(delta: number): void {
  summaryOpen.value = false;
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
  { key: "received", label: "offres reçues", to: "/candidatures/offres" },
  { key: "retained", label: "retenues", to: "/candidatures/offres" },
  { key: "applications", label: "candidatures", to: "/candidatures/suivi" },
  { key: "responses", label: "réponses", to: "/candidatures/suivi" },
  { key: "interviews", label: "entretiens", to: "/candidatures/suivi" },
  { key: "engagements", label: "engagement", to: "/candidatures/suivi" },
] as const;

const delayText = computed(() => {
  const d = insights.value?.delay;
  if (!d) return "";
  const range = d.shortest === d.longest ? "" : ` (de ${d.shortest} à ${d.longest})`;
  return `Réponse en ${d.typical} jour${d.typical > 1 ? "s" : ""} d'habitude${range}.`;
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
      :heights="['5rem', '10rem', '10rem']"
    />
    <template v-if="insights">
      <ol
        class="insights-funnel"
        aria-label="Ton parcours"
        data-test="funnel"
      >
        <li
          v-for="step in STEPS"
          :key="step.key"
        >
          <RouterLink
            :to="step.to"
            class="insights-step"
            :data-test="`funnel-${step.key}`"
          >
            <strong>{{ insights.funnel[step.key] }}</strong>
            <span>{{ step.label }}</span>
          </RouterLink>
        </li>
      </ol>
      <p
        v-if="delayText"
        class="hint insights-delay"
        data-test="delay"
      >
        {{ delayText }}
      </p>

      <p
        v-if="insights.funnel.applications === 0"
        class="hint"
        data-test="insights-empty"
      >
        Pas encore de candidature sur cette période : le bilan se remplit au fil de tes envois.
      </p>
      <template v-else>
        <p
          v-if="insights.headline"
          class="insights-headline"
          data-test="headline"
        >
          {{ insights.headline }}
        </p>

        <div class="insights-grid">
          <section
            v-for="comparison in insights.comparisons"
            :key="comparison.key"
            class="insights-card"
            :data-test="`comparison-${comparison.key}`"
          >
            <h2>{{ comparison.title }}</h2>
            <ul v-if="comparison.groups.length">
              <li
                v-for="group in comparison.groups"
                :key="group.key"
                :class="{ few: !group.enough }"
                :data-test="`group-${group.key}`"
              >
                <span class="insights-label">{{ group.label }}</span>
                <span class="insights-count">
                  {{ group.responses }} sur {{ group.total }}
                </span>
                <span
                  v-if="!group.enough"
                  class="insights-few"
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
        <p class="hint insights-note">
          Réponses sur candidatures envoyées. Un refus est une réponse ; « Sans réponse » n'en est pas une.
        </p>
      </template>

      <div
        v-if="period === 'month' && insights.orp_summary"
        class="insights-summary"
      >
        <button
          type="button"
          class="secondary small"
          :aria-expanded="summaryOpen"
          data-test="orp-summary-toggle"
          @click="summaryOpen = !summaryOpen"
        >
          Résumé pour l'ORP
        </button>
        <PushTransition>
          <div
            v-if="summaryOpen"
            class="insights-summary-body"
            data-test="orp-summary"
          >
            <p>{{ insights.orp_summary }}</p>
            <button
              type="button"
              class="link"
              data-test="orp-summary-copy"
              @click="copy"
            >
              {{ copied ? "Copié" : "Copier" }}
            </button>
          </div>
        </PushTransition>
      </div>
    </template>
  </section>
</template>
