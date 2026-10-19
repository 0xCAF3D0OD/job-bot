import { ref } from "vue";

// Dernier onglet de Progresser (docs/90) : en revenant par le menu, on retrouve Actualités ou
// Formations, avec sa rubrique. Gardé dans ce navigateur, comme pour Candidatures.
const KEY = "jobbot-progresser";
const DEFAULT = "/progresser/actualites";

function read(): string {
  try {
    const stored = localStorage.getItem(KEY);
    return stored?.startsWith("/progresser/") ? stored : DEFAULT;
  } catch {
    return DEFAULT;
  }
}

const last = ref(read());

export function useProgressMemory() {
  function remember(fullPath: string): void {
    if (!fullPath.startsWith("/progresser/")) return;
    last.value = fullPath;
    try {
      localStorage.setItem(KEY, fullPath);
    } catch {
      // Stockage indisponible (navigation privée) : retenu jusqu'au rechargement.
    }
  }

  return { last, remember };
}
