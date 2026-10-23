import { ref } from "vue";

import { api } from "../api/client";

// Nouveautés des Actualités depuis la dernière visite (docs/15 §2), pour le menu.
const count = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
// Augmente à chaque visite des Actualités : une réponse partie avant la visite arrive trop
// tard et ne doit pas ramener le compteur que la visite vient de remettre à zéro (1.6.1).
let visits = 0;

async function refresh(): Promise<void> {
  const sentAt = visits;
  try {
    const { data } = await api.GET("/api/news", { params: { query: { limit: 1 } } });
    if (data && sentAt === visits) count.value = data.new_articles + data.new_videos;
  } catch {
    // Silencieux : le compteur n'est qu'un repère.
  }
}

export function useNewsCount() {
  function start(): void {
    if (timer) return;
    void refresh();
    timer = setInterval(() => void refresh(), 5 * 60_000);
  }
  function reset(): void {
    visits += 1;
    count.value = 0;
  }
  return { count, start, refresh, reset };
}
