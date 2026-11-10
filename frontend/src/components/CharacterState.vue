<script setup lang="ts">
import type { Scene } from "../troupe";
import TroupeScene from "./TroupeScene.vue";

// Un état montré par les 4 personnages du logo (§15 du 9 novembre) : la scène, le titre, une ligne, puis les
// actions. Même mise en page que FaceState, mais avec la scène à la place du visage ; jamais les deux à la fois.
// Largeurs des maquettes AucuneOffre (330 px) et AucuneOffreOrdinateur (482 px). `full` : un écran plein, l'image
// est chargée tout de suite.
withDefaults(
  defineProps<{
    scene: Scene;
    title: string;
    full?: boolean;
    heading?: "h1" | "h2";
  }>(),
  { full: false, heading: "h2" },
);
</script>

<template>
  <div class="face-state character-state">
    <TroupeScene
      :scene="scene"
      :full="full"
      class="character-state-scene"
    />
    <component
      :is="heading"
      class="face-state-title character-state-title"
    >
      {{ title }}
    </component>
    <div
      v-if="$slots.default"
      class="face-state-line"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
/* Valeurs de la maquette AucuneOffre (390 px) : le titre à 22 px en gras, 8 px sous la scène. */
.character-state-scene { margin-inline: auto; }
.character-state-title { margin-top: var(--space-2); font-size: var(--font-section); font-weight: var(--weight-bold); }
/* Ordinateur (maquette du 8 novembre, AucuneOffreOrdinateur) : le titre de 34/42 en 800, la phrase de 18/28, les
   boutons de 44 côte à côte. */
@media (min-width: 1024px) {
  .character-state-wide { --cs-34: 34px; --cs-42: 42px; --cs-18: 18px; --cs-28: 28px; --cs-10: 10px; padding-block: var(--space-12); }
  .character-state-wide .character-state-title { margin-top: var(--space-6); font-size: var(--cs-34); line-height: var(--cs-42); font-weight: var(--weight-heavy); }
  .character-state-wide .face-state-line { max-width: 560px; font-size: var(--cs-18); line-height: var(--cs-28); color: var(--text-secondary); }
  .character-state-wide :deep(.face-state-actions) { display: flex; justify-content: center; gap: var(--cs-10); margin-top: var(--space-6); }
  .character-state-wide :deep(.face-state-actions button) { min-height: var(--target-min); padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--font-label); }
}
</style>
