import { ref } from "vue";

// L'apparence (maquette Réglages, « Affichage › Apparence » ; ModeSombre : « Automatique par défaut, suit le
// téléphone ») : Clair, Sombre ou Auto, retenue dans ce navigateur. Clair ou Sombre posent `data-theme` sur
// <html>, que style.css suit déjà ; Auto l'enlève et la page suit le système.
export type Theme = "light" | "dark" | "auto";
const KEY = "jobA1-theme";

function read(): Theme {
  try {
    const stored = localStorage.getItem(KEY);
    return stored === "light" || stored === "dark" ? stored : "auto";
  } catch {
    return "auto";
  }
}

const theme = ref<Theme>(read());

function apply(): void {
  const root = document.documentElement;
  if (theme.value === "auto") delete root.dataset.theme;
  else root.dataset.theme = theme.value;
}

function setTheme(next: Theme): void {
  theme.value = next;
  try {
    localStorage.setItem(KEY, next);
  } catch {
    // Stockage indisponible (navigation privée) : gardée jusqu'au rechargement.
  }
  apply();
}

export function useTheme() {
  return { theme, setTheme, apply };
}
