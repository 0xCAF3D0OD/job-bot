import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { dateWithTime } from "../dates";
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
  it("les premiers pas : des nombres seulement, où s'arrêtent les autres (docs/128 §4)", async () => {
    GET.mockResolvedValue({ data: { ...PLATFORM, first_steps: { accounts: 5, sent_within_week: 2, stopped_at: [0, 2, 1, 0, 0] } } });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=first-steps-rate]").text()).toContain("2 sur 5");
    const rows = wrapper.findAll("[data-test=first-steps-stopped]");
    expect(rows.map((row) => row.find(".setting-row-title").text())).toEqual([
      "Étape 2 · Alertes sur les sites d'emploi",
      "Étape 3 · Première offre gardée",
    ]);
    expect(rows.map((row) => row.find(".setting-row-control").text())).toEqual(["2 comptes", "1 compte"]);
  });

  it("le test utilisateurs : le temps entre l'inscription et chaque étape, sans nom (30.10.2026)", async () => {
    const created = "2026-10-20T08:00:00Z";
    GET.mockResolvedValue({
      data: {
        ...PLATFORM,
        milestones: [
          {
            account: 12,
            created_at: created,
            first_alert: "2026-10-20T08:25:00Z",
            first_offer: "2026-10-20T14:00:00Z",
            first_prepared: "2026-10-23T09:00:00Z",
            first_export: null,
          },
        ],
      },
    });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const table = wrapper.find("[data-test=milestones-table]");
    expect(table.findAll("thead th").map((th) => th.text())).toEqual(["Compte", "Alerte", "Offre", "Candidature", "Preuves"]);
    const row = table.find("[data-test=milestones-row]");
    expect(row.find("th").text()).toContain("n° 12");
    expect(row.findAll("td").map((td) => td.text())).toEqual(["25 min", "6 h", "3 j", "—"]);
    // Aucun nom de compte dans ce tableau.
    for (const account of PLATFORM.accounts) expect(table.text()).not.toContain(account.username);
    GET.mockResolvedValue({ data: { ...PLATFORM, milestones: [] } });
    const empty = mount(PlatformPanel);
    await flushPromises();
    expect(empty.find("[data-test=platform-milestones]").text()).toContain("Aucun compte invité");
  });

  it("l'usage de chaque compte, les actions seulement pour les autres", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const camille = wrapper.find("[data-test=account-camille]");
    expect(camille.text()).toContain("IA 0,40 CHF sur 5,00");
    expect(camille.text()).toContain("12 offres reçues");
    expect(camille.text()).toContain("jamais connecté");
    expect(wrapper.find("[data-test=account-kevin] .setting-row-title").text()).toBe("kevin (toi)");
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
    expect(fine.find("[data-test=backup-last]").text()).toContain(`Faite ${dateWithTime(PLATFORM.backup.last_at)}, 42 Mo`);
    expect(fine.find("[data-test=backup-last] [data-test=backup-state]").text()).toBe("À jour");
    expect(fine.find("[data-test=backup-last] [data-test=backup-state]").classes()).toContain("ok");
    expect(fine.find("[data-test=backup-last]").text()).toContain("3 sauvegardes gardées");
    expect(fine.find("[data-test=backup-late]").exists()).toBe(false);
    GET.mockResolvedValue({
      data: { ...PLATFORM, backup: { ...PLATFORM.backup, late: true, last_error: "pg_dump introuvable" } },
    });
    const late = mount(PlatformPanel);
    await flushPromises();
    expect(late.find("[data-test=backup-late]").text()).toContain("pg_dump introuvable");
    expect(late.find("[data-test=backup-late] [data-test=backup-state]").classes()).toContain("error");
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
    const confirm = wrapper.find("[data-test=platform-accounts] [data-test=inline-confirm]");
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

  it("la formule d'un compte se choisit sur place (docs/125 §5)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    PATCH.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    await wrapper.find("[data-test=plan-camille]").setValue("plus");
    expect(PATCH).toHaveBeenCalledWith("/api/platform/accounts/{account_id}", {
      params: { path: { account_id: 2 } },
      body: { plan: "plus" },
    });
  });

  it("le plafond total s'enregistre au changement, sans bouton (0.78.4)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    PUT.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=platform-ai] button").exists()).toBe(false);
    const input = wrapper.find("[data-test=platform-total]");
    await input.setValue("60");
    await input.trigger("change");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/platform/settings", { body: { ai_total_budget_chf: 60 } });
    expect(wrapper.find("[data-test=platform-ai] [data-test=setting-saved]").text()).toContain("Enregistré");
  });

  it("un plafond impossible n'est pas envoyé : l'ancien reste, la saisie aussi (1.6.67)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    const total = wrapper.find("[data-test=platform-total]");
    await total.setValue("20000");
    await total.trigger("change");
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=platform-ai] [data-test=setting-error]").text()).toBe(
      "Entre 0 et 10000 CHF. Le 50 reste enregistré.",
    );
    expect((total.element as HTMLInputElement).value).toBe("20000");
    expect(total.attributes("aria-invalid")).toBe("true");
    const cap = wrapper.find("[data-test=cap-camille]");
    await cap.setValue("-1");
    await cap.trigger("change");
    expect(PATCH).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=account-camille] [data-test=setting-error]").text()).toBe(
      "Entre 0 et 1000 CHF. Le 5 reste enregistré.",
    );
  });

  it("des cartes de lignes : titre, phrase, l'action à droite, sans « Enregistrer » (1.6.67)", async () => {
    GET.mockResolvedValue({ data: PLATFORM });
    const wrapper = mount(PlatformPanel);
    await flushPromises();
    expect(wrapper.find(".form-card, fieldset, legend").exists()).toBe(false);
    expect(wrapper.find("button[type=submit]").exists()).toBe(false);
    const titles = wrapper.findAll("[data-test=setting-row] .setting-row-title").map((t) => t.text());
    expect(titles).toEqual(expect.arrayContaining(["Comptes", "Demandes de compte", "Inviter quelqu'un", "Plafond total de l'IA, tous comptes"]));
    const invite = wrapper.findAll("[data-test=setting-row]").find((row) => row.text().startsWith("Inviter quelqu'un"));
    expect(invite?.find(".setting-row-control [data-test=invite]").exists()).toBe(true);
    // Chaque contrôle est nommé par sa ligne.
    const signup = wrapper.find("[data-test=signup-open]");
    const name = wrapper.find(`#${signup.attributes("aria-labelledby")}`);
    expect(name.text()).toBe("Demandes de compte");
    expect(wrapper.find("[data-test=plan-camille]").attributes("aria-labelledby")).toContain(
      wrapper.find("[data-test=account-camille] .setting-row-title").attributes("id"),
    );
    // Le lien vers la page publique est l'action de sa ligne, pas un lien dans la phrase.
    expect(wrapper.find(".setting-row-description a").exists()).toBe(false);
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
    const cards = wrapper.findAll(".setting-card");
    expect(cards[0]?.attributes("data-test")).toBe("platform-requests");
    const lea = wrapper.find("[data-test=request-lea]");
    expect(lea.text()).toContain("lea");
    expect(lea.text()).toContain("Amie de Camille.");
    expect(lea.find(".setting-row-description").text()).toMatch(/^Demandé le .+ · « Amie de Camille\. »$/);
    expect(wrapper.find("[data-test=request-noah] .setting-row-description").text()).not.toContain("«");
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
    expect(wrapper.text()).toContain("Fermées : seules tes invitations ouvrent un compte.");
    expect(wrapper.find("[data-test=platform-invite] [data-test=setting-saved]").text()).toContain("Enregistré");
  });
});
