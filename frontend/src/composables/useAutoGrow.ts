import { onMounted, onUnmounted } from "vue";

// Une zone de texte s'agrandit seule avec son contenu (planche « Champs », sans poignée). La feuille de style
// le fait avec field-sizing: content ; là où il manque (Firefox), on ajuste la hauteur à la saisie et au focus.
export function grow(area: HTMLTextAreaElement): void {
  area.style.height = "auto";
  area.style.height = `${area.scrollHeight + area.offsetHeight - area.clientHeight}px`;
}

export function useAutoGrow(): void {
  const native = typeof CSS !== "undefined" && typeof CSS.supports === "function" && CSS.supports("field-sizing", "content");
  function onEvent(event: Event): void {
    if (event.target instanceof HTMLTextAreaElement) grow(event.target);
  }
  onMounted(() => {
    if (native) return;
    document.addEventListener("input", onEvent);
    document.addEventListener("focusin", onEvent);
  });
  onUnmounted(() => {
    document.removeEventListener("input", onEvent);
    document.removeEventListener("focusin", onEvent);
  });
}
