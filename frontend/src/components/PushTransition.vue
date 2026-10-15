<script setup lang="ts">
// Ouverture fluide d'une carte qui pousse la page (retour du 2026-10-15) : sa hauteur passe
// de 0 à sa taille réelle (et inversement), la page suit en douceur. Désactivée sur
// ordinateur quand `enabled` est faux, et pour qui demande moins d'animations.
const props = withDefaults(defineProps<{ enabled?: boolean }>(), { enabled: true });

const DURATION = 220;

function animate(el: Element, from: number, to: number, done: () => void): void {
  const node = el as HTMLElement;
  const reduced = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if (!props.enabled || reduced || typeof node.animate !== "function") {
    done();
    return;
  }
  node.style.overflow = "hidden";
  const animation = node.animate(
    [
      { height: `${from}px`, opacity: from ? 1 : 0 },
      { height: `${to}px`, opacity: to ? 1 : 0 },
    ],
    { duration: DURATION, easing: "ease" },
  );
  animation.onfinish = () => {
    node.style.overflow = "";
    done();
  };
  animation.oncancel = animation.onfinish;
}

function onEnter(el: Element, done: () => void): void {
  animate(el, 0, (el as HTMLElement).scrollHeight, done);
}

function onLeave(el: Element, done: () => void): void {
  animate(el, (el as HTMLElement).offsetHeight, 0, done);
}
</script>

<template>
  <Transition
    :css="false"
    @enter="onEnter"
    @leave="onLeave"
  >
    <slot />
  </Transition>
</template>
