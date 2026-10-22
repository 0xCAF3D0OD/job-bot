import { ref } from "vue";

import { api, type Plan } from "../api/client";

// La formule et ce qui reste ce mois-ci (docs/125 §4), partagées par toutes les pages. Les
// descriptions au survol des actions IA disent « Lettres : 2 sur 10 ce mois-ci. » à une personne
// invitée ; l'exploitant, sans limite, garde le coût.
export type PlanKey = Plan["usage"][number]["key"];

const plan = ref<Plan | null>(null);
let loading: Promise<void> | null = null;

async function refresh(): Promise<void> {
  const { data } = await api.GET("/api/plan");
  if (data && Array.isArray(data.usage)) plan.value = data;
}

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// « Lettres : 2 sur 10 ce mois-ci. »
function usageText(key: PlanKey): string {
  const usage = plan.value?.usage.find((u) => u.key === key);
  if (!usage || usage.limit === null) return "";
  return `${capitalized(usage.label)} : ${usage.used} sur ${usage.limit} ce mois-ci.`;
}

// La description d'une action IA : ce qui précède (`before`), puis le coût pour l'exploitant, le
// compteur de la formule pour une personne invitée (rien pour un usage sans limite).
function aiNote(cost: string, key?: PlanKey, before = ""): string {
  const tail = !plan.value || plan.value.unlimited ? cost : key ? usageText(key) : "";
  return [before, tail].filter(Boolean).join(" ");
}

// L'usage du mois est épuisé (jamais pour l'exploitant).
function reached(key: PlanKey): boolean {
  const usage = plan.value?.usage.find((u) => u.key === key);
  return !!usage && usage.limit !== null && usage.used >= usage.limit;
}

export function usePlan() {
  loading ??= refresh().catch(() => undefined);
  return { plan, refresh, aiNote, reached, usageText };
}
