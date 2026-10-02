import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

// Chemin relatif : aucune URL d'API n'est figée dans le build.
export const api = createClient<paths>({ baseUrl: globalThis.location?.origin ?? "" });

export type StatusResponse = components["schemas"]["StatusResponse"];
export type JobRun = components["schemas"]["JobRunOut"];
