// Panneau de l'extension (docs/25 §3.1) : candidature reconnue, « Remplir le formulaire »,
// questions libres, « J'ai envoyé ». Le jeton reste dans le stockage local du navigateur.
// Chrome, Edge, Brave et Firefox (128 et plus) : même code, API `chrome.*` à promesses.

const $ = (id) => document.getElementById(id);
const show = (id, on = true) => ($(id).hidden = !on);

let config = { base: "", token: "" };
let tab = null;
let offerId = null;
let frameQuestions = []; // { frameId, key, label }

function say(id, text) {
  $(id).textContent = text || "";
  show(id, Boolean(text));
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
    throw new Error(typeof detail?.detail === "string" ? detail.detail : `Erreur ${response.status}`);
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

// --- Relier ------------------------------------------------------------------------------

function setupError(error) {
  const offline = error.message === "Failed to fetch" || error.name === "TypeError";
  say("setup-error", offline ? "Plateforme injoignable à cette adresse." : error.message);
}

async function link() {
  say("setup-error", "");
  try {
    const base = origin($("base").value);
    const token = $("token").value.trim();
    if (!token.startsWith("jbx_")) throw new Error("Le jeton commence par « jbx_ ».");
    config = { base, token };
    // Enregistré en même temps que la demande d'autorisation : Firefox ferme souvent le
    // panneau pendant cette demande, et on reprend à la réouverture (« Autoriser l'accès »).
    // La demande part sans attendre : Firefox l'exige dans le geste même du clic.
    const saving = chrome.storage.local.set(config);
    const asking = requestAccess();
    await saving;
    await connect(await asking);
  } catch (error) {
    setupError(error);
  }
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
  say("setup-error", "");
  try {
    await connect(await requestAccess());
  } catch (error) {
    setupError(error);
  }
}

async function permitted() {
  return chrome.permissions.contains({ origins: [accessPattern()] });
}

function showAuthorize() {
  show("main", false);
  show("setup");
  $("base").value = config.base;
  $("token").value = config.token;
  show("fields", false);
  show("link", false);
  show("authorize");
}

async function unlink() {
  await chrome.storage.local.remove(["base", "token"]);
  config = { base: "", token: "" };
  show("main", false);
  show("authorize", false);
  show("fields");
  show("link");
  show("setup");
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

async function start() {
  if (!(await permitted())) {
    showAuthorize();
    return;
  }
  show("setup", false);
  show("main");
  tab = await targetTab();
  if (!tab?.url?.startsWith("http")) {
    say("error", "Ouvre le formulaire de l'employeur dans cet onglet, puis clique à nouveau sur l'icône.");
    return;
  }
  try {
    const found = await (await call(`/api/extension/match?url=${encodeURIComponent(tab.url)}`)).json();
    const select = $("choices");
    select.replaceChildren();
    if (found.offer) {
      offerId = found.offer.id;
      renderOffer(found.offer);
    } else if (found.choices.length) {
      const hint = document.createElement("option");
      hint.textContent = "Quelle candidature ?";
      hint.value = "";
      select.append(hint);
      for (const choice of found.choices) {
        const option = document.createElement("option");
        option.value = String(choice.id);
        option.textContent = `${choice.title} — ${choice.company || "?"}`;
        select.append(option);
      }
      show("choices");
    } else {
      say("message", "Aucune candidature en préparation : prépare d'abord la lettre ou le CV sur ta plateforme.");
    }
    $("fill").disabled = !offerId;
  } catch (error) {
    say("error", error.name === "TypeError" ? "Plateforme injoignable." : error.message);
  }
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

$("link").addEventListener("click", link);
$("authorize").addEventListener("click", authorize);
$("unlink").addEventListener("click", unlink);
$("fill").addEventListener("click", fill);
$("sent").addEventListener("click", sent);
$("choices").addEventListener("change", (event) => {
  offerId = Number(event.target.value) || null;
  $("fill").disabled = !offerId;
});

chrome.storage.local.get(["base", "token"]).then(async (stored) => {
  if (stored.base && stored.token) {
    config = { base: stored.base, token: stored.token };
    await start();
  } else {
    show("setup");
  }
});
