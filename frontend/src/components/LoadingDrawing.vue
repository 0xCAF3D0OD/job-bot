<script setup lang="ts">
import { ref, watch } from "vue";

// Le dessin animé d'une page qui charge (docs/61 §2, docs/67 complément 0.55.1) : les dessins
// unDraw d'avant, gardés pour ce seul moment parce que leur animation fait patienter. Inséré dans
// la page pour prendre les couleurs du thème (`.drawing [fill=…]`) ; l'animation joue une fois,
// sauf celle de la maintenance, qui dure autant que l'attente (docs/80 §2).
// Préparés par scripts/illustrations-undraw.mjs. Décoratif : le nom de la page est écrit dessous.
const props = defineProps<{ name: DrawingName }>();

const files = import.meta.glob<string>("../assets/dessins/*.svg", { query: "?raw", import: "default" });
// Celui de la maintenance est dans l'application dès le départ : la page d'attente s'affiche
// justement quand le serveur ne répond plus, et ne pourrait pas le télécharger (0.82.1).
const ready = import.meta.glob<string>("../assets/dessins/maintenance.svg", {
  query: "?raw",
  import: "default",
  eager: true,
});
const host = ref<HTMLElement | null>(null);

// Le texte du dessin et son emplacement arrivent dans n'importe quel ordre : on le pose dès que
// les deux sont là.
const svg = ref("");
watch(
  () => props.name,
  async (name) => {
    const inline = ready[`../assets/dessins/${name}.svg`];
    if (inline) {
      svg.value = inline;
      return;
    }
    const load = files[`../assets/dessins/${name}.svg`];
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
export type DrawingName =
  | "absorbed"
  | "certification"
  | "done"
  | "mailbox"
  | "maintenance"
  | "message-sent"
  | "morning-plans"
  | "stepping-up";
</script>

<template>
  <span
    ref="host"
    class="illu drawing"
    aria-hidden="true"
    :data-drawing="name"
  />
</template>
