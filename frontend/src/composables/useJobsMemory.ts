import { ref } from "vue";

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

  return { last, remember, sent };
}
