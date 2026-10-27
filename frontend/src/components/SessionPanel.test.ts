// La connexion dans Réglages › Compte (docs/18 §1, 1.6.67) : une carte, une ligne par action.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import SessionPanel from "./SessionPanel.vue";

const PUT = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: vi.fn(), PUT: (...a: unknown[]) => PUT(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => {
  vi.resetAllMocks();
  useAuth().me.value = null;
});

const ME = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done" as const, demo: false };

async function mountPanel(over: Partial<typeof ME> = {}) {
  useAuth().me.value = { ...ME, ...over };
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/connexion", name: "login", component: { template: "<div />" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/reglages");
  const wrapper = mount(SessionPanel, { attachTo: document.body, global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("SessionPanel", () => {
  it("une carte : qui est connecté, puis l'accueil ; chaque action à droite de sa ligne", async () => {
    const { wrapper } = await mountPanel();
    const card = wrapper.find("[data-test=session-panel]");
    expect(card.classes()).toContain("setting-card");
    expect(wrapper.find("fieldset").exists()).toBe(false);
    const rows = card.findAll("[data-test=setting-row]");
    expect(rows.map((r) => r.find(".setting-row-title").text())).toEqual(["Connexion", "L'accueil"]);
    expect(rows[0]!.find(".setting-row-description").text()).toBe("Connecté en tant que camille.");
    expect(rows[0]!.find(".setting-row-control [data-test=logout-all]").classes()).toEqual(["secondary", "small"]);
    expect(rows[1]!.find(".setting-row-control [data-test=welcome-again]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("se déconnecter partout : confirmé sous la ligne, puis la page de connexion", async () => {
    POST.mockResolvedValue({});
    const { wrapper, router } = await mountPanel();
    await wrapper.find("[data-test=logout-all]").trigger("click");
    expect(wrapper.find("[data-test=logout-all]").exists()).toBe(false);
    expect(wrapper.find(".setting-row-form [data-test=inline-confirm]").exists()).toBe(true);
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/auth/logout-all");
    expect(router.currentRoute.value.name).toBe("login");
    wrapper.unmount();
  });

  it("refaire l'accueil : les réponses gardées, la page d'accueil", async () => {
    PUT.mockResolvedValue({});
    const { wrapper, router } = await mountPanel();
    await wrapper.find("[data-test=welcome-again]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/welcome", { body: { done: false, postponed: false, step: 1 } });
    expect(router.currentRoute.value.path).toBe("/bienvenue");
    wrapper.unmount();
  });

  it("l'exploitant ne refait pas l'accueil ; la démo et la connexion désactivée le disent", async () => {
    const owner = await mountPanel({ is_owner: true });
    expect(owner.wrapper.find("[data-test=welcome-again]").exists()).toBe(false);
    owner.wrapper.unmount();
    const demo = await mountPanel({ authenticated: false, auth_enabled: false, demo: true });
    expect(demo.wrapper.find("[data-test=auth-demo] .setting-row-description").text()).toBe("Démo : rien de ce que tu fais n'est enregistré.");
    demo.wrapper.unmount();
    const open = await mountPanel({ authenticated: false, auth_enabled: false });
    expect(open.wrapper.find("[data-test=auth-disabled]").text()).toContain("Connexion désactivée sur cette installation");
    open.wrapper.unmount();
  });
});
