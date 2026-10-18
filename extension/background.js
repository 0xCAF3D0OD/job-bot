// Fond de l'extension (docs/71) : l'onglet « Relier jobA1 » juste après l'installation, et la
// liaison en un clic. Le panneau demande l'accès à l'adresse de la plateforme, puis ce fond
// ouvre sa page « Relier ce navigateur » et retient l'onglet. Quand la page annonce le jeton
// (« ?etat=pret »), il le lit dans cet onglet seulement, sur cette adresse seulement, puis
// l'efface de la page. Le jeton ne passe jamais dans une adresse.
// Firefox (page de fond) et Chrome (service worker) : même code, API `chrome.*` à promesses.

const LINK_PATH = "/extension/relier";

chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") chrome.tabs.create({ url: chrome.runtime.getURL("popup.html?accueil=1") });
});

chrome.runtime.onMessage.addListener((message, _sender, reply) => {
  if (message?.type !== "link" || typeof message.base !== "string") return false;
  startLink(message.base).then(
    () => reply({ ok: true }),
    (error) => reply({ ok: false, error: error.message }),
  );
  return true;
});

async function startLink(base) {
  const origin = new URL(base).origin;
  const tab = await chrome.tabs.create({ url: origin + LINK_PATH });
  await chrome.storage.session.set({ linking: { tabId: tab.id, base: origin } });
}

chrome.tabs.onUpdated.addListener(async (tabId, change) => {
  if (!change.url && change.status !== "complete") return;
  const { linking } = await chrome.storage.session.get("linking");
  // Une page pas encore autorisée ou fermée entre-temps : on attend la suivante, sans erreur.
  if (linking?.tabId === tabId) await collect(linking).catch(() => undefined);
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  const { linking } = await chrome.storage.session.get("linking");
  if (linking?.tabId === tabId) await chrome.storage.session.remove("linking");
});

// Lit le jeton posé par la page de la plateforme, et seulement par elle.
async function collect({ tabId, base }) {
  const tab = await chrome.tabs.get(tabId).catch(() => null);
  if (!tab?.url || new URL(tab.url).origin !== base || !new URL(tab.url).pathname.startsWith(LINK_PATH)) return;
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const el = document.getElementById("jobbot-extension-token");
      const token = el?.dataset.token || null;
      // Effacé de la page : la page le voit et affiche « C'est relié ».
      if (token) el.removeAttribute("data-token");
      return token;
    },
  });
  const token = results?.[0]?.result;
  if (typeof token !== "string" || !token.startsWith("jbx_")) return;
  await chrome.storage.local.set({ base, token });
  await chrome.storage.session.remove("linking");
}
