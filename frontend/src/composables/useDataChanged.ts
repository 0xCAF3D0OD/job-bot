import { onMounted, onUnmounted } from "vue";

// Une action confirmée ailleurs (l'assistant, docs/52) a changé des offres ou des candidatures.
export const DATA_CHANGED_EVENT = "jobbot:data-changed";

// Recharger une page quand une action confirmée dans l'assistant a changé ses données (docs/52).
export function useDataChanged(reload: () => unknown): void {
  const listener = (): void => void reload();
  onMounted(() => globalThis.addEventListener(DATA_CHANGED_EVENT, listener));
  onUnmounted(() => globalThis.removeEventListener(DATA_CHANGED_EVENT, listener));
}

export function announceDataChanged(): void {
  globalThis.dispatchEvent(new Event(DATA_CHANGED_EVENT));
}
