import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountMenu from "./AccountMenu.vue";

const logout = vi.fn();
const me = ref<Record<string, unknown>>({ username: "kevin", auth_enabled: true, demo: false, is_owner: true });
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me, logout }) }));
vi.mock("../composables/useProfiles", () => ({ useProfiles: () => ({ load: vi.fn() }) }));

async function mountAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }],
  });
  await router.push(path);
  const wrapper = mount(AccountMenu, { attachTo: document.body, global: { plugins: [router] } });
  return { router, wrapper };
}

afterEach(() => {
  document.body.innerHTML = "";
  me.value = { username: "kevin", auth_enabled: true, demo: false, is_owner: true };
});

describe("Menu du compte (docs/89 ; décision de Kevin du 2026-11-05, C2)", () => {
  it("l'initiale n'ouvre que « Compte » et « Se déconnecter »", async () => {
    const { router, wrapper } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    // L'initiale seule (1.6.46) : ni nom, ni flèche ; la légende reprend le nom accessible.
    expect(trigger.text()).toBe("K");
    expect(trigger.find(".icon").exists()).toBe(false);
    expect(trigger.attributes("data-label")).toBe(trigger.attributes("aria-label"));
    await trigger.trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Connecté : kevin");
    const items = wrapper.findAll("[role=menuitem]");
    expect(items.map((item) => item.text())).toEqual(["Compte", "Se déconnecter"]);
    expect(wrapper.find("[data-test=account-page-link]").attributes("href")).toBe("/compte");
    // Le premier choix prend le focus ; une page choisie ferme le menu.
    expect(document.activeElement?.getAttribute("data-test")).toBe("account-page-link");
    await router.push("/compte");
    await flushPromises();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
  });

  it("au clavier : les flèches parcourent, Échap ferme et rend le focus à l'initiale", async () => {
    const { wrapper } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    await trigger.trigger("click");
    await flushPromises();
    const panel = wrapper.find("[data-test=account-panel]");
    await panel.trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("logout");
    await panel.trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("account-page-link");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
    expect(document.activeElement).toBe(trigger.element);
  });

  it("démo, sans connexion : « Compte » seul", async () => {
    me.value = { username: "demo", auth_enabled: false, demo: true };
    const { wrapper } = await mountAt("/aujourdhui");
    await wrapper.find("[data-test=account-menu]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[role=menuitem]").map((item) => item.text())).toEqual(["Compte"]);
  });
});
