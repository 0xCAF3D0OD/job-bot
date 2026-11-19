<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

// La barre du bas du téléphone, la même partout (Kevin, 19.11.2026, d'après la barre de la planche Offre) : une
// seule ligne, 12 px 16 px plus la zone de sécurité du bas, fond de la page, trait de 1 px en haut. Une action
// principale pleine, qui prend le reste de la largeur ; au plus une secondaire à contour, à sa gauche, large comme
// son texte (placée à gauche quel que soit l'ordre du code) ; 10 px entre elles, 48 px de haut. Les enfants portent `bottom-bar-primary` et `bottom-bar-secondary` ;
// `bottom-bar-note` est une ligne au-dessus (une erreur), sur toute la largeur. Sa hauteur est donnée à la page
// (--bottom-bar-h) pour que la fin du contenu ne passe pas dessous. Rendue seulement sur téléphone par l'appelant.
const bar = ref<HTMLElement | null>(null);
let observer: ResizeObserver | undefined;
const root = document.documentElement;

onMounted(() => {
  const el = bar.value;
  if (!el || typeof ResizeObserver !== "function") return;
  observer = new ResizeObserver(() => root.style.setProperty("--bottom-bar-h", `${el.offsetHeight}px`));
  observer.observe(el);
});
onBeforeUnmount(() => {
  observer?.disconnect();
  root.style.removeProperty("--bottom-bar-h");
});
</script>

<template>
  <div
    ref="bar"
    class="bottom-bar"
    data-test="bottom-bar"
  >
    <slot />
  </div>
</template>

<style>
.bottom-bar {
  --bb-gap: 10px; --bb-h: 48px; --bb-line: 1.5px;
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 21; box-sizing: border-box;
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--bb-gap);
  padding: var(--space-3) var(--space-4) calc(var(--space-3) + env(safe-area-inset-bottom));
  background: var(--bg); border-top: 1px solid var(--line);
}
:root:has(.tab-bar) .bottom-bar { bottom: calc(var(--tabbar-h) + env(safe-area-inset-bottom)); padding-bottom: var(--space-3); }
html:root:has(.bottom-bar) main { padding-bottom: calc(var(--bottom-bar-h, var(--space-12)) + var(--space-6)); }
.bottom-bar > .bottom-bar-note { flex: 1 0 100%; margin: 0; }
.bottom-bar > :is(.bottom-bar-primary, .bottom-bar-secondary) {
  box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  min-height: var(--bb-h); margin: 0; border-radius: var(--radius-pill); font-weight: var(--weight-bold);
  line-height: var(--leading-tight); text-align: center; text-decoration: none;
}
.bottom-bar > .bottom-bar-secondary {
  flex: none; white-space: nowrap; order: -1; padding: 0 var(--space-5); border: var(--bb-line) solid var(--action);
  background: var(--surface); color: var(--primary-text); font-size: var(--font-label);
}
.bottom-bar > .bottom-bar-primary {
  flex: 1; min-width: 0; padding: 0 var(--space-4); border: 0; white-space: normal;
  background: var(--action); color: var(--on-action); font-size: var(--font-body);
}
.bottom-bar > .busy-button { display: inline-grid; justify-items: center; }
.bottom-bar > .bottom-bar-primary .icon { width: 1.125rem; height: 1.125rem; }
</style>
