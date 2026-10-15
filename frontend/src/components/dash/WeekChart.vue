<script setup lang="ts">
import { computed, ref } from "vue";

import type { Today } from "../../api/client";
import { localDate, plural } from "../../format";

// « Ta semaine » (docs/54 §2) : barres des 7 derniers jours, offres reçues ou candidatures
// envoyées ; la valeur dans une bulle sombre au survol (ou au focus) d'une barre.
const props = defineProps<{ week: Today["week"] }>();
const kind = ref<"offers" | "applications">("offers");
const active = ref<number | null>(null);
const dayName = new Intl.DateTimeFormat("fr-CH", { weekday: "short" });
const dayLong = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" });

const max = computed(() => Math.max(1, ...props.week.map((d) => d[kind.value])));
const total = computed(() => props.week.reduce((n, d) => n + d[kind.value], 0));
function amount(n: number): string {
  return kind.value === "offers" ? plural(n, "offre", "offres", "aucune offre") : plural(n, "candidature", "candidatures", "aucune candidature");
}
</script>

<template>
  <section
    class="dash-card week-chart"
    data-test="week-chart"
  >
    <header class="dash-card-head">
      <h2>Ta semaine</h2>
      <div
        class="segmented small"
        role="radiogroup"
        aria-label="Ce que montrent les barres"
      >
        <button
          type="button"
          role="radio"
          :aria-checked="kind === 'offers'"
          data-test="week-offers"
          @click="kind = 'offers'"
        >
          Offres reçues
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="kind === 'applications'"
          data-test="week-applications"
          @click="kind = 'applications'"
        >
          Candidatures
        </button>
      </div>
    </header>
    <p class="hint week-total">
      {{ amount(total) }} sur 7 jours
    </p>
    <ol class="bar-chart">
      <li
        v-for="(day, index) in week"
        :key="day.day"
        :class="{ today: index === week.length - 1, active: active === index }"
        tabindex="0"
        :aria-label="`${dayLong.format(localDate(day.day))} : ${amount(day[kind])}`"
        @pointerenter="active = index"
        @pointerleave="active = null"
        @focus="active = index"
        @blur="active = null"
      >
        <span class="bar-track">
          <span
            v-if="active === index"
            class="bar-tip"
            aria-hidden="true"
          ><small>{{ dayLong.format(localDate(day.day)) }}</small>{{ amount(day[kind]) }}</span>
          <span
            class="bar-fill"
            :style="{ height: `${Math.max(day[kind] ? 6 : 2, (day[kind] / max) * 100)}%` }"
            data-test="week-bar"
          />
        </span>
        <span class="bar-label">{{ dayName.format(localDate(day.day)).replace(".", "") }}</span>
      </li>
    </ol>
  </section>
</template>
