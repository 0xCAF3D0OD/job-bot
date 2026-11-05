import { ref, watch } from "vue";

// Le modèle de la lettre et du CV (maquette Preparer, Kevin 2026-11-05) : le même pour les deux, choisi sur
// cet appareil. Il habille l'aperçu et les PDF (`?modele=`) ; rien n'est gardé sur le serveur.
export type DocTemplate = "sobre" | "moderne" | "bandeau" | "classique";
export const DOC_TEMPLATES: { value: DocTemplate; label: string }[] = [
  { value: "sobre", label: "Sobre" },
  { value: "moderne", label: "Moderne" },
  { value: "bandeau", label: "Bandeau" },
  { value: "classique", label: "Classique" },
];
const KEY = "jobA1.modele";
// La maquette ouvre sur « Moderne ».
const DEFAULT: DocTemplate = "moderne";

function stored(): DocTemplate {
  try {
    const value = localStorage.getItem(KEY);
    return DOC_TEMPLATES.some((t) => t.value === value) ? (value as DocTemplate) : DEFAULT;
  } catch {
    return DEFAULT;
  }
}

const template = ref<DocTemplate>(stored());
watch(template, (value) => {
  try {
    localStorage.setItem(KEY, value);
  } catch {
    // Stockage refusé : le choix vaut pour la visite.
  }
});

export function useDocTemplate() {
  return { template };
}

// Le lien du PDF dans le modèle choisi.
export function pdfHref(base: string, value: DocTemplate): string {
  return `${base}?modele=${value}`;
}
