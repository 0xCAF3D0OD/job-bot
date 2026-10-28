// Les textes de la recherche globale (série du 27.10, point 2) : la phrase de chaque résultat et
// la confirmation de « Suivre cette recherche ». Fonctions pures, testées à part.
import type { components } from "./api/schema";
import { onDay, plural } from "./format";

type ApplicationHit = components["schemas"]["ApplicationHit"];
type CompanyHit = components["schemas"]["CompanyHit"];
type FollowOut = components["schemas"]["FollowOut"];

/** « jobup, jobs.ch, LinkedIn et Indeed ». */
export function andList(items: string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} et ${items.at(-1)}`;
}

/** « Démo Data SA · envoyée le 12 oct. », ou l'entretien à venir. */
export function applicationLine(hit: ApplicationHit, now: Date): string {
  if (hit.interview_at && Date.parse(hit.interview_at) > now.getTime()) {
    return `${hit.company} · entretien ${onDay(hit.interview_at, now)}`;
  }
  return `${hit.company} · envoyée ${onDay(`${hit.sent_at}T12:00:00`, now)}`;
}

/** « 2 offres, 1 candidature ». */
export function companyLine(hit: CompanyHit): string {
  return [
    hit.offers ? plural(hit.offers, "offre", "offres") : "",
    hit.applications ? plural(hit.applications, "candidature", "candidatures") : "",
  ]
    .filter(Boolean)
    .join(", ");
}

/** La confirmation de « Suivre cette recherche ». Jamais « suivie » tant qu'un site reste à créer
 *  (les cellules « todo » rendues par le serveur) : créer la recherche ne crée l'alerte nulle part. */
export function followMessage(found: FollowOut): { title: string; todo: string | null } {
  const summary = [found.terms, found.locations.join(", "), found.sites.join(", ")].filter(Boolean).join(" · ");
  if (!found.todo.length) return { title: `Recherche suivie : ${summary}`, todo: null };
  const where = found.todo.length === found.sites.length && found.sites.length > 1 ? `sur chaque site : ${andList(found.todo)}` : `sur ${andList(found.todo)}`;
  return {
    title: `Recherche ajoutée : ${summary}`,
    todo: `Il te reste à créer l'alerte ${where}. Tant qu'elle n'est pas créée, rien n'arrive.`,
  };
}
