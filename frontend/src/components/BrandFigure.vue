<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

// Le personnage du titre (docs/68) : une fois connecté, il remplace le « 1 » de jobA1 et change à
// chaque heure, le même pour tout le monde à la même heure. Préparés par scripts/personnages.mjs ;
// insérés dans la page pour prendre les couleurs du thème (`.drawing [fill=…]`). Immobile au repos ;
// au survol du titre, ses propres animations jouent et il grandit un peu pour qu'on les voie
// (feuille de style). Décoratif : le lien du titre s'annonce « jobA1, accueil ».
const host = ref<HTMLElement | null>(null);
const name = ref(figureAt(new Date()));
const svg = ref("");
let timer: ReturnType<typeof setTimeout> | undefined;

// À l'heure pile, le suivant.
function schedule(): void {
  const now = new Date();
  const next = new Date(now);
  next.setHours(now.getHours() + 1, 0, 0, 0);
  timer = setTimeout(() => {
    name.value = figureAt(new Date());
    schedule();
  }, next.getTime() - now.getTime());
}

watch(
  name,
  async (current) => {
    const load = files[`../assets/personnages/${current}.svg`];
    const text = load ? await load() : "";
    if (current === name.value) svg.value = text;
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

onMounted(schedule);
onBeforeUnmount(() => clearTimeout(timer));
</script>

<script lang="ts">
const files = import.meta.glob<string>("../assets/personnages/*.svg", { query: "?raw", import: "default" });
// Les personnages, dans l'ordre alphabétique ; l'heure (0 à 23) choisit le sien.
export const FIGURES = Object.keys(files)
  .map((path) => path.replace(/^.*\/(.+)\.svg$/, "$1"))
  .sort();

export function figureAt(date: Date): string {
  return FIGURES[date.getHours() % FIGURES.length] ?? "";
}
</script>

<template>
  <span
    ref="host"
    class="drawing brand-figure"
    aria-hidden="true"
    :data-figure="name"
  />
</template>
