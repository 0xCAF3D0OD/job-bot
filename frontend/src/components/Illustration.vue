<script setup lang="ts">
import { ref, watch } from "vue";

// Illustration unDraw (règles dans docs/interface.md, docs/62) : insérée dans la page pour prendre
// les couleurs du thème (feuille de style, `.illu [fill=…]`) ; son animation joue une fois.
// Chargée seulement quand elle s'affiche.
// Décorative par défaut ; `label` la décrit aux lecteurs d'écran quand elle dit quelque chose.
const props = withDefaults(defineProps<{ name: IllustrationName; label?: string; size?: "small" | "medium" | "large" }>(), {
  label: "",
  size: "medium",
});

const files = import.meta.glob<string>("../assets/illustrations/*.svg", { query: "?raw", import: "default" });
// Le dessin est posé tel quel dans la page (fichiers du dépôt, préparés par
// scripts/illustrations.mjs) : c'est ce qui lui permet de suivre les couleurs du thème.
const host = ref<HTMLElement | null>(null);

// Le texte du dessin et son emplacement arrivent dans n'importe quel ordre : on le pose dès que
// les deux sont là (sinon une illustration peut rester vide).
const svg = ref("");
watch(
  () => props.name,
  async (name) => {
    const load = files[`../assets/illustrations/${name}.svg`];
    const text = load ? await load() : "";
    if (name === props.name) svg.value = text;
  },
  { immediate: true },
);
watch(
  [host, svg],
  ([el, text]) => {
    if (el) el.innerHTML = text;
  },
  { flush: "post", immediate: true },
);
</script>

<script lang="ts">
export type IllustrationName =
  | "absorbed"
  | "certification"
  | "detailed-answer"
  | "done"
  | "handshake-deal"
  | "lock-screen-notifications"
  | "login"
  | "mailbox"
  | "message-sent"
  | "morning-plans"
  | "my-resume"
  | "page-eaten"
  | "stepping-up"
  | "tight-deadline";
</script>

<template>
  <span
    ref="host"
    :class="['illu', size]"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    :data-illustration="name"
  />
</template>
