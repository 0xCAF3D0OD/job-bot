import type { IconName } from "./icons";

// Le genre d'une notification décide du libellé de son lien sur ordinateur (maquette NotificationsOrdinateur) et de
// son icône sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.9) : une icône de 24 px par type, en
// --primary-graphic, sauf retard ou limite en --peach-text. Offres : porte-documents ; justificatifs ou budget :
// point d'exclamation dans un cercle ; relance : avion en papier ; bilan : courbe. Les genres que la maquette ne
// montre pas prennent l'icône la plus proche : rendez-vous et entretien, le calendrier ; formation, le livre ;
// collecte, filtre Gmail ou sauvegarde en échec, le point d'exclamation en pêche ; les autres, le document.
type Kind = { action: string | null; icon: IconName; late?: boolean };

const KINDS: Record<string, Kind> = {
  offers: { action: "Voir les offres", icon: "briefcase" },
  first_alert: { action: "Voir les offres", icon: "briefcase" },
  follow_up: { action: "Relancer", icon: "send" },
  contact_follow_up: { action: "Relancer", icon: "send" },
  orp_due: { action: "Compléter", icon: "alert-circle", late: true },
  orp_target: { action: "Compléter", icon: "alert-circle" },
  orp_meeting: { action: "Préparer", icon: "calendar" },
  interview: { action: "Préparer", icon: "calendar" },
  training_funding: { action: "Voir la formation", icon: "book" },
  rhythm_week: { action: null, icon: "trend" },
  budget: { action: "Voir le budget", icon: "alert-circle", late: true },
  collect_failed: { action: "Voir", icon: "alert-circle", late: true },
  gmail_filter: { action: "Voir", icon: "alert-circle", late: true },
  backup_failed: { action: "Voir", icon: "alert-circle", late: true },
};

export function notificationKind(kind: string): Kind {
  return KINDS[kind] ?? { action: null, icon: "file" };
}
