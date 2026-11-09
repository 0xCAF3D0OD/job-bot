import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AlertsView from "./AlertsView.vue";
import NotificationsView from "./NotificationsView.vue";
import SettingsView from "./SettingsView.vue";

// Ordinateur : la requête de 1 024 px répond oui, celle du téléphone non (maquette du 8 novembre, lot 7).
vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: (query?: string) => ({ phone: ref(query === "(min-width: 1024px)") }),
  useNarrow: () => ({ phone: ref(false) }),
}));
const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a), PUT: vi.fn(), DELETE: vi.fn(), PATCH: vi.fn() },
}));
enableAutoUnmount(afterEach);
afterEach(() => vi.resetAllMocks());

const router = () => createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

describe("Notifications sur ordinateur (NotificationsOrdinateur)", () => {
  it("le titre, Toutes · Non lues · N, « Tout marquer comme lu », des lignes sans icône au point à gauche", async () => {
    const now = new Date().toISOString();
    GET.mockResolvedValue({
      data: {
        unread: 1,
        items: [
          { id: 1, kind: "offers", title: "3 nouvelles offres", message: "La meilleure.", link: "/candidatures/offres", created_at: now, read_at: null },
          { id: 2, kind: "orp_due", title: "Preuves", message: "Deux lignes.", link: "/bilan/orp", created_at: now, read_at: now },
        ],
      },
    });
    const r = router();
    await r.push("/notifications");
    const wrapper = mount(NotificationsView, { global: { plugins: [r] } });
    await flushPromises();
    expect(wrapper.find(".notifications-wide").exists()).toBe(true);
    expect(wrapper.find("[data-test=notifications-back]").exists()).toBe(false);
    expect(wrapper.find("[data-test=filter-unread]").text()).toBe("Non lues · 1");
    expect(wrapper.find("[data-test=read-all]").text()).toBe("Tout marquer comme lu");
    // Pas d'icône à fond (D23) : le point « non lue » seulement, sur la ligne non lue.
    expect(wrapper.find(".notif-icon").exists()).toBe(false);
    const rows = wrapper.findAll("[data-test=notification]");
    expect(rows[0]!.find("[data-test=unread-dot]").exists()).toBe(true);
    expect(rows[1]!.find("[data-test=unread-dot]").exists()).toBe(false);
    expect(rows[0]!.find("[data-test=notification-action] .icon").exists()).toBe(true);
  });
});

describe("Mes alertes e-mail sur ordinateur (AlertesOrdinateur du 9 novembre, §2.8)", () => {
  it("le titre, la phrase, les familles, une carte par alerte ; plus de bandeau ni de menu « … »", async () => {
    const today = new Date().toISOString();
    GET.mockResolvedValue({
      data: {
        mailbox: "moi@exemple.ch",
        folder: "job-bot",
        sites: [
          { slug: "jobup", name: "jobup", senders: [], prefilled: true },
          { slug: "linkedin", name: "LinkedIn", senders: [], prefilled: true },
        ],
        searches: [
          {
            id: 1,
            terms: "DevOps",
            location: "Lausanne",
            active: true,
            cells: [
              { site: "jobup", url: null, status: "received", received_at: today, created_at: null },
              { site: "linkedin", url: null, status: "todo", received_at: null, created_at: null },
            ],
          },
        ],
        to_confirm: [{ search_id: 1, site: "jobup", subject: "Confirmez", received_at: today, url: "https://jobup.example/ok" }],
      },
    });
    const wrapper = mount(AlertsView, { global: { stubs: { teleport: true } } });
    await flushPromises();
    expect(wrapper.find("h1").text()).toBe("Mes alertes e-mail");
    expect(wrapper.find("[data-test=alerts-sentence]").text()).toMatch(/^1 recherche suivie\. Dernière alerte reçue/);
    expect(wrapper.find("[data-test=add-search]").text()).toBe("+ Ajouter une recherche");
    expect(wrapper.find("[data-test=action-band]").exists()).toBe(false);
    expect(wrapper.find("[data-test=alerts-banner]").exists()).toBe(false);
    expect(wrapper.find(".more-button").exists()).toBe(false);
    expect(wrapper.findAll(".alerts-family-title").map((h) => h.text())).toEqual(["À confirmer · 1", "À créer · 1"]);
    const confirm = wrapper.find("[data-test=alert-card-1-jobup]");
    expect(confirm.text()).toContain("Lausanne · jobup");
    expect(confirm.find(".block-row-aside").classes()).toContain("todo");
    // Le panneau « cf » : le bouton plein « Confirmer sur jobup ».
    await confirm.trigger("click");
    expect(wrapper.find("[data-test=alert-confirm]").text()).toContain("Confirmer sur jobup");
  });
});

describe("Réglages sur ordinateur (ReglagesOrdinateur)", () => {
  it("une page « Réglages » : Notifications, Affichage, Connexions et Mes données à la suite", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/notifications"
            ? { configured: false, server: "https://ntfy.sh" }
            : { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 10, rhythm_days: [0, 1, 2, 3, 4] },
      }),
    );
    const r = router();
    await r.push({ path: "/reglages", query: { rubrique: "notifications" } });
    const wrapper = mount(SettingsView, {
      global: {
        plugins: [r],
        stubs: { StatusPanel: true, SitesPanel: true, PlatformPanel: true, ConnectionsPanel: true, ExtensionPanel: true, GetemallPanel: true, SessionPanel: true, AccountDataPanel: true, AppearancePanel: true },
      },
    });
    await flushPromises();
    expect(wrapper.find("[data-test=settings-title]").text()).toBe("Réglages");
    expect(wrapper.find("[data-test=settings-back]").exists()).toBe(false);
    for (const id of ["notifications", "affichage", "connexions", "donnees"]) {
      expect(wrapper.find(`[data-test=section-${id}]`).exists()).toBe(true);
    }
    expect(wrapper.find("[data-test=section-recherche]").exists()).toBe(false);
  });
});
