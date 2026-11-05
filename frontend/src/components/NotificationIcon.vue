<script setup lang="ts">
import { FACE_MOUTH, ICON_EYE, ICON_ONE, ICON_SPARK } from "../brandPaths";
import { ICONS } from "../icons";
import type { NotificationShape } from "../notificationKinds";

// L'icône d'une notification, 40 px (maquette Notifications, N8) : le visage du 1 dans une forme qui dit
// le genre. Carré gris : un rappel ORP ou de suivi ; triangle orange : un souci ; dôme bleu : une nouvelle
// calme. Les offres ont une icône fixe, sans anneau ni chiffre (D3, décision de Kevin du 2026-11-04).
// Décorative : le titre de la ligne dit tout.
defineProps<{ shape: NotificationShape }>();
// Le visage se place dans la forme : centre, échelle (d'après la maquette).
const FACE = {
  orp: { y: 52, scale: 0.6, mouth: FACE_MOUTH.attentif },
  warning: { y: 63, scale: 0.5, mouth: "M36 77 L 64 77" },
  calm: { y: 60, scale: 0.54, mouth: FACE_MOUTH.content },
} as const;
</script>

<!-- eslint-disable vue/no-v-html -- le tracé de la mallette est une constante de src/icons.ts, jamais une donnée -->
<template>
  <svg
    :class="['notif-icon', `notif-icon-${shape}`]"
    width="40"
    height="40"
    viewBox="0 0 100 100"
    aria-hidden="true"
    focusable="false"
    :data-shape="shape"
  >
    <template v-if="shape === 'offers'">
      <circle
        class="notif-icon-bg"
        cx="50"
        cy="50"
        r="44"
      />
      <g
        class="notif-icon-glyph"
        transform="translate(20 20) scale(2.5)"
        v-html="ICONS.briefcase"
      />
    </template>
    <template v-else>
      <rect
        v-if="shape === 'orp'"
        class="notif-icon-bg"
        x="7"
        y="7"
        width="86"
        height="86"
        rx="30"
      />
      <path
        v-else-if="shape === 'warning'"
        class="notif-icon-bg"
        d="M56.77 22.25 L85.23 73.75 Q92 86 78 86 L22 86 Q8 86 14.77 73.75 L43.23 22.25 Q50 10 56.77 22.25 Z"
      />
      <path
        v-else
        class="notif-icon-bg"
        d="M5 84 V58 A45 45 0 0 1 95 58 V84 Q95 91 88 91 H12 Q5 91 5 84 Z"
      />
      <g :transform="`translate(50 ${FACE[shape].y}) scale(${FACE[shape].scale}) translate(-50 -52)`">
        <path
          class="notif-icon-line"
          :d="ICON_ONE"
        />
        <circle
          class="notif-icon-eye"
          :cx="ICON_EYE.x"
          :cy="ICON_EYE.y"
          r="10"
        />
        <circle
          class="notif-icon-spark"
          :cx="ICON_SPARK.x"
          :cy="ICON_SPARK.y"
          r="10"
        />
        <path
          class="notif-icon-line"
          :d="FACE[shape].mouth"
        />
      </g>
    </template>
  </svg>
</template>
