// Les dates de jobA1 (1.6.74, planche « Pastille d'état et dates », règle §5) : une seule façon de
// les écrire, en français de Suisse, à l'heure de Zurich. Jamais « il y a 3 h » : aujourd'hui ou
// hier, sinon la date ; l'heure seulement quand elle compte (« aujourd'hui à 14 h »).
// Seule exception : la feuille ORP imprimée, qui reprend le format du formulaire officiel.

const ZONE = "Europe/Zurich";
const dayMonth = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short", timeZone: ZONE });
const dayMonthYear = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short", year: "numeric", timeZone: ZONE });
const longDayMonth = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", timeZone: ZONE });
const longDayMonthYear = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric", timeZone: ZONE });
const weekdayLong = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long", timeZone: ZONE });
const parts = new Intl.DateTimeFormat("fr-CH", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: ZONE,
});

function zoned(date: Date): { day: string; year: number; hour: number; minute: number } {
  const get = (type: string) => parts.formatToParts(date).find((p) => p.type === type)?.value ?? "0";
  return {
    day: `${get("year")}-${get("month")}-${get("day")}`,
    year: Number(get("year")),
    hour: Number(get("hour")),
    minute: Number(get("minute")),
  };
}

function toDate(value: string | Date): Date {
  return typeof value === "string" ? new Date(value) : value;
}

// Le nombre de jours de calendrier (à Zurich) entre deux instants.
function calendarDays(from: Date, to: Date): number {
  const a = Date.parse(`${zoned(from).day}T00:00:00Z`);
  const b = Date.parse(`${zoned(to).day}T00:00:00Z`);
  return Math.round((b - a) / 86_400_000);
}

// Les points des abréviations de mois de fr-CH sont gardés (« oct. ») ; « mai » n'en a pas.
function clean(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/** Dans une liste : « aujourd'hui », « hier », « 12 oct. », « 12 oct. 2025 » (une autre année). */
export function dateInList(value: string | Date, now: Date = new Date()): string {
  const date = toDate(value);
  const days = calendarDays(date, now);
  if (days === 0) return "aujourd'hui";
  if (days === 1) return "hier";
  return clean((zoned(date).year === zoned(now).year ? dayMonth : dayMonthYear).format(date));
}

/** Dans une phrase : « le 12 octobre » (« le 12 octobre 2025 » une autre année). */
export function dateInSentence(value: string | Date, now: Date = new Date()): string {
  const date = toDate(value);
  const text = (zoned(date).year === zoned(now).year ? longDayMonth : longDayMonthYear).format(date);
  return `le ${clean(text).replace(/^1 /, "1er ")}`;
}

/** L'heure : « 14 h 05 », « 14 h ». */
export function timeOfDay(value: string | Date): string {
  const { hour, minute } = zoned(toDate(value));
  return minute ? `${hour} h ${String(minute).padStart(2, "0")}` : `${hour} h`;
}

/** Quand l'heure compte : « aujourd'hui à 14 h », « hier à 9 h 30 », « 12 oct. à 8 h ». */
export function dateWithTime(value: string | Date, now: Date = new Date()): string {
  return `${dateInList(value, now)} à ${timeOfDay(value)}`;
}

/** Un rendez-vous : « jeudi 29 octobre à 9 h 30 ». */
export function meetingDate(value: string | Date): string {
  const date = toDate(value);
  return `${clean(weekdayLong.format(date)).replace(/ 1 /, " 1er ")} à ${timeOfDay(date)}`;
}

/** Depuis quand : « depuis aujourd'hui », « depuis hier », « depuis 9 jours ». */
export function sinceDays(value: string | Date, now: Date = new Date()): string {
  const days = Math.max(0, calendarDays(toDate(value), now));
  if (days === 0) return "depuis aujourd'hui";
  if (days === 1) return "depuis hier";
  return `depuis ${days} jours`;
}

/** Dans combien de temps : « aujourd'hui », « demain », « dans 3 jours ». */
export function inDays(value: string | Date, now: Date = new Date()): string {
  const days = calendarDays(now, toDate(value));
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "demain";
  return `dans ${days} jours`;
}

/** Le groupe d'une notification (maquette Notifications) : « Aujourd'hui », « Hier », « Cette semaine », « Plus tôt ». */
export function dayGroup(value: string | Date, now: Date = new Date()): string {
  const days = calendarDays(toDate(value), now);
  if (days <= 0) return "Aujourd'hui";
  if (days === 1) return "Hier";
  return days < 7 ? "Cette semaine" : "Plus tôt";
}

/** L'heure d'une notification, à droite de son titre : « 9 h 12 » aujourd'hui, « Hier », sinon « 30 oct. ». */
export function timeInList(value: string | Date, now: Date = new Date()): string {
  const days = calendarDays(toDate(value), now);
  if (days <= 0) return timeOfDay(value);
  if (days === 1) return "Hier";
  return dateInList(value, now);
}

const weekday = new Intl.DateTimeFormat("fr-CH", { weekday: "long", timeZone: ZONE });
const weekdayShort = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "short", timeZone: ZONE });

/** Les jours de calendrier (à Zurich) écoulés depuis une date. */
export function daysSince(value: string | Date, now: Date = new Date()): number {
  return calendarDays(toDate(value), now);
}

/** Le jour d'un envoi dans une carte (maquette Envoyees) : « aujourd'hui », « hier », « lundi » dans la semaine, sinon « le 21 oct. ». */
export function sentDay(value: string | Date, now: Date = new Date()): string {
  const days = calendarDays(toDate(value), now);
  if (days < 2) return dateInList(value, now);
  if (days < 7) return weekday.format(toDate(value));
  return `le ${dateInList(value, now)}`;
}

/** Un entretien dans une puce (maquette Envoyees) : « Jeudi 12 nov., 14 h ». */
export function meetingChip(value: string | Date): string {
  const text = clean(weekdayShort.format(toDate(value)));
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}, ${timeOfDay(value)}`;
}

// Le sélecteur de date et heure (maquette du 8 novembre, docs/143, D26) : des jours de calendrier sans heure ni
// fuseau (« 2026-11-10 ») et des heures « 09:30 ». Les calculs se font en UTC pour éviter les décalages d'heure d'été.
const longDay = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const shortDay = new Intl.DateTimeFormat("fr-CH", { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const monthYear = new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric", timeZone: "UTC" });
const monthAbbr = new Intl.DateTimeFormat("fr-CH", { month: "short", timeZone: "UTC" });
const dayAria = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

function capital(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Un jour de calendrier en Date à minuit UTC. */
export function dayToDate(day: string): Date {
  return new Date(`${day}T00:00:00Z`);
}

/** Une Date (minuit UTC) en jour de calendrier « 2026-11-10 ». */
export function dateToDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

/** Aujourd'hui à Zurich, en jour de calendrier. */
export function todayDay(now: Date = new Date()): string {
  return zoned(now).day;
}

/** Ajoute des jours ou des mois à un jour de calendrier. */
export function addDays(day: string, days: number): string {
  const date = dayToDate(day);
  date.setUTCDate(date.getUTCDate() + days);
  return dateToDay(date);
}
export function addMonths(day: string, months: number): string {
  const date = dayToDate(day);
  const wanted = date.getUTCDate();
  date.setUTCDate(1);
  date.setUTCMonth(date.getUTCMonth() + months);
  const last = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
  date.setUTCDate(Math.min(wanted, last));
  return dateToDay(date);
}

/** « Mardi 10 novembre 2026 ». */
export function longDate(day: string): string {
  return capital(clean(longDay.format(dayToDate(day))).replace(",", ""));
}

/** « Mar. 10 nov. 2026 » (pilule étroite du téléphone, maquette RendezVous). */
export function shortDate(day: string): string {
  return capital(clean(shortDay.format(dayToDate(day))).replace(",", ""));
}

/** « Novembre 2026 ». */
export function monthTitle(day: string): string {
  return capital(clean(monthYear.format(dayToDate(day))));
}

/** « 10 novembre 2026 » : le nom accessible d'un jour du calendrier. */
export function dayLabel(day: string): string {
  return clean(dayAria.format(dayToDate(day))).replace(/^1 /, "1er ");
}

/** Le mois abrégé en capitales de l'icône calendrier : « NOV », « SEPT », « FÉVR ». */
export function monthCaps(month: number): string {
  return clean(monthAbbr.format(new Date(Date.UTC(2026, month - 1, 1)))).replace(".", "").toUpperCase();
}

/** « 09:30 » en « 9 h 30 », « 14:00 » en « 14 h ». */
export function clockLabel(time: string): string {
  const [h, m] = time.split(":").map(Number);
  return m ? `${h} h ${String(m).padStart(2, "0")}` : `${h} h`;
}

/** « 10.11.2026 » ou « 10.11.26 » en jour de calendrier, sinon null. */
export function parseTypedDay(text: string): string | null {
  const match = text.trim().match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2}|\d{4})$/);
  if (!match) return null;
  const [, d, m, y] = match;
  const year = y!.length === 2 ? 2000 + Number(y) : Number(y);
  const date = new Date(Date.UTC(year, Number(m) - 1, Number(d)));
  if (date.getUTCMonth() !== Number(m) - 1 || date.getUTCDate() !== Number(d)) return null;
  return dateToDay(date);
}

/** Un jour de calendrier en « 10.11.2026 ». */
export function typedDay(day: string): string {
  const [y, m, d] = day.split("-");
  return `${d}.${m}.${y}`;
}

/** « 9:30 », « 09h30 », « 930 » en « 09:30 », sinon null. */
export function parseTypedTime(text: string): string | null {
  const match = text.trim().match(/^(\d{1,2})\s*(?:[:h.]\s*(\d{2})?|(\d{2}))?$/i);
  if (!match) return null;
  const hour = Number(match[1]);
  const minute = Number(match[2] ?? match[3] ?? 0);
  if (hour > 23 || minute > 59) return null;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}
