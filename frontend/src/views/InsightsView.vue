<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import type { components } from "../api/schema";
import ActionBand from "../components/ActionBand.vue";
import AppIcon from "../components/AppIcon.vue";
import SegmentedControl, { type SegmentOption } from "../components/SegmentedControl.vue";
import BilanCompare from "../components/bilan/BilanCompare.vue";
import BilanFunnel from "../components/bilan/BilanFunnel.vue";
import BilanInterviews from "../components/bilan/BilanInterviews.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import { formatMonth, shiftMonth } from "../format";
import CopyButton from "../components/CopyButton.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import FaceState from "../components/FaceState.vue";
import IconButton from "../components/IconButton.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import {
  bestComparison,
  bestSite,
  conclusion,
  interviewsLine,
  monthName,
} from "../bilanText";

// Bilan › Résultats (docs/42 ; maquette Explorer, onglet Bilan, B13 et B14, Kevin, 2026-11-04). De haut en bas :
// la phrase, la carte du site qui répond le plus (sans la bande bleue), la période, trois chiffres, la carte
// Parcours, puis les lignes « Mois par mois » (vers le Suivi ORP), « Ce qui marche » et « Entretiens ».
// Sur ordinateur, les mêmes blocs en deux colonnes.
type Insights = components["schemas"]["SearchReportOut"];
type Period = "recent" | "month" | "all";

const route = useRoute();
const router = useRouter();
const insights = ref<Insights | null>(null);
const { phone } = usePhone();
const error = ref("");
const offline = ref(false);
usePageReady("insights", () => !!insights.value || !!error.value);

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
  offline.value = false;
  try {
    const { data } = await api.GET("/api/insights", {
      params: { query: period.value === "month" ? { period: "month", month: month.value } : { period: period.value } },
    });
    if (!data) throw new Error();
    insights.value = data;
  } catch (cause) {
    offline.value = isNetworkError(cause);
    error.value = "Bilan indisponible pour l’instant.";
  }
}

// Les trois chiffres de la maquette.
const figures = computed(() => {
  const f = insights.value?.funnel;
  if (!f) return [];
  return [
    { key: "applications", value: f.applications, label: f.applications <= 1 ? "candidature" : "candidatures" },
    { key: "responses", value: f.responses, label: f.responses <= 1 ? "réponse" : "réponses" },
    { key: "interviews", value: f.interviews, label: f.interviews <= 1 ? "entretien" : "entretiens" },
  ];
});
// « Mois par mois » : l'objectif ORP mensuel, s'il est indiqué.
const goalLine = computed(() => {
  const target = insights.value?.month_target;
  return target ? `Objectif ORP : ${target} par mois` : "Objectif ORP à indiquer";
});

watch(() => route.query, () => void load());
onMounted(() => void load());

// La conclusion, la bande et la phrase de chaque repliable (1.6.62, planche « 3 et 4. Bilan »).
const summary = computed(() => (insights.value ? conclusion(insights.value, period.value) : null));
const site = computed(() => (insights.value ? bestSite(insights.value.comparisons) : null));
// « Le résumé d'octobre à copier », « Le résumé de mai à copier ».
const orpDescription = computed(() => {
  const name = monthName(month.value);
  return `Le résumé ${/^[aeiou]/.test(name) ? "d’" : "de "}${name} à copier`;
});
// Sur téléphone, plus de sélecteur : une ligne dit la période des chiffres (Kevin, 6.11).
const periodLine = computed(() => {
  if (period.value === "month") return `En ${formatMonth(month.value).toLowerCase()}`;
  return period.value === "all" ? "Depuis le début" : "Sur les 3 derniers mois";
});
const PERIODS: { key: Period; label: string }[] = [
  { key: "month", label: "Un mois" },
  { key: "recent", label: "3 mois" },
  { key: "all", label: "Tout" },
];
const periodSegments: SegmentOption[] = PERIODS.map((p) => ({ value: p.key, label: p.label, test: `period-${p.key}` }));
</script>

<template>
  <section class="jobs-body insights">
    <p
      v-if="phone"
      class="insights-period-line"
      data-test="insights-period-line"
    >
      {{ periodLine }}
    </p>
    <!-- La phrase (règles §3.2) : l'état général, comparé à la période d'avant. -->
    <p
      v-if="insights && summary && insights.funnel.applications > 0"
      class="bilan-sentence"
      data-test="headline"
    >
      {{ summary.before }}<strong>{{ summary.accent }}</strong>{{ summary.after }}
    </p>

    <NetworkError
      v-if="error && offline"
      @retry="load()"
    />
    <p
      v-else-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>

    <LoadingBlocks
      v-if="!insights && !error"
      :heights="['8rem', '6rem', '14rem']"
    />
    <div
      v-if="insights"
      class="bilan"
    >
      <div class="bilan-main">
        <!-- Le site qui répond le plus, et le cibler dans les alertes ; sans site qui se détache, rien. -->
        <ActionBand
          v-if="site && insights.funnel.applications > 0"
          class="bilan-site"
          :title="site.title"
          :summary="site.summary"
          :action="`Cibler ${site.label} dans mes alertes`"
          to="/candidatures/alertes"
        />
        <!-- La période en contrôle segmenté (D4, 2026-11-03), au-dessus des chiffres. Sur téléphone, plus de
             période (maquette Progresser, Kevin 2026-11-06) : les chiffres des 3 derniers mois, sauf adresse avec un mois. -->
        <div
          v-if="!phone"
          class="insights-head"
          data-test="insights-period"
        >
          <SegmentedControl
            :model-value="period"
            :options="periodSegments"
            label="Période"
            class="bilan-period"
            @update:model-value="choose($event as Period)"
          />
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
        <FaceState
          v-if="insights.funnel.applications === 0"
          title="Trop tôt pour conclure"
          illustration="trop-tot"
          data-test="insights-empty"
        >
          <p>Le Bilan se remplit avec tes premières candidatures et réponses.</p>
          <div class="face-state-actions">
            <RouterLink
              to="/candidatures/offres"
              class="button-link primary-link"
            >
              <span class="with-icon"><AppIcon name="briefcase" />Voir les offres</span>
            </RouterLink>
          </div>
        </FaceState>
        <template v-else>
          <ul
            class="bilan-figures"
            data-test="bilan-figures"
          >
            <li
              v-for="figure in figures"
              :key="figure.key"
              :data-test="`figure-${figure.key}`"
            >
              <strong>{{ figure.value }}</strong>
              <span>{{ figure.label }}</span>
            </li>
          </ul>
          <BilanFunnel :funnel="insights.funnel" />
        </template>
      </div>
      <!-- Le détail en lignes (B13) : « Mois par mois » mène au Suivi ORP ; les autres se déplient. -->
      <section
        v-if="insights.funnel.applications > 0"
        class="bilan-detail"
        aria-label="Le détail"
        data-test="bilan-detail"
      >
        <RouterLink
          to="/bilan/orp"
          class="bilan-link"
          data-test="detail-months"
        >
          <span><strong>Mois par mois</strong><span>{{ goalLine }}</span></span>
          <span
            class="arrow-circle small"
            aria-hidden="true"
          ><AppIcon name="arrow-right" /></span>
        </RouterLink>
        <DisclosureRow
          title="Ce qui marche"
          :description="bestComparison(insights.comparisons, !!site)"
          data-test="detail-compare"
        >
          <BilanCompare :comparisons="insights.comparisons" />
        </DisclosureRow>
        <DisclosureRow
          title="Entretiens"
          :description="interviewsLine(insights.interviews)"
          data-test="detail-interviews"
        >
          <BilanInterviews :lines="insights.interviews" />
        </DisclosureRow>
        <!-- « Pour l'ORP » (période « Un mois ») : le résumé du mois à copier pour le rendez-vous. -->
        <DisclosureRow
          v-if="period === 'month' && insights.orp_summary"
          title="Pour l’ORP"
          :description="orpDescription"
          data-test="detail-orp"
        >
          <div
            class="bilan-summary"
            data-test="orp-summary"
          >
            <p>{{ insights.orp_summary }}</p>
            <CopyButton
              :value="insights.orp_summary"
              label="Copier le résumé"
              test-id="orp-summary-copy"
            />
          </div>
        </DisclosureRow>
      </section>
    </div>
  </section>
</template>

<style scoped>
/* Bilan › Résultats sur téléphone (maquette Progresser, Kevin 2026-11-06) : la phrase en gras d'un bloc, sans mot
   en bleu ; des tuiles de 72 px (chiffre sans interligne, libellé serré) ; le parcours en lignes de 26 px. */
.insights-period-line { margin: 0 0 var(--space-2); color: var(--text-secondary); font-size: var(--font-small); }
@media (max-width: 820px) {
  .bilan-sentence strong { color: inherit; }
  .insights :deep(.bilan-figures strong) { line-height: var(--leading-none); }
  .insights :deep(.bilan-figures span) { line-height: var(--leading-tight); }
  .insights :deep(.bilan-funnel ul) { gap: var(--space-2); }
  .insights :deep(.bilan-funnel li) { line-height: var(--leading-tight); }
}
</style>
