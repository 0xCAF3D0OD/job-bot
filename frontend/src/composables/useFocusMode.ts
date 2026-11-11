import { ref } from "vue";

// Le mode concentration (récapitulatif du 11 novembre, PR 42) : une page de travail cache l'en-tête, la barre du bas
// et l'Assistant le temps d'une tâche (une question d'entraînement), sans changer de route. La page l'allume et
// l'éteint ; App.vue et BottomNav le lisent.
const focus = ref(false);

export function useFocusMode() {
  return { focus };
}
