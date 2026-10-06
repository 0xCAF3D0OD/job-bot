// Libellés des filtres des Actualités (docs/16 §3).
export const COUNTRIES: Record<string, string> = {
  CH: "Suisse",
  FR: "France",
  BE: "Belgique",
  LU: "Luxembourg",
  CA: "Canada",
  DE: "Allemagne",
  AT: "Autriche",
  INT: "International",
};

export const LANGUAGES: Record<string, string> = {
  fr: "français",
  de: "allemand",
  en: "anglais",
  it: "italien",
  es: "espagnol",
};

export const countryLabel = (code: string): string => COUNTRIES[code] ?? code;
export const languageLabel = (code: string): string => LANGUAGES[code] ?? code;

export interface Segment {
  text: string;
  hit: boolean;
}

function pattern(keyword: string): string {
  // « CI/CD » doit trouver « ci-cd » : les mots du mot-clé, séparés par n'importe quelle ponctuation.
  return keyword
    .split(/[^\p{L}\p{N}]+/u)
    .filter(Boolean)
    .map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("[^\\p{L}\\p{N}]+");
}

// Découpe le texte pour surligner les mots de « Mon domaine » trouvés par le serveur.
export function highlight(text: string, keywords: string[]): Segment[] {
  const parts = keywords.map(pattern).filter(Boolean);
  if (!parts.length) return [{ text, hit: false }];
  const regex = new RegExp(`(?<![\\p{L}\\p{N}])(${parts.join("|")})(?![\\p{L}\\p{N}])`, "giu");
  const segments: Segment[] = [];
  let last = 0;
  for (const match of text.matchAll(regex)) {
    const start = match.index ?? 0;
    if (start > last) segments.push({ text: text.slice(last, start), hit: false });
    segments.push({ text: match[0], hit: true });
    last = start + match[0].length;
  }
  if (last < text.length) segments.push({ text: text.slice(last), hit: false });
  return segments;
}
