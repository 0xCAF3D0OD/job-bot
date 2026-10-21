// Fond de l'extension (extension/background.js, docs/71 §3, §4) : onglet d'accueil à
// l'installation, liaison par la page de la plateforme, jeton lu dans cet onglet seulement.
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

type Listener = (...args: unknown[]) => unknown;
const listeners: Record<string, Listener> = {};
const on = (name: string) => ({ addListener: (fn: Listener) => (listeners[name] = fn) });
let session: Record<string, unknown> = {};
const local: Record<string, unknown> = {};
const tabs = new Map<number, { id: number; url: string }>();
const executeScript = vi.fn();

const chrome = {
  runtime: { onInstalled: on("installed"), onMessage: on("message"), getURL: (p: string) => `moz-extension://x/${p}` },
  tabs: {
    onUpdated: on("updated"),
    onRemoved: on("removed"),
    create: vi.fn(async ({ url }: { url: string }) => {
      const tab = { id: tabs.size + 1, url };
      tabs.set(tab.id, tab);
      return tab;
    }),
    get: vi.fn(async (id: number) => {
      const tab = tabs.get(id);
      if (!tab) throw new Error("onglet fermé");
      return tab;
    }),
  },
  scripting: { executeScript },
  storage: {
    session: {
      get: async (key: string) => ({ [key]: session[key] }),
      set: async (values: Record<string, unknown>) => void Object.assign(session, values),
      remove: async (key: string) => void delete session[key],
    },
    local: {
      set: async (values: Record<string, unknown>) => void Object.assign(local, values),
      get: async (keys: string[]) => Object.fromEntries(keys.map((k) => [k, local[k]])),
    },
  },
  permissions: { contains: vi.fn(async () => true) },
};

beforeAll(async () => {
  Object.assign(globalThis, { chrome });
  // @ts-expect-error script de l'extension, sans types
  await import("../../extension/background.js");
});

beforeEach(() => {
  session = {};
  for (const key of Object.keys(local)) delete local[key];
  tabs.clear();
  vi.clearAllMocks();
});

async function link(base: string): Promise<unknown> {
  return new Promise((resolve) => listeners.message!({ type: "link", base }, {}, resolve));
}

describe("fond de l'extension", () => {
  it("ouvre l'onglet « Relier jobA1 » à l'installation seulement", () => {
    listeners.installed!({ reason: "update" });
    expect(chrome.tabs.create).not.toHaveBeenCalled();
    listeners.installed!({ reason: "install" });
    expect(chrome.tabs.create).toHaveBeenCalledWith({ url: "moz-extension://x/popup.html?accueil=1" });
  });

  it("ouvre la page de la plateforme, lit le jeton quand elle l'annonce, et le garde", async () => {
    expect(await link("https://joba1.exemple.ch/reglages")).toEqual({ ok: true });
    expect(chrome.tabs.create).toHaveBeenCalledWith({ url: "https://joba1.exemple.ch/extension/relier" });
    executeScript.mockResolvedValue([{ result: "jbx_secret" }]);
    tabs.get(1)!.url = "https://joba1.exemple.ch/extension/relier?etat=pret";
    await listeners.updated!(1, { url: tabs.get(1)!.url });
    expect(executeScript).toHaveBeenCalledWith(expect.objectContaining({ target: { tabId: 1 } }));
    expect(local).toEqual({ base: "https://joba1.exemple.ch", token: "jbx_secret" });
    expect(session.linking).toBeUndefined();
  });

  it("ne lit rien dans un autre onglet ni sur une autre adresse", async () => {
    await link("https://joba1.exemple.ch");
    executeScript.mockResolvedValue([{ result: "jbx_secret" }]);
    // L'onglet est parti ailleurs (un autre site) : rien n'est lu.
    tabs.get(1)!.url = "https://piege.exemple.com/extension/relier?etat=pret";
    await listeners.updated!(1, { url: tabs.get(1)!.url });
    // Un autre onglet que celui ouvert pour la liaison : ignoré.
    tabs.set(2, { id: 2, url: "https://joba1.exemple.ch/extension/relier?etat=pret" });
    await listeners.updated!(2, { url: tabs.get(2)!.url });
    expect(executeScript).not.toHaveBeenCalled();
    expect(local).toEqual({});
    // Onglet fermé : la liaison en cours est oubliée.
    await listeners.removed!(1);
    expect(session.linking).toBeUndefined();
  });

  it("ignore ce qui n'est pas un jeton", async () => {
    await link("https://joba1.exemple.ch");
    executeScript.mockResolvedValue([{ result: "autre chose" }]);
    tabs.get(1)!.url = "https://joba1.exemple.ch/extension/relier?etat=pret";
    await listeners.updated!(1, { url: tabs.get(1)!.url });
    expect(local).toEqual({});
  });
});

// Les codes des sites (docs/112) : sur la page qui demande le code, il est rempli dès qu'il
// arrive, puis « Continuer ».
type Codes = {
  codePage: (url: string) => { site: string } | null;
  fillCode: (code: string) => boolean;
  watchCode: (tabId: number, page: { site: string; host: string }, sleep?: () => Promise<void>) => Promise<boolean>;
};
const codes = () => (globalThis as unknown as { jobA1Codes: Codes }).jobA1Codes;

describe("les codes des sites", () => {
  const CHALLENGE = "https://auth.jobup.ch/u/email-identifier/challenge?state=x";

  it("reconnaît la page du code, et seulement elle", () => {
    expect(codes().codePage(CHALLENGE)?.site).toBe("jobup");
    expect(codes().codePage("https://auth.jobup.ch/u/login")).toBeNull();
    expect(codes().codePage("https://piege.exemple.com/challenge")).toBeNull();
  });

  it("remplit le champ du code et clique « Continuer »", () => {
    document.body.innerHTML =
      '<form><input name="email" type="hidden"><input id="code" name="code" type="text"><button type="submit">Continuer</button></form>';
    const clicked = vi.fn((event: Event) => event.preventDefault());
    document.querySelector("form")!.addEventListener("submit", clicked);
    const typed = vi.fn();
    document.querySelector("#code")!.addEventListener("input", typed);
    expect(codes().fillCode("482913")).toBe(true);
    expect((document.querySelector("#code") as HTMLInputElement).value).toBe("482913");
    expect(typed).toHaveBeenCalled();
    expect(clicked).toHaveBeenCalled();
    document.body.innerHTML = "<p>rien</p>";
    expect(codes().fillCode("482913")).toBe(false);
  });

  it("prévient la plateforme, attend le code, puis le remplit dans l'onglet", async () => {
    Object.assign(local, { base: "https://joba1.exemple.ch", token: "jbx_secret" });
    tabs.set(5, { id: 5, url: CHALLENGE });
    const answers = [{ code: null }, { code: { site: "jobup", code: "482913", received_at: "x" } }];
    const fetch = vi.fn(async (url: string, options: { method?: string }) => ({
      ok: true,
      json: async () => (options?.method === "POST" ? { code: null } : answers.shift()),
      url,
    }));
    Object.assign(globalThis, { fetch });
    const filled = await codes().watchCode(5, { site: "jobup", host: "auth.jobup.ch" }, async () => undefined);
    expect(filled).toBe(true);
    expect(fetch.mock.calls[0]).toEqual([
      "https://joba1.exemple.ch/api/extension/codes/expect",
      { method: "POST", headers: { Authorization: "Bearer jbx_secret" } },
    ]);
    expect(fetch.mock.calls[1]![0]).toBe("https://joba1.exemple.ch/api/extension/codes?site=jobup");
    expect(executeScript).toHaveBeenCalledWith(
      expect.objectContaining({ target: { tabId: 5 }, args: ["482913"] }),
    );
  });

  it("ne remplit rien si l'onglet a quitté la page du code", async () => {
    Object.assign(local, { base: "https://joba1.exemple.ch", token: "jbx_secret" });
    tabs.set(6, { id: 6, url: "https://ailleurs.exemple.com/" });
    Object.assign(globalThis, {
      fetch: vi.fn(async () => ({ ok: true, json: async () => ({ code: { site: "jobup", code: "482913" } }) })),
    });
    expect(await codes().watchCode(6, { site: "jobup", host: "auth.jobup.ch" }, async () => undefined)).toBe(false);
    expect(executeScript).not.toHaveBeenCalled();
  });
});
