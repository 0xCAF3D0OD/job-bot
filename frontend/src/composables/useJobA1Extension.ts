import { onMounted, onUnmounted, ref } from "vue";

// L'extension jobA1 vue depuis la page (section 42 du 16.11 ; contrat écrit dans
// docs/decisions/2026-11-16-2130-extension-contrat-page.md). Jamais de requête au serveur pour la détecter :
// - l'attribut data-joba1-extension="x.y.z" que son script pose sur <html> au chargement ;
// - le message { source: "joba1-extension", type: "ready", version }, pour une extension installée page ouverte ;
// - le suivi de l'alerte : { source: "joba1-extension", type: "alert-progress", site, step }, l'étape seulement,
//   jamais le code ni l'adresse. La page peut demander l'étape courante par { source: "joba1-page", type:
//   "alert-progress?" }.
// Seuls les messages de cette fenêtre et de cette origine comptent.
export const ALERT_STEPS = ["filled", "sent", "code-pasted", "fallback", "created"] as const;
export type AlertStep = (typeof ALERT_STEPS)[number];

const readAttribute = (): string | null => document.documentElement.dataset.joba1Extension || null;

export function useJobA1Extension(site = "jobup") {
  const version = ref<string | null>(readAttribute());
  const step = ref<AlertStep | null>(null);

  function onMessage(event: MessageEvent): void {
    if (event.source !== window || event.origin !== window.location.origin) return;
    const data: unknown = event.data;
    if (!data || typeof data !== "object") return;
    const message = data as { source?: unknown; type?: unknown; version?: unknown; site?: unknown; step?: unknown };
    if (message.source !== "joba1-extension") return;
    if (message.type === "ready") version.value = typeof message.version === "string" && message.version ? message.version : version.value ?? "?";
    if (message.type === "alert-progress" && message.site === site && ALERT_STEPS.includes(message.step as AlertStep)) {
      version.value ??= readAttribute() ?? "?";
      step.value = message.step as AlertStep;
    }
  }
  // Revenue sur l'onglet (après l'installation, ou depuis jobup) : l'attribut, puis l'étape courante.
  function onVisible(): void {
    if (document.visibilityState !== "visible") return;
    version.value ??= readAttribute();
    ask();
  }
  function ask(): void {
    if (version.value) window.postMessage({ source: "joba1-page", type: "alert-progress?" }, window.location.origin);
  }

  onMounted(() => {
    window.addEventListener("message", onMessage);
    document.addEventListener("visibilitychange", onVisible);
    version.value ??= readAttribute();
    ask();
  });
  onUnmounted(() => {
    window.removeEventListener("message", onMessage);
    document.removeEventListener("visibilitychange", onVisible);
  });

  return { version, step };
}
