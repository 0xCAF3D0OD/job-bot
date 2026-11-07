import type { Application } from "./api/client";
import { followUpList } from "./applicationState";
import { daysSince, meetingChip, sentDay } from "./dates";
import type { IconName } from "./icons";

// Envoyées (maquette Envoyees, 7.11.2026) : les rubriques, les puces et le statut de chaque carte.

export type SentSectionKey = "follow" | "interviews" | "week" | "earlier";
export type SentSection = { key: SentSectionKey; title: string; items: Application[] };

const TITLES: Record<SentSectionKey, string> = {
  follow: "À relancer",
  interviews: "Entretiens",
  week: "Cette semaine",
  earlier: "Plus tôt",
};

function day(a: Application): string {
  return `${a.sent_at}T12:00:00`;
}

// À relancer (plus de 10 jours sans réponse, docs/38), puis les entretiens, puis les envois des 7 derniers jours,
// puis le reste, du plus récent au plus ancien. Une candidature n'est que dans une rubrique ; les vides sont omises.
export function sentSections(all: Application[], now: Date = new Date()): SentSection[] {
  const follow = followUpList(all);
  const taken = new Set(follow.map((a) => a.id));
  const interviews = all
    .filter((a) => !taken.has(a.id) && a.status === "entretien")
    .sort((a, b) => (a.interview_at ?? "9").localeCompare(b.interview_at ?? "9"));
  interviews.forEach((a) => taken.add(a.id));
  const rest = all.filter((a) => !taken.has(a.id)).sort((a, b) => b.sent_at.localeCompare(a.sent_at) || b.id - a.id);
  const week = rest.filter((a) => daysSince(day(a), now) < 7);
  const earlier = rest.filter((a) => daysSince(day(a), now) >= 7);
  const groups: [SentSectionKey, Application[]][] = [
    ["follow", follow],
    ["interviews", interviews],
    ["week", week],
    ["earlier", earlier],
  ];
  return groups.filter(([, items]) => items.length).map(([key, items]) => ({ key, title: TITLES[key], items }));
}

export type SentChip = { text: string; tone?: "green" };

// Le canal, dans la semaine seulement (maquette) : un formulaire quand l'adresse de l'offre est connue.
function channel(a: Application): string {
  if (a.method === "ecrit") return "Par courrier";
  if (a.method === "telephone") return "Par téléphone";
  if (a.method === "personnel") return "En personne";
  return a.application_url ? "Formulaire en ligne" : "Par e-mail";
}

export function sentChips(a: Application, section: SentSectionKey, now: Date = new Date()): SentChip[] {
  if (section === "follow") {
    const relaunched = a.status === "relancee" && a.followed_up_at;
    const days = daysSince(relaunched ? `${a.followed_up_at}T12:00:00` : day(a), now);
    return [{ text: `${relaunched ? "Relancée" : "Envoyée"} il y a ${days} jours` }];
  }
  if (section === "interviews" && a.interview_at) return [{ text: meetingChip(a.interview_at), tone: "green" }];
  const sent = { text: `Envoyée ${sentDay(day(a), now)}` };
  return section === "week" ? [sent, { text: channel(a) }] : [sent];
}

export type SentStatus = { word: string; icon: IconName; tone: "peach" | "green" | "grey" | "muted" };

// À droite de la carte : une icône dans un rond et un mot (Sans réponse, Entretien, Envoyée, Refusée…).
export function sentStatus(a: Application, section: SentSectionKey): SentStatus {
  if (section === "follow" || a.status === "sans_reponse") return { word: "Sans réponse", icon: "clock", tone: "peach" };
  if (a.status === "entretien") return { word: "Entretien", icon: "calendar", tone: "green" };
  if (a.status === "engagement") return { word: "Poste obtenu", icon: "done", tone: "green" };
  if (a.status === "refus") return { word: "Refusée", icon: "close", tone: "muted" };
  if (a.status === "relancee") return { word: "Relancée", icon: "reply", tone: "grey" };
  return { word: "Envoyée", icon: "send", tone: "grey" };
}
