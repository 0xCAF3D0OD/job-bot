import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { isoDay } from "../contactLabels";
import ContactsPanel from "./ContactsPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => {
  vi.resetAllMocks();
  vi.restoreAllMocks();
});

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return isoDay(d);
}

const contact = (id: number, extra: Record<string, unknown>) => ({
  id,
  offer_id: 7,
  application_id: 3,
  name: null,
  role: "recruiter",
  channel: "linkedin_invite",
  contacted_on: daysAgo(8),
  answered_on: null,
  note: null,
  ...extra,
});

function page(contacts: unknown[]) {
  return {
    data: {
      company: "Acme SA",
      website: "https://acme.ch",
      searches: [
        { kind: "recruiting", label: "Recrutement", url: "https://www.linkedin.com/search/results/people/?keywords=a" },
        { kind: "team", label: "L'équipe du poste", url: "https://www.linkedin.com/search/results/people/?keywords=b" },
      ],
      contacts,
    },
  };
}

describe("ContactsPanel", () => {
  it("ouvre les recherches dans un nouvel onglet et propose la relance après 7 jours", async () => {
    GET.mockResolvedValue(page([contact(1, { name: "Marie" }), contact(2, { contacted_on: daysAgo(2) })]));
    const wrapper = mount(ContactsPanel, { props: { applicationId: 3, company: "Acme SA", bare: true } });
    await flushPromises();
    const links = wrapper.findAll("[data-test=contact-search]");
    expect(links).toHaveLength(2);
    expect(links[0]!.attributes("target")).toBe("_blank");
    expect(wrapper.find("[data-test=contact-website]").exists()).toBe(true);
    const due = wrapper.findAll("[data-test=contact-due]");
    expect(due).toHaveLength(1);
    expect(due[0]!.text()).toContain("relancer Marie");
  });

  it("enregistre une prise de contact sans nom, datée d'aujourd'hui", async () => {
    GET.mockResolvedValue(page([]));
    POST.mockResolvedValue({ data: contact(5, {}) });
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    await wrapper.find("[data-test=contact-add]").trigger("click");
    await wrapper.find("[data-test=contact-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body).toMatchObject({ offer_id: 7, name: null, contacted_on: isoDay() });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("note la réponse", async () => {
    GET.mockResolvedValue(page([contact(1, {})]));
    PUT.mockResolvedValue({ data: {} });
    const wrapper = mount(ContactsPanel, { props: { applicationId: 3, company: "Acme SA", bare: true } });
    await flushPromises();
    await wrapper.find("[data-test=contact-answered]").trigger("click");
    await wrapper.find("[data-test=contact-note]").setValue("Appel jeudi");
    await wrapper.find(".contacts-list form").trigger("submit");
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body).toMatchObject({ answered_on: isoDay(), note: "Appel jeudi" });
  });

  it("rédige un message, compte les caractères d'une invitation et reprend le rôle", async () => {
    GET.mockResolvedValue(page([]));
    POST.mockResolvedValueOnce({ data: { text: "Bonjour [Prénom], ".repeat(20), limit: 300 } });
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    await wrapper.find("[data-test=contact-writer] select").setValue("team");
    await wrapper.find("[data-test=contact-writer] form").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![0]).toBe("/api/contacts/message");
    expect(POST.mock.calls[0]![1].body).toMatchObject({ offer_id: 7, role: "team", channel: "linkedin_invite" });
    expect(wrapper.find("[data-test=contact-count]").text()).toContain("trop long");
    await wrapper.find("[data-test=contact-add]").trigger("click");
    expect((wrapper.find("[data-test=contact-form] select").element as HTMLSelectElement).value).toBe("team");
  });

  it("explique pourquoi le message n'a pas pu être rédigé", async () => {
    GET.mockResolvedValue(page([]));
    POST.mockResolvedValueOnce({ error: { detail: "plafond mensuel de l'IA atteint" } });
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    await wrapper.find("[data-test=contact-writer] form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Rédaction impossible : plafond mensuel de l'IA atteint.");
  });

  it("dit que le chargement a échoué, réseau coupé compris", async () => {
    GET.mockRejectedValue(new TypeError("Failed to fetch"));
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    const error = wrapper.find("[data-test=contacts-error]");
    expect(error.attributes("role")).toBe("alert");
    expect(error.text()).toBe("Impossible de charger les contacts.");
  });

  it("demande confirmation avant de retirer un contact et dit l'échec", async () => {
    GET.mockResolvedValue(page([contact(1, {})]));
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    const remove = wrapper.findAll(".contact-actions button").find((b) => b.text() === "Retirer")!;
    await remove.trigger("click");
    await flushPromises();
    expect(confirm).toHaveBeenCalledWith("Retirer ce contact ?");
    expect(DELETE).not.toHaveBeenCalled();

    confirm.mockReturnValue(true);
    DELETE.mockResolvedValue({ error: { detail: "introuvable" } });
    await remove.trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledTimes(1);
    expect(wrapper.find("[data-test=contact-error]").text()).toBe("Retrait impossible : réessaie dans un instant.");
    expect(wrapper.emitted("changed")).toBeUndefined();
  });

  it("dit que l'ajout a échoué", async () => {
    GET.mockResolvedValue(page([]));
    POST.mockResolvedValue({ error: { detail: "invalide" } });
    const wrapper = mount(ContactsPanel, { props: { offerId: 7, company: "Acme SA", bare: true } });
    await flushPromises();
    await wrapper.find("[data-test=contact-add]").trigger("click");
    await wrapper.find("[data-test=contact-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=contact-error]").attributes("role")).toBe("alert");
  });
});
