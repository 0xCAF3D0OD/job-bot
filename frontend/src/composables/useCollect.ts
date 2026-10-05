import { ref } from "vue";

import { api } from "../api/client";

// État partagé : le bouton de la barre du haut et celui du Journal affichent le même message.
const message = ref("");
const running = ref(false);

export function useCollect() {
  async function collectNow(): Promise<void> {
    running.value = true;
    try {
      const { data, response } = await api.POST("/api/alerts/refresh");
      if (response.status === 409) {
        message.value =
          "Collecte non configurée : renseigne JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD dans .env.";
      } else if (data?.result === "already_queued") {
        message.value = "Une collecte attend déjà son tour.";
      } else if (data?.result === "queued") {
        message.value = "Collecte lancée. Le journal se met à jour d'ici une minute.";
      } else if (response.status >= 500) {
        message.value = `L'API ne répond pas (HTTP ${response.status}) : vérifie que make dev tourne, puis réessaie.`;
      } else {
        message.value = `La collecte n'a pas pu être lancée (HTTP ${response.status}).`;
      }
    } catch {
      message.value = "API injoignable : vérifie que make dev tourne, puis réessaie.";
    } finally {
      running.value = false;
    }
  }

  return { message, running, collectNow };
}
