// Les drapeaux de fonctionnalité, lus à la construction (variables VITE_*). Éteints par défaut.
export const FLAGS = {
  // Le lien vers Get'emAll à la fin d'un entraînement (récapitulatif du 11 novembre, PR 42).
  getemallLink: import.meta.env.VITE_GETEMALL_LINK === "1",
};
