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
  api: Record<string, unknown>;
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
  Object.assign(globalThis, { chrome });
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = url.replace(stored.base ?? "", "");
      calls.push({ path, init });
      const key = Object.keys(page.api)
        .sort((a, b) => b.length - a.length)
        .find((k) => path.startsWith(k));
      const value = key ? page.api[key] : undefined;
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

describe("fenêtre de l'extension", () => {
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

  it("« Se connecter » sans adresse connue : les réglages, l'adresse à donner", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: {}, api: {}, scripts: {} });
    document.getElementById("signin-go")!.click();
    expect(shownState()).toBe("settings");
    expect(document.getElementById("setup-message")?.textContent).toContain("adresse de ta plateforme");
    expect(document.getElementById("gear")?.getAttribute("aria-expanded")).toBe("true");
  });

  it("« Se connecter » avec l'adresse connue : la page « Relier ce navigateur » s'ouvre", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: { base: linked.base }, api: {}, scripts: {} });
    document.getElementById("signin-go")!.click();
    await new Promise((r) => setTimeout(r, 0));
    const { chrome } = globalThis as unknown as { chrome: { runtime: { sendMessage: ReturnType<typeof vi.fn> } } };
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({ type: "link", base: linked.base });
    expect(document.getElementById("signin-message")?.textContent).toContain("Relier ce navigateur");
  });

  it("autre site (ExtAutreSite) : « Rien à faire sur cette page », la pastille de l'hôte", async () => {
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
    expect(injected.map((i) => i.name)).toEqual(["countFields"]);
  });

  it("page du navigateur (about:, boutique) : rien à faire, sans pastille ni appel", async () => {
    await openPopup({ tab: { id: 1, url: "about:newtab" }, stored: linked, api: nothingHere, scripts: {} });
    expect(shownState()).toBe("idle");
    expect(visible("site")).toBe(false);
    expect(calls).toHaveLength(0);
  });

  it("formulaire de l'employeur reconnu : l'état d'avant la maquette, dans la nouvelle fenêtre", async () => {
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

  it("accès à la plateforme pas encore donné : « Autoriser l'accès »", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: {}, scripts: {}, granted: false });
    expect(shownState()).toBe("authorize-state");
  });

  it("roue dentée : les réglages (délier), puis retour à l'état d'avant", async () => {
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

  it("délier : le jeton est oublié, retour à « Relie l'extension »", async () => {
    await openPopup({ tab: { id: 1, url: "https://www.google.ch/" }, stored: linked, api: nothingHere, scripts: {} });
    document.getElementById("gear")!.click();
    document.getElementById("unlink")!.click();
    await new Promise((r) => setTimeout(r, 0));
    expect(shownState()).toBe("signin");
  });
});

describe("couleurs de la fenêtre", () => {
  it("les jetons de l'app, en clair et en sombre (prefers-color-scheme)", () => {
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
