import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FollowUpPanel from "./FollowUpPanel.vue";

const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { POST: (...a: unknown[]) => POST(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));
afterEach(() => vi.resetAllMocks());

const application = {
  id: 3,
  job_title: "DevOps Engineer",
  company: "Exemple AG",
  sent_at: "2026-09-12",
  contact_email: "rh@exemple.ch",
};

const draft = (extra: Record<string, unknown> = {}) => ({
  data: {
    subject: "Relance – candidature DevOps Engineer",
    text: "Madame, Monsieur, …\n\nCamille",
    language: "fr",
    ai: true,
    reason: null,
    kept: false,
    failed: false,
    ...extra,
  },
});

describe("Relancer une candidature (docs/38, décision du 14.11)", () => {
  it("écrit le message à l’ouverture, le montre en lecture, propose la messagerie, puis marque comme relancée", async () => {
    POST.mockResolvedValueOnce(draft({ ai: false, reason: "IA non configurée" }));
    POST.mockResolvedValueOnce({ data: { id: 3, status: "relancee" } });
    const wrapper = mount(FollowUpPanel, { props: { application: application as never } });
    await flushPromises();
    expect(POST.mock.calls[0]![0]).toBe("/api/applications/{application_id}/follow-up/draft");
    expect(POST.mock.calls[0]![1].params.query).toEqual({});
    expect(wrapper.find("[data-test=follow-up-subject-read]").text()).toContain("Relance – candidature DevOps Engineer");
    expect(wrapper.find("[data-test=follow-up-message]").text()).toContain("Camille");
    expect(wrapper.find("[data-test=follow-up-template]").text()).toContain("IA non configurée");
    const mail = wrapper.find("[data-test=follow-up-mail]").attributes("href")!;
    expect(mail.startsWith("mailto:rh%40exemple.ch?subject=Relance%20%E2%80%93%20candidature")).toBe(true);
    expect(mail).toContain("body=Madame%2C%20Monsieur");

    await wrapper.find("[data-test=follow-up-done]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[1]![0]).toBe("/api/applications/{application_id}/follow-up");
    expect(wrapper.emitted("done")).toHaveLength(1);
  });

  it("« Réécrire » demande un nouveau message", async () => {
    POST.mockResolvedValueOnce(draft({ kept: true }));
    POST.mockResolvedValueOnce(draft({ text: "Nouveau texte" }));
    const wrapper = mount(FollowUpPanel, { props: { application: application as never } });
    await flushPromises();
    await wrapper.find("[data-test=follow-up-rewrite]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[1]![1].params.query).toEqual({ rewrite: true });
    expect(wrapper.find("[data-test=follow-up-message]").text()).toContain("Nouveau texte");
  });

  it("« Modifier le message » rend objet et message modifiables, puis les garde", async () => {
    POST.mockResolvedValueOnce(draft());
    PUT.mockResolvedValueOnce(draft({ text: "Texte revu", kept: true }));
    const wrapper = mount(FollowUpPanel, { props: { application: application as never } });
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-text]").exists()).toBe(false);
    await wrapper.find("[data-test=follow-up-modify]").trigger("click");
    await wrapper.find("[data-test=follow-up-text]").setValue("Texte revu");
    await wrapper.find("[data-test=follow-up-save]").trigger("click");
    await flushPromises();
    expect(PUT.mock.calls[0]![0]).toBe("/api/applications/{application_id}/follow-up/draft");
    expect(PUT.mock.calls[0]![1].body.text).toBe("Texte revu");
    expect(wrapper.find("[data-test=follow-up-message]").text()).toContain("Texte revu");
  });

  it("écriture en échec : carte « Réessayer »", async () => {
    POST.mockResolvedValueOnce(draft({ failed: true }));
    POST.mockResolvedValueOnce(draft());
    const wrapper = mount(FollowUpPanel, { props: { application: application as never } });
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-failed]").exists()).toBe(true);
    expect(wrapper.find("[data-test=follow-up-mail]").exists()).toBe(false);
    await wrapper.find("[data-test=follow-up-retry]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-failed]").exists()).toBe(false);
    expect(wrapper.find("[data-test=follow-up-message]").exists()).toBe(true);
  });

  it("sans e-mail du contact : seulement « Copier la relance »", async () => {
    POST.mockResolvedValueOnce(draft());
    const wrapper = mount(FollowUpPanel, { props: { application: { ...application, contact_email: null } as never } });
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-mail]").exists()).toBe(false);
    expect(wrapper.find("[data-test=follow-up-copy]").exists()).toBe(true);
    expect(wrapper.find("[data-test=follow-up-template]").exists()).toBe(false);
  });
});
