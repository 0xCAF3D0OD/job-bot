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

// La dictée du navigateur envoie souvent l'audio à son éditeur (Google, Apple) : un service de transcription tiers
// qui n'est pas sur la page Confidentialité (docs/regles-securite-donnees.md, O-4). Tant que ce n'est pas réglé, le
// micro reste caché partout, même quand `mic` est demandé.
export const DICTATION_ALLOWED = false;
