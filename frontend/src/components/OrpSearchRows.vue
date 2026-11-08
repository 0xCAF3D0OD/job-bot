<script setup lang="ts">
import { computed } from "vue";

import type { OrpMonth } from "../api/client";
import AppIcon from "./AppIcon.vue";
import CalendarDate from "./CalendarDate.vue";

// Les recherches du mois (maquettes Explorer et Orp) : le jour, l'entreprise, « poste · moyen » et l'étiquette
// « justificatif joint » ou « justificatif à joindre ». Les plus récentes d'abord ; `limit` pour les dernières seulement. Avec `open`,
// chaque ligne ouvre sa candidature.
// `link` (maquette du 8 novembre, Bilan sur ordinateur) : chaque ligne mène à sa candidature dans le Suivi ORP du
// mois ; l'icône calendrier de 36 px, « justificatif joint » en vert ou « justificatif à joindre » en pêche, puis « › ».
const props = defineProps<{ rows: OrpMonth["rows"]; limit?: number; open?: boolean; link?: string }>();
defineEmits<{ open: [id: number] }>();

const SHORT_MONTH = new Intl.DateTimeFormat("fr-CH", { month: "short" });
// Les lignes du formulaire ont leur date en « 28.10.2026 ».
const shown = computed(() =>
  props.rows
    .map((row) => {
      const [day, month, year] = row.date.split(".").map(Number);
      const date = new Date(year!, month! - 1, day!);
      return { ...row, day, monthNumber: month!, month: SHORT_MONTH.format(date), time: date.getTime() };
    })
    .sort((a, b) => b.time - a.time)
    .slice(0, props.limit),
);
// « Électronique » se dit « En ligne » (lot 16.4).
const how = (method: string) => (/^[ée]lectronique$/i.test(method.trim()) ? "En ligne" : method.charAt(0).toUpperCase() + method.slice(1));
</script>

<template>
  <ul
    v-if="shown.length && link"
    class="orp-rows orp-rows-link"
    data-test="orp-rows"
  >
    <li
      v-for="row in shown"
      :key="row.application_id"
    >
      <RouterLink
        :to="{ path: '/bilan/orp', query: { mois: link, candidature: row.application_id } }"
        class="orp-row"
        :data-test="`orp-row-${row.application_id}`"
      >
        <CalendarDate
          :day="row.day!"
          :month="row.monthNumber"
          tone="past"
          :size="36"
        />
        <span class="orp-what"><strong>{{ row.company }}</strong><span class="orp-sub"><span class="orp-job">{{ row.job_title }}</span><span class="orp-channel"> · {{ how(row.method) }}</span></span></span>
        <span :class="['orp-row-state', row.missing.length ? 'todo' : 'ok']">{{ row.missing.length ? "justificatif à joindre" : "justificatif joint" }}</span>
        <AppIcon
          name="chevron"
          class="orp-row-chevron"
        />
      </RouterLink>
    </li>
    <slot name="last" />
  </ul>
  <ul
    v-else-if="shown.length"
    class="orp-rows"
    data-test="orp-rows"
  >
    <li
      v-for="row in shown"
      :key="row.application_id"
    >
      <component
        :is="open ? 'button' : 'div'"
        :type="open ? 'button' : undefined"
        class="orp-row"
        :data-test="`orp-row-${row.application_id}`"
        @click="open && $emit('open', row.application_id)"
      >
        <span class="orp-day"><strong>{{ row.day }}</strong>{{ row.month }}</span>
        <span class="orp-what"><strong>{{ row.company }}</strong><span class="orp-sub"><span class="orp-job">{{ row.job_title }}</span><span class="orp-channel"> · {{ how(row.method) }}</span></span></span>
        <span
          v-if="row.missing.length"
          class="status-pill expired"
        ><AppIcon name="bang" />justificatif à joindre</span>
        <span
          v-else
          class="status-pill applied"
        ><AppIcon name="tick" />justificatif joint</span>
      </component>
    </li>
  </ul>
  <p
    v-else
    class="orp-none"
  >
    Aucune recherche ce mois-ci.
  </p>
</template>
