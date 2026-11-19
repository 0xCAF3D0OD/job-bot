import { computed, ref } from "vue";

// La sélection multiple des offres (§72q, Kevin le 19.11) : la liste Offres l'allume avec « Sélectionner » et
// l'éteint avec la croix, « Annuler », Échap ou « Écarter N offres ». L'état est partagé : sur téléphone, l'en-tête de
// Candidatures (JobsView) laisse la place à celui de la sélection.
const selecting = ref(false);
const checked = ref<Set<number>>(new Set());

function start(): void {
  checked.value = new Set();
  selecting.value = true;
}

function stop(): void {
  selecting.value = false;
  checked.value = new Set();
}

function toggle(id: number): void {
  const next = new Set(checked.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  checked.value = next;
}

// Coche (ou décoche) toutes les offres données d'un coup : « Toutes les expirées ».
function setMany(ids: number[], on: boolean): void {
  const next = new Set(checked.value);
  for (const id of ids) {
    if (on) next.add(id);
    else next.delete(id);
  }
  checked.value = next;
}

export function useOfferSelection() {
  return { selecting, checked, count: computed(() => checked.value.size), start, stop, toggle, setMany };
}
