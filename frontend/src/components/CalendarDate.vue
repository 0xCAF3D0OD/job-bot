<script setup lang="ts">
import { computed } from "vue";

import { monthCaps } from "../dates";

// L'icône calendrier qui contient la date (maquette du 8 novembre, docs/143, D26 ; modèle
// docs/mobile/calendrier-date.html) : au trait, mois abrégé en capitales en haut, jour en gras au centre. Remplace les
// carrés de date colorés. Tons : à venir (bleu), ORP ou à noter, passé. Décorative si la date est écrite à côté.
const props = withDefaults(
  defineProps<{ day: number; month: number; tone?: "blue" | "orp" | "past"; size?: 36 | 40 | 44 | 48 | 56; label?: string }>(),
  { tone: "blue", size: 48, label: "" },
);
const height = computed(() => Math.round((props.size * 52) / 48));
const caps = computed(() => monthCaps(props.month));
</script>

<template>
  <svg
    :class="['calendar-date', `calendar-date-${tone}`]"
    :width="size"
    :height="height"
    viewBox="0 0 48 52"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    data-test="calendar-date"
  >
    <rect
      x="3"
      y="7"
      width="42"
      height="42"
      rx="10"
      class="calendar-date-frame"
      stroke-width="2.5"
    />
    <path
      d="M3 21 H45"
      class="calendar-date-line"
      stroke-width="2"
    />
    <path
      d="M14 2.5 V9 M34 2.5 V9"
      class="calendar-date-line"
      stroke-width="3"
      stroke-linecap="round"
    />
    <text
      x="24"
      y="18"
      text-anchor="middle"
      font-size="8.5"
      font-weight="800"
      letter-spacing=".4"
      class="calendar-date-month"
    >{{ caps }}</text>
    <text
      x="24"
      y="42"
      text-anchor="middle"
      font-size="18"
      font-weight="800"
      class="calendar-date-day"
    >{{ day }}</text>
  </svg>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.calendar-date-orp { --cal-tone: var(--warning); }
/* Passé : le cadre et les traits en --field-border (#8C8478, permis pour les traits), le mois écrit en
   --text-secondary comme le jour (#596070, #ABA398 en sombre : corrections du 13.11, §3, pas de #8C8478 en texte). */
.calendar-date-past { --cal-tone: var(--field-border); --cal-month: var(--text-secondary); --cal-day: var(--text-secondary); }
.calendar-date-frame { fill: var(--surface); stroke: var(--cal-tone); }
.calendar-date-line { stroke: var(--cal-tone); fill: none; }
.calendar-date-month { fill: var(--cal-month, var(--cal-tone)); font-family: inherit; }
.calendar-date-day { fill: var(--cal-day); font-family: inherit; }
</style>
