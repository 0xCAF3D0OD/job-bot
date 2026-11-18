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

export async function readOfferFile(offerId: number, file: File): Promise<{ text?: string; error?: string }> {
  if (file.size > MAX_FILE) return { error: PROBLEMS["too-big"] };
  const { data, error: refused } = await api.POST("/api/offers/{offer_id}/file", {
    params: { path: { offer_id: offerId } },
    body: { file: "" },
    bodySerializer: () => {
      const form = new FormData();
      form.append("file", file);
      return form;
    },
  });
  if (!data) {
    const detail = (refused as { detail?: unknown } | undefined)?.detail;
    return { error: typeof detail === "string" ? detail : "Import impossible pour l’instant : réessaie." };
  }
  if (data.limit) return { error: data.limit };
  if (!data.text) return { error: PROBLEMS[data.problem ?? "unreadable"] ?? PROBLEMS.unreadable };
  return { text: data.text };
}
