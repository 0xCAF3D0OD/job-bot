// Les 4 personnages du logo (MODIFICATIONS du 9 novembre, §15) : le point bleu, le « 1 », le sourire et le
// point orange, une scène par état de la plateforme, en clair et en sombre. Ils remplacent le personnage à
// capuche partout, sauf dans les notifications. Seulement pour un moment neutre ou positif : jamais pour un
// refus, une échéance ORP dépassée, une perte de données ou une erreur grave (icône sobre à la place).
export type Scene =
  | "groupe"
  | "hors-ligne"
  | "maintenance"
  | "mise-a-jour"
  | "introuvable"
  | "aucune-offre"
  | "envoyee"
  | "objectif"
  | "un";

// Les fichiers de public/troupe/ : `phone` et `desk` sont les largeurs des deux fichiers (2× de la largeur
// affichée dans les maquettes : 680 pour 340 px) ; `ratio`, largeur sur hauteur, pour réserver la place.
// « un » (le 1 seul) n'a qu'un fichier, affiché par sa hauteur (72, 100 ou 150 px).
export const SCENES: Record<Scene, { phone: number; desk: number; ratio: number }> = {
  groupe: { phone: 412, desk: 1200, ratio: 1200 / 687 },
  "hors-ligne": { phone: 680, desk: 1224, ratio: 1224 / 440 },
  maintenance: { phone: 680, desk: 850, ratio: 850 / 480 },
  "mise-a-jour": { phone: 680, desk: 818, ratio: 818 / 480 },
  introuvable: { phone: 680, desk: 784, ratio: 784 / 480 },
  "aucune-offre": { phone: 660, desk: 964, ratio: 964 / 480 },
  envoyee: { phone: 680, desk: 942, ratio: 942 / 480 },
  objectif: { phone: 680, desk: 946, ratio: 946 / 480 },
  un: { phone: 400, desk: 400, ratio: 323 / 660 },
};

// Servies telles quelles depuis public/troupe/ ; `TROUPE` change quand les images changent.
export const TROUPE = "20261109";
export function sceneFile(scene: Scene, width: number, dark: boolean): string {
  return `/troupe/${scene}${dark ? "-sombre" : ""}-${width}.webp?v=${TROUPE}`;
}
