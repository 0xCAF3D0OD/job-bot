<script setup lang="ts">
import { computed, ref } from "vue";

import type { components } from "../../api/schema";
import { localDate, plural } from "../../format";
import { firstTime } from "../../composables/useIntro";

// « Par mois » du Bilan (docs/55 §2) : candidatures et réponses en barres doubles, mois par
// mois (ou semaine par semaine pour un mois choisi) ; la valeur dans une bulle au survol,
// comme « Ta semaine » d'Aujourd'hui.
type Bucket = components["schemas"]["BucketOut"];
const props = defineProps<{ buckets: Bucket[]; unit: "month" | "week" }>();
const active = ref<number | null>(null);

const monthShort = new Intl.DateTimeFormat("fr-CH", { month: "short" });
const monthLong = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric" });
const dayMonth = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

function short(bucket: Bucket): string {
  const day = localDate(bucket.start);
  return props.unit === "week" ? dayMonth.format(day).replace(".", "") : monthShort.format(day).replace(".", "");
}
function long(bucket: Bucket): string {
  const day = localDate(bucket.start);
  return props.unit === "week" ? `semaine du ${dayMonth.format(day)}` : monthLong.format(day);
}
function counts(bucket: Bucket): string {
  return `${plural(bucket.applications, "candidature", "candidatures", "aucune candidature")}, ${plural(bucket.responses, "réponse", "réponses", "aucune réponse")}`;
}
const max = computed(() => Math.max(1, ...props.buckets.map((b) => b.applications)));
function height(n: number): string {
  return `${Math.max(n ? 6 : 2, (n / max.value) * 100)}%`;
}
// Les barres montent à la première ouverture (docs/60 §3).
const intro = firstTime("period-chart");
</script>

<template>
  <section
    class="dash-card period-chart"
    data-test="period-chart"
  >
    <header class="dash-card-head">
      <h2>{{ unit === "week" ? "Par semaine" : "Par mois" }}</h2>
      <p class="period-legend">
        <span class="period-key sent">Candidatures</span>
        <span class="period-key answered">Réponses</span>
      </p>
    </header>
    <ol
      :class="['bar-chart', 'period-bars', { intro }]"
      :style="{ gridTemplateColumns: `repeat(${buckets.length}, minmax(0, 1fr))` }"
    >
      <li
        v-for="(bucket, index) in buckets"
        :key="bucket.start"
        :class="{ active: active === index }"
        tabindex="0"
        :aria-label="`${long(bucket)} : ${counts(bucket)}`"
        data-test="period-bucket"
        @pointerenter="active = index"
        @pointerleave="active = null"
        @focus="active = index"
        @blur="active = null"
      >
        <span class="bar-track period-track">
          <span
            v-if="active === index"
            class="bar-tip"
            aria-hidden="true"
          ><small>{{ long(bucket) }}</small>{{ counts(bucket) }}</span>
          <span
            class="bar-fill"
            :style="{ height: height(bucket.applications) }"
          />
          <span
            class="bar-fill answered"
            :style="{ height: height(bucket.responses) }"
          />
        </span>
        <span class="bar-label">{{ short(bucket) }}</span>
      </li>
    </ol>
  </section>
</template>
