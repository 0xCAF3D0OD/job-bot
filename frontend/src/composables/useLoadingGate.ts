import { onUnmounted, ref, watch, type Ref } from "vue";

// Chargement d'une page (docs/58 §3.2) : rien ne change sous 0,4 s (les blocs gris) ; au-delà,
// l'illustration animée prend leur place et reste au moins 0,6 s, pour ne pas clignoter.
// Aucune attente imposée : une page prête en 0,2 s s'affiche en 0,2 s.
export const ILLUSTRATE_AFTER_MS = 400;
export const ILLUSTRATION_MIN_MS = 600;

export function useLoadingGate(isReady: () => boolean): { ready: Ref<boolean>; illustrated: Ref<boolean> } {
  const ready = ref(isReady());
  const illustrated = ref(false);
  let shownAt = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;

  function clear(): void {
    if (timer !== undefined) clearTimeout(timer);
    timer = undefined;
  }
  function wait(): void {
    clear();
    timer = setTimeout(() => {
      illustrated.value = true;
      shownAt = Date.now();
    }, ILLUSTRATE_AFTER_MS);
  }
  function settle(): void {
    clear();
    const left = illustrated.value ? ILLUSTRATION_MIN_MS - (Date.now() - shownAt) : 0;
    if (left <= 0) {
      ready.value = true;
      illustrated.value = false;
      return;
    }
    timer = setTimeout(() => {
      ready.value = true;
      illustrated.value = false;
    }, left);
  }

  if (!ready.value) wait();
  watch(
    isReady,
    (now) => {
      if (now) settle();
      else {
        ready.value = false;
        illustrated.value = false;
        wait();
      }
    },
    { flush: "sync" },
  );
  onUnmounted(clear);
  return { ready, illustrated };
}
