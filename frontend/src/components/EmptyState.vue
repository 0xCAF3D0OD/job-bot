<script setup lang="ts">
import type { IconName } from "../icons";
import type { Scene } from "../troupe";
import AppIcon from "./AppIcon.vue";
import TroupeScene from "./TroupeScene.vue";

// L'état vide commun (maquette du 15 novembre, §13) : l'illustration, le titre, une pastille à la place d'une phrase
// d'explication (« texte hors carte = titre ou lien seulement »), les boutons, puis un lien. Centré sur toute la
// largeur, au milieu de l'espace sous l'en-tête de page, un peu au-dessus du centre exact. Un seul composant pour tous
// les écrans vides (règle de Kevin du 15.11) : Offres, Envoyées, Rendez-vous, filtres, fin du tri, alertes.
withDefaults(
  defineProps<{
    title: string;
    scene?: Scene;
    pill?: string;
    pillIcon?: IconName;
    heading?: "h1" | "h2";
  }>(),
  { scene: undefined, pill: undefined, pillIcon: "clock", heading: "h2" },
);
</script>

<template>
  <div class="empty-state">
    <slot name="illustration">
      <TroupeScene
        v-if="scene"
        :scene="scene"
        :width="260"
        :desktop-width="400"
        class="empty-state-scene"
      />
    </slot>
    <component
      :is="heading"
      class="empty-state-title"
    >
      {{ title }}
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
/* Valeurs des planches CandidaturesVide (téléphone) et CandidaturesOrdinateurVide (ordinateur) : illustration de 260
   (400 sur ordinateur) ; titre 22/28 en 800, sans resserrement, 20 px dessous (28/34, 28 px sur ordinateur) ; pastille 14/20 600 en
   6/12, coins ronds, icône 16, 12 px sous le titre ; boutons de 48 empilés, 300 px au plus, écart 12, 24 px sous la
   pastille (52 côte à côte, 28 px dessous, sur ordinateur) ; lien 15/700 de 44 px, 8 px dessous (20 sur ordinateur). Contour des boutons secondaires : --line-strong (#C9C5BA
   sur la planche, absent des jetons, comme sur AucuneOffreOrdinateur). */
.empty-state {
  --es-t: var(--title-sub); --es-lh: var(--title-login); --es-top: 20px; --es-btn: var(--btn-tertiary); --es-gap: var(--space-6); --es-link: var(--space-2);
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 0 var(--space-5) var(--btn-compact);
}
.empty-state-title { margin: var(--es-top) 0 0; font-size: var(--es-t); line-height: var(--es-lh); font-weight: var(--weight-heavy); letter-spacing: 0; }
.empty-state-pill {
  display: inline-flex; align-items: center; gap: var(--space-1); --es-6: 6px; margin-top: var(--space-3); padding: var(--es-6) var(--space-3);
  border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-semibold);
}
.empty-state-pill svg { width: var(--space-4); height: var(--space-4); }
.empty-state-actions { --es-300: 300px; display: flex; flex-direction: column; gap: var(--space-3); width: 100%; max-width: var(--es-300); margin-top: var(--es-gap); }
.empty-state-actions > * {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2); min-height: var(--es-btn); margin: 0;
  padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none;
}
.empty-state-actions svg, .empty-state > .link svg { --es-18: 18px; width: var(--es-18); height: var(--es-18); }
.empty-state-actions > .secondary { --es-22: 22px; padding-inline: var(--es-22); border: 1.5px solid var(--line-strong); background: var(--surface); color: var(--text); }
.empty-state > .link { --es-15: 15px; --es-2: 2px; display: inline-flex; align-items: center; gap: var(--es-2); min-height: var(--target-min); margin-top: var(--es-link); font-size: var(--es-15); font-weight: var(--weight-bold); color: var(--primary-text); }
@media (min-width: 1024px) {
  .empty-state { --es-t: var(--title-login); --es-lh: var(--title-block); --es-top: 28px; --es-btn: var(--btn-secondary); --es-gap: 28px; --es-link: var(--space-5); --es-72: 72px; padding: 0 0 var(--es-72); }
  .empty-state-actions { flex-direction: row; justify-content: center; width: auto; max-width: none; }
}
</style>
