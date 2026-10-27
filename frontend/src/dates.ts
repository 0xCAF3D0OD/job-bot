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
