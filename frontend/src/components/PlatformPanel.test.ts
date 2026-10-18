import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import PlatformPanel from "./PlatformPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PATCH = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
    PUT: vi.fn(),
  },
}));
afterEach(() => vi.resetAllMocks());

const ACCOUNT = {
  created_at: "2026-10-01T10:00:00Z",
  last_login_at: null,
  suspended: false,
  has_password: true,
  month_spend_chf: "0.40",
  month_offers: 12,
};
const PLATFORM = {
  accounts: [
    { ...ACCOUNT, id: 1, username: "kevin", is_owner: true, ai_budget_chf: "10", last_login_at: "2026-10-16T08:00:00Z" },
    { ...ACCOUNT, id: 2, username: "camille", is_owner: false, ai_budget_chf: "5" },
  ],
  invitations: [],
  ai_total_budget_chf: "50",
  ai_month_spend_chf: "0.80",
  auth_enabled: true,
  database_admin: false,
};

describe("Plateforme (docs/65 §5)", () => {
  it("l'usage de chaque compte, les actions seulement pour les autres", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const camille = wrapper.find("[data-test=account-camille]");
    expect(camille.text()).toContain("IA 0,40 CHF sur 5,00");
    expect(camille.text()).toContain("12 offres reçues");
    expect(camille.text()).toContain("jamais connecté");
    expect(wrapper.find("[data-test=account-kevin]").text()).toContain("toi");
    expect(wrapper.find("[data-test=reset-kevin]").exists()).toBe(false);
    expect(wrapper.find("[data-test=platform-ai]").text()).toContain("0,80 CHF");
  });

  it("une connexion à la base en administrateur est signalée (docs/78 §3.1)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const calm = mount(PlatformPanel);
    await flushPromises();
    expect(calm.find("[data-test=platform-database-admin]").exists()).toBe(false);
    GET.mockResolvedValue({ data: { ...PLATFORM, database_admin: true } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=platform-database-admin]").text()).toContain("jobbot_app");
  });

  it("une invitation : le lien, montré une fois", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    POST.mockResolvedValue({ data: { id: 7, token: "jba_secret", expires_at: "2026-10-23T10:00:00Z" } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    await wrapper.find("[data-test=invite]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/platform/invitations");
    expect(wrapper.find("[data-test=platform-link]").text()).toContain("/acces/jba_secret");
  });

  it("supprimer demande d'écrire l'identifiant", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    DELETE.mockResolvedValue({ data: { ...PLATFORM, accounts: [PLATFORM.accounts[0]] } });
    const prompt = vi.spyOn(window, "prompt").mockReturnValueOnce("autre").mockReturnValueOnce("camille");
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    await wrapper.find("[data-test=account-more-camille]").trigger("click");
    await wrapper.find("[data-test=delete-camille]").trigger("click");
    expect(DELETE).not.toHaveBeenCalled();
    await wrapper.find("[data-test=account-more-camille]").trigger("click");
    await wrapper.find("[data-test=delete-camille]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/platform/accounts/{account_id}", { params: { path: { account_id: 2 } } });
    expect(wrapper.find("[data-test=account-camille]").exists()).toBe(false);
    prompt.mockRestore();
  });

  it("le plafond d'un compte se change sur place", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    PATCH.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const input = wrapper.find("[data-test=cap-camille]");
    await input.setValue("2");
    await input.trigger("change");
    expect(PATCH).toHaveBeenCalledWith("/api/platform/accounts/{account_id}", {
      params: { path: { account_id: 2 } },
      body: { ai_budget_chf: 2 },
    });
  });
});
