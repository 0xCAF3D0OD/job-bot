// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6.11.2026) : ce qui est
// calculé, sans affichage, pour être testé seul. La liste « À venir » mêle le prochain rendez-vous ORP et les
// entretiens d'embauche à venir (applications.interview_at), triés par date.
import type { Application } from "./api/client";
import type { components } from "./api/schema";
import { dateInSentence, inDays, meetingDate, timeOfDay } from "./dates";
import { plural } from "./format";

type Meeting = components["schemas"]["MeetingOut"];
type Preparation = components["schemas"]["PreparationOut"];

export type Upcoming =
  | { kind: "orp"; key: string; at: string; meeting: Meeting }
  | { kind: "entretien"; key: string; at: string; application: Application };

/** Le prochain rendez-vous ORP (s'il n'a pas commencé) et les entretiens à venir, du plus proche au plus lointain. */
export function upcomingAppointments(meeting: Meeting | null, applications: Application[], now: Date = new Date()): Upcoming[] {
  const after = (iso: string) => Date.parse(iso) > now.getTime();
  const items: Upcoming[] = [];
  if (meeting && after(meeting.starts_at)) items.push({ kind: "orp", key: `orp-${meeting.id}`, at: meeting.starts_at, meeting });
  for (const application of applications) {
    // Un refus annule l'entretien prévu.
    if (!application.interview_at || application.status === "refus" || !after(application.interview_at)) continue;
    items.push({ kind: "entretien", key: `entretien-${application.id}`, at: application.interview_at, application });
  }
  // À la même heure, l'ORP d'abord, puis l'ordre des candidatures (stable).
  return items.sort((a, b) => Date.parse(a.at) - Date.parse(b.at));
}

const ZONE = "Europe/Zurich";
const weekday = new Intl.DateTimeFormat("fr-CH", { weekday: "short", timeZone: ZONE });
const day = new Intl.DateTimeFormat("fr-CH", { day: "numeric", timeZone: ZONE });
const month = new Intl.DateTimeFormat("fr-CH", { month: "short", timeZone: ZONE });

/** Le bloc date de la maquette : « mar. », « 10 », « nov. » (décoratif ; la date est aussi écrite en texte). */
export function dateBlock(iso: string): { weekday: string; day: string; month: string } {
  const at = new Date(iso);
  return { weekday: weekday.format(at), day: day.format(at), month: month.format(at) };
}

/** La date en texte pour les lecteurs d'écran : « Mardi 10 novembre ». */
export function dateText(iso: string): string {
  const text = meetingDate(iso).replace(/ à .*$/, "");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** « Aujourd'hui », « Demain », « Dans 4 jours ». */
export function countdown(iso: string, now: Date = new Date()): string {
  const text = inDays(iso, now);
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** « 9 h 30 · ORP Renens, rue de Lausanne 35 » (sans lieu : l'heure seule). */
export function timeAndPlace(iso: string, place: string | null | undefined): string {
  return [timeOfDay(iso), place?.trim()].filter(Boolean).join(" · ");
}

/** Les trois lignes de la carte ORP, tirées de la feuille (docs/83) ; une partie vide ne s'affiche pas. */
export function sheetLines(prep: Preparation): { label: string; text: string }[] {
  const lines: { label: string; text: string }[] = [];
  const last = prep.months?.at(-1);
  if (last) {
    lines.push({
      label: "Ton mois",
      text: last.target ? `${last.count} ${last.count === 1 ? "recherche" : "recherches"} sur ${last.target}` : plural(last.count, "recherche", "recherches"),
    });
  }
  const blocker = prep.blockers[0];
  if (blocker) lines.push({ label: "Ce qui bloque", text: blocker.replace(/\.$/, "") });
  const missing = prep.missing[0];
  if (missing) {
    lines.push({ label: "Ce qui te manque", text: `${missing.skill}, demandé dans ${missing.count} ${prep.offers === 1 ? "offre" : "offres"} sur ${prep.offers}` });
  }
  return lines;
}

/** « 2 cochées », « 1 cochée », « aucune cochée ». */
export function checkedCount(count: number): string {
  return plural(count, "cochée", "cochées", "aucune cochée");
}

/** « Rendez-vous ORP du 13 octobre ». */
export function pastTitle(iso: string, now: Date = new Date()): string {
  return `Rendez-vous ORP ${dateInSentence(iso, now).replace(/^le /, "du ")}`;
}

/** Ce qui a été convenu, en trois lignes au plus : objectif, mesure(s), prochain rendez-vous. */
export function agreedLines(meeting: Meeting): { label: string; text: string }[] {
  const lines: { label: string; text: string }[] = [];
  if (meeting.agreed_target) lines.push({ label: "Objectif", text: `${meeting.agreed_target} recherches par mois` });
  if (meeting.measures.length) {
    lines.push({ label: meeting.measures.length > 1 ? "Mesures" : "Mesure", text: meeting.measures.map((m) => m.text).join(", ") });
  }
  if (meeting.next_starts_at) {
    lines.push({ label: "Prochain", text: `${dateText(meeting.next_starts_at)}, ${timeOfDay(meeting.next_starts_at)}` });
  }
  return lines;
}
