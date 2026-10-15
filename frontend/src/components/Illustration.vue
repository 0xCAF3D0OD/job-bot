<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

// Illustration unDraw animée (docs/58) : insérée dans la page pour prendre les couleurs du
// thème (feuille de style, `.illu [fill=…]`). Chargée seulement quand elle s'affiche.
// Décorative par défaut ; `label` la décrit aux lecteurs d'écran quand elle dit quelque chose.
const props = withDefaults(defineProps<{ name: IllustrationName; label?: string; size?: "small" | "medium" | "large" }>(), {
  label: "",
  size: "medium",
});

const files = import.meta.glob<string>("../assets/illustrations/*.svg", { query: "?raw", import: "default" });
// Le dessin est posé tel quel dans la page (fichiers du dépôt, préparés par
// scripts/illustrations.mjs) : c'est ce qui lui permet de suivre les couleurs du thème.
const host = ref<HTMLElement | null>(null);

// Posé une fois l'emplacement monté (un fichier déjà chargé arrive avant sinon).
async function draw(): Promise<void> {
  const wanted = props.name;
  const load = files[`../assets/illustrations/${wanted}.svg`];
  const text = load ? await load() : "";
  if (wanted === props.name && host.value) host.value.innerHTML = text;
}
onMounted(draw);
watch(() => props.name, draw);
</script>

<script lang="ts">
export type IllustrationName =
  | "ai-generated-document"
  | "certification"
  | "date-picker"
  | "done"
  | "loading-ui"
  | "lock-screen-notifications"
  | "mailbox"
  | "message-sent"
  | "mobile-inbox"
  | "my-resume"
  | "online-connection"
  | "processing"
  | "profile"
  | "settings"
  | "stepping-up";
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
