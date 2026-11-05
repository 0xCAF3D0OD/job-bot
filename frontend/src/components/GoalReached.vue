<script setup lang="ts">
import { ref } from "vue";

import type { OrpMonth } from "../api/client";
import { ofMonth } from "../format";
import AppIcon from "./AppIcon.vue";
import MoodAnimation from "./MoodAnimation.vue";
import OrpSheet from "./OrpSheet.vue";

// « C'est fait ! » (maquette ObjectifAtteint, docs/139 étape 8c ; B10 à B12, Kevin, 2026-11-04) : quand
// « J'ai postulé » atteint l'objectif ORP du mois, cet écran remplace « Candidature notée ». Le visage
// ravi dans le feston pêche, « n recherches à faire » barré une fois, « C'est fait ! » en Caveat Brush
// (un sous-ensemble partagé avec les titres des premiers pas, 3,8 Ko), l'export de la feuille, puis l'accueil.
// Le soleil saute une fois (docs/139 étape 12).
// « Je n'ai pas postulé » reste, en lien discret.
defineProps<{ data: OrpMonth }>();
const emit = defineEmits<{ cancel: [] }>();
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);

// Le gribouillis qui barre « à faire » : le tracé de la maquette.
const SCRIBBLE =
  "M2 22 10.3 3.9 14.3 34.2 18.8 6 25.4 31.4 32 8 37.6 34.8 43 5.4 46.3 36.2 51.3 3.7 58.9 32.1 65.3 5.2 69.4 31.4 76.8 5.6 83.5 33.7 91 7.2 97.9 34.2 104 4.7 107.5 33.5 111.6 5.9 119.2 35.6 126.6 4.9 132.6 34.5 140 8.7 146.7 31.4 152.9 9 157.4 33.3 161.2 5.8 166.3 31.4 170.3 4.5 178 31.5 184.3 8.3 191.1 32.7 196.7 8.3 198 32.1M196 14C150 30 90 6 40 26S8 18 4 30";

// Confettis : direction, distance et couleur fixes, comme pour l'engagement.
const PIECES = Array.from({ length: 24 }, (_, i) => {
  const angle = (i / 24) * Math.PI * 2;
  const distance = 100 + (i % 3) * 25;
  return {
    "--x": `${Math.round(Math.cos(angle) * distance)}px`,
    "--y": `${Math.round(Math.sin(angle) * distance)}px`,
    "--r": `${(i * 47) % 360}deg`,
    "--c": ["var(--primary-text)", "var(--peach)", "var(--mint)", "var(--spark)"][i % 4],
    animationDelay: `${(i % 4) * 30}ms`,
  };
});
</script>

<template>
  <section
    class="goal-reached"
    data-test="goal-reached"
  >
    <RouterLink
      to="/"
      class="icon-button icon-only goal-reached-close"
      aria-label="Fermer"
      data-test="goal-close"
    >
      <AppIcon name="close" />
    </RouterLink>
    <div
      class="goal-reached-body"
      role="status"
    >
      <div class="goal-reached-art">
        <!-- Objectif atteint (maquette Animations) : le soleil s'accroupit, saute, rayonne. -->
        <MoodAnimation kind="objectif" />
        <span
          class="confetti"
          aria-hidden="true"
        >
          <span
            v-for="(piece, index) in PIECES"
            :key="index"
            :style="piece"
          />
        </span>
      </div>
      <p class="goal-reached-todo">
        <span>
          <s>{{ data.target }} recherches à faire</s>
          <svg
            viewBox="0 0 200 40"
            preserveAspectRatio="none"
            aria-hidden="true"
          ><path
            pathLength="1"
            :d="SCRIBBLE"
          /></svg>
        </span>
      </p>
      <h1 class="goal-reached-title">
        C'est fait !
      </h1>
      <p class="goal-reached-line">
        Objectif ORP {{ ofMonth(data.month) }} atteint, {{ data.count }} recherches sur {{ data.target }}.
        Ta feuille est prête pour le rendez-vous.
      </p>
    </div>
    <div class="goal-reached-actions">
      <button
        type="button"
        class="primary"
        data-test="goal-export"
        @click="sheet?.printPdf()"
      >
        <AppIcon name="download" />Exporter ma feuille ORP
      </button>
      <RouterLink
        to="/"
        class="goal-reached-home"
        data-test="goal-home"
      >
        Retour à l'accueil
      </RouterLink>
      <button
        type="button"
        class="link goal-reached-cancel"
        data-test="cancel-applied"
        @click="emit('cancel')"
      >
        Je n'ai pas postulé
      </button>
    </div>
    <OrpSheet
      ref="sheet"
      :data="data"
    />
  </section>
</template>
