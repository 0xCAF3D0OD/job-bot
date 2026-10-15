import { ref } from "vue";

import { api } from "../api/client";

// État partagé : le bouton de la barre du haut et celui du Journal affichent le même message.
const message = ref("");
const running = ref(false);
// Erreur : la bulle reste un peu plus longtemps (docs/32 §4).
const failed = ref(false);

export function useCollect() {
  async function collectNow(): Promise<void> {
    running.value = true;
    failed.value = false;
    try {
      const { data, response } = await api.POST("/api/alerts/refresh");
      if (response.status === 409) {
        failed.value = true;
        message.value =
          "Collecte non configurée : renseigne JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD dans .env.";
      } else if (data?.result === "already_queued") {
        message.value = "Une collecte attend déjà son tour.";
      } else if (data?.result === "queued") {
        message.value = "Collecte lancée. Le journal se met à jour d'ici une minute.";
      } else if (response.status >= 500) {
        failed.value = true;
        message.value = `L'API ne répond pas (HTTP ${response.status}) : vérifie que make dev tourne, puis réessaie.`;
      } else {
        failed.value = true;
        message.value = `La collecte n'a pas pu être lancée (HTTP ${response.status}).`;
      }
    } catch {
      failed.value = true;
      message.value = "API injoignable : vérifie que make dev tourne, puis réessaie.";
    } finally {
      running.value = false;
    }
  }

  return { message, running, failed, collectNow };
}
