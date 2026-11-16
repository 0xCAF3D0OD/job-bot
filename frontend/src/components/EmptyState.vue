<script setup lang="ts">
import type { IconName } from "../icons";
import type { Scene } from "../troupe";
import AppIcon from "./AppIcon.vue";
import TroupeScene from "./TroupeScene.vue";

// L'état vide commun (maquette du 15 novembre, §13) : l'illustration, le titre, une pastille à la place d'une phrase
// d'explication (« texte hors carte = titre ou lien seulement »), les boutons, puis un lien. Centré sur toute la
// largeur, au milieu de l'espace sous l'en-tête de page, un peu au-dessus du centre exact. Un seul composant pour tous
// les écrans vides (règle de Kevin du 15.11) : Offres, Envoyées, Rendez-vous, filtres, fin du tri, alertes. Le titre
// peut venir d'un emplacement `title` (titre manuscrit de Trier) ; `title` reste son nom accessible par défaut.
// `width` et `desktopWidth` : la largeur du dessin de la planche (260 et 400 par défaut, comme Offres).
withDefaults(
  defineProps<{
    title: string;
    // La phrase sous le titre, seulement là où une planche la dessine (Candidatures vide avec alertes, §41 du 16.11).
    text?: string;
    scene?: Scene;
    pill?: string;
    pillIcon?: IconName;
    heading?: "h1" | "h2";
    width?: number;
    desktopWidth?: number;
  }>(),
  { text: undefined, scene: undefined, pill: undefined, pillIcon: "clock", heading: "h2", width: 260, desktopWidth: 400 },
);
</script>

<template>
  <div class="empty-state">
    <slot name="illustration">
      <TroupeScene
        v-if="scene"
        :scene="scene"
        :width="width"
        :desktop-width="desktopWidth"
        class="empty-state-scene"
      />
    </slot>
    <component
      :is="heading"
      class="empty-state-title"
    >
      <slot name="title">
        {{ title }}
      </slot>
    </component>
    <p
      v-if="text"
      class="empty-state-text"
      data-test="empty-text"
    >
      {{ text }}
    </p>
    <span
      v-if="pill"
      class="empty-state-pill"
      data-test="empty-pill"
    ><AppIcon :name="pillIcon" />{{ pill }}</span>
    <div
      v-if="$slots.actions"
      class="empty-state-actions"
    >
      <slot name="actions" />
    </div>
    <slot />
  </div>
</template>
