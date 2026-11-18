import { reactive, ref } from "vue";

import { api } from "./api/client";

// « Ton nom sur la feuille » (LISEZMOI §70, planche FeuilleNom ; Kevin, 18.11.2026) : ton nom, ton conseiller ORP et
// ton office régional, gardés dans ton compte. Chaque champ s'enregistre quand on le quitte : « Enregistrement… », puis
// « Enregistré » ; s'il échoue, « Pas enregistré · Réessayer » et la saisie reste dans le champ.
export type IdentityField = "name" | "advisor" | "office";
export type SaveState = "idle" | "saving" | "saved" | "failed";

const FIELDS: IdentityField[] = ["name", "advisor", "office"];

export function useSheetIdentity() {
  const values = reactive<Record<IdentityField, string>>({ name: "", advisor: "", office: "" });
  const states = reactive<Record<IdentityField, SaveState>>({ name: "idle", advisor: "idle", office: "idle" });
  // Ce que le serveur a : un champ quitté sans changement ne s'enregistre pas.
  const stored: Record<IdentityField, string> = { name: "", advisor: "", office: "" };
  const loaded = ref(false);
  // La valeur en cours d'envoi : la même ne part pas deux fois.
  const sending: Partial<Record<IdentityField, string>> = {};

  async function load(): Promise<void> {
    try {
      const { data } = await api.GET("/api/orp-meeting/nom");
      if (data) {
        for (const field of FIELDS) {
          stored[field] = data[field] ?? "";
          // Une saisie commencée avant la réponse n'est pas écrasée.
          if (states[field] === "idle" && !values[field]) values[field] = stored[field];
        }
      }
    } catch {
      // Hors ligne : les champs restent vides ; un enregistrement dira s'il échoue.
    }
    loaded.value = true;
  }

  async function save(field: IdentityField): Promise<void> {
    const value = values[field].trim();
    if (value === stored[field] && states[field] !== "failed") return;
    if (states[field] === "saving" && sending[field] === value) return;
    states[field] = "saving";
    sending[field] = value;
    try {
      const { data } = await api.PUT("/api/orp-meeting/nom", { body: { [field]: value } });
      if (!data) throw new Error("refusé");
      stored[field] = data[field] ?? "";
      // Une nouvelle saisie pendant l'enregistrement reste là ; sinon, la valeur nettoyée par le serveur.
      if (values[field].trim() === value) values[field] = stored[field];
      if (sending[field] === value) states[field] = "saved";
    } catch {
      if (sending[field] === value) states[field] = "failed";
    }
  }

  // Une nouvelle saisie efface « Enregistré » (il redira l'état au prochain départ du champ).
  function edit(field: IdentityField): void {
    if (states[field] === "saved") states[field] = "idle";
  }

  return { values, states, loaded, load, save, edit };
}
