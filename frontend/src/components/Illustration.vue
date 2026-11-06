<script lang="ts">
import type { Pose } from "../personnage";

// Largeur des fichiers -400 (hauteur 400) : sert à fixer width et height, sans saut de mise en page.
export const POSE_WIDTH: Record<Pose, number> = {
  debout: 129,
  bonjour: 150,
  cv: 131,
  marche: 231,
  assis: 285,
  perplexe: 146,
  revelation: 196,
  avion: 275,
  cables: 198,
  "hors-ligne": 167,
  loupe: 200,
  celebration: 192,
};

// Hauteurs permises (consigne du 6.11.2026) : 200 px au plus dans une liste, 240 à 280 px sur un écran
// plein, 400 px au plus sur ordinateur.
export const MAX_HEIGHT = { list: 200, full: 280, desktop: 400 } as const;
</script>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { poseFile } from "../personnage";

// `height` : la hauteur sur téléphone ; `desktopHeight` : sur ordinateur (dès 821 px), sinon la même.
// `full` : un écran plein, l'image est chargée tout de suite ; ailleurs, à l'affichage (loading="lazy").
// Décoratif (alt vide, aria-hidden) ; un fondu de 200 ms à l'arrivée, coupé par « réduire les animations ».
const props = withDefaults(defineProps<{ pose: Pose; height: number; desktopHeight?: number; full?: boolean }>(), {
  desktopHeight: undefined,
  full: false,
});

const phoneHeight = computed(() => Math.min(props.height, props.full ? MAX_HEIGHT.full : MAX_HEIGHT.list));
const wideHeight = computed(() => Math.min(props.desktopHeight ?? phoneHeight.value, MAX_HEIGHT.desktop));
const width = computed(() => Math.round((POSE_WIDTH[props.pose] * phoneHeight.value) / 400));
const src = computed(() => poseFile(props.pose, 400));
const srcset = computed(() => `${src.value} 1x, ${poseFile(props.pose, 800)} 2x`);

const loaded = ref(false);
const img = ref<HTMLImageElement | null>(null);
watch(
  () => props.pose,
  () => (loaded.value = false),
);
// Une image déjà en cache peut être prête avant que la page écoute son chargement.
onMounted(() => {
  if (img.value?.complete && img.value.naturalWidth) loaded.value = true;
});
</script>

<template>
  <img
    ref="img"
    :class="['personnage', { loaded }]"
    :src="src"
    :srcset="srcset"
    :width="width"
    :height="phoneHeight"
    :style="{ '--perso-h': `${phoneHeight}px`, '--perso-h-wide': `${wideHeight}px` }"
    alt=""
    aria-hidden="true"
    :loading="full ? 'eager' : 'lazy'"
    decoding="async"
    :data-pose="pose"
    data-illustration="personnage"
    @load="loaded = true"
  >
</template>

<style scoped>
.personnage { display: block; flex: none; width: auto; height: var(--perso-h); max-width: none; opacity: 0; transition: opacity 200ms ease-out; }
.personnage.loaded { opacity: 1; }
@media (min-width: 821px) { .personnage { height: var(--perso-h-wide); } }
@media (prefers-reduced-motion: reduce) { .personnage { transition: none; } }
</style>
