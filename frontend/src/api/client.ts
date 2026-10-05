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
