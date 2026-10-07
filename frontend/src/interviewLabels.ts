// Libellés du retour d'entretien (docs/23 §2).
export const KINDS: Record<string, string> = {
  rh: "Premier contact (RH)",
  manager: "Avec le manager",
  technique: "Technique",
  test: "Test ou étude de cas",
  final: "Final",
  autre: "Autre",
};
export const FORMATS: Record<string, string> = { sur_place: "Sur place", visio: "Visio", telephone: "Téléphone" };
export const DURATIONS: Record<string, string> = { moins_30: "Moins de 30 min", "30_60": "30 à 60 min", plus_60: "Plus d'une heure" };
export const INTERVIEWERS: Record<string, string> = {
  rh: "RH",
  manager: "Futur manager",
  equipe: "Équipe",
  direction: "Direction",
};
export const INTEREST: Record<string, string> = { more: "Plus qu'avant", same: "Pareil", less: "Moins" };
export const OUTLOOK: Record<string, string> = {
  positive: "Probablement positive",
  unsure: "Incertaine",
  negative: "Probablement négative",
};
export const NEXT_STEPS: Record<string, string> = {
  rien: "Rien de dit",
  entretien: "Un autre entretien",
  reponse: "Une réponse attendue",
  test: "Un test à rendre",
};
export const THANKS: Record<string, string> = { sent: "Envoyé", no: "Non", todo: "À faire" };
export const SUGGESTED_QUESTIONS = [
  "Présentez-vous",
  "Pourquoi ce poste ?",
  "Pourquoi notre entreprise ?",
  "Vos points forts ?",
  "Vos points faibles ?",
  "Vos prétentions salariales ?",
  "Une situation difficile que vous avez gérée ?",
  "Où vous voyez-vous dans 5 ans ?",
  "Questions techniques",
];
