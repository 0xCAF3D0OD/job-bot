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
    scene?: Scene;
    pill?: string;
    pillIcon?: IconName;
    heading?: "h1" | "h2";
    width?: number;
    desktopWidth?: number;
  }>(),
  { scene: undefined, pill: undefined, pillIcon: "clock", heading: "h2", width: 260, desktopWidth: 400 },
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

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.empty-state .empty-state-title { margin: var(--es-top) 0 0; font-size: var(--es-t); line-height: var(--es-lh); font-weight: var(--weight-heavy); letter-spacing: 0; }
@media (min-width: 1024px) {
.empty-state { --es-t: var(--title-login); --es-lh: var(--title-block); --es-top: 28px; --es-btn: var(--btn-secondary); --es-gap: 28px; --es-link: var(--space-5); --es-72: 72px; padding: 0 0 var(--es-72); }
.empty-state-actions { flex-direction: row; justify-content: center; width: auto; max-width: none; }
}
</style>
