<script setup lang="ts">
import { computed } from "vue";

import type { OrpMonth } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Les recherches du mois (maquettes Explorer et Orp) : le jour, l'entreprise, « poste · moyen » et l'étiquette
// « Preuve » ou « À joindre ». Les plus récentes d'abord ; `limit` pour les dernières seulement. Avec `open`,
// chaque ligne ouvre sa candidature.
const props = defineProps<{ rows: OrpMonth["rows"]; limit?: number; open?: boolean }>();
defineEmits<{ open: [id: number] }>();

const SHORT_MONTH = new Intl.DateTimeFormat("fr-CH", { month: "short" });
// Les lignes du formulaire ont leur date en « 28.10.2026 ».
const shown = computed(() =>
  props.rows
    .map((row) => {
      const [day, month, year] = row.date.split(".").map(Number);
      const date = new Date(year!, month! - 1, day!);
      return { ...row, day, month: SHORT_MONTH.format(date), time: date.getTime() };
    })
    .sort((a, b) => b.time - a.time)
    .slice(0, props.limit),
);
const how = (method: string) => method.charAt(0).toUpperCase() + method.slice(1);
</script>

<template>
  <ul
    v-if="shown.length"
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
        <span class="orp-what"><strong>{{ row.company }}</strong><span>{{ row.job_title }} · {{ how(row.method) }}</span></span>
        <span
          v-if="row.missing.length"
          class="status-pill expired"
        ><AppIcon name="bang" />À joindre</span>
        <span
          v-else
          class="status-pill applied"
        ><AppIcon name="tick" />Preuve</span>
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
