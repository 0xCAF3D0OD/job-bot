<script setup lang="ts">
import type { Pose } from "../personnage";
import Illustration from "./Illustration.vue";

// Un état montré par le personnage (docs/141 §3) : la pose, le titre, une ligne, puis les actions. Même
// mise en page que FaceState, mais avec le personnage à la place du visage ; jamais les deux à la fois.
// `full` : un écran plein (240 à 280 px) ; sinon l'état tient dans une liste (200 px au plus).
// `accessory` : un objet du kit posé au sol à droite du personnage (la tasse de l'attente, docs/141 §3).
withDefaults(
  defineProps<{
    pose: Pose;
    title: string;
    height?: number;
    desktopHeight?: number;
    full?: boolean;
    heading?: "h1" | "h2";
    accessory?: string;
  }>(),
  { height: 200, desktopHeight: undefined, full: false, heading: "h2", accessory: undefined },
);
</script>

<template>
  <div class="face-state character-state">
    <div class="character-state-scene">
      <Illustration
        :pose="pose"
        :height="height"
        :desktop-height="desktopHeight"
        :full="full"
      />
      <img
        v-if="accessory"
        class="character-state-accessory"
        :src="accessory"
        alt=""
        aria-hidden="true"
        width="40"
        height="53"
        loading="lazy"
        data-test="character-accessory"
      >
    </div>
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
/* Valeurs de la maquette AucuneOffre (390 px) : le titre à 22 px en gras, 8 px sous le personnage. */
.character-state-scene { display: flex; align-items: flex-end; justify-content: center; gap: var(--space-1); }
.character-state-accessory { width: 40px; height: auto; }
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
