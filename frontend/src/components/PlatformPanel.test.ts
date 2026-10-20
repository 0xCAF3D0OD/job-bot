import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import PlatformPanel from "./PlatformPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PATCH = vi.fn();
const DELETE = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
    PUT: (...a: unknown[]) => PUT(...a),
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
  signup_requests: [] as { id: number; username: string; created_at: string; note: string | null }[],
  signup_open: true,
  ai_total_budget_chf: "50",
  ai_month_spend_chf: "0.80",
  auth_enabled: true,
  database_admin: false,
  backup: {
    configured: true,
    folder: "/Users/x/iCloud/jobA1",
    count: 3,
    last_at: new Date(Date.now() - 5 * 3600_000).toISOString(),
    last_size: 42_000_000,
    last_error: null,
    test_at: null,
    test_ok: null,
    test_error: null,
    late: false,
  },
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

  it("les sauvegardes : la dernière, l'essai, et ce qui ne va pas (docs/82)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const fine = mount(PlatformPanel);
    await flushPromises();
    expect(fine.find("[data-test=backup-last]").text()).toContain("il y a 5 h, 42 Mo");
    expect(fine.find("[data-test=backup-last]").text()).toContain("3 sauvegardes gardées");
    expect(fine.find("[data-test=backup-late]").exists()).toBe(false);
    GET.mockResolvedValue({
      data: { ...PLATFORM, backup: { ...PLATFORM.backup, late: true, last_error: "pg_dump introuvable" } },
    });
    const late = mount(PlatformPanel);
    await flushPromises();
    expect(late.find("[data-test=backup-late]").text()).toContain("pg_dump introuvable");
    GET.mockResolvedValue({ data: { ...PLATFORM, backup: { ...PLATFORM.backup, configured: false } } });
    const missing = mount(PlatformPanel);
    await flushPromises();
    expect(missing.find("[data-test=backup-not-configured]").text()).toContain("JOBBOT_BACKUP_PASSPHRASE");
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

  it("supprimer demande d'écrire l'identifiant, dans la page (docs/108 §1)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    DELETE.mockResolvedValue({ data: { ...PLATFORM, accounts: [PLATFORM.accounts[0]] } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    await wrapper.find("[data-test=account-more-camille]").trigger("click");
    await wrapper.find("[data-test=delete-camille]").trigger("click");
    const confirm = wrapper.find("[data-test=account-camille] [data-test=inline-confirm]");
    expect(confirm.text()).toContain("Écris son identifiant");
    await wrapper.find("[data-test=delete-account-name]").setValue("autre");
    expect(wrapper.find("[data-test=inline-confirm-yes]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=delete-account-name]").setValue("camille");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/platform/accounts/{account_id}", { params: { path: { account_id: 2 } } });
    expect(wrapper.find("[data-test=account-camille]").exists()).toBe(false);
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

  it("le plafond total s'enregistre au changement, sans bouton (0.78.4)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    PUT.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=platform-ai] button[type=submit]").exists()).toBe(false);
    const input = wrapper.find("#platform-total");
    await input.setValue("60");
    await input.trigger("change");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/platform/settings", { body: { ai_total_budget_chf: 60 } });
    expect(wrapper.find("[data-test=platform-ai] .saved-flash").text()).toBe("Enregistré");
  });
});

describe("Plateforme, demandes de compte (docs/102)", () => {
  const REQUESTS = [
    { id: 8, username: "lea", created_at: "2026-10-19T09:00:00Z", note: "Amie de Camille." },
    { id: 9, username: "noah", created_at: "2026-10-20T09:00:00Z", note: null },
  ];

  it("sans demande, pas de rubrique", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=platform-requests]").exists()).toBe(false);
  });

  it("les demandes en tête : identifiant, date, mot laissé", async () => {
    GET.mockResolvedValue({ data: { ...PLATFORM, signup_requests: REQUESTS } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const cards = wrapper.findAll(".form-card");
    expect(cards[0]?.attributes("data-test")).toBe("platform-requests");
    const lea = wrapper.find("[data-test=request-lea]");
    expect(lea.text()).toContain("lea");
    expect(lea.text()).toContain("Amie de Camille.");
    expect(lea.find(".meta-line .icon").exists()).toBe(true);
    expect(wrapper.find("[data-test=request-noah] .platform-request-note").exists()).toBe(false);
  });

  it("accepter, puis refuser après confirmation", async () => {
    GET.mockResolvedValue({ data: { ...PLATFORM, signup_requests: REQUESTS } });
    POST.mockResolvedValue({ data: { ...PLATFORM, signup_requests: [REQUESTS[1]] } });
    DELETE.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    await wrapper.find("[data-test=approve-lea]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/platform/accounts/{account_id}/approve", { params: { path: { account_id: 8 } } });
    expect(wrapper.find("[data-test=request-lea]").exists()).toBe(false);
    // Refuser se confirme dans la page (docs/108 §1) ; « Garder » ne fait rien.
    await wrapper.find("[data-test=refuse-noah]").trigger("click");
    await wrapper.find("[data-test=inline-confirm-no]").trigger("click");
    expect(DELETE).not.toHaveBeenCalled();
    await wrapper.find("[data-test=refuse-noah]").trigger("click");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/platform/accounts/{account_id}", { params: { path: { account_id: 9 } } });
    expect(wrapper.find("[data-test=platform-requests]").exists()).toBe(false);
  });

  it("l'interrupteur enregistre les demandes ouvertes ou fermées", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    PUT.mockResolvedValue({ data: { ...PLATFORM, signup_open: false } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const input = wrapper.find("[data-test=signup-open]");
    expect((input.element as HTMLInputElement).checked).toBe(true);
    await input.trigger("change");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/platform/settings", { body: { signup_open: false } });
    expect((wrapper.find("[data-test=signup-open]").element as HTMLInputElement).checked).toBe(false);
    expect(wrapper.text()).toContain("Demandes de compte fermées.");
  });
});
