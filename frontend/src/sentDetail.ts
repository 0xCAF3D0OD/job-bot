import type { Application, OrpRow } from "./api/client";
import { followUpDue, noAnswerDue } from "./applicationState";
import { CHANNELS, ROLES } from "./contactLabels";
import { dateInList, daysSince } from "./dates";

// Le détail d'une candidature envoyée (MODIFICATIONS du 9 novembre, §8 ; maquettes CandidaturesOrdinateurB onglet
// Envoyées, EnvoyeeDetail) : les mots de statut, le Suivi en 5 étapes (ordinateur) et l'Historique.

const REMIND_AFTER_DAYS = 10;

function noon(day: string): string {
  return day.length === 10 ? `${day}T12:00:00` : day;
}
function short(day: string, now: Date): string {
  return dateInList(noon(day), now);
}
function days(n: number): string {
  return n <= 1 ? `${n} jour` : `${n} jours`;
}
function addDays(day: string, n: number): string {
  const d = new Date(`${day}T12:00:00`);
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export type SentWord = { text: string; tone: "peach" | "green" | "grey" | "muted"; check?: boolean; test: string };

// « Sans réponse · 57 jours » (#8A4A16), « ✓ Déclarée à l’ORP » (#17734A) : des mots colorés, pas de pastille.
export function sentWords(a: Application, row: OrpRow | null | undefined, now: Date = new Date()): SentWord[] {
  const words: SentWord[] = [];
  const since = (day: string) => days(daysSince(noon(day), now));
  if (followUpDue(a) || noAnswerDue(a) || a.status === "sans_reponse") {
    words.push({ text: `Sans réponse · ${since(a.followed_up_at ?? a.sent_at)}`, tone: "peach", test: "word-no-answer" });
  } else if (a.status === "relancee") {
    words.push({ text: `Relancée · il y a ${since(a.followed_up_at ?? a.sent_at)}`, tone: "grey", test: "word-status" });
  } else if (a.status === "entretien") {
    words.push({ text: "Entretien", tone: "green", test: "word-status" });
  } else if (a.status === "engagement") {
    words.push({ text: "Poste obtenu", tone: "green", test: "word-status" });
  } else if (a.status === "refus") {
    words.push({ text: "Refus", tone: "muted", test: "word-status" });
  } else {
    words.push({ text: `Envoyée · il y a ${since(a.sent_at)}`, tone: "grey", test: "word-status" });
  }
  if (row?.declared_at) words.push({ text: "Déclarée à l’ORP", tone: "green", check: true, test: "word-declared" });
  return words;
}

export type SentStep = { label: string; sub: string; state: "done" | "current" | "todo" };

const ANSWERS: Partial<Record<Application["status"], string>> = {
  entretien: "Entretien",
  refus: "Refus",
  engagement: "Poste obtenu",
};

// Préparée, Envoyée, Déclarée ORP, Relance, Réponse. L'étape en cours est la première qui n'est pas faite ; les
// suivantes sont grises.
export function sentSteps(a: Application, row: OrpRow | null | undefined, now: Date = new Date()): SentStep[] {
  const answered = a.status in ANSWERS;
  const prepared = [a.letter_draft_id && "Lettre", a.cv_draft_id && "CV"].filter(Boolean).join(" et ");
  const remindOn = a.follow_up_on ?? addDays(a.sent_at, REMIND_AFTER_DAYS);
  const raw: { label: string; sub: string; done: boolean; current?: string }[] = [
    { label: "Préparée", sub: prepared || "faite", done: true },
    { label: "Envoyée", sub: short(a.sent_at, now), done: true },
    {
      label: "Déclarée ORP",
      sub: row?.declared_at ? short(row.declared_at, now) : "à faire",
      done: !!row?.declared_at || !row,
    },
    {
      label: "Relance",
      sub: a.followed_up_at ? short(a.followed_up_at, now) : answered ? "pas besoin" : followUpDue(a) ? "conseillée" : short(remindOn, now),
      done: !!a.followed_up_at || answered,
    },
    {
      label: "Réponse",
      sub: answered ? (ANSWERS[a.status] ?? "") : a.status === "sans_reponse" ? "aucune" : "en attente",
      done: answered,
    },
  ];
  // Sans ligne ORP (candidature hors du mois suivi), l'étape ORP n'a rien à dire : faite, sans date.
  if (!row) raw[2]!.sub = "—";
  const current = raw.findIndex((s) => !s.done);
  return raw.map((s, i) => ({ label: s.label, sub: s.sub, state: s.done ? "done" : i === current ? "current" : "todo" }));
}

export type SentEvent = { day: string; date: string; title: string; detail: string };

function sentChannel(a: Application): string {
  if (a.method === "ecrit") return "Candidature envoyée par courrier";
  if (a.method === "telephone") return "Candidature faite par téléphone";
  if (a.method === "personnel") return "Candidature remise en personne";
  if (a.application_url?.startsWith("http")) {
    try {
      return `Candidature envoyée sur ${new URL(a.application_url).hostname.replace(/^www\./, "")}`;
    } catch {
      return "Candidature envoyée en ligne";
    }
  }
  return "Candidature envoyée par e-mail";
}

function monthName(day: string): string {
  return new Intl.DateTimeFormat("fr-CH", { month: "long" }).format(new Date(noon(day)));
}

// L'Historique, du plus récent au plus ancien : réponse, entretiens, prises de contact, relance, déclaration, envoi.
export function sentHistory(a: Application, row: OrpRow | null | undefined, now: Date = new Date()): SentEvent[] {
  const events: SentEvent[] = [];
  const add = (day: string | null | undefined, title: string, detail = "") => {
    if (day) events.push({ day: day.slice(0, 10), date: short(day, now), title, detail });
  };
  if (a.status in ANSWERS && a.status !== "entretien") add(a.status_at, `Réponse : ${(ANSWERS[a.status] ?? "").toLowerCase()}`, a.status_reason ?? "");
  for (const i of a.interviews ?? []) add(i.held_at, "Entretien", `Ressenti ${i.rating}/5`);
  for (const c of a.contacts ?? []) {
    add(c.contacted_on, `Contact : ${c.name || ROLES[c.role]}`, CHANNELS[c.channel]);
    add(c.answered_on, `Réponse de ${c.name || ROLES[c.role].toLowerCase()}`, c.note ?? "");
  }
  add(a.followed_up_at, "Relance envoyée");
  if (row?.declared_at) {
    const month = monthName(a.orp_month ? `${a.orp_month.slice(0, 7)}-01` : a.sent_at);
    add(row.declared_at, "Déclarée à l’ORP", `Formulaire ${/^[aeiou]/.test(month) ? "d’" : "de "}${month}`);
  }
  const sentWith = [a.letter_draft_id && "Lettre", a.cv_draft_id && "CV adapté"].filter(Boolean).join(" et ");
  add(a.sent_at, sentChannel(a), sentWith);
  // Le même jour, l'ordre d'arrivée ci-dessus (le plus récent d'abord) est gardé.
  return events.map((e, i) => ({ e, i })).sort((x, y) => y.e.day.localeCompare(x.e.day) || x.i - y.i).map(({ e }) => e);
}
