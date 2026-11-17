// Les sept langues de l'interface (docs/147), à part de i18n.ts : seul le sélecteur de Réglages en a besoin.
// L'ordre du sélecteur (planche ReglagesLangue, §62 du 17.11) ; chaque nom est écrit dans sa langue.
export const LANGUAGES = [
  { code: "fr", name: "Français", french: "Français" },
  { code: "de", name: "Deutsch", french: "Allemand" },
  { code: "it", name: "Italiano", french: "Italien" },
  { code: "en", name: "English", french: "Anglais" },
  { code: "pt", name: "Português", french: "Portugais" },
  { code: "es", name: "Español", french: "Espagnol" },
  { code: "sq", name: "Shqip", french: "Albanais" },
] as const;
export type Lang = (typeof LANGUAGES)[number]["code"];
