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
    local: { set: async (values: Record<string, unknown>) => void Object.assign(local, values) },
  },
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
