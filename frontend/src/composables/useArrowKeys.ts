import { onBeforeUnmount, onMounted } from "vue";

// Les flèches ← et → pour décider sans souris (tri des offres du jour) : ← la première action
// (Écarter), → la seconde (Garder). Rien quand on écrit dans un champ, quand une touche de modification
// est tenue, quand une fenêtre modale est ouverte ou quand la touche est maintenue. Les boutons portent
// aria-keyshortcuts="ArrowLeft" / "ArrowRight" ; KeyHints les montre à l'écran.
export function useArrowKeys(handlers: { left?: () => void; right?: () => void }): void {
  function editable(target: EventTarget | null): boolean {
    if (!(target instanceof HTMLElement)) return false;
    return target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
  }
  function onKey(event: KeyboardEvent): void {
    if (event.defaultPrevented || event.repeat || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (editable(event.target) || document.querySelector("dialog[open]")) return;
    const run = event.key === "ArrowLeft" ? handlers.left : event.key === "ArrowRight" ? handlers.right : undefined;
    if (!run) return;
    event.preventDefault();
    run();
  }
  onMounted(() => document.addEventListener("keydown", onKey));
  onBeforeUnmount(() => document.removeEventListener("keydown", onKey));
}
