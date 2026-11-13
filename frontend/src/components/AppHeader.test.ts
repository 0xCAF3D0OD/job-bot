import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { computed, ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

const me = ref<{ authenticated: boolean } | null>({ authenticated: true });
const loggedIn = computed(() => Boolean(me.value?.authenticated));
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me, loggedIn }) }));
vi.mock("../composables/useJobsMemory", () => ({ useJobsMemory: () => ({ last: ref("/candidatures/offres"), menuLink: () => "/candidatures/offres" }) }));

import AppHeader from "./AppHeader.vue";

const view = { template: "<div />" };
const stubs = { GlobalSearch: true, NotificationBell: true, AccountMenu: true, BrandMark: true };

async function headerAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/aujourdhui", name: "today", component: view },
      { path: "/candidatures/offres", name: "offers", component: view, meta: { tab: "offres" } },
      { path: "/bilan", name: "insights", component: view, meta: { tab: "resultats" } },
      { path: "/compte", name: "account", component: view },
      { path: "/reglages", name: "settings", component: view },
      { path: "/profil", name: "profile", component: view },
      { path: "/a-propos", name: "about", component: view },
    ],
  });
  await router.push(path);
  return mount(AppHeader, { global: { plugins: [router], stubs } });
}

describe("L’en-tête (docs/139, maquettes strictes du 2026-11-02)", () => {
  it("Accueil : la variante logo et cloche, sans titre", async () => {
    const header = await headerAt("/aujourdhui");
    expect(header.attributes("data-variant")).toBe("home");
    expect(header.find("[data-test=header-title]").exists()).toBe(false);
  });

  it("une page d’onglet porte son titre, caché aux lecteurs d’écran (le h1 de la page reste)", async () => {
    for (const [path, title] of [["/candidatures/offres", "Candidatures"], ["/bilan", "Bilan"], ["/compte", "Compte"], ["/reglages", "Réglages"]]) {
      const header = await headerAt(path!);
      expect(header.attributes("data-variant"), path).toBe("tab");
      const shown = header.find("[data-test=header-title]");
      expect(shown.text()).toBe(title);
      expect(shown.attributes("aria-hidden")).toBe("true");
      expect(header.text()).not.toContain("Progresser");
    }
  });

  it("une fiche ouverte, une rubrique ou le Profil (PR 20) est une sous-page : pas de titre d’onglet", async () => {
    for (const path of ["/candidatures/offres?offre=12", "/reglages?rubrique=rythme", "/a-propos", "/profil"]) {
      const header = await headerAt(path);
      expect(header.attributes("data-variant"), path).toBe("page");
      expect(header.find("[data-test=header-title]").exists()).toBe(false);
    }
  });

  it("sans connexion, l’en-tête public", async () => {
    me.value = null;
    const header = await headerAt("/a-propos");
    expect(header.attributes("data-variant")).toBe("public");
    expect(header.classes()).not.toContain("has-burger");
    me.value = { authenticated: true };
  });
});

describe("Les règles de l’en-tête du téléphone", async () => {
  const { readFileSync } = await import("node:fs");
  const { resolve } = await import("node:path");
  const css = readFileSync(resolve(process.cwd(), "src/style.css"), "utf8");
  it("ni loupe ni menu du compte, la cloche sur l’Accueil seulement", () => {
    expect(css).toContain('.topbar.has-burger :is(.global-search, .account-menu) { display: none; }');
    expect(css).toContain('.topbar.has-burger:not([data-variant="home"]) .bell { display: none; }');
    expect(css).toMatch(/\.topbar\[data-variant="tab"\] \.topbar-title \{[^}]*font-size: var\(--title-tab\)/);
  });
});
