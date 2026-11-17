import { onMounted, onUnmounted, ref } from "vue";

import { api } from "../api/client";

// Le code de confirmation que jobup envoie à l'adresse jobA1 (section 15 du paquet du 15.11 ; décisions de Kevin des 15
// et 16.11), partagé par la boîte du panneau Alertes (JobupCodeBox) et l'étape « Crée ton alerte sur jobup » des
// premiers pas (WelcomeAlertSteps, section 41 du 16.11). Le serveur reçoit le code dans la boîte jobA1 ; la page ne
// fait que le lire, jamais le saisir ni l'écrire ailleurs.
// - La relecture toutes les 5 s ne tourne que pendant l'attente et quand l'écran est visible. 10 minutes sans code :
//   elle s'arrête, l'étape reste en attente (Kevin, 16.11) ; « expiré » seulement pour un code reçu puis périmé.
// - Le serveur ne relève la boîte que si on le lui demande (« watch-code ») : dès l'affichage, puis chaque minute.
// - `relisten` (premiers pas) : un code périmé relance l'écoute, le nouveau code s'affiche tout seul.
export type JobupCode = { code: string; received_at: string; valid_minutes: number };

export function useJobupCode(options: { relisten?: boolean } = {}) {
  const state = ref<"waiting" | "received" | "expired">("waiting");
  const code = ref<JobupCode | null>(null);
  const copied = ref(false);
  // La boîte jobA1 a raté ses 3 dernières lectures (décision de Kevin du 15.11, 19 h 02).
  const down = ref(false);
  // « Toujours rien ? » après 2 minutes d'attente sans code (section 24 du 15.11).
  const late = ref(false);
  let since = 0;
  let seen = "";
  let timer = 0;
  let expiry = 0;
  let asked = 0;
  let lateTimer = 0;
  let listening = false;
  const ends = (c: JobupCode): number => Date.parse(c.received_at) + c.valid_minutes * 60_000;

  function stop(): void {
    clearInterval(timer);
    listening = false;
  }

  async function watch(): Promise<void> {
    try {
      down.value = !!(await api.POST("/api/alert-searches/watch-code"))?.data?.mailbox_down;
    } catch {
      // Hors ligne : la ligne reste telle quelle, la relecture suivante réessaie.
    }
  }

  async function tick(): Promise<void> {
    if (Date.now() - since >= 10 * 60_000) return stop();
    if (document.visibilityState !== "visible") return;
    if (down.value || Date.now() - asked >= 60_000) {
      asked = Date.now();
      void watch();
    }
    const { data } = await api.GET("/api/alert-searches/codes/last", { params: { query: { site: "jobup" } } });
    if (!listening || !data || data.received_at === seen) return;
    seen = data.received_at;
    if (!(ends(data) > Date.now())) return;
    code.value = data;
    state.value = "received";
    stop();
    clearTimeout(lateTimer);
    expiry = window.setTimeout(expired, ends(data) - Date.now());
  }

  function expired(): void {
    state.value = "expired";
    code.value = null;
    if (options.relisten) listen(false);
  }

  function listen(reset: boolean): void {
    clearTimeout(expiry);
    stop();
    if (reset) state.value = "waiting";
    since = Date.now();
    late.value = false;
    clearTimeout(lateTimer);
    lateTimer = window.setTimeout(() => (late.value = true), 120_000);
    listening = true;
    timer = window.setInterval(tick, 5000);
    void tick();
  }
  const restart = (): void => listen(true);

  const onVisible = (): void => void (listening && tick());

  function copy(): void {
    void navigator.clipboard?.writeText(code.value?.code ?? "").then(() => {
      copied.value = true;
      setTimeout(() => (copied.value = false), 2000);
    }, () => undefined);
  }

  onMounted(() => {
    document.addEventListener("visibilitychange", onVisible);
    restart();
  });
  onUnmounted(() => {
    document.removeEventListener("visibilitychange", onVisible);
    stop();
    clearTimeout(expiry);
    clearTimeout(lateTimer);
  });

  return { state, code, copied, down, late, restart, copy };
}
