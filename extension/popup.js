// Panneau de l'extension (docs/25, docs/71, docs/142). La fenêtre de la maquette du 6.11.2026
// (360 × 480, boards Ext*) : un en-tête, la pastille du site de l'onglet ouvert, un état à la fois.
// États : non connectée (ExtNonConnecte), rien à faire (ExtAutreSite), réglages (roue dentée), et
// ceux d'avant la maquette : formulaire de l'employeur (docs/25), Job-Room (docs/70), codes
// (docs/112). Le jeton reste dans le stockage local du navigateur.
// Chrome, Edge, Brave et Firefox (140 et plus) : même code, API `chrome.*` à promesses.

const $ = (id) => document.getElementById(id);
const show = (id, on = true) => ($(id).hidden = !on);

let config = { base: "", token: "" };
// Réglage : remplir aussi le formulaire d'alerte de LinkedIn (sinon l'adresse est copiée).
let fillLinkedIn = false;
let tab = null;
let offerId = null;
let frameQuestions = []; // { frameId, key, label }
// Ouvert dans un onglet à l'installation (docs/71 §3) plutôt que depuis l'icône.
const welcomeTab = new URLSearchParams(location.search).has("accueil");

function say(id, text) {
  $(id).textContent = text || "";
  show(id, Boolean(text));
}

// --- Les états de la fenêtre ------------------------------------------------------------

const STATES = ["signin", "linked", "authorize-state", "idle", "annonce", "alerte", "gmail", "settings", "main", "job-room", "codes"];
// Sans pastille : ces états ne parlent pas de la page ouverte.
const NO_SITE = new Set(["signin", "linked", "authorize-state", "settings"]);
let current = null;
let beforeSettings = null;

function view(id) {
  for (const state of STATES) show(state, state === id);
  if (id !== "settings") beforeSettings = null;
  current = id;
  $("gear").setAttribute("aria-expanded", String(id === "settings"));
  show("site", !NO_SITE.has(id) && Boolean($("site-name").textContent));
}

// La pastille : l'hôte de l'onglet ouvert (« www.google.ch »), ou un libellé donné.
function setSite(url, label) {
  let host = "";
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") host = parsed.hostname;
  } catch {
    host = "";
  }
  $("site-name").textContent = label || host;
}

// La roue dentée : les réglages, et retour à l'état d'avant au second clic.
function toggleSettings() {
  if (current === "settings") {
    view(beforeSettings || (config.token ? "idle" : "signin"));
    return;
  }
  const back = current;
  openSettings();
  beforeSettings = back;
}

function openSettings() {
  const linked = Boolean(config.token);
  $("base").value = config.base;
  $("token").value = "";
  say("setup-error", "");
  say("setup-message", "");
  show("fields", !linked);
  show("link", !linked);
  show("unlink", linked);
  show("linkedin-row", linked);
  show("gmail-row", linked);
  $("linkedin-fill").checked = fillLinkedIn;
  say("linked-to", linked ? `Reliée à ${config.base}.` : "");
  view("settings");
}

function origin(value) {
  const url = new URL(value.trim().includes("://") ? value.trim() : `https://${value.trim()}`);
  return url.origin;
}

async function call(path, options = {}) {
  const response = await fetch(config.base + path, {
    ...options,
    headers: { Authorization: `Bearer ${config.token}`, ...(options.body ? { "Content-Type": "application/json" } : {}) },
  });
  if (response.status === 401) throw new Error("Jeton refusé : relie à nouveau l'extension.");
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const error = new Error(typeof detail?.detail === "string" ? detail.detail : `Erreur ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response;
}

async function base64(path) {
  const buffer = await (await call(path)).arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

function offline(error) {
  return error.message === "Failed to fetch" || error.name === "TypeError";
}

// --- Relier ------------------------------------------------------------------------------

// « Se connecter à jobA1 » : l'adresse connue, on relie par la page de la plateforme ; sinon
// les réglages, pour la donner.
function signIn() {
  say("signin-error", "");
  say("signin-message", "");
  if (!config.base) {
    openSettings();
    beforeSettings = "signin";
    say("setup-message", "Indique l'adresse de ta plateforme jobA1, puis « Relier ».");
    $("base").focus();
    return;
  }
  link(config.base, "", "signin");
}

// « Relier » (réglages) : par la page de la plateforme (docs/71 §4), ou avec un jeton collé.
function linkFromSettings() {
  say("setup-error", "");
  say("setup-message", "");
  link($("base").value, $("token").value.trim(), "setup");
}

// La demande d'accès part dans le geste même du clic (Firefox l'exige) : pas d'attente avant.
async function link(baseValue, token, where) {
  try {
    const base = origin(baseValue);
    if (token && !token.startsWith("jbx_")) throw new Error("Le jeton commence par « jbx_ ».");
    config = { base, token };
    // Enregistré en même temps que la demande d'autorisation : Firefox ferme souvent le
    // panneau pendant cette demande, et on reprend à la réouverture (« Autoriser l'accès »).
    const saving = token ? chrome.storage.local.set(config) : chrome.storage.local.set({ base }).then(() => chrome.storage.local.remove("token"));
    const asking = requestAccess();
    await saving;
    const granted = await asking;
    if (token) await connect(granted);
    else await linkByPage(granted, where);
  } catch (error) {
    say(`${where}-error`, offline(error) ? "Plateforme injoignable à cette adresse." : error.message);
  }
}

// La page « Relier ce navigateur » de la plateforme s'ouvre ; le fond y lit le jeton.
async function linkByPage(granted, where) {
  if (!granted) throw new Error("Autorisation refusée : l'extension ne peut pas joindre ta plateforme.");
  const answer = await chrome.runtime.sendMessage({ type: "link", base: config.base });
  if (!answer?.ok) throw new Error(answer?.error || "La page de ta plateforme ne s'est pas ouverte.");
  say(
    `${where}-message`,
    "Ta plateforme s'est ouverte dans un nouvel onglet : clique sur « Relier ce navigateur ».",
  );
}

// Autorisation par hôte, sans le port : Firefox refuse un port dans le motif demandé, et un
// motif sans port couvre tous les ports, dans Firefox comme dans Chrome.
function accessPattern() {
  const url = new URL(config.base);
  return `${url.protocol}//${url.hostname}/*`;
}

function requestAccess() {
  return chrome.permissions.request({ origins: [accessPattern()] });
}

async function connect(granted) {
  if (!granted) throw new Error("Autorisation refusée : l'extension ne peut pas joindre ta plateforme.");
  await call("/api/extension/me");
  await start();
}

async function authorize() {
  say("authorize-error", "");
  try {
    const granted = await requestAccess();
    if (config.token) await connect(granted);
    else await linkByPage(granted, "signin").then(() => view("signin"));
  } catch (error) {
    say("authorize-error", offline(error) ? "Plateforme injoignable à cette adresse." : error.message);
  }
}

async function permitted() {
  return chrome.permissions.contains({ origins: [accessPattern()] });
}

// Délier : le jeton est oublié ici ; il se révoque dans Réglages › Connexions de jobA1.
async function unlink() {
  await chrome.storage.local.remove("token");
  config = { base: config.base, token: "" };
  view("signin");
}

function openApp(event) {
  event.preventDefault();
  if (config.base) chrome.tabs.create({ url: config.base });
  window.close();
}

// --- La page ouverte ----------------------------------------------------------------------

// Un formulaire à remplir ? Seulement le nombre de champs, dans chaque cadre ; rien d'autre
// n'est lu, et rien ne part (docs/142 §2).
function countFields() {
  return document.querySelectorAll("input:not([type=hidden]):not([type=search]), textarea, select").length;
}

async function hasForm() {
  try {
    const results = await chrome.scripting.executeScript({ target: { tabId: tab.id, allFrames: true }, func: countFields });
    return results.some(({ result }) => Number(result) >= 3);
  } catch {
    // Page interdite aux extensions (boutique, réglages du navigateur).
    return false;
  }
}

async function start() {
  if (!config.token) {
    view("signin");
    return;
  }
  if (!(await permitted())) {
    view("authorize-state");
    return;
  }
  tab = await targetTab();
  setSite(tab?.url);
  if (isCodePage(tab?.url)) {
    await startCodes();
    return;
  }
  if (isJobRoom(tab?.url)) {
    view("job-room");
    await startJobRoom();
    return;
  }
  if (!tab?.url?.startsWith("http")) {
    view("idle");
    return;
  }
  if (isGmail(tab.url)) {
    await startGmail();
    return;
  }
  const alertSite = alertSiteOf(tab.url);
  if (alertSite && (await startAlert(alertSite))) return;
  let found;
  try {
    found = await (await call(`/api/extension/match?url=${encodeURIComponent(tab.url)}`)).json();
  } catch (error) {
    view("idle");
    say("idle-error", offline(error) ? "Plateforme injoignable." : error.message);
    return;
  }
  const ad = await probeAnnonce();
  const form = (found.offer || found.choices.length) && (await hasForm());
  // Le formulaire de candidature d'une offre connue l'emporte ; sinon l'annonce de la page.
  if (found.offer && (form || !ad)) {
    offerId = found.offer.id;
    renderOffer(found.offer);
    $("fill").disabled = false;
    view("main");
    return;
  }
  if (ad) {
    showAnnonce(ad);
    return;
  }
  if (found.choices.length && form) {
    renderChoices(found.choices);
    view("main");
    return;
  }
  view("idle");
}

// --- Le formulaire « Créer une alerte » (docs/142 §4) -------------------------------------

let alertSlug = null;
let alertAddress = null;
// Le libellé de la pastille : « jobup.ch · Créer une alerte ».
const ALERT_PILL = { jobup: "jobup.ch", jobsch: "jobs.ch", linkedin: "linkedin.com" };

function alertSiteOf(url) {
  try {
    const { protocol, hostname } = new URL(url);
    if (protocol !== "https:") return null;
    const rules = globalThis.jobA1AlertSelectors || {};
    return Object.keys(rules).find((slug) => rules[slug].hosts.includes(hostname)) ?? null;
  } catch {
    return null;
  }
}

async function alertForm(rules, address) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: globalThis.jobA1AlertForm, args: [rules, address] });
    return { form: result?.form === true, filled: result?.filled === true };
  } catch {
    return { form: false, filled: false };
  }
}

async function copyAddress() {
  try {
    await navigator.clipboard.writeText(alertAddress);
    $("al-copy").textContent = "Copiée";
    return true;
  } catch {
    return false;
  }
}

function alertText(title, text) {
  $("al-title").textContent = title;
  $("al-text").textContent = text;
}

// Le formulaire est ouvert : l'adresse jobA1 dans son champ e-mail (sauf LinkedIn, par défaut),
// sinon le repli « Copier ». Faux : pas de formulaire d'alerte, on continue.
async function startAlert(slug) {
  const rules = globalThis.jobA1AlertSelectors[slug];
  if (!(await alertForm(rules, null)).form) return false;
  alertSlug = slug;
  setSite(tab.url, `${ALERT_PILL[slug]} · Créer une alerte`);
  show("al-todo");
  show("al-done", false);
  $("al-copy").textContent = "Copier";
  view("alerte");
  try {
    ({ address: alertAddress } = await (await call("/api/extension/alerts")).json());
  } catch (error) {
    if (error.status === 404) say("al-error", "Mets ta plateforme jobA1 à jour pour remplir les alertes.");
    else say("al-error", offline(error) ? "Plateforme injoignable." : error.message);
    alertText("Adresse jobA1", "");
    show("al-mark", false);
    show("al-row", false);
    show("al-hint", false);
    return true;
  }
  if (!alertAddress) {
    alertText("Pas encore d’adresse jobA1", "Ouvre Alertes dans jobA1 : ton adresse y est créée.");
    show("al-mark", false);
    show("al-row", false);
    show("al-hint", false);
    return true;
  }
  $("al-address").textContent = alertAddress;
  show("al-row");
  const allowed = slug !== "linkedin" || fillLinkedIn;
  const { filled } = allowed ? await alertForm(rules, alertAddress) : { filled: false };
  // La coche seulement quand c'est fait (rempli ou copié).
  show("al-mark", filled);
  if (filled) {
    alertText("Adresse jobA1 remplie", `Vérifie le formulaire sur ${rules.name}, puis valide-le toi-même.`);
    show("al-hint");
  } else if (!allowed) {
    // LinkedIn, par défaut : l'adresse copiée, à coller.
    const copied = await copyAddress();
    show("al-mark", copied);
    alertText(
      copied ? "Adresse jobA1 copiée" : "Copie ton adresse jobA1",
      `Colle-la dans le champ e-mail du formulaire ${rules.name}, puis valide-le toi-même.`,
    );
    show("al-hint", false);
  } else {
    alertText("Copie ton adresse jobA1", `Le champ e-mail du formulaire ${rules.name} n’a pas été trouvé.`);
    show("al-hint");
  }
  return true;
}

// « J'ai créé l'alerte » : comme le bouton de l'assistant des alertes.
async function alertCreated() {
  say("al-error", "");
  $("al-created").disabled = true;
  try {
    await call(`/api/extension/alerts/${alertSlug}`, { method: "PUT" });
    $("al-done-title").textContent = `Alerte ${globalThis.jobA1AlertSelectors[alertSlug].name} enregistrée`;
    show("al-todo", false);
    show("al-done");
  } catch (error) {
    say("al-error", offline(error) ? "Plateforme injoignable." : error.message);
  } finally {
    $("al-created").disabled = false;
  }
}

// --- Transfert Gmail (docs/142 §5) ---------------------------------------------------------
// Un parcours guidé : l'adresse de transfert, le code de Gmail, puis un filtre pour les seules
// alertes des trois sites. Jamais de transfert de tout le courrier. L'extension ne lit rien dans
// Gmail : elle ouvre ses réglages dans un onglet, la personne fait elle-même chaque étape.

const GMAIL_STEPS = ["gm-start", "gm-address", "gm-code", "gm-filter", "gm-ready", "gm-warning"];
const CODE_POLL_MS = 5000;
const CODE_WAIT_MS = 2 * 60 * 1000;
let gmailAddress = null;
let codeTimer = null;

function isGmail(url) {
  try {
    const { protocol, hostname } = new URL(url);
    return protocol === "https:" && hostname === "mail.google.com";
  } catch {
    return false;
  }
}

function gmailStep(id) {
  for (const step of GMAIL_STEPS) show(step, step === id);
  clearTimeout(codeTimer);
  if (["gm-address", "gm-code", "gm-filter", "gm-ready"].includes(id)) chrome.storage.local.set({ gmailStep: id });
  if (id === "gm-code") waitForCode();
}

async function copyText(value, button, done = "Copié") {
  try {
    await navigator.clipboard.writeText(value);
    $(button).textContent = done;
  } catch {
    // Le presse-papiers refusé : le texte reste affiché, à sélectionner.
  }
}

// L'adresse jobA1 et un éventuel « Vérifie ton filtre Gmail » encore non vu.
async function startGmail() {
  setSite(tab?.url || "https://mail.google.com/", "mail.google.com · Transfert");
  view("gmail");
  say("gm-error", "");
  $("gm-copy-address").textContent = "Copier";
  $("gm-copy-query").textContent = "Copier";
  const { gmailStep: saved, gmailWarningSeen } = await chrome.storage.local.get(["gmailStep", "gmailWarningSeen"]);
  let warning = null;
  try {
    const body = await (await call("/api/extension/alerts")).json();
    gmailAddress = body.address;
    warning = body.filter_warning_at;
  } catch (error) {
    gmailAddress = null;
    say("gm-error", error.status === 404 ? "Mets ta plateforme jobA1 à jour pour transférer tes alertes." : offline(error) ? "Plateforme injoignable." : error.message);
  }
  $("gm-address-value").textContent = gmailAddress || "";
  $("gm-forward-to").textContent = gmailAddress || "ton adresse jobA1";
  $("gm-added").disabled = !gmailAddress;
  if (warning && (!gmailWarningSeen || warning > gmailWarningSeen)) {
    chrome.storage.local.set({ gmailWarningSeen: warning });
    gmailStep("gm-warning");
    return;
  }
  if (!gmailAddress) {
    gmailStep("gm-address");
    return;
  }
  gmailStep(GMAIL_STEPS.includes(saved) ? saved : "gm-start");
}

function showCode(code) {
  $("gm-code-title").textContent = "Colle ce code dans Gmail";
  $("gm-code-text").textContent = "Gmail l’a envoyé à ton adresse jobA1. jobA1 ne lit rien d’autre de cet e-mail.";
  $("gm-code-value").textContent = code.replace(/(\d{3})(?=\d)/g, "$1 ");
  $("gm-code-note").textContent = "Dans Gmail, colle-le sous « Transfert », puis clique sur « Valider ».";
  show("gm-wait", false);
  show("gm-code-row");
  $("gm-validated").disabled = false;
}

// Le code arrive dans la boîte jobA1 : le relevé rapide, puis une question toutes les 5 s.
async function waitForCode() {
  $("gm-code-title").textContent = "Le code de Gmail";
  $("gm-code-text").textContent = "Gmail envoie un code de confirmation à ton adresse jobA1. Il s’affichera ici.";
  $("gm-code-note").textContent = "Rien après deux minutes ? Vérifie l’adresse collée à l’étape 1.";
  $("gm-copy-code").textContent = "Copier";
  show("gm-wait");
  show("gm-code-row", false);
  $("gm-validated").disabled = true;
  const until = Date.now() + CODE_WAIT_MS;
  try {
    await call("/api/extension/codes/expect", { method: "POST" });
  } catch {
    // Le relevé rapide refusé (trop souvent) : la collecte habituelle le trouvera.
  }
  const poll = async () => {
    if (current !== "gmail" || $("gm-code").hidden) return;
    try {
      const { code } = await (await call("/api/extension/codes?site=gmail")).json();
      if (code) {
        showCode(code.code);
        return;
      }
    } catch {
      // Injoignable un instant : on redemande.
    }
    // Passé deux minutes, la personne peut continuer (code déjà validé, ou recopié ailleurs).
    if (Date.now() > until) $("gm-validated").disabled = false;
    codeTimer = setTimeout(poll, CODE_POLL_MS);
  };
  await poll();
}

function gmailReady() {
  chrome.storage.local.set({ gmailStep: "gm-ready" });
  gmailStep("gm-ready");
}

// --- Envoyer une annonce (docs/142 §3) ---------------------------------------------------

let annonce = null; // l'annonce lue au clic sur « Envoyer », gardée pour « C'est bien cette offre ? »
let knownId = null;

// À l'ouverture : le titre, l'entreprise et le lieu seulement, pour la carte. Rien ne part.
async function probeAnnonce() {
  try {
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: globalThis.jobA1Annonce, args: [false] });
    return result && typeof result.title === "string" ? result : null;
  } catch {
    return null;
  }
}

function showAnnonce(ad) {
  annonce = null;
  knownId = null;
  $("an-title").textContent = ad.title || tab.title || "";
  $("an-meta").textContent = [ad.company, ad.location].filter(Boolean).join(" · ");
  show("an-meta", Boolean($("an-meta").textContent));
  show("an-idle");
  show("an-confirm", false);
  show("an-done", false);
  view("annonce");
}

const text300 = (v) => (typeof v === "string" ? v.slice(0, 300) : "");

// « Envoyer à jobA1 » : seulement maintenant, le texte de l'annonce est lu, puis envoyé.
async function readAnnonce() {
  const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: globalThis.jobA1Annonce, args: [true] });
  if (!result || typeof result.text !== "string" || !result.text.trim()) {
    throw new Error("Je ne trouve pas le texte de l'annonce : ouvre l'annonce elle-même, puis réessaie.");
  }
  const page = { url: String(result.url || tab.url).slice(0, 2000), text: result.text.slice(0, 40000) };
  // Sans balisage, le titre et l'entreprise sont lus par jobA1 dans le texte.
  if (result.kind !== "text") Object.assign(page, { title: text300(result.title), company: text300(result.company), location: text300(result.location) });
  return page;
}

function frenchDay(iso) {
  const date = new Date(iso);
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return date.toLocaleDateString("fr-CH", { day: "numeric", month: "long", ...(sameYear ? {} : { year: "numeric" }) });
}

function noteText(answer) {
  return answer.score == null ? null : `${answer.score}, ${answer.label}`;
}

function showDone(answer) {
  const note = noteText(answer);
  let title;
  let text;
  if (answer.outcome === "added") {
    title = "Offre ajoutée";
    text = note
      ? `Note : ${note}. Elle t’attend dans Candidatures › Offres.`
      : "Elle t’attend dans Candidatures › Offres. Sa note arrive dans un moment.";
  } else if (answer.filled.includes("description")) {
    title = "Annonce ajoutée à ton offre";
    text = note ? `Note refaite sur l’annonce complète : ${note}.` : "Sa note sera refaite dans un moment.";
  } else {
    title = "Offre déjà complète";
    text = note ? `Ton offre avait déjà le texte de l’annonce. Note : ${note}.` : "Ton offre avait déjà le texte de l’annonce.";
  }
  $("an-done-title").textContent = title;
  $("an-done-text").textContent = text;
  $("an-open").href = `${config.base}/candidatures/offres?offre=${answer.offer_id}`;
  show("an-idle", false);
  show("an-confirm", false);
  show("an-done");
}

function showConfirm(known) {
  knownId = known.id;
  const who = known.company ? `${known.title} chez ${known.company}` : known.title;
  const from = known.site ? ` par une alerte ${known.site}` : "";
  $("an-known").textContent = `${who}, reçue le ${frenchDay(known.received_at)}${from}.`;
  show("an-idle", false);
  show("an-confirm");
}

async function sendAnnonce(choice = null) {
  const button = choice === null ? $("an-send") : choice === "fill" ? $("an-yes") : $("an-new");
  const errorId = choice === null ? "an-error" : "an-confirm-error";
  const label = button.textContent;
  say(errorId, "");
  for (const b of ["an-send", "an-yes", "an-new"]) $(b).disabled = true;
  button.textContent = "Envoi…";
  try {
    annonce ??= await readAnnonce();
    const body = { ...annonce, ...(choice ? { choice, offer_id: choice === "fill" ? knownId : null } : {}) };
    const answer = await (await call("/api/extension/announce", { method: "POST", body: JSON.stringify(body) })).json();
    if (answer.outcome === "confirm") showConfirm(answer.known);
    else showDone(answer);
  } catch (error) {
    // Plateforme d'avant la 0.60 (docs/71 §5).
    if (error.status === 404) say(errorId, "Mets ta plateforme jobA1 à jour pour envoyer une annonce.");
    else say(errorId, offline(error) ? "Plateforme injoignable." : error.message);
  } finally {
    for (const b of ["an-send", "an-yes", "an-new"]) $(b).disabled = false;
    button.textContent = label;
  }
}

// --- Candidature -------------------------------------------------------------------------

function renderOffer(offer) {
  const box = $("offer");
  box.replaceChildren();
  if (!offer) return;
  const title = document.createElement("div");
  title.className = "offer-title";
  title.textContent = offer.title;
  const company = document.createElement("div");
  company.className = "offer-company";
  company.textContent = offer.company || "";
  box.append(title, company);
  if (offer.applied) {
    const note = document.createElement("div");
    note.className = "applied";
    note.textContent = "Candidature déjà enregistrée dans ton Suivi.";
    box.append(note);
  }
}



function renderChoices(choices) {
  const select = $("choices");
  select.replaceChildren();
  const hint = document.createElement("option");
  hint.textContent = "Quelle candidature ?";
  hint.value = "";
  select.append(hint);
  for (const choice of choices) {
    const option = document.createElement("option");
    option.value = String(choice.id);
    option.textContent = `${choice.title} — ${choice.company || "?"}`;
    select.append(option);
  }
  show("choices");
  $("fill").disabled = true;
}

// Onglet à remplir : celui d'où le panneau est ouvert. `?onglet=<début de l'adresse>` désigne
// un autre onglet quand popup.html est ouvert dans un onglet (tests automatiques, dépannage).
async function targetTab() {
  const wanted = new URLSearchParams(location.search).get("onglet");
  if (wanted) {
    const tabs = await chrome.tabs.query({});
    const found = tabs.find((t) => t.url?.startsWith(wanted));
    if (found) return found;
  }
  const [active] = await chrome.tabs.query({ active: true, currentWindow: true });
  return active;
}


// --- Remplir -----------------------------------------------------------------------------

function line(text, className) {
  const p = document.createElement("p");
  p.textContent = text;
  if (className) p.className = className;
  return p;
}

async function fill() {
  say("error", "");
  $("fill").disabled = true;
  $("fill").textContent = "Remplissage…";
  try {
    const data = await (await call(`/api/extension/offers/${offerId}`)).json();
    const files = {};
    if (data.has_cv) files.cv = { name: data.cv_filename, base64: await base64(`/api/extension/offers/${offerId}/cv.pdf`) };
    if (data.has_letter) {
      files.letter = { name: data.letter_filename, base64: await base64(`/api/extension/offers/${offerId}/letter.pdf`) };
    }
    const payload = { identity: data.identity, letterText: data.letter_text, files };
    const target = { tabId: tab.id, allFrames: true };
    await chrome.scripting.executeScript({ target, files: ["fill.js"] });
    const results = await chrome.scripting.executeScript({
      target,
      func: (input) => globalThis.jobbotFill.fill(input),
      args: [payload],
    });
    const filled = [];
    const todo = [];
    const frames = [];
    frameQuestions = [];
    for (const { frameId, result } of results) {
      if (!result) continue;
      filled.push(...result.filled);
      todo.push(...result.todo);
      frames.push(...result.frames);
      for (const q of result.questions) frameQuestions.push({ frameId, ...q });
    }
    renderReport([...new Set(filled)], [...new Set(todo)], [...new Set(frames)]);
    show("sent");
  } catch (error) {
    say("error", error.message);
  } finally {
    $("fill").disabled = false;
    $("fill").textContent = "Remplir à nouveau";
  }
}

function renderReport(filled, todo, frames) {
  const report = $("report");
  report.replaceChildren();
  report.append(
    line(filled.length ? `${filled.length} champ(s) rempli(s), encadrés en violet : ${filled.join(", ")}.` : "Aucun champ reconnu sur cette page.", filled.length ? "ok" : ""),
  );
  if (todo.length) report.append(line(`À remplir toi-même (en orange) : ${todo.join(", ")}.`, "todo"));
  report.append(line("Vérifie tout, puis envoie depuis le site."));
  show("report");

  const box = $("questions");
  box.replaceChildren();
  for (const q of frameQuestions) {
    const item = document.createElement("div");
    item.className = "question";
    const label = document.createElement("span");
    label.textContent = q.label;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "link";
    button.textContent = "Proposer une réponse";
    button.addEventListener("click", () => propose(q, button));
    item.append(label, button);
    box.append(item);
  }
  show("questions", frameQuestions.length > 0);

  const framesBox = $("frames");
  framesBox.replaceChildren();
  for (const url of frames.slice(0, 2)) {
    const p = line("Le formulaire est peut-être dans un cadre d'un autre site : ");
    const a = document.createElement("a");
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = "l'ouvrir dans un onglet";
    p.append(a, document.createTextNode(", puis clique à nouveau sur l'icône."));
    p.className = "hint";
    framesBox.append(p);
  }
  show("frames", frames.length > 0);
}

async function propose(question, button) {
  button.disabled = true;
  button.textContent = "Rédaction…";
  try {
    const { text } = await (
      await call("/api/extension/answer", {
        method: "POST",
        body: JSON.stringify({ offer_id: offerId, question: question.label }),
      })
    ).json();
    await chrome.scripting.executeScript({
      target: { tabId: tab.id, frameIds: [question.frameId] },
      func: (key, value) => globalThis.jobbotFill.setAnswer(key, value),
      args: [question.key, text],
    });
    button.textContent = "Réponse insérée : relis-la";
  } catch (error) {
    button.disabled = false;
    button.textContent = "Proposer une réponse";
    say("error", error.message);
  }
}

async function sent() {
  say("error", "");
  try {
    const result = await (
      await call(`/api/extension/offers/${offerId}/sent`, { method: "POST", body: JSON.stringify({ url: tab.url }) })
    ).json();
    say("message", `Candidature enregistrée dans ton Suivi (${result.orp_month}).`);
    show("sent", false);
  } catch (error) {
    say("error", error.message);
  }
}

// --- Job-Room (docs/70) ----------------------------------------------------------------

let declaring = null;

// --- Les codes des sites (docs/112) --------------------------------------------------------

// Les pages de connexion où un site demande le code envoyé à l'adresse jobA1.
const CODE_HOSTS = ["auth.jobup.ch", "auth.jobs.ch"];
const codeOrigins = () => CODE_HOSTS.map((host) => `https://${host}/*`);

function isCodePage(url) {
  try {
    const parsed = new URL(url);
    return CODE_HOSTS.includes(parsed.hostname) && /challenge|verif|code/i.test(parsed.pathname);
  } catch {
    return false;
  }
}

async function watchCode() {
  say("codes-message", "J'attends le code : il sera rempli ici dès qu'il arrive, puis « Continuer ».");
  show("codes-allow", false);
  const filled = await chrome.runtime.sendMessage({ type: "watch-code", tabId: tab.id, url: tab.url });
  say("codes-message", filled ? "Code rempli." : "Pas de code arrivé : recopie-le depuis la page Alertes de jobA1.");
}

async function startCodes() {
  view("codes");
  if (await chrome.permissions.contains({ origins: codeOrigins() })) await watchCode();
}

// L'accès aux pages du code, une fois : ensuite le code est rempli sans ouvrir le panneau.
async function allowCodes() {
  say("codes-error", "");
  const granted = await chrome.permissions.request({ origins: codeOrigins() });
  if (!granted) {
    say("codes-error", "Accès refusé : recopie le code depuis la page Alertes de jobA1.");
    return;
  }
  await watchCode();
}

function isJobRoom(url) {
  try {
    const { protocol, hostname } = new URL(url);
    return protocol === "https:" && (hostname === "job-room.ch" || hostname.endsWith(".job-room.ch"));
  } catch {
    return false;
  }
}

function frenchDate(iso) {
  const [year, month, day] = iso.split("-");
  return `${day}.${month}.${year}`;
}

function renderToDeclare(items) {
  const select = $("jr-choices");
  select.replaceChildren();
  for (const item of items) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = `${frenchDate(item.sent_at)} · ${item.company} — ${item.job_title}`;
    select.append(option);
  }
  declaring = items[0]?.id ?? null;
  // Coupé dans la liste s'il est long : en entier au survol.
  select.title = select.selectedOptions[0]?.textContent ?? "";
  show("jr-choices", items.length > 0);
  $("jr-fill").disabled = !declaring;
  if (!items.length) say("jr-message", "Tout est déclaré pour ce mois et le précédent.");
}

async function startJobRoom() {
  try {
    const { items } = await (await call("/api/extension/job-room")).json();
    renderToDeclare(items);
  } catch (error) {
    // Extension mise à jour par la boutique, plateforme d'avant la 0.57 (docs/71 §5).
    if (error.status === 404) say("jr-error", "Mets ta plateforme jobA1 à jour (0.57 ou plus) pour remplir Job-Room.");
    else say("jr-error", error.name === "TypeError" ? "Plateforme injoignable." : error.message);
  }
}

function copyRow(label, value) {
  const row = document.createElement("div");
  row.className = "copy-row todo";
  const text = document.createElement("span");
  text.textContent = value ? `${label} : ${value}` : label;
  row.append(text);
  if (value) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "link";
    button.textContent = "Copier";
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(value);
      button.textContent = "Copié";
    });
    row.append(button);
  }
  return row;
}

async function fillJobRoom() {
  say("jr-error", "");
  say("jr-message", "");
  $("jr-fill").disabled = true;
  $("jr-fill").textContent = "Remplissage…";
  try {
    const data = await (await call(`/api/extension/applications/${declaring}/job-room`)).json();
    // Dans la page elle-même (« MAIN ») : depuis l'espace isolé de l'extension, Firefox ne
    // laisse pas Job-Room (Angular) voir la saisie ; les champs restaient vides (docs/70,
    // complément 0.57.1). Le script ne reçoit que la candidature à saisir.
    const target = { tabId: tab.id };
    const [{ result: raw }] = await chrome.scripting.executeScript({
      target,
      world: "MAIN",
      func: globalThis.jobbotFillJobRoom,
      args: [data],
    });
    // Le rapport vient de la page : seulement des textes, en nombre borné.
    const text = (v) => (typeof v === "string" ? v.slice(0, 200) : "");
    const result = raw && {
      form: raw.form === true,
      filled: (Array.isArray(raw.filled) ? raw.filled : []).map(text).slice(0, 40),
      todo: (Array.isArray(raw.todo) ? raw.todo : []).slice(0, 40).map((t) => ({ label: text(t?.label), value: text(t?.value) })),
    };
    const report = $("jr-report");
    report.replaceChildren();
    if (!result?.form) {
      say("jr-message", "Ouvre dans Job-Room le formulaire pour saisir une recherche d'emploi, puis clique à nouveau.");
      show("jr-report", false);
      return;
    }
    report.append(line(`${result.filled.length} réponse(s) remplie(s), encadrées en violet.`, "ok"));
    if (result.todo.length) {
      report.append(line("À faire toi-même (en orange) :"));
      for (const item of result.todo) report.append(copyRow(item.label, item.value));
    }
    report.append(line("Vérifie tout, puis « Sauvegarder » dans Job-Room."));
    show("jr-report");
    show("jr-declared");
  } catch (error) {
    say("jr-error", error.message);
  } finally {
    $("jr-fill").disabled = !declaring;
    $("jr-fill").textContent = "Remplir à nouveau";
  }
}

async function declared() {
  say("jr-error", "");
  try {
    const { items } = await (await call(`/api/extension/applications/${declaring}/job-room`, { method: "PUT" })).json();
    show("jr-declared", false);
    show("jr-report", false);
    $("jr-fill").textContent = "Remplir dans Job-Room";
    renderToDeclare(items);
    if (items.length) say("jr-message", "Déclarée. Ouvre une nouvelle saisie dans Job-Room pour la suivante.");
  } catch (error) {
    say("jr-error", error.message);
  }
}

$("jr-fill").addEventListener("click", fillJobRoom);
$("jr-declared").addEventListener("click", declared);
$("jr-choices").addEventListener("change", (event) => {
  declaring = Number(event.target.value) || null;
  event.target.title = event.target.selectedOptions[0]?.textContent ?? "";
  $("jr-fill").disabled = !declaring;
  show("jr-declared", false);
  show("jr-report", false);
});


$("gear").addEventListener("click", toggleSettings);
$("an-send").addEventListener("click", () => sendAnnonce());
$("al-copy").addEventListener("click", copyAddress);
$("al-created").addEventListener("click", alertCreated);
$("gm-begin").addEventListener("click", () => gmailStep("gm-address"));
$("gm-added").addEventListener("click", () => gmailStep("gm-code"));
$("gm-validated").addEventListener("click", () => gmailStep("gm-filter"));
$("gm-filtered").addEventListener("click", gmailReady);
$("gm-review").addEventListener("click", () => gmailStep("gm-filter"));
$("gm-copy-address").addEventListener("click", () => copyText(gmailAddress, "gm-copy-address", "Copiée"));
$("gm-copy-code").addEventListener("click", () => copyText($("gm-code-value").textContent.replace(/\s/g, ""), "gm-copy-code"));
$("gm-copy-query").addEventListener("click", () => copyText($("gm-query").textContent, "gm-copy-query"));
$("gmail-row").addEventListener("click", () => startGmail());
$("linkedin-fill").addEventListener("change", (event) => {
  fillLinkedIn = event.target.checked;
  chrome.storage.local.set({ fillLinkedIn });
});
$("an-yes").addEventListener("click", () => sendAnnonce("fill"));
$("an-new").addEventListener("click", () => sendAnnonce("new"));
$("signin-go").addEventListener("click", signIn);
$("codes-allow").addEventListener("click", allowCodes);
$("link").addEventListener("click", linkFromSettings);
$("authorize").addEventListener("click", authorize);
$("unlink").addEventListener("click", unlink);
$("fill").addEventListener("click", fill);
$("sent").addEventListener("click", sent);
for (const a of document.querySelectorAll(".open-app")) a.addEventListener("click", openApp);
$("choices").addEventListener("change", (event) => {
  offerId = Number(event.target.value) || null;
  $("fill").disabled = !offerId;
});

// Le jeton arrive par le fond (liaison par la page de la plateforme).
chrome.storage.onChanged.addListener(async (changes, area) => {
  if (area !== "local" || !changes.token?.newValue) return;
  config = { base: changes.base?.newValue ?? config.base, token: changes.token.newValue };
  say("signin-message", "");
  say("setup-message", "");
  if (welcomeTab) view("linked");
  else await start();
});

if (welcomeTab) document.documentElement.classList.add("accueil");

export const ready = chrome.storage.local.get(["base", "token", "fillLinkedIn"]).then(async (stored) => {
  config = { base: stored.base || "", token: stored.token || "" };
  fillLinkedIn = stored.fillLinkedIn === true;
  if (welcomeTab) view(config.token ? "linked" : "signin");
  else await start();
});
