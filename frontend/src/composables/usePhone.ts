import { onMounted, onUnmounted, ref } from "vue";

// Téléphone (docs/33) : la même limite que les styles, 820 px de large.
export const PHONE_QUERY = "(max-width: 820px)";
// La structure téléphone (planche « Structure téléphone ») : listes groupées et contrôle segmenté,
// sous 600 px seulement.
export const NARROW_QUERY = "(max-width: 599px)";

export function useNarrow() {
  return usePhone(NARROW_QUERY);
}

export function usePhone(media: string = PHONE_QUERY) {
  // Lu tout de suite, avant le premier rendu : sinon les éléments repliés sur téléphone
  // (carte « Filtrer ») s'ouvrent puis se referment à chaque arrivée sur la page.
  const phone = ref(globalThis.matchMedia?.(media).matches ?? false);
  let query: MediaQueryList | undefined;
  const update = (): void => {
    phone.value = query?.matches ?? false;
  };
  onMounted(() => {
    query = globalThis.matchMedia?.(media);
    update();
    query?.addEventListener("change", update);
  });
  onUnmounted(() => query?.removeEventListener("change", update));
  return { phone };
}
