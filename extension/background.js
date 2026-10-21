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
  // Depuis le panneau : l'accès aux pages du code vient d'être donné, on commence (docs/112).
  if (message?.type === "watch-code" && typeof message.tabId === "number") {
    const page = codePage(message.url);
    if (!page) return false;
    watchCode(message.tabId, page).then(reply, () => reply(false));
    return true;
  }
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
  await codeOnUpdate(tabId, change).catch(() => undefined);
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

// --- Les codes des sites (docs/112) -----------------------------------------------------------
// La page d'un site demande le code de vérification envoyé à l'adresse jobA1 : le fond prévient
// la plateforme (relevé rapide de la boîte), attend le code quelques minutes, le remplit et
// clique « Continuer ». Seulement sur les pages de connexion connues, et seulement si la
// personne a donné l'accès à ces pages (une fois, depuis le panneau).

const CODE_PAGES = [
  { site: "jobup", host: "auth.jobup.ch" },
  { site: "jobsch", host: "auth.jobs.ch" },
];
const CODE_ORIGINS = CODE_PAGES.map((page) => `https://${page.host}/*`);
const CODE_POLL_MS = 5000;
const CODE_WAIT_MS = 5 * 60_000;
const watching = new Set();

function codePage(url) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:" || !/challenge|verif|code/i.test(parsed.pathname)) return null;
    return CODE_PAGES.find((page) => page.host === parsed.hostname) ?? null;
  } catch {
    return null;
  }
}

async function platformCall(path, options = {}) {
  const { base, token } = await chrome.storage.local.get(["base", "token"]);
  if (!base || !token) return null;
  const response = await fetch(base + path, { ...options, headers: { Authorization: `Bearer ${token}` } });
  return response.ok ? response.json() : null;
}

// Dans la page : le champ du code, rempli comme au clavier, puis « Continuer ».
function fillCode(code) {
  const inputs = [...document.querySelectorAll("input")].filter(
    (input) => !input.disabled && !input.hidden && /^(text|tel|number|)$/.test(input.type),
  );
  const input =
    inputs.find((i) => /code|otp/i.test(`${i.name} ${i.id} ${i.autocomplete}`)) ?? (inputs.length === 1 ? inputs[0] : null);
  if (!input) return false;
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, code);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  const scope = input.form ?? document;
  const button =
    scope.querySelector("button[type=submit]") ??
    [...document.querySelectorAll("button")].find((b) => /continuer|continue|weiter|valider|bestätigen/i.test(b.textContent));
  button?.click();
  return true;
}

async function watchCode(tabId, page, sleep = (ms) => new Promise((r) => setTimeout(r, ms))) {
  if (watching.has(tabId)) return false;
  watching.add(tabId);
  try {
    await platformCall("/api/extension/codes/expect", { method: "POST" });
    const until = Date.now() + CODE_WAIT_MS;
    while (Date.now() < until) {
      const found = await platformCall(`/api/extension/codes?site=${page.site}`);
      if (found?.code?.code) {
        const tab = await chrome.tabs.get(tabId).catch(() => null);
        // La personne a quitté la page entre-temps : rien n'est rempli ailleurs.
        if (!tab || codePage(tab.url)?.site !== page.site) return false;
        await chrome.scripting.executeScript({ target: { tabId }, func: fillCode, args: [found.code.code] });
        return true;
      }
      await sleep(CODE_POLL_MS);
    }
    return false;
  } finally {
    watching.delete(tabId);
  }
}

async function codeOnUpdate(tabId, change) {
  if (change.status !== "complete") return;
  const tab = await chrome.tabs.get(tabId).catch(() => null);
  const page = codePage(tab?.url);
  if (!page) return;
  if (!(await chrome.permissions.contains({ origins: [`https://${page.host}/*`] }))) return;
  await watchCode(tabId, page).catch(() => undefined);
}

globalThis.jobA1Codes = { codePage, fillCode, watchCode, CODE_ORIGINS };
