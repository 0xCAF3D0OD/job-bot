import { ref } from "vue";

// Dernière page de la rubrique Candidatures (docs/19, complément) : en revenant par le menu,
// on retrouve l'onglet quitté. Gardée dans ce navigateur.
const KEY = "jobbot-candidatures";
const DEFAULT = "/candidatures/offres";
// Pages jamais retenues : Mes alertes e-mail (lot 11.4), Préparer et Relances (Kevin, 13.11.2026). Sinon, sur
// l'une d'elles, « Candidatures » dans le menu mène à la page déjà ouverte et le clic ne fait rien.
const SKIPPED = /^\/candidatures\/(?:alertes|relances|offres\/\d+\/preparer)(?:[/?#]|$)/;
// Depuis Préparer et Relances, le menu ramène toujours à la liste des offres.
const TO_OFFERS = /^\/candidatures\/(?:relances|offres\/\d+\/preparer)(?:[/?#]|$)/;

function read(): string {
  try {
    const stored = localStorage.getItem(KEY);
    return stored?.startsWith("/candidatures/") && !SKIPPED.test(stored) ? stored : DEFAULT;
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
    if (fullPath.startsWith("/candidatures/") && !SKIPPED.test(fullPath)) write(fullPath);
  }

  // Le lien « Candidatures » du menu, vu depuis la page ouverte.
  function menuLink(currentPath: string): string {
    return TO_OFFERS.test(currentPath) ? DEFAULT : last.value;
  }

  return { last, remember, menuLink };
}
