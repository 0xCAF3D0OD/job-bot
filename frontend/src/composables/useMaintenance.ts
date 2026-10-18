import { onMounted, onUnmounted, ref } from "vue";

import { api, MAINTENANCE_EVENT, MAINTENANCE_READ_EVENT } from "../api/client";

// La plateforme en maintenance (docs/79, docs/80) : la page d'attente se pose par-dessus l'écran,
// sans le recharger, puis s'en va dès que l'API répond ; ce qui était en cours d'écriture reste
// là. En lecture seule, pas de page d'attente : un bandeau, et un message si l'on enregistre.
export const POLL_MS = 10_000;
export const READ_POLL_MS = 30_000;

const waiting = ref(false);
const message = ref<string | null>(null);
// L'exploitant pendant une maintenance annoncée : il passe, les autres attendent.
const bypass = ref(false);
// Maintenance en lecture seule, pour un invité : il consulte, il n'enregistre pas.
const reading = ref(false);
const refused = ref("");
let timer: ReturnType<typeof setTimeout> | null = null;
let readTimer: ReturnType<typeof setTimeout> | null = null;

type State = { active: boolean; mode?: string; message: string | null; bypass: boolean };

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

function apply(state: State): void {
  bypass.value = state.active && state.bypass;
  reading.value = state.active && state.mode === "lecture" && !state.bypass;
  if (reading.value && state.message) message.value = state.message;
  if (reading.value) readTimer ??= setTimeout(() => void pollReading(), READ_POLL_MS);
}

async function poll(): Promise<void> {
  timer = null;
  const state = await read();
  if (state && (!state.active || state.bypass || state.mode === "lecture")) {
    waiting.value = false;
    apply(state);
    return;
  }
  if (state?.message) message.value = state.message;
  timer = setTimeout(() => void poll(), POLL_MS);
}

// Le bandeau de la lecture seule s'en va tout seul quand la maintenance est levée.
async function pollReading(): Promise<void> {
  readTimer = null;
  const state = await read();
  if (state) apply(state);
  else if (reading.value) readTimer = setTimeout(() => void pollReading(), READ_POLL_MS);
}

function onMaintenance(event: Event): void {
  const detail = (event as CustomEvent<string | null>).detail;
  if (detail) message.value = detail;
  if (waiting.value) return;
  waiting.value = true;
  timer ??= setTimeout(() => void poll(), POLL_MS);
}

function onReadOnly(event: Event): void {
  const detail = (event as CustomEvent<string | null>).detail;
  refused.value = `Maintenance en cours : tu peux consulter, pas encore enregistrer.${detail ? ` ${detail}` : ""}`;
  apply({ active: true, mode: "lecture", message: detail, bypass: false });
}

export function useMaintenance() {
  onMounted(async () => {
    globalThis.addEventListener(MAINTENANCE_EVENT, onMaintenance);
    globalThis.addEventListener(MAINTENANCE_READ_EVENT, onReadOnly);
    // Au démarrage : le rappel de l'exploitant, ou le bandeau de la lecture seule.
    const { data } = await api.GET("/api/maintenance");
    if (data) apply(data);
  });
  onUnmounted(() => {
    globalThis.removeEventListener(MAINTENANCE_EVENT, onMaintenance);
    globalThis.removeEventListener(MAINTENANCE_READ_EVENT, onReadOnly);
    if (timer) clearTimeout(timer);
    if (readTimer) clearTimeout(readTimer);
    timer = readTimer = null;
  });
  return { waiting, message, bypass, reading, refused };
}
