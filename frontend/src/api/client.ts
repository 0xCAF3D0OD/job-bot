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

api.use({
  onRequest({ request }) {
    const profile = storedProfile();
    if (profile) request.headers.set(PROFILE_HEADER, profile);
    return request;
  },
});

type Schemas = components["schemas"];
export type StatusResponse = Schemas["StatusResponse"];
export type JobRun = Schemas["JobRunOut"];
export type Search = Schemas["SearchOut"];
export type SearchDetail = Schemas["SearchDetail"];
export type Offer = Schemas["OfferOut"];
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
