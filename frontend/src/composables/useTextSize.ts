import { ref } from "vue";

// La taille du texte (maquette ReglagesOrdinateur, panneau « Taille du texte ») : « Selon le navigateur » suit le zoom
// du navigateur (WCAG 1.4.4) ; « Grande » agrandit tout de 25 % (classe `text-large` sur <html>, style.css). Retenue
// dans ce navigateur, comme l'apparence.
export type TextSize = "browser" | "large";
const KEY = "jobA1-text-size";

function read(): TextSize {
  try {
    return localStorage.getItem(KEY) === "large" ? "large" : "browser";
  } catch {
    return "browser";
  }
}

const textSize = ref<TextSize>(read());

function apply(): void {
  document.documentElement.classList.toggle("text-large", textSize.value === "large");
}

function setTextSize(next: TextSize): void {
  textSize.value = next;
  try {
    localStorage.setItem(KEY, next);
  } catch {
    // Stockage indisponible (navigation privée) : gardée jusqu'au rechargement.
  }
  apply();
}

export function useTextSize() {
  return { textSize, setTextSize, apply };
}
