import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { createMemoryHistory, createRouter } from "vue-router";

import AccountMenu from "./AccountMenu.vue";
import ProfilesPanel from "./ProfilesPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  PROFILE_KEY: "jobbot-profile",
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PATCH: (...a: unknown[]) => PATCH(...a), use: vi.fn() },
}));
afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

const main = { id: 1, name: "Profil principal", occupation: null, is_main: true, domain_keywords: ["DevOps"], sources: 5 };
const nurse = { id: 2, name: "Infirmière", occupation: "infirmière", is_main: false, domain_keywords: ["soins"], sources: 3 };

describe("ProfilesPanel", () => {
  it("création d'un profil d'essai avec domaine, langues et pays", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/profiles/keywords" ? { keywords: [], available: false } : { current_id: 1, items: [main] } }),
    );
    POST.mockResolvedValue({ data: { current_id: 1, items: [main, nurse] } });
    const wrapper = mount(ProfilesPanel);
    await flushPromises();
    await wrapper.find("[data-test=add-profile-open]").trigger("click");
    await wrapper.find("[data-test=profile-name]").setValue(" Infirmière ");
    await wrapper.find("[data-test=profile-keywords]").setValue("soins, infirmière ,");
    await wrapper.find("[data-test=add-profile]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/profiles", {
      body: { name: "Infirmière", occupation: null, domain_keywords: ["soins", "infirmière"], languages: ["fr"], countries: ["CH"] },
    });
    expect(wrapper.findAll("[data-test=profile]")).toHaveLength(2);
    // « Supprimer » dans le « ⋯ » de chaque profil, sauf le principal (docs/74).
    const menus = wrapper.findAll("[data-test=profile-more]");
    for (const menu of menus) await menu.trigger("click");
    expect(wrapper.findAll("[data-test=profile-delete]")).toHaveLength(1);
    expect(wrapper.find("[data-test=propose-keywords]").exists()).toBe(false);
  });

  it("mots-clés proposés par l'IA à partir du métier", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/profiles/keywords" ? { keywords: [], available: true } : { current_id: 1, items: [main] } }),
    );
    POST.mockResolvedValue({ data: { keywords: ["infirmière", "EMS"], available: true } });
    const wrapper = mount(ProfilesPanel);
    await flushPromises();
    await wrapper.find("[data-test=add-profile-open]").trigger("click");
    // Bouton actif (docs/29 §3) : sans métier, il explique au clic.
    await wrapper.find("[data-test=propose-keywords]").trigger("click");
    expect(wrapper.text()).toContain("Indique d'abord le métier");
    await wrapper.find("[data-test=profile-occupation]").setValue("infirmière");
    await wrapper.find("[data-test=propose-keywords]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/profiles/keywords", { body: { occupation: "infirmière" } });
    expect((wrapper.find("[data-test=profile-keywords]").element as HTMLInputElement).value).toBe("infirmière, EMS");
  });

  it("menu du compte : profil affiché retenu, rechargement", async () => {
    GET.mockResolvedValue({ data: { current_id: 1, items: [main, nurse] } });
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    const wrapper = mount(AccountMenu, { global: { plugins: [router] } });
    await flushPromises();
    expect(wrapper.find("[data-test=account-panel]").exists()).toBe(false);
    await wrapper.find("[data-test=account-menu]").trigger("click");
    // Profil, Réglages, Données personnelles (docs/89, docs/90) ; le Diagnostic est à
    // l'exploitant (docs/108 §3), et personne n'est connecté ici.
    expect(wrapper.find("[data-test=account-panel]").findAll("a")).toHaveLength(3);
    await wrapper.find("[data-test=profile-switcher]").setValue("2");
    expect(localStorage.getItem("jobbot-profile")).toBe("2");
    expect(reload).toHaveBeenCalled();
    await wrapper.find("[data-test=profile-switcher]").setValue("1");
    expect(localStorage.getItem("jobbot-profile")).toBeNull();
    vi.unstubAllGlobals();
  });

  it("renommer sur place, sans fenêtre du navigateur (docs/108, 0.77.1)", async () => {
    GET.mockResolvedValue({ data: { current_id: 1, items: [main, nurse] } });
    PATCH.mockResolvedValue({ data: { current_id: 1, items: [main, { ...nurse, name: "Soins" }] } });
    const wrapper = mount(ProfilesPanel, { attachTo: document.body });
    await flushPromises();
    await wrapper.findAll("[data-test=profile-more]")[1]!.trigger("click");
    await wrapper.find("[data-test=profile-rename]").trigger("click");
    await flushPromises();
    const input = wrapper.find("[data-test=profile-rename-input]");
    expect((input.element as HTMLInputElement).value).toBe("Infirmière");
    // Échap sort sans rien changer.
    await wrapper.find("[data-test=profile-rename-form]").trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[data-test=profile-rename-form]").exists()).toBe(false);
    await wrapper.findAll("[data-test=profile-more]")[1]!.trigger("click");
    await wrapper.find("[data-test=profile-rename]").trigger("click");
    await flushPromises();
    await wrapper.find("[data-test=profile-rename-input]").setValue(" Soins ");
    await wrapper.find("[data-test=profile-rename-form]").trigger("submit");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/profiles/{profile_id}", { params: { path: { profile_id: 2 } }, body: { name: "Soins" } });
    expect(wrapper.text()).toContain("Soins");
    wrapper.unmount();
  });
});
