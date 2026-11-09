// Le genre d'une notification décide de son icône et du libellé de son lien (maquette Notifications, N8 ;
// docs/139 étape 9b). Les libellés hors maquette (Préparer, Voir la formation, Voir) sont ceux de la
// liste des écarts, validés par Kevin le 2026-11-04. Un genre absent d'ici : le visage content, sans libellé.
export type NotificationShape = "offers" | "orp" | "warning" | "calm";

const KINDS: Record<string, { shape: NotificationShape; action: string }> = {
  offers: { shape: "offers", action: "Voir les offres" },
  first_alert: { shape: "offers", action: "Voir les offres" },
  follow_up: { shape: "orp", action: "Relancer" },
  contact_follow_up: { shape: "orp", action: "Relancer" },
  orp_due: { shape: "orp", action: "Compléter" },
  orp_target: { shape: "orp", action: "Compléter" },
  orp_meeting: { shape: "orp", action: "Préparer" },
  interview: { shape: "orp", action: "Préparer" },
  training_funding: { shape: "orp", action: "Voir la formation" },
  budget: { shape: "warning", action: "Voir le budget" },
  collect_failed: { shape: "warning", action: "Voir" },
  gmail_filter: { shape: "warning", action: "Voir" },
  backup_failed: { shape: "warning", action: "Voir" },
};

export function notificationKind(kind: string): { shape: NotificationShape; action: string | null } {
  return KINDS[kind] ?? { shape: "calm", action: null };
}
