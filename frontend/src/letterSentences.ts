// Les phrases d'un paragraphe de lettre, pour « Pas vrai » (30.10.2026) : la sélection, ou le curseur
// sur téléphone, est étendue aux phrases entières qu'elle touche. Même découpe que le serveur
// (llm/claims.py) : après « . », « ! » ou « ? », devant une majuscule.
const BOUNDARY = /(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Ý«"(])/g;

export interface Span {
  start: number;
  end: number;
}

export function sentenceSpans(text: string): Span[] {
  const spans: Span[] = [];
  let start = 0;
  for (const match of text.matchAll(BOUNDARY)) {
    spans.push({ start, end: match.index });
    start = match.index + match[0].length;
  }
  if (start < text.length) spans.push({ start, end: text.length });
  return spans.filter((s) => text.slice(s.start, s.end).trim());
}

/** Les phrases entières touchées par [from, to] ; avec from === to, celle du curseur. */
export function sentencesAt(text: string, from: number, to: number): string {
  const spans = sentenceSpans(text).filter((s) => (from === to ? from >= s.start && from <= s.end : s.start < to && s.end > from));
  if (!spans.length) return "";
  return text.slice(spans[0]!.start, spans[spans.length - 1]!.end).trim();
}

/** Le paragraphe sans ces phrases, les espaces resserrés. */
export function withoutSentence(text: string, sentence: string): string {
  return text.replace(sentence, " ").replace(/\s+/g, " ").trim();
}
