// Libellés des contacts dans l'entreprise (docs/31 §4).
import type { Contact } from "./api/client";

export const ROLES: Record<Contact["role"], string> = {
  recruiter: "Recrutement",
  manager: "Futur responsable",
  team: "Membre de l'équipe",
  alumni: "Ancien de ton école",
  other: "Autre",
};
export const CHANNELS: Record<Contact["channel"], string> = {
  linkedin_invite: "Invitation LinkedIn",
  linkedin_message: "Message LinkedIn",
  email: "E-mail",
  phone: "Téléphone",
  other: "Autre",
};
// Relance proposée 7 jours après une prise de contact restée sans réponse (docs/31 §4).
export const FOLLOW_UP_DAYS = 7;

export function isoDay(date = new Date()): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function toFollowUp(contact: Contact, today = new Date()): boolean {
  if (contact.answered_on) return false;
  const limit = new Date(today);
  limit.setDate(limit.getDate() - FOLLOW_UP_DAYS);
  return contact.contacted_on <= isoDay(limit);
}

export function contactName(contact: Contact): string {
  return contact.name || ROLES[contact.role].toLowerCase();
}

// Explication du panneau, derrière son « ? » (docs/32 §1).
export const CONTACTS_HELP =
  "Recherches LinkedIn déjà remplies, ouvertes dans un nouvel onglet : rien n'est lu ni envoyé à ta place. " +
  "Pour le message, l'IA reçoit le poste, le rôle choisi et ton profil, jamais de nom : remplace « [Prénom] » " +
  "et « [ton prénom] ». Une prise de contact ne compte pas pour l'ORP ; un rappel arrive dans la cloche après " +
  "7 jours sans réponse.";
