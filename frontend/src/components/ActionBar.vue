<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

// Le panneau de commande (règles §4, planche « Tri et panneau de commande ») : sur téléphone (sous
// 600 px), on lit en haut et on agit en bas. Le panneau reste en bas, au-dessus de la barre d'onglets,
// coins du haut arrondis, zone de sécurité respectée. Il porte ce qui décide (la note et son pourquoi,
// une ligne) et les actions : principale pleine largeur, `.action-bar-row` pour deux actions de même
// largeur (Écarter/Garder), `.action-bar-note` pour une ligne grise. Sa hauteur est donnée à la page
// (--action-bar-h) pour que la fin du contenu ne passe pas dessous. Sur un écran plus large, son contenu
// reste à sa place dans la page.
const bar = ref<HTMLElement | null>(null);
let observer: ResizeObserver | undefined;
const root = document.documentElement;

onMounted(() => {
  const el = bar.value;
  if (!el || typeof ResizeObserver !== "function") return;
  observer = new ResizeObserver(() => root.style.setProperty("--action-bar-h", `${el.offsetHeight}px`));
  observer.observe(el);
});
onBeforeUnmount(() => {
  observer?.disconnect();
  root.style.removeProperty("--action-bar-h");
});
</script>

<template>
  <div
    ref="bar"
    class="action-bar"
    data-test="action-bar"
  >
    <slot />
  </div>
</template>
