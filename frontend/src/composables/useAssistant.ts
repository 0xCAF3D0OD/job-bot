import { ref } from "vue";

import { api } from "../api/client";

// Élément choisi sur la page (docs/24 §2.2), envoyé avec chaque question.
export type AssistantFocus = {
  offerId?: number;
  applicationId?: number;
  day?: string;
  month?: string;
  // Affiché dans le panneau : « offre SRE chez Exemple SA ».
  label?: string;
};

const available = ref(false);
const open = ref(false);
const focus = ref<AssistantFocus | null>(null);
// Demande venue d'un raccourci : le panneau repart sur une nouvelle discussion.
const fresh = ref(0);
let checked: Promise<void> | null = null;

export function useAssistant() {
  function check(): Promise<void> {
    checked ??= api.GET("/api/assistant/status").then(({ data }) => {
      available.value = Boolean(data?.available);
    });
    return checked;
  }

  // Les pages tiennent à jour l'élément choisi ; un raccourci l'impose et ouvre le panneau.
  function setFocus(value: AssistantFocus | null): void {
    focus.value = value;
  }

  function askAbout(value: AssistantFocus): void {
    focus.value = value;
    fresh.value += 1;
    open.value = true;
  }

  return { available, open, focus, fresh, check, setFocus, askAbout };
}

export function focusBody(value: AssistantFocus | null): Record<string, unknown> | null {
  if (!value) return null;
  const body: Record<string, unknown> = {
    offer_id: value.offerId ?? null,
    application_id: value.applicationId ?? null,
    day: value.day ?? null,
    month: value.month ?? null,
  };
  return Object.values(body).some((v) => v !== null) ? body : null;
}

// Trois suggestions selon la page et l'élément choisi (docs/24 §1).
export function suggestionsFor(page: string, value: AssistantFocus | null): string[] {
  if (value?.offerId) {
    if (page === "preparation") {
      return ["Comment améliorer ma lettre pour cette offre ?", "Que mettre en avant pour ce poste ?", "Rédige un court e-mail d'accompagnement"];
    }
    return ["Explique-moi la note de cette offre", "Dois-je postuler à cette offre ?", "Quels points mettre en avant pour ce poste ?"];
  }
  if (value?.applicationId) {
    return ["Où en est cette candidature ?", "Rédige un e-mail de relance pour cette candidature", "Comment préparer l'entretien pour ce poste ?"];
  }
  if (value?.day) {
    return ["Qu'ai-je envoyé ce jour-là ?", "Qui relancer cette semaine ?", "Où en suis-je ce mois pour l'ORP ?"];
  }
  const byPage: Record<string, string[]> = {
    today: ["Que faire aujourd'hui ?", "Qui relancer cette semaine ?", "Où en suis-je pour l'ORP ce mois-ci ?"],
    offers: ["Lesquelles postuler en priorité ?", "Pourquoi certaines offres sont-elles mal notées ?", "Comment fonctionne la note ?"],
    applications: ["Où en suis-je ce mois pour l'ORP ?", "Qui relancer cette semaine ?", "Que retenir de mes entretiens ?"],
    alerts: ["Mes alertes arrivent-elles bien ?", "Comment créer une alerte sur un site ?", "Quelles recherches ajouter ?"],
    news: ["Que retenir des dernières actualités ?", "Comment ajouter une source ?", "Comment filtrer sur mon domaine ?"],
    trainings: ["Quelle formation me serait la plus utile ?", "Où en sont mes formations ?", "Comment fonctionnent les suggestions ?"],
    profile: ["Que manque-t-il à mon profil ?", "Comment écrire un bon bloc de profil ?", "Quelles compétences mettre en avant ?"],
    settings: ["À quoi servent les seuils de note ?", "Comment ajouter un site suivi ?", "Comment fonctionne le plafond de l'IA ?"],
    diagnostic: ["Que veut dire cet état ?", "La collecte fonctionne-t-elle ?", "Pourquoi l'IA ne note-t-elle pas ?"],
  };
  return byPage[page] ?? ["Que faire aujourd'hui ?", "Où en suis-je pour l'ORP ce mois-ci ?", "Comment créer mes alertes ?"];
}
