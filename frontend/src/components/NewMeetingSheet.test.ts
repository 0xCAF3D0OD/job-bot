// « Nouveau rendez-vous » (paquet du 11 novembre, PR 41 ; maquettes CandidaturesOrdinateurB `ajrv`, RendezVous `addSheet`).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import NewMeetingSheet from "./NewMeetingSheet.vue";

const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { PUT: (...a: unknown[]) => PUT(...a) } }));
afterEach(() => PUT.mockReset());

const app = (id: number, job_title: string, company: string, extra: Record<string, unknown> = {}) => ({
  id,
  job_title,
  company,
  sent_at: `2026-10-${String(id).padStart(2, "0")}`,
  method: "électronique",
  assigned_by_orp: false,
  status: "en_attente",
  status_reason: null,
  status_at: null,
  ...extra,
});
const APPS = [
  app(1, "DevOps Engineer", "Alpstack"),
  app(2, "Internship, Software Engineer", "Lombard Odier"),
  app(3, "Ingénieur systèmes", "Refusée SA", { status: "refus" }),
];

function open(props: Record<string, unknown> = {}) {
  return mount(NewMeetingSheet, { props: { open: true, applications: APPS as never, ...props }, attachTo: document.body });
}
const label = (el: Element) => el.closest(".form-field")?.querySelector("label")?.textContent?.trim();

describe("Nouveau rendez-vous (PR 41)", () => {
  it("une entreprise : candidature avec recherche, format, date et heure vides, champ selon le format", async () => {
    const wrapper = open();
    expect(wrapper.find(".sheet-title").text()).toBe("Nouveau rendez-vous");
    const who = wrapper.get("[role=radiogroup][aria-label='Avec qui ?']");
    expect(who.findAll("[role=radio]").map((r) => [r.text(), r.attributes("aria-checked")])).toEqual([["Une entreprise", "true"], ["L’ORP", "false"]]);
    // La liste : les envoyées, la plus récente d'abord, sans les refusées ; la recherche ignore accents et casse.
    const field = wrapper.get("[data-test=meeting-application]");
    expect(field.attributes("role")).toBe("combobox");
    await field.trigger("focus");
    expect(field.attributes("aria-expanded")).toBe("true");
    expect(wrapper.findAll("[role=option]").map((o) => o.text())).toEqual(["Internship, Software Engineer · Lombard Odier", "DevOps Engineer · Alpstack"]);
    await field.setValue("ALPSTACK");
    expect(wrapper.findAll("[role=option]").map((o) => o.text())).toEqual(["DevOps Engineer · Alpstack"]);
    await wrapper.get("[data-test=meeting-application-1]").trigger("mousedown");
    expect((field.element as HTMLInputElement).value).toBe("DevOps Engineer · Alpstack");
    // Le format, et le champ qui le suit.
    const formats = wrapper.get("[role=radiogroup][aria-label='Format']");
    expect(formats.findAll("[role=radio]").map((r) => r.text())).toEqual(["Téléphone", "Visio", "Sur place"]);
    expect(label(wrapper.get("[data-test=meeting-where]").element)).toBe("Lien de la visio");
    await wrapper.get("[data-test=meeting-format-telephone]").trigger("click");
    expect(label(wrapper.get("[data-test=meeting-where]").element)).toBe("Numéro");
    await wrapper.get("[data-test=meeting-format-sur_place]").trigger("click");
    expect(label(wrapper.get("[data-test=meeting-where]").element)).toBe("Adresse");
    expect(wrapper.get("[data-test=meeting-note]").text()).toBe("La candidature passe en « Entretien ». Tu pourras t’entraîner la veille.");
    // Date et heure : vides, jamais aujourd'hui.
    expect(wrapper.get("[data-test=dt-date]").classes()).toContain("dt-pill-empty");
    expect(wrapper.get("[data-test=dt-time]").classes()).toContain("dt-pill-empty");
    expect(wrapper.get("[data-test=meeting-save]").text()).toContain("Ajouter le rendez-vous");
    wrapper.unmount();
  });

  it("enregistrer : la candidature passe en « Entretien », avec la date, l’heure, le format et le lieu", async () => {
    const saved = { ...APPS[0], status: "entretien" };
    PUT.mockResolvedValue({ data: saved });
    const wrapper = open({ applicationId: 1 });
    expect((wrapper.get("[data-test=meeting-application]").element as HTMLInputElement).value).toBe("DevOps Engineer · Alpstack");
    // Sans date : l'erreur sous le champ, rien n'est envoyé.
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    expect(wrapper.get("[data-test=meeting-when-error]").text()).toBe("Indique la date du rendez-vous.");
    expect(PUT).not.toHaveBeenCalled();
    await wrapper.get("[data-test=dt-date]").trigger("click");
    wrapper.findComponent({ name: "DateTimePanel" }).vm.$emit("confirm", { date: "2026-11-20", time: "14:00" });
    await flushPromises();
    await wrapper.get("[data-test=meeting-where]").setValue(" https://meet.example.ch/abc ");
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    await flushPromises();
    const [path, options] = PUT.mock.calls[0] as [string, { params: { path: { application_id: number } }; body: Record<string, unknown> }];
    expect(path).toBe("/api/applications/{application_id}");
    expect(options.params.path.application_id).toBe(1);
    expect(options.body).toMatchObject({
      status: "entretien",
      interview_at: new Date("2026-11-20T14:00").toISOString(),
      interview_format: "visio",
      interview_place: "https://meet.example.ch/abc",
      company: "Alpstack",
      job_title: "DevOps Engineer",
    });
    expect(wrapper.emitted("interview")?.[0]).toEqual([saved]);
    wrapper.unmount();
  });

  it("sans candidature choisie : « Choisis la candidature. »", async () => {
    const wrapper = open();
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    expect(wrapper.get("[data-test=new-meeting-form]").text()).toContain("Choisis la candidature.");
    expect(PUT).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it("l’ORP : date, heure, « Lieu ou lien (facultatif) » ; un rendez-vous déjà prévu est remplacé, et c’est dit", async () => {
    const page = { meeting: { id: 4 } };
    PUT.mockResolvedValue({ data: page });
    const wrapper = open({ planned: { id: 3, starts_at: "2026-11-25T08:30:00Z", place: "ORP Renens", advisor: "Mme Rochat" } });
    await wrapper.get("[data-test=meeting-kind-orp]").trigger("click");
    expect(wrapper.find("[data-test=meeting-application]").exists()).toBe(false);
    expect(wrapper.find("[role=radiogroup][aria-label='Format']").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-note]").exists()).toBe(false);
    expect(label(wrapper.get("[data-test=meeting-where]").element)).toBe("Lieu ou lien (facultatif)");
    expect(wrapper.get("[data-test=meeting-replaces]").text()).toContain("est remplacé par celui-ci");
    await wrapper.get("[data-test=dt-time]").trigger("click");
    wrapper.findComponent({ name: "DateTimePanel" }).vm.$emit("confirm", { date: "2026-12-02", time: "10:15" });
    await flushPromises();
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting", { body: { starts_at: new Date("2026-12-02T10:15").toISOString(), place: "", advisor: "Mme Rochat" } });
    expect(wrapper.emitted("orp")?.[0]).toEqual([page]);
    wrapper.unmount();
  });
  it("jamais d’échec silencieux : serveur en erreur ou connexion coupée, le panneau garde la saisie et le dit", async () => {
    const wrapper = open({ kind: "orp" });
    await wrapper.setProps({ open: false });
    await wrapper.setProps({ open: true });
    await wrapper.get("[data-test=dt-time]").trigger("click");
    wrapper.findComponent({ name: "DateTimePanel" }).vm.$emit("confirm", { date: "2026-12-02", time: "10:15" });
    await flushPromises();
    // Une erreur de validation : `detail` est une liste, pas une phrase à montrer.
    PUT.mockResolvedValueOnce({ error: { detail: [{ msg: "x" }] } });
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.get("[role=alert].notice").text()).toBe("Le rendez-vous n’est pas enregistré. Ta saisie est gardée, réessaie dans un instant.");
    PUT.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await wrapper.get("[data-test=new-meeting-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.get("[role=alert].notice").text()).toContain("Connexion perdue : le rendez-vous n’est pas enregistré.");
    expect(wrapper.emitted("orp")).toBeUndefined();
    expect(wrapper.emitted("close")).toBeUndefined();
    expect(wrapper.get("[data-test=dt-time]").text()).toContain("10");
    wrapper.unmount();
  });
});
