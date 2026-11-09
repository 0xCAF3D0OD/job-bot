import type { Cv } from "./api/client";

// Le panneau « Adapté pour cette offre » (MODIFICATIONS du 9 novembre, §14 ; maquette PreparerOrdinateurCVChangements) :
// ce que la version adaptée change par rapport au CV d'origine, un point par changement. L'IA ne réécrit pas les blocs
// (llm/cv.py) : elle écrit le titre et le résumé, choisit les blocs et leur ordre. Chaque retrait et chaque nouvel ordre
// peut s'annuler (`undo` : la liste de blocs à enregistrer) ; le résumé n'a pas d'« avant » gardé, il ne s'annule pas.

export type CvChange = { key: string; title: string; before: string; now: string; undo: number[] | null };

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
  if (cv.summary.trim()) {
    changes.push({
      key: "summary",
      title: "Profil",
      before: "Avant : pas de résumé ; jobA1 l’écrit à partir de tes blocs, sans rien ajouter.",
      now: `Maintenant : « ${cv.summary.trim()} »`,
      undo: null,
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
      changes.push({
        key: `order-${key}`,
        title: SECTIONS[key]!,
        before: `Avant : « ${title(id)} » venait en ${rank(before.indexOf(id) + 1)}.`,
        now: `Maintenant : il vient en ${rank(moved + 1)}, pour cette offre.`,
        undo: reorder(cv, origin, kept),
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
      before: `Avant : dans ton CV, rubrique ${SECTIONS[block.section] ?? block.section}.`,
      now: "Maintenant : retiré pour cette offre.",
      undo: restore(cv, origin, id),
    });
  }
  return changes;
}
