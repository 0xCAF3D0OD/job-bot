// Les textes du Bilan (1.6.62, planche « 3 et 4. Bilan ») : la conclusion, la bande, et la phrase de
// chaque repliable, tirés des chiffres de /api/insights. Fonctions pures, testées à part.
import type { components } from "./api/schema";

type Report = components["schemas"]["SearchReportOut"];
type Comparison = components["schemas"]["ComparisonOut"];
type Group = components["schemas"]["GroupOut"];
type Funnel = components["schemas"]["FunnelOut"];
type MonthCount = components["schemas"]["MonthCountOut"];
type InterviewLine = components["schemas"]["InterviewLineOut"];
export type Period = "recent" | "month" | "all";

function capital(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// En français, 0 et 1 prennent le singulier : « 0 poste obtenu ».
export function word(n: number, one: string, many: string): string {
  return n > 1 ? many : one;
}

/** La conclusion (règles §3) : l'état général de la période, exact et sans embellir (NN/g). Les cas se
 *  testent dans cet ordre ; « avance » seulement s'il y a plus de réponses qu'une période d'avant qui en
 *  avait. `before` précède l'accent, `accent` est en couleur, `after` suit. */
export function conclusion(report: Report, period: Period): { before: string; accent: string; after: string } {
  const n = report.funnel.applications;
  const r = report.funnel.responses;
  const p = report.previous_responses;
  if (n < 5) return { before: "", accent: "Trop tôt pour conclure", after: ` : ${n} ${word(n, "candidature", "candidatures")} sur la période.` };
  if (r === 0) return { before: "", accent: "Pas encore de réponse", after: ` : ${n} candidatures envoyées.` };
  if (p === null || p === undefined || p === 0) {
    return { before: "", accent: "Premières réponses", after: ` : ${r} sur ${n} candidatures.` };
  }
  const span = period === "month" ? "au mois d'avant" : "au trimestre d'avant";
  if (r > p) return { before: "Ta recherche ", accent: "avance", after: ` : plus de réponses qu'${span}.` };
  if (r === p) return { before: "Ta recherche ", accent: "tient le rythme", after: ` : autant de réponses qu'${span}.` };
  return { before: "Ta recherche ", accent: "ralentit", after: ` : moins de réponses qu'${span}.` };
}

const NOT_SITES = ["spontaneous", "manual"];

/** La bande : le site qui répond le plus, contre les autres sites qui ont assez de données. Rien
 *  s'il n'y a pas d'écart net (§3 : pas de bande sans action utile). */
export function bestSite(comparisons: Comparison[]): { label: string; title: string; summary: string } | null {
  const sites = (comparisons.find((c) => c.key === "source")?.groups ?? []).filter(
    (g) => g.enough && !NOT_SITES.includes(g.key),
  );
  if (sites.length < 2) return null;
  const rate = (g: Group) => (g.total ? g.responses / g.total : 0);
  const top = sites.reduce((a, b) => (rate(b) > rate(a) ? b : a));
  const others = sites.filter((g) => g !== top);
  const responses = others.reduce((n, g) => n + g.responses, 0);
  const total = others.reduce((n, g) => n + g.total, 0);
  if (top.responses < 2 || !total || rate(top) <= responses / total) return null;
  return {
    label: top.label,
    title: `${top.label} répond ${top.responses} fois sur ${top.total}.`,
    summary: `Les autres sites : ${responses} fois sur ${total}.`,
  };
}

export const STEPS = [
  { key: "received", one: "offre reçue", many: "offres reçues" },
  { key: "retained", one: "gardée", many: "gardées" },
  { key: "applications", one: "candidature", many: "candidatures" },
  { key: "responses", one: "réponse", many: "réponses" },
  { key: "interviews", one: "entretien", many: "entretiens" },
  { key: "engagements", one: "poste obtenu", many: "postes obtenus" },
] as const;

// Ce qu'on travaille quand on perd le plus avant cette étape.
const WORK: Record<string, string> = {
  applications: "postuler aux offres gardées",
  responses: "soigner les candidatures et relancer",
  interviews: "préparer les entretiens",
};

/** L'étape où l'on perd le plus, des offres gardées aux entretiens (la dernière, le poste, dépend
 *  d'autres que toi). Null sans données. */
export function weakStep(funnel: Funnel): { key: string; between: string; work: string } | null {
  let found: { key: string; between: string; work: string; rate: number } | null = null;
  for (let i = 2; i <= 4; i++) {
    const before = STEPS[i - 1]!;
    const after = STEPS[i]!;
    const from = funnel[before.key];
    if (!from) continue;
    const rate = funnel[after.key] / from;
    if (found === null || rate < found.rate) {
      const name = before.key === "retained" ? "offres gardées" : before.many;
      found = { key: after.key, between: `entre les ${name} et les ${after.many}`, work: WORK[after.key]!, rate };
    }
  }
  return found && found.rate < 1 ? { key: found.key, between: found.between, work: found.work } : null;
}

export function funnelText(funnel: Funnel): string {
  return `${STEPS.map((s) => `${funnel[s.key]} ${word(funnel[s.key], s.one, s.many)}`).join(", ")}.`;
}

// Les groupes de « Ce qui marche », nommés comme la planche.
export const COMPARE_TITLES: Record<string, string> = {
  source: "Par site",
  contact: "Avec un contact",
  follow_up: "Après une relance",
};
const GROUP_LABELS: Record<string, string> = { with: "Avec", without: "Sans", yes: "Relancées", no: "Sans relance" };
export function groupLabel(comparison: string, group: Group): string {
  // Un site garde son nom (« jobs.ch ») ; « ajoutée à la main » prend la majuscule d'un début de ligne.
  if (comparison === "source") return NOT_SITES.includes(group.key) ? capital(group.label) : group.label;
  return GROUP_LABELS[group.key] ?? group.label;
}

/** La phrase repliée de « Ce qui marche » : l'écart le plus net entre deux groupes qui ont assez de
 *  données (site, contact ou relance). Les sites sont sautés quand la bande en parle déjà (§3 : ne
 *  pas répéter). */
export function bestComparison(comparisons: Comparison[], skipSites = false): string {
  let best: { ratio: number; text: string } | null = null;
  for (const comparison of comparisons) {
    if (!(comparison.key in COMPARE_TITLES) || (skipSites && comparison.key === "source")) continue;
    const groups = comparison.groups.filter((g) => g.enough);
    if (groups.length < 2) continue;
    const rate = (g: Group) => g.responses / g.total;
    const top = groups.reduce((a, b) => (rate(b) > rate(a) ? b : a));
    const bottom = groups.reduce((a, b) => (rate(b) < rate(a) ? b : a));
    if (rate(top) <= rate(bottom)) continue;
    const ratio = rate(bottom) ? rate(top) / rate(bottom) : Infinity;
    const figures = `${top.responses} sur ${top.total}, contre ${bottom.responses} sur ${bottom.total}`;
    let lead: string;
    if (comparison.key === "follow_up") lead = top.key === "yes" ? "Une relance fait mieux répondre" : "Sans relance, plus de réponses";
    else if (comparison.key === "contact") lead = top.key === "with" ? "Un contact fait mieux répondre" : "Sans contact, plus de réponses";
    else lead = `${top.label} répond le mieux`;
    if (best === null || ratio > best.ratio) best = { ratio, text: `${lead} : ${figures}` };
  }
  return best?.text ?? (skipSites ? "Par site, avec un contact, après une relance" : "Rien de net pour l'instant");
}

const MONTH_NAMES = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const MONTH_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
export function monthName(key: string): string {
  return MONTH_NAMES[Number(key.slice(5, 7)) - 1] ?? key;
}
export function monthShort(key: string): string {
  return MONTH_SHORT[Number(key.slice(5, 7)) - 1] ?? key;
}

/** La phrase repliée de « Par mois » : le mois en cours, l'objectif et les jours qui restent. */
export function monthLine(months: MonthCount[], target: number | null | undefined, today: Date): string {
  const current = months.at(-1);
  if (!current) return "Rien encore";
  const count = `${current.count} ${word(current.count, "candidature", "candidatures")}`;
  if (!target) return `${capital(monthName(current.month))} : ${count}`;
  const last = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  const left = last - today.getDate();
  const rest = left === 0 ? "dernier jour" : `il reste ${left} ${word(left, "jour", "jours")}`;
  return `${capital(monthName(current.month))} : ${count} sur ${target}, ${rest}`;
}

/** Le texte de « Par mois » pour les lecteurs d'écran (WCAG 1.1.1). */
export function monthsText(months: MonthCount[], target: number | null | undefined): string {
  const parts = months.map((m, i) => {
    const current = i === months.length - 1;
    const name = capital(monthName(m.month));
    if (current) return `${name}, en cours : ${m.count}${target ? ` sur ${target}` : ""}.`;
    return i === 0 ? `${name} : ${m.count} ${word(m.count, "candidature", "candidatures")}.` : `${name} : ${m.count}.`;
  });
  if (target) parts.push(`Objectif : ${target} par mois.`);
  return parts.join(" ");
}

const dayMonth = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
export const dayShort = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

/** La phrase repliée de « Entretiens » : combien, et le prochain. */
export function interviewsLine(lines: InterviewLine[]): string {
  if (!lines.length) return "Pas encore d'entretien";
  const next = lines.filter((l) => l.state === "upcoming").at(-1);
  const count = `${lines.length} ${word(lines.length, "entretien", "entretiens")}`;
  return next ? `${count}, le prochain le ${dayMonth.format(new Date(`${next.day}T12:00:00`))}` : `${count}, aucun à venir`;
}
