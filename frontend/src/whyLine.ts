// La phrase « pourquoi » de l'écran de tri (décision de Kevin du 27.10) : une ligne de 80 caractères
// au plus, coupée proprement, sans « … » (règle §3). On garde d'abord la première phrase ou la
// première proposition qui tient ; sinon on coupe au dernier mot entier.
export const WHY_MAX = 80;

const STOPS = /[.;:!?](\s|$)|,\s|\s[–—-]\s/g;

export function whyLine(text: string, max = WHY_MAX): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  const room = max - 1; // la place du point final
  let cut = 0;
  for (const match of clean.matchAll(STOPS)) {
    const end = match.index;
    if (end > room) break;
    if (end >= 20) cut = end;
  }
  if (!cut) cut = clean.lastIndexOf(" ", room);
  if (cut <= 0) cut = room;
  const line = clean.slice(0, cut).replace(/[\s,;:–—-]+$/, "");
  return /[.!?]$/.test(line) ? line : `${line}.`;
}
