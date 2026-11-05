import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ConnectionsPanel from "./ConnectionsPanel.vue";

const GET = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), DELETE: (...a: unknown[]) => DELETE(...a) },
}));
afterEach(() => vi.resetAllMocks());

const GOOGLE = { id: 7, provider: "google", email: "camille@example.ch", created_at: "2026-11-05T10:00:00Z", last_used_at: null };

async function mountPanel(answer: unknown, path = "/reglages?rubrique=connexions") {
  GET.mockResolvedValue({ data: answer });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push(path);
  const wrapper = mount(ConnectionsPanel, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("Compte › Connexions (docs/65, complément du 2026-11-05)", () => {
  it("les comptes liés, et « Lier » pour chaque fournisseur configuré et pas encore lié", async () => {
    const wrapper = await mountPanel({ providers: ["google", "apple"], links: [GOOGLE], has_password: true });
    expect(wrapper.find("[data-test=connection-google]").text()).toContain("camille@example.ch");
    expect(wrapper.find("[data-test=connection-link-apple]").attributes("href")).toBe("/api/auth/oauth/apple/start?lier=1");
    expect(wrapper.find("[data-test=connection-link-microsoft]").exists()).toBe(false);
    // Google est déjà lié : pas de seconde ligne « Lier ».
    expect(wrapper.find("[data-test=connection-link-google]").exists()).toBe(false);
    // Avec un mot de passe, le lien peut partir : confirmation, puis retrait.
    DELETE.mockResolvedValue({ response: { ok: true } });
    await wrapper.find("[data-test=connection-remove-google]").trigger("click");
    await wrapper.find(".inline-confirm-actions button").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/account/connexions/{connection_id}", { params: { path: { connection_id: 7 } } });
  });

  it("le dernier moyen de se connecter ne se retire pas", async () => {
    const wrapper = await mountPanel({ providers: ["google"], links: [GOOGLE], has_password: false });
    expect(wrapper.find("[data-test=connection-remove-google]").attributes("disabled")).toBeDefined();
    expect(wrapper.find("[data-test=connections-only-way]").text()).toContain("seul moyen de te connecter");
  });

  it("le retour du fournisseur : lié, ou déjà lié ailleurs", async () => {
    let wrapper = await mountPanel({ providers: ["google"], links: [GOOGLE], has_password: true }, "/reglages?rubrique=connexions&lie=google");
    expect(wrapper.find("[data-test=connections-linked]").text()).toBe("Ton compte Google est lié.");
    wrapper = await mountPanel({ providers: ["google"], links: [], has_password: true }, "/reglages?rubrique=connexions&erreur=deja-lie&fournisseur=google");
    expect(wrapper.find("[data-test=connections-error]").text()).toBe("Ce compte Google est déjà lié à un autre compte jobA1.");
  });
});
