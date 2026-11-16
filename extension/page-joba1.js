// Sur la page jobA1 seulement (l'adresse de la plateforme reliée, docs/71) : le contrat de la
// page (docs/decisions/2026-11-16-2130-extension-contrat-page.md, section 42 de la maquette).
// - l'extension est là : data-joba1-extension sur <html>, et un message « ready » ;
// - le suivi de l'alerte jobup : l'étape relayée telle quelle (filled, sent, code-pasted,
//   fallback, created), jamais le code ni l'adresse ;
// - la page peut demander l'étape courante (« alert-progress? »).
// Aucune requête au serveur, rien n'est lu dans la page.

(() => {
  const version = chrome.runtime.getManifest().version;
  const post = (data) => window.postMessage({ source: "joba1-extension", ...data }, location.origin);
  document.documentElement.dataset.joba1Extension = version;
  post({ type: "ready", version });

  const STEPS = ["filled", "sent", "code-pasted", "fallback", "created"];
  const progress = (state) => {
    if (state && STEPS.includes(state.step)) post({ type: "alert-progress", site: state.site, step: state.step });
  };

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === "alert-progress") progress(message);
  });

  window.addEventListener("message", async (event) => {
    if (event.source !== window || event.data?.source !== "joba1-page" || event.data.type !== "alert-progress?") return;
    progress(await chrome.runtime.sendMessage({ type: "alert-progress?" }).catch(() => null));
  });
})();
