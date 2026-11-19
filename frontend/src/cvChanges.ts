import type { Cv } from "./api/client";

// Le panneau « Adapté pour cette offre » (MODIFICATIONS du 9 novembre, §14 ; maquette PreparerOrdinateurCVChangements) :
// ce que la version adaptée change par rapport au CV d'origine, un point par changement. L'IA ne réécrit pas les blocs
// (llm/cv.py) : elle écrit le titre et le résumé, choisit les blocs et leur ordre. Chaque retrait et chaque nouvel ordre
// peut s'annuler (`undo` : la liste de blocs à enregistrer). Le résumé aussi (Kevin, 19.11) : `summaryUndo` est le
// résumé de la version de départ (`origin_summary`, vide pour une première version), qu'« Annuler » remet.

// `mark` : ce que « Voir les changements » surligne dans l'aperçu (§34 du 16.11), le résumé ou le bloc déplacé ; un
// bloc retiré n'est plus dans l'aperçu, il n'a rien à surligner.
// `target` : ce que vise la ligne « Pourquoi » du serveur (`reasons`, §37 du 16.11), le résumé ou le bloc déplacé ou retiré.
export type CvChange = {
  key: string;
  title: string;
  before: string;
  now: string;
  undo: number[] | null;
  summaryUndo?: string;
  mark?: number | "summary";
  target: number | "summary";
};

export function canUndo(change: CvChange): boolean {
  return change.undo !== null || change.summaryUndo !== undefined;
}

// « Expérience chez Nordwind Cloud » (planche PreparerOrdinateurCVChangements, Kevin 19.11) : l'entreprise est ce qui
// suit le dernier « — », « · », « | » ou « , » du titre du bloc, sans la période entre parenthèses ; introuvable, la
// ligne garde le nom de la rubrique.
export function employerOf(title: string): { role: string; company: string } | null {
  const bare = title.replace(/\s*\([^()]*\)\s*$/, "").trim();
  const match = /^(.+?)\s*(?:\s[—–·|-]\s|,\s)\s*([^—–·|,]+)$/.exec(bare);
  if (!match) return null;
  const role = match[1]!.trim();
  const company = match[2]!.trim();
  return role && company ? { role, company } : null;
}

const SECTIONS: Record<string, string> = {
  experience: "Expériences",
  competence: "Compétences",
  formation: "Formation",
  langues: "Langues",
};

function rank(n: number): string {
  return n === 1 ? "première position" : `${n}e position`;
}

// Remet un bloc retiré à sa place d'origine parmi les blocs gardés de sa rubrique (sinon à la fin).
function restore(cv: Cv, origin: number[], id: number): number[] {
  const section = cv.blocks.find((b) => b.id === id)?.section;
  const at = origin.indexOf(id);
  const ids = [...cv.chunk_ids];
  const sameSection = ids.filter((i) => cv.blocks.find((b) => b.id === i)?.section === section);
  const after = sameSection.filter((i) => origin.indexOf(i) < at).pop();
  const before = sameSection.find((i) => origin.indexOf(i) > at);
  if (after !== undefined) ids.splice(ids.indexOf(after) + 1, 0, id);
  else if (before !== undefined) ids.splice(ids.indexOf(before), 0, id);
  else ids.push(id);
  return ids;
}

// Les blocs d'une rubrique reprennent l'ordre d'origine, aux mêmes places dans la liste.
function reorder(cv: Cv, origin: number[], kept: number[]): number[] {
  const sorted = [...kept].sort((a, b) => origin.indexOf(a) - origin.indexOf(b));
  let next = 0;
  return cv.chunk_ids.map((id) => (kept.includes(id) ? sorted[next++]! : id));
}

export function cvChanges(cv: Cv): CvChange[] {
  const origin = cv.origin_ids ?? [];
  const changes: CvChange[] = [];
  const summary = (cv.summary ?? "").trim();
  const originSummary = (cv.origin_summary ?? "").trim();
  if (summary !== originSummary) {
    changes.push({
      key: "summary",
      title: "Profil",
      before: originSummary ? `Avant : « ${originSummary} »` : "Avant : pas de résumé ; jobA1 l’écrit à partir de tes blocs, sans rien ajouter.",
      now: summary ? `Maintenant : « ${summary} »` : "Maintenant : pas de résumé.",
      undo: null,
      summaryUndo: originSummary,
      mark: "summary",
      target: "summary",
    });
  }
  if (!origin.length) return changes;
  const title = (id: number) => cv.blocks.find((b) => b.id === id)?.title ?? "";
  for (const key of Object.keys(SECTIONS)) {
    const kept = cv.chunk_ids.filter((id) => cv.blocks.find((b) => b.id === id)?.section === key);
    const before = origin.filter((id) => kept.includes(id));
    const moved = kept.findIndex((id, i) => id !== before[i]);
    if (moved >= 0) {
      const id = kept[moved]!;
      const employer = key === "experience" ? employerOf(title(id)) : null;
      changes.push({
        key: `order-${key}`,
        title: employer ? `Expérience chez ${employer.company}` : SECTIONS[key]!,
        before: `Avant : « ${employer ? employer.role : title(id)} » venait en ${rank(before.indexOf(id) + 1)}.`,
        now: `Maintenant : il vient ${moved === 0 ? "en premier" : `en ${rank(moved + 1)}`}.`,
        undo: reorder(cv, origin, kept),
        mark: id,
        target: id,
      });
    }
  }
  for (const id of origin) {
    if (cv.chunk_ids.includes(id)) continue;
    const block = cv.blocks.find((b) => b.id === id);
    if (!block) continue;
    changes.push({
      key: `removed-${id}`,
      title: block.title,
      before: `Avant : dans ta rubrique ${SECTIONS[block.section] ?? block.section}.`,
      now: "Maintenant : retiré pour cette offre.",
      undo: restore(cv, origin, id),
      target: id,
    });
  }
  return changes;
}
