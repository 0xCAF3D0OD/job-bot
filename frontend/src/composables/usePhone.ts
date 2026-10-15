import { onMounted, onUnmounted, ref } from "vue";

// Téléphone (docs/33) : la même limite que les styles, 820 px de large.
export const PHONE_QUERY = "(max-width: 820px)";

export function usePhone() {
  // Lu tout de suite, avant le premier rendu : sinon les éléments repliés sur téléphone
  // (carte « Filtrer ») s'ouvrent puis se referment à chaque arrivée sur la page.
  const phone = ref(globalThis.matchMedia?.(PHONE_QUERY).matches ?? false);
  let query: MediaQueryList | undefined;
  const update = (): void => {
    phone.value = query?.matches ?? false;
  };
  onMounted(() => {
    query = globalThis.matchMedia?.(PHONE_QUERY);
    update();
    query?.addEventListener("change", update);
  });
  onUnmounted(() => query?.removeEventListener("change", update));
  return { phone };
}
