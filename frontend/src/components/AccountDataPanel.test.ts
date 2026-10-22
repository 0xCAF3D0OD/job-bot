import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountDataPanel from "./AccountDataPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const SUMMARY = {
  offers: 12,
  applications: 3,
  documents: 1,
  profile_blocks: 5,
  alert_emails: 20,
  conversations: 0,
  notifications: 2,
  can_delete: true,
};

async function mountPanel(summary = SUMMARY, path = "/reglages") {
  GET.mockResolvedValue({ data: summary });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push(path);
  const wrapper = mount(AccountDataPanel, { attachTo: document.body, global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Tes données (docs/65 §6)", () => {
  it("le résumé et l'export en un clic", async () => {
    const { wrapper } = await mountPanel();
    // Une ligne par compteur (docs/132).
    const counts = wrapper.findAll("[data-test=account-counts] li").map((li) => li.text());
    expect(counts.slice(0, 2)).toEqual(["Offres12", "Candidatures3"]);
    const link = wrapper.find("[data-test=export]");
    expect(link.attributes("href")).toBe("/api/account/export");
    expect(link.attributes("download")).toBeDefined();
  });

  it("fermer demande le mot de passe, puis renvoie à la connexion", async () => {
    POST.mockResolvedValueOnce({ error: { detail: "mot de passe incorrect" }, response: { ok: false } });
    POST.mockResolvedValueOnce({ response: { ok: true } });
    const { wrapper, router } = await mountPanel();
    expect(wrapper.find("[data-test=delete-account]").text()).toBe("Fermer mon compte");
    await wrapper.find("[data-test=delete-account]").trigger("click");
    expect(wrapper.find("[data-test=inline-confirm-yes]").text()).toBe("Fermer définitivement");
    await wrapper.find("[data-test=delete-password]").setValue("faux");
    await wrapper.find("[data-test=delete-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=delete-error]").text()).toBe("Mot de passe incorrect.");
    await wrapper.find("[data-test=delete-password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=delete-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/account/delete", { body: { password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.path).toBe("/connexion");
  });

  it("l'exploitant ne ferme pas son compte ici, même venu du menu", async () => {
    const { wrapper } = await mountPanel({ ...SUMMARY, can_delete: false }, "/reglages?rubrique=compte&fermer=1");
    expect(wrapper.find("[data-test=delete-account]").exists()).toBe(false);
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(false);
  });

  it("venu de « Fermer mon compte » (docs/105) : la confirmation est ouverte, le mot de passe a le focus", async () => {
    const { wrapper } = await mountPanel(SUMMARY, "/reglages?rubrique=compte&fermer=1");
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(true);
    expect(document.activeElement).toBe(wrapper.find("[data-test=delete-password]").element);
    wrapper.unmount();
  });

  it("téléphone (0.77.4) : « Fermer définitivement » grisé sans mot de passe, puis il ferme", async () => {
    POST.mockResolvedValueOnce({ response: { ok: true } });
    const { wrapper, router } = await mountPanel(SUMMARY, "/reglages?rubrique=compte&fermer=1");
    expect(wrapper.find("[data-test=inline-confirm-yes]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=delete-password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/account/delete", { body: { password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.path).toBe("/connexion");
    wrapper.unmount();
  });
});

