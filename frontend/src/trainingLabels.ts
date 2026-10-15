// Libellés de la page Formations (docs/16 §5).
export const KINDS: Record<string, string> = {
  certification: "Certification",
  cours: "Cours",
  parcours: "Parcours",
  atelier: "Atelier",
};

export const FORMATS: Record<string, string> = {
  self_paced: "en ligne, à ton rythme",
  live: "en ligne, en direct",
  in_person: "en présentiel",
  exam: "examen en centre ou en ligne",
  exam_online: "examen en ligne surveillé",
};

// Sur la carte, sur une ligne (docs/43 n° 22) ; le format complet reste dans l'infobulle.
export const SHORT_FORMATS: Record<string, string> = {
  self_paced: "à ton rythme",
  live: "en direct",
  in_person: "en présentiel",
  exam: "examen",
  exam_online: "examen en ligne",
};

export const LEVELS: Record<string, string> = {
  beginner: "débutant",
  intermediate: "intermédiaire",
  advanced: "avancé",
};

export const PRICES: Record<string, string> = { free: "gratuit", paid: "payant" };

export const STATUSES: Record<string, string> = {
  interested: "Intéressé",
  in_progress: "En cours",
  done: "Terminée",
};

// Pages officielles sur les formations financées par l'assurance chômage (vérifiées le 2026-10-06).
export const ORP_LINKS = [
  {
    label: "Mesures relatives au marché du travail (arbeit.swiss)",
    url: "https://www.arbeit.swiss/fr/demandeurs-demploi/mesures-relatives-au-marche-du-travail",
  },
  {
    label: "Adresses des offices cantonaux et des ORP",
    url: "https://www.arbeit.swiss/fr/centre-dinformation/adresses-et-liens",
  },
];
