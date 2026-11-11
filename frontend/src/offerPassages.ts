import type { Offer } from "./api/client";

// Les passages de l'annonce qui correspondent au profil (lot du 11 novembre au soir, PR 45 et 47) : une seule
// source pour le tri et pour le détail d'une offre. Ce sont les citations données par l'IA avec la note
// (score-v8), dont le serveur n'a gardé que celles retrouvées dans l'annonce, écrites comme dans l'annonce
// (`passages`). Une note plus ancienne n'en a pas : ni surlignage ni légende.
export interface Segment {
  text: string;
  mark: boolean;
}

type Texted = Pick<Offer, "passages">;

export function offerText(offer: Pick<Offer, "description" | "snippet">): string {
  return (offer.description || offer.snippet || "").replace(/\s+/g, " ").trim();
}

function escape(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Le texte affiché a ses espaces réduites à une seule : un passage se retrouve quels que soient ses espaces
// (insécables, retours à la ligne), sa casse et ses apostrophes (droite ou courbe), comme sur le serveur.
function finder(passages: string[]): RegExp | null {
  const parts = passages
    .map((p) => p.trim())
    .filter(Boolean)
    .sort((a, b) => b.length - a.length)
    .map((p) => escape(p).replace(/\s+/g, "\\s+").replace(/['’‘ʼ]/g, "['’‘ʼ]"));
  return parts.length ? new RegExp(parts.join("|"), "giu") : null;
}

/** Les passages retrouvés dans l'annonce, tels que le serveur les a vérifiés. */
export function matchedPassages(offer: Texted): string[] {
  return offer.passages ?? [];
}

/** Le texte découpé en morceaux, les passages retrouvés marqués. */
export function markSegments(text: string, passages: string[]): Segment[] {
  const re = finder(passages);
  if (!re) return text ? [{ text, mark: false }] : [];
  const out: Segment[] = [];
  let last = 0;
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push({ text: text.slice(last, m.index), mark: false });
    out.push({ text: m[0], mark: true });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ text: text.slice(last), mark: false });
  return out;
}

export interface Excerpt {
  segments: Segment[];
  // Le texte ne tient pas en entier : « Lire toute l’annonce ».
  built: boolean;
  // Le nombre de passages surlignés dans l'extrait, pour la légende.
  count: number;
}

const GAP = " (…) ";
const AROUND = 22;
const HEAD = 400;

function wordStart(text: string, at: number): number {
  let i = Math.max(0, at);
  while (i > 0 && !/\s/.test(text[i - 1]!)) i--;
  return i;
}
function wordEnd(text: string, at: number): number {
  let i = Math.min(text.length, at);
  while (i < text.length && !/\s/.test(text[i]!)) i++;
  return i;
}

/**
 * L'extrait du tri. Un texte court passe en entier. Un texte long est construit, pas tronqué : les fragments
 * autour des passages retrouvés, reliés par « (…) ». Un fragment qui ne tient pas est retiré en entier : jamais
 * un passage surligné coupé.
 */
export function buildExcerpt(text: string, passages: string[], max = 135): Excerpt {
  const whole = markSegments(text, passages);
  if (text.length <= max) return { segments: whole, built: false, count: whole.filter((s) => s.mark).length };
  const re = finder(passages);
  const hits = re ? [...text.matchAll(re)] : [];
  // Sans passage retrouvé : le début de l'annonce, que la page coupe à 4 lignes (téléphone) ou 5 (ordinateur).
  if (!hits.length) return { segments: [{ text: text.slice(0, wordStart(text, HEAD)).trimEnd(), mark: false }], built: true, count: 0 };
  // Une fenêtre par première occurrence de chaque passage, élargie aux mots voisins ; les fenêtres qui se
  // touchent fusionnent.
  const first = new Map<string, RegExpMatchArray>();
  for (const m of hits) if (!first.has(m[0].toLowerCase())) first.set(m[0].toLowerCase(), m);
  const windows: [number, number][] = [];
  for (const m of [...first.values()].sort((a, b) => a.index! - b.index!)) {
    const start = wordStart(text, m.index! - AROUND);
    const end = wordEnd(text, m.index! + m[0].length + AROUND);
    const previous = windows.at(-1);
    if (previous && start <= previous[1] + GAP.length) previous[1] = Math.max(previous[1], end);
    else windows.push([start, end]);
  }
  const kept: [number, number][] = [];
  let length = 0;
  for (const w of windows) {
    const cost = w[1] - w[0] + GAP.length;
    if (length + cost > max && kept.length) break;
    kept.push(w);
    length += cost;
  }
  const segments: Segment[] = [];
  kept.forEach(([start, end], i) => {
    const lead = i === 0 ? (start > 0 ? "(…) " : "") : GAP;
    if (lead) segments.push({ text: lead, mark: false });
    segments.push(...markSegments(text.slice(start, end), passages));
  });
  if (kept.at(-1)![1] < text.length) segments.push({ text: " (…)", mark: false });
  return { segments, built: true, count: segments.filter((s) => s.mark).length };
}

// --- La lettre (lot du 11 novembre au soir, PR 51) -------------------------------------------------------------------
// « Repris de l’annonce » : ce que l'annonce demande (les demandes relevées avec la note, `keywords_asks`) et ses
// passages vérifiés, quand la lettre les reprend mot pour mot. Rien n'est deviné : un terme n'est gardé que s'il se
// lit dans l'annonce (quand son texte est connu), et il n'est surligné que s'il se lit dans la lettre, en mot entier.
type Asked = Pick<Offer, "passages" | "description" | "snippet"> & { keywords_asks?: { text: string }[] | null };

function wholeWords(terms: string[]): RegExp | null {
  const parts = terms
    .map((t) => t.trim())
    .filter(Boolean)
    .sort((a, b) => b.length - a.length)
    .map((t) => escape(t).replace(/\s+/g, "\\s+").replace(/['’‘ʼ]/g, "['’‘ʼ]"));
  return parts.length ? new RegExp(`(?<![\\p{L}\\p{N}])(?:${parts.join("|")})(?![\\p{L}\\p{N}])`, "giu") : null;
}

/** Les termes de l'annonce qu'une lettre peut reprendre. */
export function letterTerms(offer: Asked | null | undefined): string[] {
  if (!offer) return [];
  const terms = [...(offer.keywords_asks ?? []).map((k) => k.text), ...(offer.passages ?? [])].map((t) => t.trim()).filter((t) => t.length > 1);
  const ad = offerText(offer);
  const seen = new Map<string, string>();
  for (const t of terms) if (!seen.has(t.toLowerCase())) seen.set(t.toLowerCase(), t);
  const unique = [...seen.values()];
  return ad ? unique.filter((t) => wholeWords([t])!.test(ad)) : unique;
}

/** Un paragraphe de la lettre découpé, les termes repris marqués. */
export function letterSegments(text: string, terms: string[]): Segment[] {
  const re = wholeWords(terms);
  if (!re) return text ? [{ text, mark: false }] : [];
  const out: Segment[] = [];
  let last = 0;
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push({ text: text.slice(last, m.index), mark: false });
    out.push({ text: m[0], mark: true });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ text: text.slice(last), mark: false });
  return out;
}

/** Le nombre de termes différents repris dans la lettre, pour la légende. */
export function letterPoints(paragraphs: string[], terms: string[]): number {
  const re = wholeWords(terms);
  if (!re) return 0;
  const found = new Set<string>();
  for (const text of paragraphs) for (const m of text.matchAll(re)) found.add(m[0].toLowerCase().replace(/\s+/g, " "));
  return found.size;
}
