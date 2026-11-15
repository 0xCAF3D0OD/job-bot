// La carte Google Emplois d'Aujourd'hui (docs/144, §22 du 15.11.2026) : le serveur décide quand la montrer
// (aucune offre, pas masquée, un métier ou une alerte) ; ici, ses textes et « Masquer ». Le lien de Candidatures
// vide appelle /api/google-jobs lui-même, pour ne pas créer un petit fichier partagé de plus.
import { api, type GoogleJobs } from "../api/client";

export const GOOGLE_JOBS_TITLE = "Des offres pour toi, en attendant";
// Le bouton, raccourci (Kevin, 15.11) ; son aria-label reste « Voir les offres sur Google Emplois (nouvel onglet) ».
export const GOOGLE_JOBS_BUTTON = "Voir sur Google Emplois";
export const GOOGLE_JOBS_HIDE_LABEL = "Masquer les offres Google Emplois";

// Le sous-titre : « Comptable · Sion », sans lieu s'il n'y en a pas. Aucune promesse de date : la
// recherche ne filtre pas par date (Kevin, 15.11).
export function googleJobsPill(search: GoogleJobs): string {
  return [search.terms, search.location].filter(Boolean).join(" · ");
}

// « Masquer » : retenu pour le compte, la carte d'Aujourd'hui ne revient plus.
export async function hideGoogleJobs(keepalive = false): Promise<boolean> {
  const { response } = await api.PUT("/api/google-jobs", { body: { hidden: true }, keepalive });
  return response.ok;
}
