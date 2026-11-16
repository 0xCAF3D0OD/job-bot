// Fond de l'extension (docs/71) : l'onglet « Relier jobA1 » juste après l'installation, et la
// liaison en un clic. Le panneau demande l'accès à l'adresse de la plateforme, puis ce fond
// ouvre sa page « Relier ce navigateur » et retient l'onglet. Quand la page annonce le jeton
// (« ?etat=pret »), il le lit dans cet onglet seulement, sur cette adresse seulement, puis
// l'efface de la page. Le jeton ne passe jamais dans une adresse.
// Firefox (page de fond) et Chrome (service worker) : même code, API `chrome.*` à promesses.

const LINK_PATH = "/extension/relier";

// Chrome (service worker) charge ici les sélecteurs et les fonctions copiées dans la page ;
// Firefox les charge par la liste `background.scripts` du manifeste.
if (typeof importScripts === "function" && !globalThis.jobA1AlertProbe) importScripts("alert-selectors.js", "alertes.js");

chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") chrome.tabs.create({ url: chrome.runtime.getURL("popup.html?accueil=1") });
  // Le script de la page jobA1 (section 42), enregistré de nouveau à chaque mise à jour.
  registerPage().catch(() => undefined);
});

chrome.runtime.onMessage.addListener((message, sender, reply) => {
  // Le suivi de l'alerte jobup (section 42) : la fenêtre, et la page jobA1.
  if (message?.type === "alert-track" && typeof message.tabId === "number" && !sender?.tab) {
    trackAlert(message).then(reply, () => reply(null));
    return true;
  }
  if (message?.type === "alert-flow" && typeof message.tabId === "number" && !sender?.tab) {
    flowOf(message.tabId).then(reply, () => reply(null));
    return true;
  }
  if (message?.type === "alert-progress?") {
    pageProgress(sender).then(reply, () => reply(null));
    return true;
  }
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
  await flowOnUpdate(tabId, change).catch(() => undefined);
  await codeOnUpdate(tabId, change).catch(() => undefined);
  if (!change.url && change.status !== "complete") return;
  const { linking } = await chrome.storage.session.get("linking");
  // Une page pas encore autorisée ou fermée entre-temps : on attend la suivante, sans erreur.
  if (linking?.tabId === tabId) await collect(linking).catch(() => undefined);
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  await endFlow(tabId).catch(() => undefined);
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
  await registerPage().catch(() => undefined);
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

// Dans la page : le champ du code, rempli comme au clavier, puis « Continuer », sauf sur jobup
// (`click` faux) : jobA1 ne clique jamais sur un bouton de jobup (règle 1 de la section 42).
function fillCode(code, click = true) {
  const inputs = [...document.querySelectorAll("input")].filter(
    (input) => !input.disabled && !input.hidden && /^(text|tel|number|)$/.test(input.type),
  );
  const input =
    inputs.find((i) => /code|otp/i.test(`${i.name} ${i.id} ${i.autocomplete}`)) ?? (inputs.length === 1 ? inputs[0] : null);
  if (!input) return false;
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, code);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  if (!click) return true;
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
        await chrome.scripting.executeScript({ target: { tabId }, func: fillCode, args: [found.code.code, page.site !== "jobup"] });
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
  // L'onglet d'une alerte jobup suivie : le suivi s'en occupe (section 42).
  if (await flowOf(tabId)) return;
  if (!(await chrome.permissions.contains({ origins: [`https://${page.host}/*`] }))) return;
  await watchCode(tabId, page).catch(() => undefined);
}

globalThis.jobA1Codes = { codePage, fillCode, watchCode, CODE_ORIGINS };


// --- L'alerte jobup suivie (section 42 de la maquette, docs/142 §4 bis) ----------------------
// La fenêtre, ouverte sur le formulaire « Créer une alerte » de jobup, confie l'onglet au fond :
// il suit cet onglet, et lui seul, jusqu'à l'alerte créée. Étapes, dans l'ordre : filled
// (formulaire rempli), sent (alerte envoyée, jobup demande le code), code-pasted (code collé dans
// son champ) ou fallback (champ introuvable : le code est à copier depuis la fenêtre), created.
// Jamais un clic sur jobup : la personne crée et confirme l'alerte elle-même.
// Gardé dans le stockage de session du navigateur : l'onglet, l'étape, le résumé de la recherche
// (lu dans l'adresse de la page), si le champ e-mail est resté vide. Jamais le code : il passe de
// la plateforme au champ de jobup dans une variable, puis il est oublié ; il n'est jamais écrit
// dans la console.

const FLOW_KEY = "alertFlow";
const FLOW_POLL_MS = 4000;
const FLOW_MS = 20 * 60_000;
const flowRuns = new Set();

function hostOf(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" ? parsed.hostname : null;
  } catch {
    return null;
  }
}

async function readFlow() {
  const { [FLOW_KEY]: flow } = await chrome.storage.session.get(FLOW_KEY);
  return flow ?? null;
}

async function flowOf(tabId) {
  const flow = await readFlow();
  return flow?.tabId === tabId ? flow : null;
}

async function endFlow(tabId) {
  if (await flowOf(tabId)) await chrome.storage.session.remove(FLOW_KEY);
}

async function trackAlert({ tabId, summary, emailEmpty }) {
  const before = await flowOf(tabId);
  // Déjà en route sur cet onglet (code attendu ou collé) : on ne revient pas en arrière.
  const flow =
    before && !["filled", "created"].includes(before.step)
      ? before
      : {
          tabId,
          site: "jobup",
          step: "filled",
          summary: typeof summary === "string" ? summary.slice(0, 200) : "",
          emailEmpty: emailEmpty === true,
        };
  await chrome.storage.session.set({ [FLOW_KEY]: flow });
  await announce(flow);
  runFlow(tabId).catch(() => undefined);
  return flow;
}

// Le nouvel état, à la fenêtre (si elle est ouverte) et aux pages jobA1 ouvertes (le contrat de
// docs/decisions/2026-11-16-2130-extension-contrat-page.md) : l'étape seulement.
async function announce(flow) {
  chrome.runtime.sendMessage({ type: "alert-changed", tabId: flow.tabId })?.catch?.(() => undefined);
  const origin = await platformOrigin();
  if (!origin || !chrome.tabs.query) return;
  for (const tab of await chrome.tabs.query({})) {
    if (tab.url && originOf(tab.url) === origin) {
      chrome.tabs.sendMessage(tab.id, { type: "alert-progress", site: flow.site, step: flow.step })?.catch?.(() => undefined);
    }
  }
}

function originOf(url) {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

async function platformOrigin() {
  const { base } = await chrome.storage.local.get(["base"]);
  return base ? originOf(base) : null;
}

// La page jobA1 demande où en est l'alerte : l'étape, rien d'autre, et seulement à elle.
async function pageProgress(sender) {
  const origin = await platformOrigin();
  if (!origin || originOf(sender?.tab?.url ?? sender?.url) !== origin) return null;
  const flow = await readFlow();
  return flow ? { site: flow.site, step: flow.step } : null;
}

async function probePage(tabId, rules) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId }, func: globalThis.jobA1AlertProbe, args: [rules] });
    return result ?? null;
  } catch {
    // Page en chargement, ou page du code sans accès donné : rien n'est lu.
    return null;
  }
}

// Le code de jobup reçu depuis l'envoi de l'alerte, par la requête authentifiée de l'extension.
async function freshCode(since) {
  const found = await platformCall("/api/extension/codes?site=jobup");
  const code = found?.code;
  if (!code?.code || Date.parse(code.received_at) < since - 60_000) return null;
  return code.code;
}

async function pasteCode(tabId, rules, code) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId }, func: globalThis.jobA1PasteCode, args: [rules, code] });
    return result === true;
  } catch {
    return false;
  }
}

// Un pas du suivi : où en est l'onglet, et l'étape suivante s'il y a lieu.
async function stepFlow(tabId) {
  const flow = await flowOf(tabId);
  if (!flow || flow.step === "created") return flow;
  const rules = globalThis.jobA1AlertSelectors.jobup;
  const tab = await chrome.tabs.get(tabId).catch(() => null);
  const host = hostOf(tab?.url);
  // La personne a quitté jobup dans cet onglet : le suivi s'arrête, rien n'est fait ailleurs.
  if (!host || (!rules.hosts.includes(host) && !rules.codeHosts.includes(host))) {
    await endFlow(tabId);
    return null;
  }
  const onCodeHost = rules.codeHosts.includes(host);
  const probe = await probePage(tabId, rules);
  const next = { ...flow, onCodeHost: flow.onCodeHost || onCodeHost };
  if (probe?.done) {
    next.step = "created";
  } else if (flow.step === "filled") {
    if (probe?.code || probe?.asks || onCodeHost) {
      next.step = "sent";
      next.sentAt = Date.now();
    }
  } else if (flow.step === "sent") {
    let code = await freshCode(flow.sentAt ?? 0);
    if (code) {
      next.step = probe?.code && (await pasteCode(tabId, rules, code)) ? "code-pasted" : "fallback";
      code = null;
    }
  } else if (flow.onCodeHost && !onCodeHost) {
    // Code collé ou à copier : la page du code est quittée, jobup a pris le code.
    next.step = "created";
  } else if (probe && !probe.code && !probe.asks && !probe.form) {
    next.step = "created";
  }
  if (next.step === flow.step && next.onCodeHost === flow.onCodeHost) return flow;
  if (next.step === "sent") await platformCall("/api/extension/codes/expect", { method: "POST" });
  if (next.step === "created") await platformCall("/api/extension/alerts/jobup", { method: "PUT" });
  // Toujours le même onglet : la personne a pu en ouvrir un autre entre-temps.
  if ((await readFlow())?.tabId !== tabId) return null;
  await chrome.storage.session.set({ [FLOW_KEY]: next });
  if (next.step !== flow.step) await announce(next);
  return next;
}

async function runFlow(tabId, sleep = (ms) => new Promise((r) => setTimeout(r, ms))) {
  if (flowRuns.has(tabId) || globalThis.jobA1FlowManual) return;
  flowRuns.add(tabId);
  try {
    const until = Date.now() + FLOW_MS;
    while (Date.now() < until) {
      await sleep(FLOW_POLL_MS);
      const flow = await stepFlow(tabId);
      if (!flow || flow.step === "created") return;
    }
  } finally {
    flowRuns.delete(tabId);
  }
}

// Le fond a pu s'endormir : une page de l'onglet suivi qui change relance le suivi.
async function flowOnUpdate(tabId, change) {
  if (change.status !== "complete" && !change.url) return;
  const flow = await flowOf(tabId);
  if (!flow || flow.step === "created") return;
  await stepFlow(tabId);
  runFlow(tabId).catch(() => undefined);
}

// --- La page jobA1 (contrat de la page, section 42) ------------------------------------------
// Sur l'adresse de la plateforme reliée, et seulement si l'accès est donné (docs/71) : un script
// qui dit à la page que l'extension est là, et lui relaie l'étape de l'alerte jobup.

const PAGE_SCRIPT = "joba1-page";

async function registerPage() {
  if (!chrome.scripting.registerContentScripts) return false;
  const { base } = await chrome.storage.local.get(["base"]);
  await chrome.scripting.unregisterContentScripts({ ids: [PAGE_SCRIPT] }).catch(() => undefined);
  if (!base) return false;
  const url = new URL(base);
  const pattern = `${url.protocol}//${url.hostname}/*`;
  if (!(await chrome.permissions.contains({ origins: [pattern] }))) return false;
  await chrome.scripting.registerContentScripts([
    { id: PAGE_SCRIPT, matches: [pattern], js: ["page-joba1.js"], runAt: "document_start", persistAcrossSessions: true },
  ]);
  return true;
}

chrome.runtime.onStartup?.addListener(() => void registerPage().catch(() => undefined));
chrome.permissions.onAdded?.addListener(() => void registerPage().catch(() => undefined));
chrome.storage.onChanged?.addListener((changes, area) => {
  if (area === "local" && changes.base) registerPage().catch(() => undefined);
});

globalThis.jobA1Flow = { trackAlert, stepFlow, flowOf, pageProgress, registerPage, runFlow };
