<script setup lang="ts">
import { motionAllowed } from "../composables/useIntro";
import { LOGO_EYE, LOGO_ONE, LOGO_SMILE, LOGO_SPARK, LOGO_TILT } from "../brandPaths";

// Le personnage se transforme (docs/123, complément 0.96.0, d'après ta maquette « X ») : pendant
// qu'une page charge, le visage du logo prend l'objet de la page, puis redevient lui-même, en
// boucle tant que l'attente dure (2,8 s ; 3 s pour la loupe). Avec « réduire les animations » :
// le visage tel quel. Décoratif : le nom de la page est écrit dessous.
export type Transform = "today" | "offers" | "applications" | "alerts" | "insights" | "orp-meeting" | "profile" | "settings";
defineProps<{ kind: Transform; size?: number }>();
const motion = motionAllowed();
const RAYS = "M90 41 H95 M85.9 50.9 L89.4 54.4 M76 55 V60 M66.1 50.9 L62.6 54.4 M62 41 H57 M66.1 31.1 L62.6 27.6 M76 27 V22 M85.9 31.1 L89.4 27.6";
</script>

<template>
  <svg
    :class="['face-transform', motion ? `ft-${kind}` : 'ft-still']"
    :width="size ?? 120"
    :height="size ?? 120"
    :viewBox="kind === 'orp-meeting' && motion ? '0 4 104 112' : '0 0 104 104'"
    aria-hidden="true"
    focusable="false"
    :data-transform="kind"
  >
    <g :transform="LOGO_TILT">
      <path
        class="ft-line"
        :d="LOGO_ONE"
      />
      <!-- L'œil gauche : grossit sous la loupe (Offres), s'efface pour l'anneau (Bilan), devient
           la tête du profil (Profil). -->
      <circle
        class="ft-eye ft-box ft-eye-l"
        :cx="LOGO_EYE.x"
        :cy="LOGO_EYE.y"
        r="10"
      />
      <template v-if="motion && kind === 'insights'">
        <g class="ft-donut">
          <circle
            class="ft-donut-track"
            :cx="LOGO_EYE.x"
            :cy="LOGO_EYE.y"
            r="9"
          />
          <circle
            class="ft-donut-fill"
            :cx="LOGO_EYE.x"
            :cy="LOGO_EYE.y"
            r="9"
            :transform="`rotate(-90 ${LOGO_EYE.x} ${LOGO_EYE.y})`"
          />
        </g>
      </template>
      <template v-if="motion && kind === 'profile'">
        <path
          class="ft-draw ft-thin"
          d="M15 55 Q 24 46 33 55"
          style="--len: 24"
        />
        <circle
          class="ft-draw ft-ring"
          :cx="LOGO_EYE.x"
          :cy="LOGO_EYE.y"
          r="15"
          style="--len: 95"
        />
      </template>
      <!-- Le soleil d'Aujourd'hui : ses rayons, derrière la bille. -->
      <g
        v-if="motion && kind === 'today'"
        class="ft-box ft-rays"
      >
        <path :d="RAYS" />
      </g>
      <!-- La bille pêche : s'ouvre en soleil (Aujourd'hui), grossit (Offres), laisse la place à la
           cloche (Alertes) et à la roue dentée (Réglages). -->
      <circle
        class="ft-spark ft-box ft-spark-r"
        :cx="LOGO_SPARK.x"
        :cy="LOGO_SPARK.y"
        r="10"
      />
      <g
        v-if="motion && kind === 'alerts'"
        class="ft-box ft-pop"
      >
        <g class="ft-top ft-ring-bell">
          <path
            class="ft-spark-line"
            d="M76 24 V27"
          />
          <path
            class="ft-spark-shape"
            d="M66 48 Q 66 28 76 27 Q 86 28 86 48 L 89 51 L 63 51 Z"
          />
          <circle
            class="ft-spark"
            cx="76"
            cy="55"
            r="3.5"
          />
        </g>
      </g>
      <g
        v-if="motion && kind === 'settings'"
        class="ft-box ft-pop"
      >
        <g class="ft-box ft-gear">
          <circle
            class="ft-gear-teeth"
            cx="76"
            cy="41"
            r="12"
          />
          <circle
            class="ft-gear-body"
            cx="76"
            cy="41"
            r="8.5"
          />
          <circle
            class="ft-spark"
            cx="76"
            cy="41"
            r="2.5"
          />
        </g>
      </g>
      <path
        class="ft-line ft-smile"
        :d="LOGO_SMILE"
      />
      <!-- Le Suivi : le sourire devient une flèche qui avance. -->
      <path
        v-if="motion && kind === 'applications'"
        class="ft-line ft-arrow"
        d="M26 75 H74 M62 65 L74 75 L62 85"
      />
      <!-- Le rendez-vous : une cravate rayée se déroule sous le sourire. -->
      <g
        v-if="motion && kind === 'orp-meeting'"
        class="ft-top ft-tie"
      >
        <g class="ft-top ft-tie-swing">
          <path
            class="ft-spark-shape"
            d="M45.5 88 H54.5 L52.5 95 H47.5 Z"
          />
          <path
            class="ft-spark-shape"
            d="M47.5 95 H52.5 L56.5 109 L50 115 L43.5 109 Z"
          />
          <path
            class="ft-tie-stripes"
            d="M45.5 103 L54.8 99 M44.6 109 L56 104"
          />
        </g>
      </g>
      <!-- Les Offres : la loupe passe d'un œil à l'autre. -->
      <g
        v-if="motion && kind === 'offers'"
        class="ft-loupe"
      >
        <circle
          class="ft-loupe-glass"
          :cx="LOGO_EYE.x"
          :cy="LOGO_EYE.y"
          r="16"
        />
        <path
          class="ft-loupe-handle"
          d="M35.5 56.5 L46 67"
        />
      </g>
    </g>
  </svg>
</template>
