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

async function mountPanel(summary = SUMMARY) {
  GET.mockResolvedValue({ data: summary });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/reglages");
  const wrapper = mount(AccountDataPanel, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Tes données (docs/65 §6)", () => {
  it("le résumé et l'export en un clic", async () => {
    const { wrapper } = await mountPanel();
    expect(wrapper.text()).toContain("12 offres, 3 candidatures");
    const link = wrapper.find("[data-test=export]");
    expect(link.attributes("href")).toBe("/api/account/export");
    expect(link.attributes("download")).toBeDefined();
  });

  it("supprimer demande le mot de passe, puis renvoie à la connexion", async () => {
    POST.mockResolvedValueOnce({ error: { detail: "mot de passe incorrect" }, response: { ok: false } });
    POST.mockResolvedValueOnce({ response: { ok: true } });
    const { wrapper, router } = await mountPanel();
    await wrapper.find("[data-test=delete-account]").trigger("click");
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

  it("l'exploitant ne supprime pas son compte ici", async () => {
    const { wrapper } = await mountPanel({ ...SUMMARY, can_delete: false });
    expect(wrapper.find("[data-test=delete-account]").exists()).toBe(false);
  });
});
