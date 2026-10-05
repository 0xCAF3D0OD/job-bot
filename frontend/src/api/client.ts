import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

// Chemin relatif : aucune URL d'API n'est figée dans le build.
export const api = createClient<paths>({ baseUrl: globalThis.location?.origin ?? "" });

type Schemas = components["schemas"];
export type StatusResponse = Schemas["StatusResponse"];
export type JobRun = Schemas["JobRunOut"];
export type Search = Schemas["SearchOut"];
export type SearchDetail = Schemas["SearchDetail"];
export type Offer = Schemas["OfferOut"];
export type Source = Schemas["Source"];
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
