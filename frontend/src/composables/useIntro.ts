import { computed, onMounted, onUnmounted, ref, type ComputedRef } from "vue";

// Entrée des chiffres et des barres (docs/60 §3) : une fois par visite, à la première ouverture
// d'Aujourd'hui et du Bilan ; jamais si « réduire les animations » est demandé.
const seen = new Set<string>();

export function motionAllowed(): boolean {
  return typeof window.matchMedia === "function" && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Vrai la première fois qu'un élément s'affiche dans la visite (pour ajouter la classe `intro`).
export function firstTime(key: string): boolean {
  if (seen.has(key)) return false;
  seen.add(key);
  return motionAllowed();
}

// Le nombre qui compte jusqu'à sa valeur en 500 ms (départ rapide, fin douce) ; ensuite, il suit
// la valeur telle quelle.
export function useCountUp(key: string, target: () => number): ComputedRef<number> {
  const animated = ref<number | null>(null);
  let frame = 0;
  onMounted(() => {
    if (typeof requestAnimationFrame !== "function" || target() <= 0 || !firstTime(`count:${key}`)) return;
    const start = performance.now();
    animated.value = 0;
    const step = (now: number): void => {
      const t = Math.min(1, (now - start) / 500);
      animated.value = t < 1 ? Math.round(target() * (1 - (1 - t) ** 3)) : null;
      if (t < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
  });
  onUnmounted(() => cancelAnimationFrame(frame));
  return computed(() => animated.value ?? target());
}
