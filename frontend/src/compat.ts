// La compatibilité d'une offre, partagée par la fiche (OfferDetail) et Préparer (MODIFICATIONS du 9 novembre, §2.2) :
// le titre du verdict et le découpage d'un point « Critère : valeur ».
export const MATCH_TITLE: Record<string, string> = {
  "very-close": "Très proche de ton profil",
  close: "Proche de ton profil",
  dig: "À creuser",
  far: "Loin de ton profil",
};

/** « Kubernetes : plateforme de 40 services » donne le critère et sa valeur ; sans deux-points, tout est la valeur. */
export function pointParts(text: string): { key: string; rest: string } {
  const match = /^([^:]{1,40}?)\s?:\s+(.+)$/.exec(text.trim());
  return match ? { key: match[1]!, rest: match[2]! } : { key: "", rest: text };
}
