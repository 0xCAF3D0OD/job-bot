import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

// Chemin relatif : aucune URL d'API n'est figée dans le build.
export const api = createClient<paths>({ baseUrl: globalThis.location?.origin ?? "" });

// Profil d'essai choisi (docs/17), retenu par le navigateur et envoyé à chaque requête.
export const PROFILE_KEY = "jobbot-profile";
export const PROFILE_HEADER = "X-Jobbot-Profile";

export function storedProfile(): string | null {
  try {
    return globalThis.localStorage?.getItem(PROFILE_KEY) ?? null;
  } catch {
    return null;
  }
}

// Session expirée ou fermée ailleurs : la page de connexion prend le relais (docs/18 §1).
export const UNAUTHORIZED_EVENT = "jobbot:unauthorized";
// Démo publique (docs/72) : une écriture refusée ; le message est montré tel quel.
export const DEMO_REFUSED_EVENT = "jobbot:demo-refused";
// Maintenance (docs/79) : l'API répond « en maintenance », ou ne répond plus (elle redémarre,
// l'intermédiaire renvoie 502 à 504) ; la page d'attente se pose par-dessus, le message en détail.
export const MAINTENANCE_EVENT = "jobbot:maintenance";
// Maintenance en lecture seule (docs/80) : une écriture refusée ; on consulte encore.
export const MAINTENANCE_READ_EVENT = "jobbot:maintenance-read";
// Une écriture que la page fait d'elle-même, sans clic (la visite des Actualités…) : refusée
// pendant une maintenance en lecture seule, elle est abandonnée sans message (docs/81 §2).
export const BACKGROUND_HEADER = "X-Jobbot-Background";
export const BACKGROUND = { headers: { [BACKGROUND_HEADER]: "1" } };

function maintenance(message: string | null = null): void {
  globalThis.dispatchEvent?.(new CustomEvent(MAINTENANCE_EVENT, { detail: message }));
}

api.use({
  onRequest({ request }) {
    const profile = storedProfile();
    if (profile) request.headers.set(PROFILE_HEADER, profile);
    return request;
  },
  async onResponse({ request, response }) {
    if (response.status === 401 && !new URL(request.url).pathname.startsWith("/api/auth/")) {
      globalThis.dispatchEvent?.(new Event(UNAUTHORIZED_EVENT));
    }
    if ([502, 503, 504].includes(response.status)) {
      const body = (await response.clone().json().catch(() => null)) as
        | { maintenance?: boolean; mode?: string; message?: string | null }
        | null;
      if (body?.maintenance && body.mode === "lecture") {
        if (request.headers.get(BACKGROUND_HEADER)) return response;
        globalThis.dispatchEvent?.(new CustomEvent(MAINTENANCE_READ_EVENT, { detail: body.message ?? null }));
      } else if (response.status !== 503 || !body || body.maintenance) {
        // Un 503 de l'API sans « maintenance » (IA indisponible…) reste une erreur de la page.
        maintenance(body?.message ?? null);
      }
    }
    if (response.status === 403) {
      const body = (await response.clone().json().catch(() => null)) as { demo?: boolean; detail?: string } | null;
      if (body?.demo) globalThis.dispatchEvent?.(new CustomEvent(DEMO_REFUSED_EVENT, { detail: body.detail }));
    }
    return response;
  },
  onError({ error }) {
    // Le serveur ne répond pas du tout (redémarrage) : l'erreur suit son cours, la page
    // d'attente s'affiche. Une requête annulée par la page elle-même n'en est pas une.
    if (!(error instanceof DOMException && error.name === "AbortError")) maintenance();
  },
});

type Schemas = components["schemas"];
export type StatusResponse = Schemas["StatusResponse"];
export type JobRun = Schemas["JobRunOut"];
export type Search = Schemas["SearchOut"];
export type SearchDetail = Schemas["SearchDetail"];
export type Offer = Schemas["OfferOut"];
export type ChatAction = Schemas["ChatActionOut"];
// Identifiant d'un site suivi (jobup, indeed, jobsch, linkedin, ou ajouté dans les Réglages).
export type Source = string;
export type SiteOut = Schemas["SiteOut"];
export type ParseStatus = Schemas["ParseStatus"];
export type CriteriaIn = Schemas["CriteriaIn"];
export type Keywords = Schemas["KeywordsOut"];
export type ContractType = Schemas["ContractType"];
export type Language = Schemas["Language"];
export type SettingsModel = Schemas["SettingsModel"];
export type DocumentOut = Schemas["DocumentOut"];
export type DocumentText = Schemas["DocumentText"];
export type Chunk = Schemas["ChunkOut"];
export type ChunkIn = Schemas["ChunkIn"];
export type ChunkKind = Schemas["ChunkKind"];
export type OfferFacets = Schemas["OfferFacets"];
export type ScoringStatus = Schemas["ScoringStatus"];
export type ScorePoint = Schemas["ScorePoint"];
export type ChunkProposal = Schemas["ChunkProposal"];
export type Application = Schemas["ApplicationOut"];
export type ApplicationIn = Schemas["ApplicationIn"];
export type ApplicationUpdate = Schemas["ApplicationUpdate"];
export type ApplicationPrefill = Schemas["ApplicationPrefill"];
export type ApplicationMethod = Schemas["ApplicationMethod"];
export type ApplicationStatus = Schemas["ApplicationStatus"];
export type MonthSummary = Schemas["MonthSummary"];
export type Identity = Schemas["Identity"];
export type Letter = Schemas["LetterOut"];
export type LetterParagraph = Schemas["LetterParagraph"];
export type LetterLanguage = Letter["language"];
export type Cv = Schemas["CvOut"];
export type CvBlock = Schemas["CvBlock"];
export type OrpMonth = Schemas["OrpMonthOut"];
export type OrpRow = Schemas["OrpRowOut"];
export type Today = Schemas["TodayOut"];
export type Contact = Schemas["ContactOut"];
export type ContactIn = Schemas["ContactIn"];
export type ContactsPage = Schemas["ContactsPage"];
export type FilterKey = Schemas["OfferFiltersVisible"]["visible"][number];
export type RegistryCandidate = Schemas["RegistryCandidate"];
export type Inbox = Schemas["Inbox"];
export type InboxItem = Schemas["NotificationOut"];
export type NewsItem = Schemas["NewsItemOut"];
export type NewsPage = Schemas["NewsPage"];
export type NewsSource = Schemas["NewsSourceOut"];
export type NewsPreferences = Schemas["NewsPreferences"];
export type NewsCatalog = Schemas["NewsCatalog"];
export type Training = Schemas["TrainingOut"];
export type TrainingMark = Schemas["TrainingMarkOut"];
export type Profile = Schemas["ProfileOut"];
export type ProfileList = Schemas["ProfileList"];
export type Me = Schemas["Me"];
export type PlatformOut = Schemas["PlatformOut"];
export type AccountOut = Schemas["AccountOut"];
export type AlertsPage = Schemas["AlertsPage"];
export type AlertSearch = Schemas["AlertSearchOut"];
export type Interview = Schemas["InterviewOut"];
export type InterviewIn = Schemas["InterviewIn"];
export type InterviewInsights = Schemas["InsightsOut"];
export type Practice = Schemas["PracticeOut"];
export type PracticeDefaults = Schemas["PracticeDefaults"];
