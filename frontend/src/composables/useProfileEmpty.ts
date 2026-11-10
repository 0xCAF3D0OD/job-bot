import { ref } from "vue";

import { api } from "../api/client";

// Le profil sans bloc actif (test du 10 novembre) : les offres restent « Pas encore notées » et les lettres ne
// peuvent pas s'écrire. Partagé par la liste et la fiche : la page le relit à son ouverture, les cartes le lisent.
const empty = ref(false);

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/profile-chunks");
    empty.value = Array.isArray(data) && !data.some((chunk) => chunk.active);
  } catch {
    empty.value = false;
  }
}

export function useProfileEmpty(): { empty: typeof empty; refresh: () => Promise<void> } {
  return { empty, refresh };
}

// Le lien qui ouvre Profil › Expériences avec le formulaire d'un nouveau bloc.
export const ADD_EXPERIENCE = { path: "/profil", query: { onglet: "experiences", nouveau: "1" } };
