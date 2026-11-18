import { api } from "./api/client";

// « Refaire la note » avec un fichier (Kevin, 17.11, Q1) : le fichier part au serveur, qui en rend le texte (PDF sans IA,
// capture PNG ou JPG recopiée par l'IA), ou ce qui l'a empêché. Chargé à la demande par OfferTextNotice.
const MAX_FILE = 5 * 1024 * 1024;
const PROBLEMS: Record<string, string> = {
  "no-text": "Je ne trouve pas de texte d’annonce dans ce fichier. Colle le texte de l’annonce.",
  "too-big": "Ce fichier est trop lourd (5 Mo au plus). Colle le texte de l’annonce.",
  "not-supported": "Seuls les PDF, PNG et JPG sont acceptés. Colle le texte de l’annonce.",
  unreadable: "Ce fichier ne peut pas être lu. Colle le texte de l’annonce.",
  "ai-off": "La capture ne peut pas être lue pour l’instant. Colle le texte de l’annonce.",
  "ai-down": "La capture ne peut pas être lue pour l’instant : réessaie dans un moment.",
  budget: "La capture ne peut pas être lue pour l’instant. Colle le texte de l’annonce.",
};

type FileAnswer = { text?: string | null; problem?: string | null; limit?: string | null } | undefined;
function form(file: File): () => FormData {
  return () => {
    const body = new FormData();
    body.append("file", file);
    return body;
  };
}
function answer(data: FileAnswer, refused: unknown): { text?: string; error?: string } {
  if (!data) {
    const detail = (refused as { detail?: unknown } | undefined)?.detail;
    return { error: typeof detail === "string" ? detail : "Import impossible pour l’instant : réessaie." };
  }
  if (data.limit) return { error: data.limit };
  if (!data.text) return { error: PROBLEMS[data.problem ?? "unreadable"] ?? PROBLEMS.unreadable };
  return { text: data.text };
}

export async function readOfferFile(offerId: number, file: File): Promise<{ text?: string; error?: string }> {
  if (file.size > MAX_FILE) return { error: PROBLEMS["too-big"] };
  const { data, error: refused } = await api.POST("/api/offers/{offer_id}/file", {
    params: { path: { offer_id: offerId } },
    body: { file: "" },
    bodySerializer: form(file),
  });
  return answer(data, refused);
}

// « Capture ou PDF » dans « Ajouter une offre » (§72 du 18.11, planche AjouterOffreTel) : la même lecture, pour une
// offre pas encore ajoutée. Le texte arrive dans le champ, à relire avant « Ajouter l'offre ».
export async function readManualFile(file: File): Promise<{ text?: string; error?: string }> {
  if (file.size > MAX_FILE) return { error: PROBLEMS["too-big"] };
  const { data, error: refused } = await api.POST("/api/offers/manual/file", { body: { file: "" }, bodySerializer: form(file) });
  return answer(data, refused);
}
