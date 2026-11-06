<script lang="ts">
const loadMood = () => import("./MoodAnimation.vue");
// Chargé d'avance au premier moment libre, une fois pour toutes : hors ligne, le geste « Connexion
// perdue » ne pourrait plus venir du serveur (maquette ErreurConnexion).
const idle = globalThis.requestIdleCallback ?? ((run: () => void) => setTimeout(run, 1500));
idle(() => void loadMood().catch(() => undefined));
</script>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";

import type { Mood } from "../brandPaths";
import FaceMark from "./FaceMark.vue";
import type { MoodKind } from "./MoodAnimation.vue";
import Illustration, { type IllustrationName } from "./Illustration.vue";

// Un état de jobA1 (docs/123 §2, T) : le visage de 120 px au centre, le titre, une ligne. Pour
// une liste vide et pour une page qui charge (`waiting` : l'œil et la bille pulsent).
// `illustration` (1.6.73, règle §4) : une illustration décorative à la place du visage, pour un
// écran vide, des premiers pas, une réussite ou une erreur ; jamais les deux à la fois.
// `animation` (docs/139 étape 12, maquette Animations) : le visage dans sa forme d'humeur, avec son geste,
// chargé à part pour ne pas alourdir le premier écran.
const MoodAnimation = defineAsyncComponent(loadMood);
withDefaults(
  defineProps<{
    title: string;
    mood?: Mood;
    waiting?: boolean;
    heading?: "h1" | "h2" | "p";
    illustration?: IllustrationName;
    animation?: MoodKind;
  }>(),
  {
    mood: "content",
    heading: "h2",
    illustration: undefined,
    animation: undefined,
  },
);
</script>

<template>
  <div class="face-state">
    <Illustration
      v-if="illustration"
      :name="illustration"
      class="spot"
      sizes="(max-width: 820px) 260px, 424px"
    />
    <MoodAnimation
      v-else-if="animation"
      :kind="animation"
    />
    <FaceMark
      v-else
      :mood="mood"
      :size="120"
      :waiting="waiting"
    />
    <component
      :is="heading"
      class="face-state-title"
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
