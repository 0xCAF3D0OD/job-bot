import { ref } from "vue";

// Annuler plutôt que confirmer (docs/108 §1) : l'action se voit tout de suite, le serveur ne
// la reçoit qu'au bout de 6 secondes, sauf « Annuler ». Un bandeau à la fois : le suivant
// valide le précédent ; la page qui se ferme l'envoie aussi (keepalive).
export const UNDO_MS = 6000;

export interface UndoOffer {
  message: string;
  // Envoie l'action au serveur ; `false` si elle a échoué : ce qui était caché revient.
  commit: (keepalive: boolean) => Promise<boolean | void> | boolean | void;
  // Remet ce qui avait disparu de l'écran (rien n'est parti au serveur).
  restore: () => Promise<void> | void;
}

const pending = ref<(UndoOffer & { id: number }) | null>(null);
let timer: ReturnType<typeof setTimeout> | undefined;
let seq = 0;

function schedule(): void {
  clearTimeout(timer);
  timer = setTimeout(() => void flush(), UNDO_MS);
}

async function flush(keepalive = false): Promise<void> {
  const offer = pending.value;
  if (!offer) return;
  clearTimeout(timer);
  pending.value = null;
  let ok: boolean | void = false;
  try {
    ok = await offer.commit(keepalive);
  } catch {
    ok = false;
  }
  if (ok === false) await offer.restore();
}

export function offerUndo(offer: UndoOffer): Promise<void> {
  const previous = flush();
  pending.value = { ...offer, id: ++seq };
  schedule();
  return previous;
}

async function undo(): Promise<void> {
  const offer = pending.value;
  if (!offer) return;
  clearTimeout(timer);
  pending.value = null;
  await offer.restore();
}

// Le compte s'arrête tant que la souris ou le focus est sur le bandeau.
function hold(): void {
  clearTimeout(timer);
}

function release(): void {
  if (pending.value) schedule();
}

globalThis.addEventListener?.("pagehide", () => void flush(true));

export function useUndo() {
  return { pending, undo, hold, release, flush };
}
