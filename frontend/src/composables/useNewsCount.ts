import { ref } from "vue";

import { api } from "../api/client";

// Nouveautés des Actualités depuis la dernière visite (docs/15 §2), pour le menu.
const count = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/news", { params: { query: { limit: 1 } } });
    if (data) count.value = data.new_articles + data.new_videos;
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
    count.value = 0;
  }
  return { count, start, refresh, reset };
}
