// Le détail d'Envoyées sur ordinateur (MODIFICATIONS du 9 novembre, §8.1).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SentDetail from "./SentDetail.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) } }));
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-08T09:00:00"));
  GET.mockResolvedValue({
    data: {
      company: "Lombard Odier",
      website: null,
      contacts: [],
      searches: [
        { kind: "recruiting", label: "Recrutement", url: "https://www.linkedin.com/search/rh" },
        { kind: "team", label: "L'équipe du poste (Application Monitoring)", url: "https://www.linkedin.com/search/team" },
      ],
    },
  });
  POST.mockResolvedValue({ data: { subject: "Relance", text: "Bonjour, je me permets de revenir vers vous.", language: "fr", ai: true, reason: null } });
});
afterEach(() => {
  vi.useRealTimers();
  vi.resetAllMocks();
});

const application = {
  id: 9,
  sent_at: "2026-09-13",
  method: "electronique",
  assigned_by_orp: false,
  company: "Lombard Odier",
  location: "Genève",
  job_title: "Internship, Software Engineer",
  status: "en_attente",
  application_url: "https://www.linkedin.com/jobs/1",
  letter_draft_id: 4,
  cv_draft_id: 5,
  follow_up_on: null,
  followed_up_at: null,
  interviews: [],
  contacts: [],
  orp_month: "2026-09",
  created_at: "2026-09-12T10:00:00Z",
};

function mountDetail(overrides: Record<string, unknown> = {}) {
  return mount(SentDetail, {
    props: { application: { ...application, ...overrides } as never, orpRow: { declared_at: "2026-10-05", missing: [], job_room: [] } as never },
    global: { stubs: { teleport: true, ContactsPanel: true } },
  });
}

describe("Le détail d'Envoyées en cartes (§8.1)", () => {
  it("en-tête : titre en H2, entreprise · ville, mots de statut, puis le Suivi en 5 étapes avec l'étape en cours", async () => {
    const wrapper = mountDetail();
    await flushPromises();
    expect(wrapper.find("[data-test=panel-title]").element.tagName).toBe("H2");
    expect(wrapper.find(".sent-head-title p").text()).toBe("Lombard Odier · Genève");
    expect(wrapper.find("[data-test=word-no-answer]").text()).toBe("Sans réponse · 56 jours");
    expect(wrapper.find("[data-test=word-declared]").text()).toBe("Déclarée à l’ORP");
    const steps = wrapper.findAll("[data-test=sent-steps] li");
    expect(steps.map((s) => s.find(".sent-step-label").text())).toEqual(["Préparée", "Envoyée", "Déclarée ORP", "Relance", "Réponse"]);
    expect(steps[3]!.attributes("aria-current")).toBe("step");
    // Traits verts jusqu'à l'étape en cours, gris ensuite.
    expect(steps.map((s) => s.find(".sent-step-line").exists() && s.find(".sent-step-line").classes("on"))).toEqual([true, true, true, false, false]);
  });

  it("à droite : « Ce que tu as envoyé » (PDF et annonce) et « Trouver un contact » depuis les recherches", async () => {
    const wrapper = mountDetail();
    await flushPromises();
    expect(wrapper.find("[data-test=sent-letter]").attributes("href")).toBe("/api/letters/4/pdf");
    expect(wrapper.find("[data-test=sent-cv]").attributes("href")).toBe("/api/cvs/5/pdf");
    expect(wrapper.find("[data-test=sent-offer]").text()).toContain("Sur linkedin.com");
    expect(wrapper.find("[data-test=find-recruiting]").text()).toContain("Lombard Odier sur LinkedIn");
    expect(wrapper.find("[data-test=find-team] b").text()).toBe("L'équipe du poste");
    expect(wrapper.find("[data-test=find-team]").text()).toContain("Application Monitoring");
  });

  it("la relance conseillée montre le message déjà écrit ; sans adresse e-mail, « Copier et ouvrir LinkedIn »", async () => {
    // Une autre candidature : la rédaction est gardée par candidature pendant la session.
    const wrapper = mountDetail({ id: 15 });
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/applications/{application_id}/follow-up/draft", expect.anything());
    expect(wrapper.find("[data-test=follow-quote]").text()).toBe("Bonjour, je me permets de revenir vers vous.");
    expect(wrapper.find("[data-test=follow-to]").text()).toContain("Recrutement, Lombard Odier · LinkedIn");
    expect(wrapper.find("[data-test=follow-open]").text()).toContain("Copier et ouvrir LinkedIn");
  });

  it("avec une adresse : « Ouvrir l’e-mail » prépare le message ; « Modifier » rend le texte modifiable", async () => {
    const wrapper = mountDetail({ id: 10, contact_email: "rh@exemple.ch", contact_name: "Mme Rochat" });
    await flushPromises();
    const open = wrapper.find("a[data-test=follow-open]");
    expect(open.attributes("href")).toMatch(/^mailto:rh%40exemple\.ch\?subject=Relance&body=Bonjour/);
    expect(wrapper.find("[data-test=follow-to]").text()).toContain("Mme Rochat · E-mail");
    await wrapper.find("[data-test=follow-edit]").trigger("click");
    expect(wrapper.find("textarea[data-test=follow-text]").exists()).toBe(true);
  });

  it("au retour après l'envoi, la candidature passe à « Relancée »", async () => {
    const wrapper = mountDetail({ id: 11, contact_email: "rh@exemple.ch" });
    await flushPromises();
    await wrapper.find("a[data-test=follow-open]").trigger("click");
    POST.mockResolvedValueOnce({ data: { ...application, status: "relancee" } });
    window.dispatchEvent(new Event("focus"));
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/applications/{application_id}/follow-up", { params: { path: { application_id: 11 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("rédaction impossible : « Le message n’a pas pu être écrit » et « Réessayer »", async () => {
    POST.mockResolvedValueOnce({ data: undefined });
    const wrapper = mountDetail({ id: 12 });
    await flushPromises();
    expect(wrapper.find(".follow-card-title").text()).toBe("Le message n’a pas pu être écrit");
    expect(wrapper.find("[data-test=follow-retry]").exists()).toBe(true);
  });

  it("une réponse reçue : pas de carte de relance, l'Historique et « J’ai contacté quelqu’un » restent", async () => {
    const wrapper = mountDetail({ id: 13, status: "refus", status_at: "2026-10-30" });
    await flushPromises();
    expect(wrapper.find("[data-test=follow-card]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sent-history] li").text()).toContain("Réponse : refus");
    await wrapper.find("[data-test=contacted-open]").trigger("click");
    expect(wrapper.find("contacts-panel-stub").attributes("part")).toBe("follow");
  });

  it("« Changer le statut » dans « … » ouvre le choix du statut", async () => {
    const wrapper = mountDetail({ id: 14 });
    await flushPromises();
    await wrapper.find("[data-test=panel-more] button, button[data-test=panel-more]").trigger("click");
    const item = wrapper.find("[data-test=panel-status-open]");
    await item.trigger("click");
    await wrapper.find("[data-test=panel-status] input[value=entretien]").setValue(true);
    expect(wrapper.emitted("status")?.[0]?.[1]).toBe("entretien");
  });
});

describe("Le détail d'Envoyées sur téléphone (§8.3)", () => {
  function mountPhone(overrides: Record<string, unknown> = {}) {
    return mount(SentDetail, {
      props: { phone: true, application: { ...application, ...overrides } as never, orpRow: { declared_at: "2026-10-05", missing: [], job_room: [] } as never },
      global: { stubs: { teleport: true, ContactsPanel: true } },
    });
  }

  it("barre « ‹ Envoyées » et « … » ; titre en H1, mots de statut, sans avatar ni Suivi", async () => {
    const wrapper = mountPhone({ id: 20 });
    await flushPromises();
    expect(wrapper.find("[data-test=sent-back]").text()).toBe("Envoyées");
    expect(wrapper.find("[data-test=panel-title]").element.tagName).toBe("H1");
    expect(wrapper.find(".sent-head-logo").exists()).toBe(false);
    expect(wrapper.find("[data-test=sent-steps]").exists()).toBe(false);
    expect(wrapper.find("[data-test=word-no-answer]").exists()).toBe(true);
    await wrapper.find("[data-test=sent-back]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("carte de relance compacte : « Voir et envoyer » ouvre la feuille Relance avec le message entier", async () => {
    const wrapper = mountPhone({ id: 21 });
    await flushPromises();
    expect(wrapper.find(".follow-card-help").text()).toBe("Court et poli, à envoyer sur LinkedIn à Lombard Odier.");
    await wrapper.find("[data-test=follow-sheet-open]").trigger("click");
    expect(wrapper.find("[data-test=follow-sheet] [data-test=follow-quote]").text()).toBe("Bonjour, je me permets de revenir vers vous.");
    expect(wrapper.find("[data-test=follow-edit]").text()).toBe("Modifier le message");
  });

  it("deux lignes « Ce que tu as envoyé » et « Trouver un contact », chacune ouvre sa feuille", async () => {
    const wrapper = mountPhone({ id: 22 });
    await flushPromises();
    expect(wrapper.find("[data-test=sent-docs-open]").text()).toContain("Lettre, CV adapté et l’annonce");
    expect(wrapper.find("[data-test=sent-find-open]").text()).toContain("2 pistes chez Lombard Odier");
    expect(wrapper.find("[data-test=section-documents]").exists()).toBe(false);
    await wrapper.find("[data-test=sent-docs-open]").trigger("click");
    expect(wrapper.find("[data-test=sent-docs-sheet] [data-test=sent-cv]").attributes("href")).toBe("/api/cvs/5/pdf");
    await wrapper.find("[data-test=sent-find-open]").trigger("click");
    expect(wrapper.find("[data-test=sent-find-sheet] [data-test=find-recruiting]").exists()).toBe(true);
  });
});
