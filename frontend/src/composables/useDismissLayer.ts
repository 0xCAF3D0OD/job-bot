import { computed, onUnmounted, ref, shallowRef } from "vue";

// Un seul panneau ou menu ouvert à la fois dans toute l'application (maquette du 8 novembre, docs/143, D24).
// Ouvrir A ferme B. Une couche transparente plein écran (`DismissLayer`, z-index 35) se pose sous le panneau et
// ferme tout au clic ; l'en-tête reste au-dessus (z-index 38), donc la cloche bascule directement vers le compte.
// Échap ferme et rend le focus au déclencheur.

interface Layer {
  id: symbol;
  kind: string;
  hide: (returnFocus?: boolean) => void;
}

const current = shallowRef<Layer | null>(null);

/** Le genre du panneau ou du menu ouvert (« compte », « notifications », « filtres »…), ou null. */
export const openLayerKind = computed(() => current.value?.kind ?? null);
export const anyLayerOpen = computed(() => current.value !== null);

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape" || !current.value) return;
  event.preventDefault();
  current.value.hide(true);
}

let listening = false;
function listen(on: boolean): void {
  if (typeof document === "undefined" || on === listening) return;
  listening = on;
  if (on) document.addEventListener("keydown", onKeydown);
  else document.removeEventListener("keydown", onKeydown);
}

/** Ferme le panneau ou le menu ouvert (clic sur la couche, changement de page). */
export function closeAllLayers(returnFocus = false): void {
  current.value?.hide(returnFocus);
}

export function useDismissLayer(kind: string, onClose?: () => void) {
  const id = Symbol(kind);
  const open = ref(false);
  let trigger: HTMLElement | null = null;

  function hide(returnFocus = true): void {
    if (!open.value) return;
    open.value = false;
    if (current.value?.id === id) {
      current.value = null;
      listen(false);
    }
    onClose?.();
    if (returnFocus && trigger?.isConnected) trigger.focus();
  }

  function show(from?: HTMLElement | null): void {
    if (current.value && current.value.id !== id) current.value.hide(false);
    trigger = from ?? (typeof document !== "undefined" && document.activeElement instanceof HTMLElement ? document.activeElement : null);
    current.value = { id, kind, hide };
    open.value = true;
    listen(true);
  }

  function toggle(from?: HTMLElement | null): void {
    if (open.value) hide(true);
    else show(from);
  }

  onUnmounted(() => hide(false));

  return { open, show, hide, toggle };
}
