// Google Emplois tant qu'aucune offre n'est arrivée (docs/144, accord de Kevin du 15.11.2026) : la carte
// « Des offres pour toi, en attendant » sur Aujourd'hui et le lien sous les boutons de Candidatures vide.
// Le serveur décide quand la montrer (aucune offre, pas masquée, un métier ou une alerte) ; ici, les textes
// et les deux appels. La mise en page attend les planches.
import { api, type GoogleJobs } from "../api/client";

export const GOOGLE_JOBS_TITLE = "Des offres pour toi, en attendant";
export const GOOGLE_JOBS_ACTION = "Voir les offres sur Google Emplois";
// Le bouton de la carte d'Aujourd'hui, raccourci (Kevin, 15.11) ; son aria-label reste le libellé long.
export const GOOGLE_JOBS_BUTTON = "Voir sur Google Emplois";
export const GOOGLE_JOBS_HIDE_LABEL = "Masquer les offres Google Emplois";

// La pastille : « Comptable · Sion », sans lieu s'il n'y en a pas. Aucune promesse de date : la
// recherche ne filtre pas par date (Kevin, 15.11).
export function googleJobsPill(search: GoogleJobs): string {
  return [search.terms, search.location].filter(Boolean).join(" · ");
}

// Candidatures vide : le lien, sans offre et avec un métier ; « Masquer » ne le cache pas. null sinon ou hors ligne.
export async function loadGoogleJobs(): Promise<GoogleJobs | null> {
  try {
    const { data } = await api.GET("/api/google-jobs");
    return data ?? null;
  } catch {
    return null;
  }
}

// « Masquer » : retenu pour le compte, la carte d'Aujourd'hui ne revient plus.
export async function hideGoogleJobs(keepalive = false): Promise<boolean> {
  const { response } = await api.PUT("/api/google-jobs", { body: { hidden: true }, keepalive });
  return response.ok;
}
