<script setup lang="ts">
import { computed, ref, watch } from "vue";

// Illustration de jobA1 (docs/67) : une image générée pour la plateforme, préparée par
// scripts/illustrations.mjs. Chargée seulement quand elle s'affiche ; elle entre une fois, en
// fondu, quand elle est là. En sombre, la série sombre si elle existe, sinon la claire assombrie.
// Décorative par défaut ; `label` la décrit aux lecteurs d'écran quand elle dit quelque chose.
const props = withDefaults(defineProps<{ name: IllustrationName; label?: string; size?: "small" | "medium" | "large" }>(), {
  label: "",
  size: "medium",
});

const files = import.meta.glob<string>("../assets/illustrations/*.webp", { query: "?url", import: "default", eager: true });

function srcset(name: string): string {
  return [480, 800]
    .map((width) => [files[`../assets/illustrations/${name}-${width}.webp`], width] as const)
    .filter(([url]) => url)
    .map(([url, width]) => `${url} ${width}w`)
    .join(", ");
}

const light = computed(() => srcset(props.name));
const dark = computed(() => srcset(`${props.name}-sombre`));
const loaded = ref(false);
watch(
  () => props.name,
  () => (loaded.value = false),
);
</script>

<script lang="ts">
export type IllustrationName =
  | "accueil-reseau"
  | "actualites-video"
  | "alertes-carte"
  | "aucune-offre"
  | "bilan"
  | "emails-tries"
  | "formations"
  | "lecture-calme"
  | "lieux-carte"
  | "messager"
  | "offres-profils"
  | "porte-ouverte"
  | "preuves-orp"
  | "suivi-envoi"
  | "tableau-de-bord";
</script>

<template>
  <span
    :class="['illu', size, { loaded, 'no-dark': !dark }]"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    :data-illustration="name"
  >
    <picture :key="name">
      <source
        v-if="dark"
        media="(prefers-color-scheme: dark)"
        :srcset="dark"
        sizes="(max-width: 820px) 240px, 440px"
      >
      <img
        :src="files[`../assets/illustrations/${name}-480.webp`]"
        :srcset="light"
        sizes="(max-width: 820px) 240px, 440px"
        alt=""
        loading="lazy"
        decoding="async"
        @load="loaded = true"
      >
    </picture>
  </span>
</template>
