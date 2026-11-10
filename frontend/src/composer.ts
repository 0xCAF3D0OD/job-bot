import type { IconName } from "./icons";

// Les types et la règle de la zone de saisie unique (Composer, docs/143, D25).

export interface ComposerItem {
  id: string;
  label: string;
  hint?: string;
  icon: IconName;
}
export interface ComposerAttachment {
  id: string;
  label: string;
}

// La dictée du navigateur (décision de Kevin du 10 novembre, PR 19) : Chrome envoie l'audio à Google, Safari à Apple,
// pour le transcrire. C'est un service de transcription tiers (docs/regles-securite-donnees.md, O-4) : il est écrit sur
// la page Confidentialité (« La dictée »), et le premier appui sur le micro demande l'accord de la personne, gardé sur
// cet appareil seulement (c'est le navigateur de cet appareil qui envoie l'audio). jobA1 ne reçoit que le texte.
export const DICTATION_ALLOWED = true;
const DICTATION_KEY = "jobA1.dictee";

export function dictationAccepted(): boolean {
  try {
    return globalThis.localStorage?.getItem(DICTATION_KEY) === "oui";
  } catch {
    return false;
  }
}

export function acceptDictation(): void {
  try {
    globalThis.localStorage?.setItem(DICTATION_KEY, "oui");
  } catch {
    // Stockage refusé (navigation privée) : l'accord sera redemandé la prochaine fois.
  }
}
