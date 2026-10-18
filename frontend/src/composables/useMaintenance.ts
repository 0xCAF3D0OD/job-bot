import { onMounted, onUnmounted, ref } from "vue";

import { api, MAINTENANCE_EVENT } from "../api/client";

// La plateforme en maintenance (docs/79) : la page d'attente se pose par-dessus l'écran, sans
// le recharger, puis s'en va dès que l'API répond ; ce qui était en cours d'écriture reste là.
export const POLL_MS = 10_000;

const waiting = ref(false);
const message = ref<string | null>(null);
// L'exploitant pendant une maintenance annoncée : il passe, les autres attendent.
const bypass = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;

type State = { active: boolean; message: string | null; bypass: boolean };

// L'état se lit sans passer par le client de l'API : une réponse ratée ne relance pas la page.
async function read(): Promise<State | null> {
  try {
    const response = await fetch("/api/maintenance", { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as State;
  } catch {
    return null;
  }
}

async function poll(): Promise<void> {
  timer = null;
  const state = await read();
  if (state && (!state.active || state.bypass)) {
    waiting.value = false;
    bypass.value = state.active && state.bypass;
    return;
  }
  if (state?.message) message.value = state.message;
  timer = setTimeout(() => void poll(), POLL_MS);
}

function onMaintenance(event: Event): void {
  const detail = (event as CustomEvent<string | null>).detail;
  if (detail) message.value = detail;
  if (waiting.value) return;
  waiting.value = true;
  timer ??= setTimeout(() => void poll(), POLL_MS);
}

export function useMaintenance() {
  onMounted(async () => {
    globalThis.addEventListener(MAINTENANCE_EVENT, onMaintenance);
    // Au démarrage : l'exploitant qui passe pendant une maintenance annoncée le voit rappelé.
    const { data } = await api.GET("/api/maintenance");
    bypass.value = Boolean(data?.active && data.bypass);
  });
  onUnmounted(() => {
    globalThis.removeEventListener(MAINTENANCE_EVENT, onMaintenance);
    if (timer) clearTimeout(timer);
    timer = null;
  });
  return { waiting, message, bypass };
}
