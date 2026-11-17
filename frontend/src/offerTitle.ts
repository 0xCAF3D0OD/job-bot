// Le titre d'une offre tel qu'on l'affiche (Kevin, 17.11, Q3 : à l'affichage seulement, aucune donnée modifiée) :
// - « | » devient « · » ;
// - un titre tout en majuscules passe en casse normale (première lettre en capitale) ;
// - les sigles connus restent intacts (AWS, DevOps, SRE, CI/CD…), ainsi que les mots du lieu et de l'entreprise de l'offre
//   (« LAUSANNE » redevient « Lausanne » quand le lieu de l'offre est Lausanne).
// Un titre déjà en casse mixte ne change pas de casse : seul le séparateur change.

// Sigles et noms propres courants dans les annonces, écrits comme il faut. Clé : le mot en minuscules.
const KNOWN = new Map(
  [
    "AWS", "GCP", "SRE", "CI/CD", "DevOps", "DevSecOps", "MLOps", "FinOps", "IT", "ICT", "IoT", "HR", "RH", "SAP", "UX", "UI",
    "QA", "CEO", "CFO", "CTO", "COO", "CIO", "CISO", "IA", "AI", "ML", "LLM", "BI", "PHP", "SQL", "NoSQL", "ERP", "CRM", "HES",
    "HEG", "EPFL", "ETH", "CFC", "AFP", "ORP", "SEO", "SEA", "API", "REST", "SaaS", "B2B", "B2C", ".NET", "C#", "C++", "iOS",
    "macOS", "JavaScript", "TypeScript", "Java", "Python", "Kotlin", "Swift", "React", "Angular", "Vue.js", "Node.js",
    "Azure", "Linux", "Windows", "Kubernetes", "Docker", "Terraform", "Salesforce", "PostgreSQL", "Oracle", "Microsoft",
    "Google", "SharePoint", "PMO", "KAM", "HSE", "QHSE", "R&D", "PME", "CDI", "CDD", "SA", "AG", "GmbH", "Sàrl",
    "H/F", "F/H", "M/F", "F/M", "H/F/X", "M/W", "W/M", "M/W/D", "W/M/D", "M/F/D", "VD", "GE", "VS", "NE", "JU", "ZH", "BS",
    "TI", "FR", "BE",
  ].map((word) => [word.toLowerCase(), word] as const),
);
// Un mot : lettres et chiffres, avec « / », « . », « + », « # », « & » à l'intérieur (CI/CD, Node.js, C++, C#, R&D).
const WORD = /\.?[\p{L}\p{N}][\p{L}\p{N}+#&]*(?:[/.][\p{L}\p{N}+#&]+)*/gu;

function shouting(title: string): boolean {
  const letters = title.match(/\p{L}/gu) ?? [];
  if (letters.length < 4) return false;
  const upper = letters.filter((letter) => letter !== letter.toLowerCase()).length;
  return upper / letters.length >= 0.8;
}

// Les mots du lieu et de l'entreprise, quand ils ne sont pas eux-mêmes en majuscules.
function properWords(...sources: (string | null | undefined)[]): Map<string, string> {
  const out = new Map<string, string>();
  for (const source of sources) {
    if (!source || shouting(source)) continue;
    for (const word of source.match(WORD) ?? []) if (word !== word.toLowerCase()) out.set(word.toLowerCase(), word);
  }
  return out;
}

function capitalize(text: string): string {
  return text.replace(/\p{L}/u, (letter) => letter.toLocaleUpperCase("fr-CH"));
}

export function displayTitle(title: string | null | undefined, place?: { location?: string | null; company?: string | null }): string {
  if (!title) return "";
  const joined = title.replace(/\s*\|\s*/g, " · ").replace(/\s+/g, " ").trim();
  if (!shouting(joined)) return joined;
  const proper = properWords(place?.location, place?.company);
  const lowered = joined.replace(WORD, (word) => {
    const key = word.toLocaleLowerCase("fr-CH");
    return KNOWN.get(key) ?? proper.get(key) ?? key;
  });
  // Casse normale : la première lettre du titre, et celle de chaque partie après « · ».
  return lowered.split(" · ").map(capitalize).join(" · ");
}
