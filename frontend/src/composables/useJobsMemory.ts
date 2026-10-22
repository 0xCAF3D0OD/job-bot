import { ref } from "vue";

import { api } from "../api/client";

// Dernière page de la rubrique Candidatures (docs/19, complément) : en revenant par le menu,
// on retrouve la candidature commencée, ou l'onglet quitté. Gardée dans ce navigateur.
const KEY = "jobbot-candidatures";
const DEFAULT = "/candidatures/offres";
const PREPARATION = /^\/candidatures\/offres\/(\d+)\/preparer/;

function read(): string {
  try {
    const stored = localStorage.getItem(KEY);
    return stored?.startsWith("/candidatures/") ? stored : DEFAULT;
  } catch {
    return DEFAULT;
  }
}

const last = ref(read());

function write(path: string): void {
  last.value = path;
  try {
    localStorage.setItem(KEY, path);
  } catch {
    // Stockage indisponible (navigation privée) : retenu jusqu'au rechargement.
  }
}

export function useJobsMemory() {
  function remember(fullPath: string): void {
    if (fullPath.startsWith("/candidatures/")) write(fullPath);
  }

  // Candidature envoyée : plus rien à reprendre, le menu ramène au suivi.
  function sent(offerId: number): void {
    const match = PREPARATION.exec(last.value);
    if (match && Number(match[1]) === offerId) write("/candidatures/suivi");
  }

  // Une page retenue qui n'existe plus (offre supprimée, démo refaite chaque nuit) : le menu
  // ramène aux Offres plutôt qu'à « Cette offre n'existe plus » (audit du 22.10.2026).
  function forget(fullPath: string): void {
    if (last.value === fullPath || last.value.split("?")[0] === fullPath.split("?")[0]) write("/candidatures/offres");
  }

  // Au chargement : une candidature retenue dont l'offre n'existe plus est oubliée tout de suite.
  async function check(): Promise<void> {
    const match = PREPARATION.exec(last.value);
    if (!match) return;
    const { response } = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: Number(match[1]) } } });
    if (response?.status === 404) write(DEFAULT);
  }

  return { last, remember, sent, forget, check };
}
