// La fenêtre de l'extension (extension/popup.html, popup.js ; maquette du 6.11.2026, boards Ext*,
// docs/142) : un état à la fois, la pastille du site, la roue dentée vers les réglages.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const root = resolve(__dirname, "../../extension");
const html = readFileSync(resolve(root, "popup.html"), "utf-8");
const css = readFileSync(resolve(root, "popup.css"), "utf-8");

type Tab = { id: number; url: string; title?: string };
type Frame = { frameId: number; result: unknown };

export interface Page {
  tab: Tab;
  stored: Record<string, string>;
  // Réponses de la plateforme, par début de chemin.
  api: Record<string, unknown | ((init?: RequestInit) => unknown)>;
  // Ce que rend chaque script injecté dans la page, par nom de fonction.
  scripts: Record<string, Frame[] | ((args: unknown[]) => Frame[])>;
  granted?: boolean;
}

export const calls: { path: string; init?: RequestInit }[] = [];
export const injected: { name: string; args: unknown[] }[] = [];

export async function openPopup(page: Page): Promise<Document> {
  document.documentElement.className = "";
  document.body.innerHTML = html.replace(/^[\s\S]*<body>|<script[\s\S]*$/g, "");
  calls.length = 0;
  injected.length = 0;
  const stored = { ...page.stored };
  const chrome = {
    storage: {
      local: {
        get: vi.fn(async (keys: string[]) => Object.fromEntries(keys.filter((k) => k in stored).map((k) => [k, stored[k]]))),
        set: vi.fn(async (values: Record<string, string>) => void Object.assign(stored, values)),
        remove: vi.fn(async (keys: string | string[]) => {
          for (const k of [keys].flat()) delete stored[k];
        }),
      },
      onChanged: { addListener: vi.fn() },
    },
    permissions: {
      contains: vi.fn(async () => page.granted ?? true),
      request: vi.fn(async () => true),
    },
    tabs: {
      query: vi.fn(async () => [page.tab]),
      create: vi.fn(),
    },
    runtime: { sendMessage: vi.fn(async () => ({ ok: true })) },
    scripting: {
      executeScript: vi.fn(async ({ func, args = [] }: { func?: { name: string }; args?: unknown[] }) => {
        const name = func?.name ?? "";
        injected.push({ name, args });
        const answer = page.scripts[name];
        if (typeof answer === "function") return answer(args);
        return answer ?? [{ frameId: 0, result: null }];
      }),
    },
  };
  // Le script de lecture de l'annonce (annonce.js) : seul son nom compte ici.
  Object.assign(globalThis, { chrome, jobA1Annonce: function jobA1Annonce() {}, jobA1AlertForm: function jobA1AlertForm() {} });
  // @ts-expect-error script de l'extension, sans types : les vrais sélecteurs des sites
  await import("../../extension/alert-selectors.js");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = url.replace(stored.base ?? "", "");
      calls.push({ path, init });
      const key = Object.keys(page.api)
        .sort((a, b) => b.length - a.length)
        .find((k) => path.startsWith(k));
      const entry = key ? page.api[key] : undefined;
      const value = typeof entry === "function" ? entry(init) : entry;
      if (value instanceof Response) return value;
      if (value === undefined) return new Response(JSON.stringify({ detail: "introuvable" }), { status: 404 });
      return new Response(JSON.stringify(value), { status: 200 });
    }),
  );
  // Un module neuf à chaque ouverture, comme un panneau qu'on rouvre.
  vi.resetModules();
  // @ts-expect-error script de l'extension, sans types
  const module = await import("../../extension/popup.js");
  await module.ready;
  await new Promise((r) => setTimeout(r, 0));
  return document;
}

export function visible(id: string): boolean {
  return document.getElementById(id)?.hidden === false;
}

export function shownState(): string {
  return [...document.querySelectorAll<HTMLElement>("section.state")].filter((s) => !s.hidden).map((s) => s.id).join(",");
}

const linked = { base: "https://joba1.exemple.ch", token: "jbx_essai" };
const nothingHere = { "/api/extension/match": { offer: null, choices: [] } };

afterEach(() => vi.unstubAllGlobals());

describe("fenêtre de l’extension", () => {
  beforeEach(() => vi.clearAllMocks());

  it("non connectée (ExtNonConnecte) : « Se connecter à jobA1 », sans pastille, rien demandé à la page", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: {}, api: {}, scripts: {} });
    expect(shownState()).toBe("signin");
    expect(document.querySelector("#signin h1")?.textContent).toBe("Relie l’extension à ton compte");
    expect(document.querySelectorAll("#signin .checks li")).toHaveLength(3);
    expect(document.querySelectorAll("#signin button.primary")).toHaveLength(1);
    expect(visible("site")).toBe(false);
    expect(calls).toHaveLength(0);
    expect(injected).toHaveLength(0);
  });

  it("« Se connecter » sans adresse connue : les réglages, l’adresse à donner", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: {}, api: {}, scripts: {} });
    document.getElementById("signin-go")!.click();
    expect(shownState()).toBe("settings");
    expect(document.getElementById("setup-message")?.textContent).toContain("adresse de ta plateforme");
    expect(document.getElementById("gear")?.getAttribute("aria-expanded")).toBe("true");
  });

  it("« Se connecter » avec l’adresse connue : la page « Relier ce navigateur » s’ouvre", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: { base: linked.base }, api: {}, scripts: {} });
    document.getElementById("signin-go")!.click();
    await new Promise((r) => setTimeout(r, 0));
    const { chrome } = globalThis as unknown as { chrome: { runtime: { sendMessage: ReturnType<typeof vi.fn> } } };
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({ type: "link", base: linked.base });
    expect(document.getElementById("signin-message")?.textContent).toContain("Relier ce navigateur");
  });

  it("autre site (ExtAutreSite) : « Rien à faire sur cette page », la pastille de l’hôte", async () => {
    await openPopup({
      tab: { id: 1, url: "https://www.google.ch/search?q=emploi" },
      stored: linked,
      api: { ...nothingHere, "/api/extension/match": { offer: null, choices: [{ id: 3, title: "Dev", company: "X", applied: false }] } },
      scripts: { countFields: [{ frameId: 0, result: 1 }] },
    });
    expect(shownState()).toBe("idle");
    expect(visible("site")).toBe(true);
    expect(document.getElementById("site-name")?.textContent).toBe("www.google.ch");
    expect(document.querySelector("#idle .title-md")?.textContent).toBe("Rien à faire sur cette page");
    // Seule l'adresse de l'onglet part, et seul le nombre de champs est lu.
    expect(calls.map((c) => c.path)).toEqual(["/api/extension/match?url=https%3A%2F%2Fwww.google.ch%2Fsearch%3Fq%3Demploi"]);
    expect(injected).toEqual([
      { name: "jobA1Annonce", args: [false] },
      { name: "countFields", args: [] },
    ]);
  });

  it("page du navigateur (about:, boutique) : rien à faire, sans pastille ni appel", async () => {
    await openPopup({ tab: { id: 1, url: "about:newtab" }, stored: linked, api: nothingHere, scripts: {} });
    expect(shownState()).toBe("idle");
    expect(visible("site")).toBe(false);
    expect(calls).toHaveLength(0);
  });

  it("formulaire de l’employeur reconnu : l’état d’avant la maquette, dans la nouvelle fenêtre", async () => {
    await openPopup({
      tab: { id: 1, url: "https://careers.exemple.ch/jobs/1/apply" },
      stored: linked,
      api: { "/api/extension/match": { offer: { id: 7, title: "DevOps", company: "Sword", applied: false }, choices: [] } },
      scripts: {},
    });
    expect(shownState()).toBe("main");
    expect(document.querySelector(".offer-title")?.textContent).toBe("DevOps");
    expect(document.querySelectorAll("#main button.primary")).toHaveLength(1);
  });

  it("accès à la plateforme pas encore donné : « Autoriser l’accès »", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: {}, scripts: {}, granted: false });
    expect(shownState()).toBe("authorize-state");
  });

  it("roue dentée : les réglages (délier), puis retour à l’état d’avant", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: nothingHere, scripts: {} });
    const gear = document.getElementById("gear")!;
    expect(gear.getAttribute("aria-label")).toBe("Réglages de l’extension");
    gear.click();
    expect(shownState()).toBe("settings");
    expect(visible("unlink")).toBe(true);
    expect(visible("link")).toBe(false);
    expect(document.getElementById("linked-to")?.textContent).toBe(`Reliée à ${linked.base}.`);
    gear.click();
    expect(shownState()).toBe("idle");
  });

  it("délier : le jeton est oublié, retour à « Relie l’extension »", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: nothingHere, scripts: {} });
    document.getElementById("gear")!.click();
    document.getElementById("unlink")!.click();
    await new Promise((r) => setTimeout(r, 0));
    expect(shownState()).toBe("signin");
  });
});

const posting = { kind: "posting", url: "https://careers.specitec.com/jobs/7", title: "DevOps Engineer", company: "Sword Services", location: "Genève" };
const annoncePage = (api: Page["api"]): Page => ({
  tab: { id: 1, url: "https://careers.specitec.com/jobs/7" },
  stored: linked,
  api: { ...nothingHere, ...api },
  scripts: {
    jobA1Annonce: (args) => [{ frameId: 0, result: args[0] ? { ...posting, text: "Tu automatises nos déploiements. ".repeat(10) } : posting }],
    countFields: [{ frameId: 0, result: 0 }],
  },
});
const click = async (id: string) => {
  document.getElementById(id)!.click();
  await new Promise((r) => setTimeout(r, 0));
  await new Promise((r) => setTimeout(r, 0));
};
const sentBodies = () => calls.filter((c) => c.init?.method === "POST").map((c) => JSON.parse(String(c.init!.body)));

describe("envoyer une annonce (ExtAnnonce)", () => {
  it("à l’ouverture : la carte de l’annonce, rien d’envoyé, seul le titre lu", async () => {
    await openPopup(annoncePage({}));
    expect(shownState()).toBe("annonce");
    expect(document.getElementById("site-name")?.textContent).toBe("careers.specitec.com");
    expect(document.getElementById("an-title")?.textContent).toBe("DevOps Engineer");
    expect(document.getElementById("an-meta")?.textContent).toBe("Sword Services · Genève");
    expect(document.getElementById("an-send")?.textContent).toBe("Envoyer à jobA1");
    expect(document.querySelectorAll("#an-idle button.primary")).toHaveLength(1);
    expect(injected.filter((i) => i.name === "jobA1Annonce")).toEqual([{ name: "jobA1Annonce", args: [false] }]);
    expect(sentBodies()).toEqual([]);
  });

  it("« Envoyer à jobA1 » : l’annonce lue maintenant, envoyée seule ; « Offre ajoutée » et sa note", async () => {
    await openPopup(annoncePage({ "/api/extension/announce": { outcome: "added", offer_id: 12, score: 76, label: "Proche", filled: [], known: null } }));
    await click("an-send");
    expect(injected.filter((i) => i.name === "jobA1Annonce").map((i) => i.args)).toEqual([[false], [true]]);
    const [body] = sentBodies();
    expect(Object.keys(body).sort()).toEqual(["company", "location", "text", "title", "url"]);
    expect(body.url).toBe("https://careers.specitec.com/jobs/7");
    expect(document.getElementById("an-done")?.hidden).toBe(false);
    expect(document.querySelector("#an-done [role=status]")).not.toBeNull();
    expect(document.getElementById("an-done-title")?.textContent).toBe("Offre ajoutée");
    expect(document.getElementById("an-done-text")?.textContent).toBe("Note : 76, Proche. Elle t’attend dans Candidatures › Offres.");
    expect(document.getElementById("an-open")?.getAttribute("href")).toBe(`${linked.base}/candidatures/offres?offre=12`);
  });

  it("même poste chez la même entreprise : « C’est bien cette offre ? », puis « Oui, compléter cette offre »", async () => {
    let n = 0;
    await openPopup(
      annoncePage({
        "/api/extension/announce": () =>
          n++ === 0
            ? { outcome: "confirm", known: { id: 5, title: "DevOps Engineer", company: "Sword Services", received_at: `${new Date().getFullYear()}-10-30T08:00:00Z`, site: "jobs.ch" }, filled: [] }
            : { outcome: "filled", offer_id: 5, score: 76, label: "Proche", filled: ["description"], known: null },
      }),
    );
    await click("an-send");
    expect(document.getElementById("an-confirm")?.hidden).toBe(false);
    expect(document.getElementById("an-known")?.textContent).toBe("DevOps Engineer chez Sword Services, reçue le 30 octobre par une alerte jobs.ch.");
    expect(document.getElementById("an-yes")?.textContent).toBe("Oui, compléter cette offre");
    expect(document.getElementById("an-new")?.textContent).toBe("Ajouter comme nouvelle offre");
    expect(document.querySelectorAll("#an-confirm button.primary")).toHaveLength(1);
    await click("an-yes");
    const bodies = sentBodies();
    expect(bodies[1]).toMatchObject({ choice: "fill", offer_id: 5 });
    // La page n'est lue qu'une fois.
    expect(injected.filter((i) => i.name === "jobA1Annonce" && i.args[0] === true)).toHaveLength(1);
    expect(document.getElementById("an-done-title")?.textContent).toBe("Annonce ajoutée à ton offre");
    expect(document.getElementById("an-done-text")?.textContent).toBe("Note refaite sur l’annonce complète : 76, Proche.");
  });

  it("« Ajouter comme nouvelle offre »", async () => {
    let n = 0;
    await openPopup(
      annoncePage({
        "/api/extension/announce": () =>
          n++ === 0
            ? { outcome: "confirm", known: { id: 5, title: "DevOps Engineer", company: null, received_at: "2025-10-30T08:00:00Z", site: null }, filled: [] }
            : { outcome: "added", offer_id: 13, score: null, label: null, filled: [], known: null },
      }),
    );
    await click("an-send");
    expect(document.getElementById("an-known")?.textContent).toBe("DevOps Engineer, reçue le 30 octobre 2025.");
    await click("an-new");
    expect(sentBodies()[1]).toMatchObject({ choice: "new", offer_id: null });
    expect(document.getElementById("an-done-text")?.textContent).toBe("Elle t’attend dans Candidatures › Offres. Sa note arrive dans un moment.");
  });

  it("30 envois par jour : le message du serveur", async () => {
    const limit = () => new Response(JSON.stringify({ detail: "30 annonces envoyées aujourd’hui : c’est le maximum. Réessaie demain." }), { status: 429 });
    await openPopup(annoncePage({ "/api/extension/announce": limit }));
    await click("an-send");
    expect(document.getElementById("an-error")?.textContent).toBe("30 annonces envoyées aujourd’hui : c’est le maximum. Réessaie demain.");
    expect(document.getElementById("an-error")?.getAttribute("role")).toBe("alert");
    expect(document.getElementById("an-send")?.hasAttribute("disabled")).toBe(false);
  });

  it("le formulaire de candidature d’une offre connue l’emporte sur l’annonce", async () => {
    const page = annoncePage({ "/api/extension/match": { offer: { id: 7, title: "DevOps", company: "Sword", applied: false }, choices: [] } });
    page.scripts.countFields = [{ frameId: 0, result: 6 }];
    await openPopup(page);
    expect(shownState()).toBe("main");
  });
});

const alertPage = (url: string, filled: boolean, stored: Record<string, string | boolean> = {}): Page => ({
  tab: { id: 1, url },
  stored: { ...linked, ...stored } as Record<string, string>,
  api: { ...nothingHere, "/api/extension/alerts": { address: "kevin.k3x@alertes.joba1.ch", todo: {} } },
  scripts: {
    jobA1AlertForm: (args) => [{ frameId: 0, result: { form: true, filled: args[1] ? filled : false } }],
  },
});
const alertCalls = () => injected.filter((i) => i.name === "jobA1AlertForm").map((i) => i.args[1]);

describe("formulaire d’alerte (ExtAlerte)", () => {
  let clipboard: string[];
  beforeEach(() => {
    clipboard = [];
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn(async (t: string) => void clipboard.push(t)) },
    });
  });

  it("jobup : « Adresse jobA1 remplie », la pastille du formulaire, rien d’autre demandé", async () => {
    await openPopup(alertPage("https://www.jobup.ch/fr/emplois/?term=devops", true));
    expect(shownState()).toBe("alerte");
    expect(document.getElementById("site-name")?.textContent).toBe("jobup.ch · Créer une alerte");
    expect(document.getElementById("al-title")?.textContent).toBe("Adresse jobA1 remplie");
    expect(document.getElementById("al-text")?.textContent).toBe("Vérifie le formulaire sur jobup, puis valide-le toi-même.");
    expect(document.getElementById("al-address")?.textContent).toBe("kevin.k3x@alertes.joba1.ch");
    expect(visible("al-hint")).toBe(true);
    // D'abord reconnaître le formulaire (sans adresse), puis remplir.
    expect(alertCalls()).toEqual([null, "kevin.k3x@alertes.joba1.ch"]);
    expect(calls.map((c) => c.path)).toEqual(["/api/extension/alerts"]);
    expect(document.querySelectorAll("#al-todo button.primary")).toHaveLength(1);
  });

  it("champ pas trouvé : le repli, l’adresse à copier et la phrase de la maquette", async () => {
    await openPopup(alertPage("https://www.jobs.ch/fr/offres-emplois/?term=devops", false));
    expect(document.getElementById("site-name")?.textContent).toBe("jobs.ch · Créer une alerte");
    expect(document.getElementById("al-title")?.textContent).toBe("Copie ton adresse jobA1");
    // Pas de coche : rien n'a été rempli.
    expect(visible("al-mark")).toBe(false);
    expect(document.getElementById("al-hint")?.textContent).toBe(
      "Le champ n’a pas été rempli ? Copie l’adresse et colle-la dans le champ e-mail du formulaire.",
    );
    await click("al-copy");
    expect(clipboard).toEqual(["kevin.k3x@alertes.joba1.ch"]);
    expect(document.getElementById("al-copy")?.textContent).toBe("Copiée");
  });

  it("LinkedIn, par défaut : rien n’est rempli, l’adresse est copiée", async () => {
    await openPopup(alertPage("https://www.linkedin.com/jobs/search/?keywords=devops", true));
    expect(alertCalls()).toEqual([null]);
    expect(clipboard).toEqual(["kevin.k3x@alertes.joba1.ch"]);
    expect(document.getElementById("al-title")?.textContent).toBe("Adresse jobA1 copiée");
    expect(document.getElementById("site-name")?.textContent).toBe("linkedin.com · Créer une alerte");
  });

  it("LinkedIn, avec le réglage : rempli comme les autres", async () => {
    await openPopup(alertPage("https://www.linkedin.com/jobs/search/?keywords=devops", true, { fillLinkedIn: true }));
    expect(alertCalls()).toEqual([null, "kevin.k3x@alertes.joba1.ch"]);
    expect(document.getElementById("al-title")?.textContent).toBe("Adresse jobA1 remplie");
  });

  it("le réglage LinkedIn, dans la roue dentée, gardé dans le navigateur", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: nothingHere, scripts: {} });
    document.getElementById("gear")!.click();
    const box = document.getElementById("linkedin-fill") as HTMLInputElement;
    expect(visible("linkedin-row")).toBe(true);
    expect(box.checked).toBe(false);
    box.click();
    const { chrome } = globalThis as unknown as { chrome: { storage: { local: { set: ReturnType<typeof vi.fn> } } } };
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ fillLinkedIn: true });
  });

  it("« J’ai créé l’alerte » : la route de l’assistant, « Alerte jobup enregistrée »", async () => {
    const page = alertPage("https://www.jobup.ch/fr/emplois/?term=devops", true);
    page.api["/api/extension/alerts/jobup"] = { site: "jobup", marked: 2 };
    await openPopup(page);
    await click("al-created");
    const put = calls.find((c) => c.init?.method === "PUT");
    expect(put?.path).toBe("/api/extension/alerts/jobup");
    expect(document.getElementById("al-done")?.getAttribute("role")).toBe("status");
    expect(document.getElementById("al-done-title")?.textContent).toBe("Alerte jobup enregistrée");
  });

  it("sur jobup sans fenêtre d’alerte ouverte : on continue (annonce, ou rien à faire)", async () => {
    const page = alertPage("https://www.jobup.ch/fr/emplois/", true);
    page.scripts.jobA1AlertForm = [{ frameId: 0, result: { form: false, filled: false } }];
    await openPopup(page);
    expect(shownState()).toBe("idle");
    expect(alertCalls()).toEqual([null]);
  });
});

describe("couleurs de la fenêtre", () => {
  it("les jetons de l’app, en clair et en sombre (prefers-color-scheme)", () => {
    const app = readFileSync(resolve(__dirname, "style.css"), "utf-8");
    const light = css.split("@media (prefers-color-scheme: dark)")[0]!;
    const dark = css.split("@media (prefers-color-scheme: dark)")[1]!;
    for (const name of ["--bg", "--surface", "--surface-muted", "--line", "--text", "--text-secondary", "--primary", "--primary-text", "--success", "--success-soft"]) {
      const inApp = app.match(new RegExp(`${name}: (#[0-9A-Fa-f]{6});`))![1];
      expect(light).toContain(`${name}: ${inApp};`);
      const darkApp = app.split("@media (prefers-color-scheme: dark)")[1]!.match(new RegExp(`${name}: (#[0-9A-Fa-f]{6});`))![1];
      expect(dark).toContain(`${name}: ${darkApp};`);
    }
    // Aucune couleur écrite en dur hors des jetons.
    const rules = css.replace(/:root\s*\{[^}]*\}/g, "");
    expect(rules.match(/#[0-9A-Fa-f]{3,6}\b/g) ?? []).toEqual([]);
  });

  it("une fenêtre de 360 × 480", () => {
    expect(css).toMatch(/width: 360px;\s*height: 480px;/);
  });
});

describe("icônes (maquette du 8 novembre, ExtAnnonce et ExtAlerte)", () => {
  it("les coches de 30 px, sans fond", () => {
    for (const mark of ["done-mark", "lead-mark"]) {
      const rule = css.match(new RegExp(`\\.${mark} \\{([^}]*)\\}`))![1]!;
      expect(rule).not.toContain("background");
      expect(rule).not.toContain("border-radius");
    }
    const marks = [...html.matchAll(/class="(?:done|lead)-mark"><svg width="(\d+)"/g)].map((m) => m[1]);
    expect(marks.length).toBeGreaterThan(0);
    expect(new Set(marks)).toEqual(new Set(["30"]));
  });
});

// --- Le transfert Gmail (docs/142 §5, écrans validés le 9.11.2026) : trois étapes, l'adresse puis
// le code de Gmail puis le filtre ; jamais de transfert global, rien n'est lu dans Gmail ;
// « Vérifie ton filtre Gmail » quand le serveur a supprimé un e-mail.

const ADDRESS = "kevin.k3x@alertes.joba1.ch";
const gmailTab = { id: 1, url: "https://mail.google.com/mail/u/0/#inbox" };

function gmailPage(stored: Record<string, string> = {}, extra: Page["api"] = {}): Page {
  return {
    tab: gmailTab,
    stored: { ...linked, ...stored },
    api: {
      "/api/extension/alerts": { address: ADDRESS, todo: {}, filter_warning_at: null },
      "/api/extension/codes/expect": { code: null },
      "/api/extension/codes": { code: null },
      ...extra,
    },
    scripts: {},
  };
}

const step = () => ["gm-start", "gm-address", "gm-code", "gm-filter", "gm-ready", "gm-warning"].filter(visible).join(",");
const text = (id: string) => document.getElementById(id)?.textContent;

async function gmClick(id: string) {
  document.getElementById(id)!.click();
  await new Promise((r) => setTimeout(r, 0));
  await new Promise((r) => setTimeout(r, 0));
}

let gmClipboard: string[];
function gmailClipboard() {
  gmClipboard = [];
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: vi.fn(async (t: string) => void gmClipboard.push(t)) },
  });
}

describe("transfert Gmail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    gmailClipboard();
  });

  it("sur Gmail : la présentation, la pastille, rien lu dans la page", async () => {
    await openPopup(gmailPage());
    expect(shownState()).toBe("gmail");
    expect(step()).toBe("gm-start");
    expect(text("site-name")).toBe("mail.google.com · Transfert");
    expect(document.querySelectorAll("#gm-start .checks li")).toHaveLength(3);
    expect(text("gm-start")).toContain("Jamais tout ton courrier.");
    // Aucun script dans Gmail : l'extension ne lit rien de la boîte.
    expect(injected).toHaveLength(0);
    expect(calls.map((c) => c.path)).toEqual(["/api/extension/alerts"]);
  });

  it("étape 1 : l’adresse jobA1 à copier, le lien vers les réglages de transfert", async () => {
    await openPopup(gmailPage());
    await gmClick("gm-begin");
    expect(step()).toBe("gm-address");
    expect(text("gm-address-value")).toBe(ADDRESS);
    await gmClick("gm-copy-address");
    expect(gmClipboard).toEqual([ADDRESS]);
    expect(text("gm-copy-address")).toBe("Copiée");
    const link = document.getElementById("gm-open-settings") as HTMLAnchorElement;
    expect(link.href).toBe("https://mail.google.com/mail/u/0/#settings/fwdandpop");
    expect(document.querySelectorAll("#gm-address button.primary")).toHaveLength(1);
  });

  it("étape 2 : en attente, puis le code de Gmail à copier", async () => {
    let arrived = false;
    const page = gmailPage({}, {
      "/api/extension/codes?site=gmail": () => ({ code: arrived ? { site: "gmail", code: "482913557", received_at: "2026-11-09T10:00:00Z" } : null }),
    });
    await openPopup(page);
    await gmClick("gm-begin");
    await gmClick("gm-added");
    expect(step()).toBe("gm-code");
    expect(visible("gm-wait")).toBe(true);
    expect((document.getElementById("gm-validated") as HTMLButtonElement).disabled).toBe(true);
    // Le relevé rapide est demandé, puis le code de Gmail seulement.
    expect(calls.some((c) => c.path === "/api/extension/codes/expect" && c.init?.method === "POST")).toBe(true);
    expect(calls.filter((c) => c.path.startsWith("/api/extension/codes?")).map((c) => c.path)).toEqual(["/api/extension/codes?site=gmail"]);

    arrived = true;
    // L'étape revient : la question est reposée tout de suite.
    await openPopup({ ...page, stored: { ...page.stored, gmailStep: "gm-code" } });
    expect(step()).toBe("gm-code");
    await new Promise((r) => setTimeout(r, 0));
    expect(visible("gm-code-row")).toBe(true);
    expect(text("gm-code-value")).toBe("482 913 557");
    expect(text("gm-code-title")).toBe("Colle ce code dans Gmail");
    expect((document.getElementById("gm-validated") as HTMLButtonElement).disabled).toBe(false);
    await gmClick("gm-copy-code");
    expect(gmClipboard).toEqual(["482913557"]);
  });

  it("étape 3 : le filtre des trois sites seulement, transféré à l’adresse jobA1", async () => {
    await openPopup(gmailPage({ gmailStep: "gm-filter" }));
    expect(step()).toBe("gm-filter");
    expect(text("gm-query")).toBe("jobup.ch OR jobs.ch OR linkedin.com");
    expect(text("gm-forward-to")).toBe(ADDRESS);
    await gmClick("gm-copy-query");
    expect(gmClipboard).toEqual(["jobup.ch OR jobs.ch OR linkedin.com"]);
    await gmClick("gm-filtered");
    expect(step()).toBe("gm-ready");
    expect(document.getElementById("gm-ready")?.getAttribute("role")).toBe("status");
    expect(text("gm-ready")).toContain("Transfert prêt");
  });

  it("« Vérifie ton filtre Gmail » : une fois, puis « Revoir le filtre » ramène à l’étape 3", async () => {
    const warned = { "/api/extension/alerts": { address: ADDRESS, todo: {}, filter_warning_at: "2026-11-09T08:00:00+00:00" } };
    await openPopup(gmailPage({ gmailStep: "gm-ready" }, warned));
    expect(step()).toBe("gm-warning");
    expect(document.getElementById("gm-warning")?.getAttribute("role")).toBe("alert");
    expect(text("gm-warning")).toContain("Un e-mail qui n’est pas une alerte est arrivé : vérifie ton filtre Gmail.");
    await gmClick("gm-review");
    expect(step()).toBe("gm-filter");
    // Déjà vu : la fois suivante, l'étape reprend.
    await openPopup(gmailPage({ gmailStep: "gm-ready", gmailWarningSeen: "2026-11-09T08:00:00+00:00" }, warned));
    expect(step()).toBe("gm-ready");
  });

  it("depuis la roue dentée, sur un autre site", async () => {
    await openPopup({ ...gmailPage(), tab: { id: 1, url: "https://www.google.ch/" }, api: { ...gmailPage().api, "/api/extension/match": { offer: null, choices: [] } } });
    expect(shownState()).toBe("idle");
    document.getElementById("gear")!.click();
    expect(visible("gmail-row")).toBe(true);
    await gmClick("gmail-row");
    expect(shownState()).toBe("gmail");
    expect(step()).toBe("gm-start");
  });
});
