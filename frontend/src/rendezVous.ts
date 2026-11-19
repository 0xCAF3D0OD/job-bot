// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6.11.2026) : ce qui est
// calculé, sans affichage, pour être testé seul. La liste « À venir » mêle le prochain rendez-vous ORP et les
// entretiens d'embauche à venir (applications.interview_at), triés par date.
import type { Application, Interview } from "./api/client";
import type { components } from "./api/schema";
import { dateInSentence, addDays, inDays, meetingDate, timeOfDay, todayDay } from "./dates";
import { FEELINGS } from "./interviewLabels";
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

/** La 2e ligne d'une carte « À venir » (§39 du 16.11), en deux parties : ce qui n'est jamais coupé, l'heure et le délai
 *  (« 9 h · dans 3 jours »), puis le reste, coupé par « … » s'il le faut (le lieu ; pour un entretien, l'entreprise,
 *  le format et le lieu). */
export function upcomingWhen(item: Upcoming, now: Date = new Date()): string {
  return `${timeOfDay(item.at)} · ${inDays(item.at, now)}`;
}

export function upcomingWhere(item: Upcoming): string {
  if (item.kind === "orp") return item.meeting.place?.trim() ?? "";
  const a = item.application;
  return [a.company, interviewFormat(a), interviewPlace(a)].filter(Boolean).join(" · ");
}

/** La 2e ligne entière : « 9 h · dans 3 jours · ORP Renens ». */
export function upcomingLine(item: Upcoming, now: Date = new Date()): string {
  return [upcomingWhen(item, now), upcomingWhere(item)].filter(Boolean).join(" · ");
}

/** Le nom de la carte « À venir » pour les lecteurs d'écran (§39 du 16.11) : titre, état de la pastille, date et heure,
 *  délai, lieu. « Rendez-vous ORP, feuille prête, mardi 19 novembre à 9 h, dans 3 jours, ORP Renens ». */
export function upcomingLabel(item: Upcoming, chip: string, now: Date = new Date()): string {
  const title = item.kind === "orp" ? "Rendez-vous ORP" : item.application.job_title || "Poste non indiqué";
  const company = item.kind === "orp" ? null : item.application.company;
  const place = item.kind === "orp" ? item.meeting.place?.trim() : [interviewFormat(item.application), interviewPlace(item.application)].filter(Boolean).join(", ");
  const day = dateText(item.at);
  return [title, company, chip.toLowerCase(), `${day.charAt(0).toLowerCase()}${day.slice(1)} à ${timeOfDay(item.at)}`, inDays(item.at, now), place]
    .filter(Boolean)
    .join(", ");
}

/** Où a lieu l'entretien : le lieu ou le lien saisi sur la candidature, sinon l'adresse de l'entreprise. */
export function interviewPlace(application: Pick<Application, "interview_place" | "company_address" | "interview_format">): string | null {
  // Au téléphone ou en visio (PR 41), l'adresse de l'entreprise n'est pas le lieu de l'entretien.
  const remote = application.interview_format === "telephone" || application.interview_format === "visio";
  return application.interview_place?.trim() || (remote ? null : application.company_address?.trim()) || null;
}

/** Le format de l'entretien en mots (PR 41) ; vide s'il n'a pas été indiqué. */
export function interviewFormat(application: Pick<Application, "interview_format">): string | null {
  const names = { telephone: "Téléphone", visio: "Visio", sur_place: "Sur place" } as const;
  return application.interview_format ? names[application.interview_format] : null;
}

/** Les trois lignes de la carte ORP, tirées de la feuille (docs/83) ; une partie vide ne s'affiche pas. */
export function sheetLines(prep: Preparation): { label: string; text: string }[] {
  const lines: { label: string; text: string }[] = [];
  const last = prep.months?.at(-1);
  if (last) {
    lines.push({
      label: "Ton mois",
      text: last.target ? `${last.count} ${last.count <= 1 ? "recherche" : "recherches"} sur ${last.target}` : plural(last.count, "recherche", "recherches"),
    });
  }
  const blocker = prep.blockers[0];
  if (blocker) lines.push({ label: "Ce qui bloque", text: blocker.replace(/\.$/, "") });
  const missing = prep.missing[0];
  if (missing) {
    lines.push({ label: "Ce qui te manque", text: `${missing.skill}, demandé dans ${missing.count} ${prep.offers <= 1 ? "offre" : "offres"} sur ${prep.offers}` });
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

type Page = components["schemas"]["MeetingPage"];

// Maquettes RendezVous et RendezVousOrdinateur du 7.11.2026 : « À noter » (un rendez-vous ORP passé dont rien
// n'est noté) et « Derniers rendez-vous ORP » (ceux qui sont notés).
function pastMeetings(page: Page, now: Date): Meeting[] {
  const meeting = page.meeting;
  const started = meeting && Date.parse(meeting.starts_at) <= now.getTime() ? [meeting] : [];
  return [...started, ...page.past.filter((m) => m.id !== meeting?.id)];
}

/** Les rendez-vous ORP passés sans rien de noté, du plus récent au plus ancien. */
export function meetingsToNote(page: Page, now: Date = new Date()): Meeting[] {
  return pastMeetings(page, now).filter((m) => !m.outcome_at);
}

/** Les rendez-vous ORP passés où ce qui a été convenu est noté, du plus récent au plus ancien. */
export function notedMeetings(page: Page, now: Date = new Date()): Meeting[] {
  return pastMeetings(page, now).filter((m) => !!m.outcome_at);
}

/** Une ligne sous le titre d'un rendez-vous noté : « Objectif 8 par mois · financement Terraform ». */
export function notedSummary(meeting: Meeting): string {
  const parts = [meeting.agreed_target ? `Objectif ${meeting.agreed_target} par mois` : ""];
  for (const m of meeting.measures) parts.push(m.text.charAt(0).toLowerCase() + m.text.slice(1));
  return parts.filter(Boolean).join(" · ") || "Rien de particulier";
}

/** « 15 septembre : 8 recherches par mois, demander le financement Terraform. » */
export function lastAgreed(meeting: Meeting, now: Date = new Date()): string {
  const parts = [meeting.agreed_target ? `${meeting.agreed_target} recherches par mois` : ""];
  for (const m of meeting.measures) parts.push(m.text.charAt(0).toLowerCase() + m.text.slice(1));
  if (meeting.note) parts.push(meeting.note.charAt(0).toLowerCase() + meeting.note.slice(1).replace(/\.$/, ""));
  const said = parts.filter(Boolean).join(", ");
  return `${dateInSentence(meeting.starts_at, now).replace(/^le /, "")} : ${said || "rien de particulier"}.`;
}

/** Une ligne de la feuille en titre et précision (« Formulaires en ligne » / « 0 réponse sur 9 »). */
export function splitLine(text: string): { main: string; sub: string } {
  const at = text.search(/ : |, /);
  if (at < 0) return { main: text, sub: "" };
  const sub = text.slice(at + 2).trim();
  return { main: text.slice(0, at), sub: sub.charAt(0).toUpperCase() + sub.slice(1) };
}

// La recherche de l'onglet Rendez-vous sur téléphone (maquette du 14 novembre, RendezVous, §6 ; décision de Kevin du
// 14.11) : « Poste, entreprise, lieu », sans accents ni casse, tous les mots doivent se trouver. Un rendez-vous ORP se
// trouve par « Rendez-vous ORP », « ORP » ou son lieu ; un entretien par le poste, l'entreprise, le lieu de l'offre ou
// celui de l'entretien.
function plainText(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
export function searchWords(query: string): string[] {
  return plainText(query).split(/\s+/).filter(Boolean);
}
function hasAll(text: string, words: string[]): boolean {
  const plain = plainText(text);
  return words.every((word) => plain.includes(word));
}
export function meetingMatches(meeting: Pick<Meeting, "place">, words: string[]): boolean {
  return !words.length || hasAll(`Rendez-vous ORP ${meeting.place ?? ""}`, words);
}
export function appointmentMatches(item: Upcoming, words: string[]): boolean {
  if (!words.length) return true;
  if (item.kind === "orp") return meetingMatches(item.meeting, words);
  const a = item.application;
  return hasAll(`${a.job_title} ${a.company} ${a.location ?? ""} ${interviewPlace(a) ?? ""}`, words);
}

// « Faire le point » sur ordinateur (planche FairePointOrdinateur, §72m ; accord de Kevin du 19.11.2026) : les entretiens
// passés vont dans Rendez-vous. « À noter » tant que le point n'est pas fait, puis « Passés », pour garder tout
// l'historique au même endroit.
export type InterviewToNote = { key: string; at: string; application: Application };
export type NotedInterview = { key: string; at: string; application: Application; interview: Interview };

/** Les entretiens passés dont le point n'est pas fait (aucun retour ce jour-là), du plus récent au plus ancien. */
export function interviewsToNote(applications: Application[], now: Date = new Date()): InterviewToNote[] {
  const items: InterviewToNote[] = [];
  for (const application of applications) {
    const at = application.interview_at;
    if (!at || application.status !== "entretien") continue;
    // Même règle que le badge de l'onglet (serveur, notify/interviews.py pending) : un jour passé, 14 jours au plus.
    const day = todayDay(new Date(at));
    const today = todayDay(now);
    if (day >= today || day < addDays(today, -14)) continue;
    if (application.interviews?.some((i) => i.held_at === day)) continue;
    items.push({ key: `point-${application.id}`, at, application });
  }
  return items.sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
}

/** Les retours d'entretien faits, du plus récent au plus ancien. L'heure n'est connue que pour l'entretien prévu. */
export function notedInterviews(applications: Application[], now: Date = new Date()): NotedInterview[] {
  const items: NotedInterview[] = [];
  for (const application of applications) {
    for (const interview of application.interviews ?? []) {
      if (!interview.held_at || interview.held_at > todayDay(now)) continue;
      const planned = application.interview_at;
      const at = planned && todayDay(new Date(planned)) === interview.held_at ? planned : `${interview.held_at}T00:00:00`;
      items.push({ key: `retour-${interview.id}`, at, application, interview });
    }
  }
  return items.sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
}

/** « Entretien · DevOps Engineer ». */
export function interviewTitle(application: Application): string {
  return `Entretien · ${application.job_title || "Poste non indiqué"}`;
}

/** Sous un retour fait : « Point fait · Moyen » (le ressenti en mots, s'il a été donné). */
export function pointDone(interview: Interview): string {
  return interview.feeling ? `Point fait · ${FEELINGS[interview.feeling]}` : "Point fait";
}
