<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { usePhone } from "../composables/usePhone";
import { useTheme } from "../composables/useTheme";
import { SCENES, sceneFile, type Scene } from "../troupe";

// Une scène des 4 personnages du logo (MODIFICATIONS du 9 novembre, §15 ; troupe.ts). Largeurs des maquettes :
// la moitié du fichier, sur téléphone (`width`) et dès 1 024 px (`desktopWidth`), jamais plus que la place
// (`max-width: 100%`). `height` : affichée par sa hauteur (le « 1 » seul des petits emplacements).
// La variante sombre suit l'apparence choisie dans Réglages, ou le système en Auto. Décorative (alt vide,
// aria-hidden) ; un fondu de 200 ms à l'arrivée, coupé par « réduire les animations ». `full` : un écran plein,
// chargée tout de suite ; ailleurs, à l'affichage.
const props = withDefaults(defineProps<{ scene: Scene; width?: number; desktopWidth?: number; height?: number; full?: boolean }>(), {
  width: undefined,
  desktopWidth: undefined,
  height: undefined,
  full: false,
});

const { theme } = useTheme();
const { phone: systemDark } = usePhone("(prefers-color-scheme: dark)");
const dark = computed(() => theme.value === "dark" || (theme.value === "auto" && systemDark.value));

const info = computed(() => SCENES[props.scene]);
const phoneWidth = computed(() => (props.height ? Math.round(props.height * info.value.ratio) : (props.width ?? info.value.phone / 2)));
const deskWidth = computed(() => (props.height ? phoneWidth.value : (props.desktopWidth ?? info.value.desk / 2)));
const phoneHeight = computed(() => props.height ?? Math.round(phoneWidth.value / info.value.ratio));
const src = computed(() => sceneFile(props.scene, info.value.phone, dark.value));
const srcset = computed(() =>
  info.value.desk === info.value.phone
    ? undefined
    : `${src.value} ${info.value.phone}w, ${sceneFile(props.scene, info.value.desk, dark.value)} ${info.value.desk}w`,
);
const sizes = computed(() => (srcset.value ? `(min-width: 1024px) ${deskWidth.value}px, ${phoneWidth.value}px` : undefined));

const loaded = ref(false);
const img = ref<HTMLImageElement | null>(null);
watch(src, () => (loaded.value = false));
// Une image déjà en cache peut être prête avant que la page écoute son chargement.
onMounted(() => {
  if (img.value?.complete && img.value.naturalWidth) loaded.value = true;
});
</script>

<template>
  <img
    ref="img"
    :class="['troupe', { loaded }]"
    :src="src"
    :srcset="srcset"
    :sizes="sizes"
    :width="phoneWidth"
    :height="phoneHeight"
    :style="{ '--troupe-w': `${phoneWidth}px`, '--troupe-w-wide': `${deskWidth}px` }"
    alt=""
    aria-hidden="true"
    :loading="full ? 'eager' : 'lazy'"
    decoding="async"
    :data-scene="scene"
    :data-dark="dark ? '' : undefined"
    data-illustration="troupe"
    @load="loaded = true"
  >
</template>

<style scoped>
.troupe { display: block; flex: none; width: var(--troupe-w); max-width: var(--troupe-max, 100%); height: auto; opacity: 0; transition: opacity 200ms ease-out; }
.troupe.loaded { opacity: 1; }
@media (min-width: 1024px) { .troupe { width: var(--troupe-w-wide); } }
@media (prefers-reduced-motion: reduce) { .troupe { transition: none; } }
</style>
