import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountMenu from "./AccountMenu.vue";

const collectNow = vi.fn();
const me = ref<Record<string, unknown>>({ username: "kevin", auth_enabled: true, demo: false });
vi.mock("../composables/useCollect", () => ({ useCollect: () => ({ running: ref(false), collectNow }) }));
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me, logout: vi.fn() }) }));
vi.mock("../composables/useProfiles", () => ({
  useProfiles: () => ({ list: ref(null), current: ref(null), load: vi.fn(), choose: vi.fn() }),
}));

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
  me.value = { username: "kevin", auth_enabled: true, demo: false };
});

describe("Menu du compte (docs/89)", () => {
  it("l'initiale ouvre Profil, Réglages, Données personnelles, Diagnostic, la collecte et la déconnexion", async () => {
    const { router, wrapper } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    expect(trigger.text()).toContain("K");
    expect(trigger.classes()).not.toContain("active");
    await trigger.trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Connecté : kevin");
    expect(wrapper.find("[data-test=account-profile]").attributes("href")).toBe("/profil");
    expect(wrapper.find("[data-test=account-settings]").attributes("href")).toBe("/reglages");
    expect(wrapper.find("[data-test=account-privacy]").attributes("href")).toBe("/tes-donnees");
    expect(wrapper.find("[data-test=account-diagnostic]").attributes("href")).toBe("/reglages/diagnostic");
    expect(wrapper.find("[data-test=logout]").exists()).toBe(true);
    // Le premier choix prend le focus ; une page choisie ferme le menu.
    expect(document.activeElement?.getAttribute("data-test")).toBe("account-profile");
    await wrapper.find("[data-test=account-collect]").trigger("click");
    expect(collectNow).toHaveBeenCalled();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
    await trigger.trigger("click");
    await router.push("/reglages");
    await flushPromises();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
    expect(trigger.classes()).toContain("active");
  });

  it("au clavier : les flèches parcourent, Échap ferme et rend le focus à l'initiale", async () => {
    const { wrapper } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    await trigger.trigger("click");
    await flushPromises();
    const panel = wrapper.find("[data-test=account-panel]");
    await panel.trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("account-settings");
    await panel.trigger("keydown", { key: "ArrowUp" });
    await panel.trigger("keydown", { key: "ArrowUp" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("logout");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
    expect(document.activeElement).toBe(trigger.element);
  });

  it("démo : pas de collecte ni de déconnexion, Réglages reste", async () => {
    me.value = { username: "demo", auth_enabled: false, demo: true };
    const { wrapper } = await mountAt("/aujourdhui");
    await wrapper.find("[data-test=account-menu]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=account-collect]").exists()).toBe(false);
    expect(wrapper.find("[data-test=logout]").exists()).toBe(false);
    expect(wrapper.find("[data-test=account-settings]").exists()).toBe(true);
  });
});
