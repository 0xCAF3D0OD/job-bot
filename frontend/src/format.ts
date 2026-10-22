import type { ParseStatus } from "./api/client";

export const SITE_NAMES: Record<string, string> = {
  jobup: "jobup",
  indeed: "Indeed",
  jobroom: "Job-Room",
  jobsch: "jobs.ch",
  linkedin: "LinkedIn",
  // Le code de Gmail qui confirme un transfert vers l'adresse jobA1 (docs/116 §1).
  gmail: "Gmail",
  // Offre ajoutée par toi (docs/111) : son lien mène à l'annonce elle-même.
  manual: "l'annonce",
  unknown: "inconnu",
};

// Nom affiché d'un site ; un site ajouté dans les Réglages garde son identifiant.
export const sourceLabel: Record<string, string> = new Proxy(SITE_NAMES, {
  get: (names, slug: string) => names[slug] ?? slug,
});

export const parseStatusLabel: Record<ParseStatus, string> = {
  parsed: "analysé",
  empty: "sans offre",
  unrecognized: "non reconnu",
  failed: "erreur d'analyse",
};

const dateTime = new Intl.DateTimeFormat("fr-CH", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "Europe/Zurich",
});

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export function rateText(min: number | null, max: number | null): string {
  if (min === null || max === null) return "";
  return min === max ? `${min} %` : `${min}–${max} %`;
}

const shortDate = new Intl.DateTimeFormat("fr-CH", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "Europe/Zurich",
});

export function formatDate(iso: string): string {
  return shortDate.format(new Date(iso));
}

// Jours de la liste des offres (docs/73 §3), à l'heure suisse.
const ZURICH = "Europe/Zurich";
export function dayKey(iso: string): string {
  return new Date(iso).toLocaleDateString("sv-SE", { timeZone: ZURICH });
}
function daysBefore(iso: string, now: Date): number {
  return Math.round((Date.parse(dayKey(now.toISOString())) - Date.parse(dayKey(iso))) / 86_400_000);
}
/** Ligne d'un jour : « Aujourd'hui », « Hier », « Jeudi 15 octobre » (avec l'année si autre). */
export function dayName(iso: string, now: Date = new Date()): string {
  const before = daysBefore(iso, now);
  if (before === 0) return "Aujourd'hui";
  if (before === 1) return "Hier";
  const sameYear = dayKey(iso).slice(0, 4) === dayKey(now.toISOString()).slice(0, 4);
  const text = new Date(iso).toLocaleDateString("fr-CH", {
    weekday: "long",
    day: "numeric",
    month: "long",
    ...(sameYear ? {} : { year: "numeric" }),
    timeZone: ZURICH,
  });
  // « mercredi, 31 décembre 2025 » : sans la virgule qu'ajoute l'année.
  const clean = text.replace(/,/g, "");
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}
/** Le jour en bref, dans une offre : « aujourd'hui », « hier », « 15 oct. ». */
export function dayShort(iso: string, now: Date = new Date()): string {
  const before = daysBefore(iso, now);
  if (before === 0) return "aujourd'hui";
  if (before === 1) return "hier";
  const sameYear = dayKey(iso).slice(0, 4) === dayKey(now.toISOString()).slice(0, 4);
  return new Date(iso).toLocaleDateString("fr-CH", {
    day: "numeric",
    month: "short",
    ...(sameYear ? {} : { year: "numeric" }),
    timeZone: ZURICH,
  });
}

/** Couleur stable (0 à 3) pour la pastille d'une entreprise. */
export function colorIndex(name: string): number {
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return hash % 4;
}

/** Niveau d'une note, pour sa couleur : bonne (≥ 70), moyenne (≥ 50) ou faible. */
// La note en mots (docs/121 §C.5), sur les seuils des couleurs : 85, 70, 50.
export type ScoreTone = "very-close" | "close" | "dig" | "far";
export function scoreWord(score: number): { word: string; mood: "ravi" | "content" | "attentif" | "neutre"; tone: ScoreTone } {
  if (score >= 85) return { word: "Très proche", mood: "ravi", tone: "very-close" };
  if (score >= 70) return { word: "Proche", mood: "content", tone: "close" };
  if (score >= 50) return { word: "À creuser", mood: "attentif", tone: "dig" };
  return { word: "Loin", mood: "neutre", tone: "far" };
}

export const methodLabel: Record<"electronique" | "ecrit" | "telephone" | "personnel", string> = {
  electronique: "Électronique",
  ecrit: "Écrit (courrier)",
  telephone: "Téléphone",
  personnel: "En personne",
};

export const applicationStatusLabel: Record<
  "en_attente" | "relancee" | "entretien" | "refus" | "engagement" | "sans_reponse",
  string
> = {
  en_attente: "En attente",
  relancee: "Relancée",
  entretien: "Entretien",
  refus: "Refus",
  engagement: "Engagement",
  sans_reponse: "Sans réponse",
};

const monthFormat = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric", timeZone: "UTC" });

/** « 2026-10 » → « octobre 2026 ». */
// « 2026-10-15 » en date locale, à minuit (sans le décalage UTC de `new Date("2026-10-15")`).
export function localDate(day: string): Date {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(y ?? 2000, (m ?? 1) - 1, d ?? 1);
}

export function formatMonth(month: string): string {
  const [year, m] = month.split("-").map(Number);
  return monthFormat.format(new Date(Date.UTC(year ?? 2000, (m ?? 1) - 1, 1)));
}

// « de septembre », « d'octobre », « d'août » : le nom du mois après « de », élidé.
export function ofMonth(month: string): string {
  const name = formatMonth(month).split(" ")[0]!.toLowerCase();
  return /^[aeiouyàâéèêî]/.test(name) ? `d'${name}` : `de ${name}`;
}

export function shiftMonth(month: string, delta: number): string {
  const [year, m] = month.split("-").map(Number);
  const date = new Date(Date.UTC(year ?? 2000, (m ?? 1) - 1 + delta, 1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

// Bandeau d'une offre retirée (docs/10 §1) : certaine (page introuvable) ou probable (Indeed).
export function expiredText(offer: { expired_at?: string | null; expiry_source?: string | null }): string {
  if (!offer.expired_at) return "";
  const day = new Date(offer.expired_at).toLocaleDateString("fr-CH");
  if (offer.expiry_source === "manual") return `Signalée expirée par toi le ${day}.`;
  return offer.expiry_source === "age"
    ? `Probablement expirée : plus vue dans aucune alerte depuis 30 jours (${day}).`
    : `Offre expirée le ${day} : l'annonce n'est plus en ligne.`;
}

// « il y a 2 h » : cloche des alertes, dernier relevé des Actualités.
export function since(iso: string): string {
  const minutes = Math.max(0, Math.round((Date.now() - Date.parse(iso)) / 60_000));
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `il y a ${hours} h`;
  const days = Math.round(hours / 24);
  return days === 1 ? "hier" : `il y a ${days} jours`;
}

// Télétravail d'une offre (docs/26 §2) : « Télétravail 2 j », « 100 % télétravail · Europe ».
export function remoteText(offer: {
  remote?: string | null;
  remote_days?: number | null;
  remote_region?: string | null;
}): string | null {
  if (offer.remote === "hybrid") return offer.remote_days ? `Télétravail ${offer.remote_days} j` : "Télétravail partiel";
  if (offer.remote === "full") return offer.remote_region ? `100 % télétravail · ${offer.remote_region}` : "100 % télétravail";
  return null;
}

// « 1 offre », « 3 offres », « aucune offre » : de vrais accords plutôt que « offre(s) » (docs/43 n° 2).
export function plural(count: number, one: string, many: string, none?: string): string {
  if (count === 0 && none) return none;
  return `${count} ${count === 1 ? one : many}`;
}

// La compétence d'un manque de la note (docs/121 §C.3) : « Spark : pas d'expérience… »,
// « Pas d'Ansible », « Allemand courant demandé ». Une phrase longue (« Le poste demande plus
// de développement… ») n'est pas une compétence à ajouter : null, et pas de « Je l'ai ».
export function gapSkill(text: string): string | null {
  const skill = text
    .split(/ : | \(|[.;]/)[0]!
    .replace(/^(pas de |pas d'|pas d\u2019|aucune |aucun |il manque |manque de |manque d')/i, "")
    .replace(/ demandée?s?$/i, "")
    .trim();
  return skill && skill.split(/\s+/).length <= 4 ? skill : null;
}

// Le mois ORP en une humeur (docs/123 §2, Q) : atteint, dans les temps, ou à rattraper. Le
// rythme attendu suit les jours ouvrables (lundi à vendredi) passés avant aujourd'hui ; « On
// rattrape » seulement quand le compte est sous ce rythme. Sans objectif : rien à dire.
export type OrpPace = {
  state: "reached" | "on-track" | "behind";
  mood: "ravi" | "content" | "attentif";
  word: string;
  line: string;
};

function workdays(from: Date, to: Date): number {
  let count = 0;
  for (const day = new Date(from); day <= to; day.setDate(day.getDate() + 1)) {
    if (day.getDay() !== 0 && day.getDay() !== 6) count += 1;
  }
  return count;
}

export function orpPace(count: number, target: number | null | undefined, month: string, now = new Date()): OrpPace | null {
  if (!target) return null;
  if (count >= target) return { state: "reached", mood: "ravi", word: "Objectif atteint.", line: "Le reste du mois est à toi." };
  const [year, monthNumber] = month.split("-").map(Number);
  const first = new Date(year!, monthNumber! - 1, 1);
  const last = new Date(year!, monthNumber!, 0);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const total = workdays(first, last);
  const passed = today > last ? total : workdays(first, yesterday);
  const left = target - count;
  const daysLeft = today > last ? 0 : workdays(today < first ? first : today, last);
  if (count >= Math.floor((target * passed) / Math.max(1, total))) {
    const end = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" }).format(last);
    return { state: "on-track", mood: "content", word: "Dans les temps.", line: `Encore ${left} d'ici le ${end}.` };
  }
  const days = daysLeft === 1 ? "1 jour ouvrable" : `${daysLeft} jours ouvrables`;
  return {
    state: "behind",
    mood: "attentif",
    word: "On rattrape.",
    line: `Il reste ${left} ${left === 1 ? "candidature" : "candidatures"} en ${days}.`,
  };
}
