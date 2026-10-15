import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FollowUpPanel from "./FollowUpPanel.vue";

const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));
afterEach(() => vi.resetAllMocks());

const application = {
  id: 3,
  job_title: "DevOps Engineer",
  company: "Exemple AG",
  sent_at: "2026-09-12",
  contact_email: "rh@exemple.ch",
};

describe("Relancer une candidature (docs/38)", () => {
  it("rédige, propose la messagerie (sans rien envoyer), puis marque comme relancée", async () => {
    POST.mockResolvedValueOnce({
      data: { subject: "Relance – candidature DevOps Engineer", text: "Madame, Monsieur, …\n\nCamille", language: "fr", ai: false, reason: "IA non configurée" },
    });
    POST.mockResolvedValueOnce({ data: { id: 3, status: "relancee" } });
    const wrapper = mount(FollowUpPanel, { props: { application: application as never } });
    await wrapper.find("[data-test=follow-up-write]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]![0]).toBe("/api/applications/{application_id}/follow-up/draft");
    expect(wrapper.find("[data-test=follow-up-template]").text()).toContain("IA non configurée");
    const mail = wrapper.find("[data-test=follow-up-mail]").attributes("href")!;
    expect(mail.startsWith("mailto:rh%40exemple.ch?subject=Relance%20%E2%80%93%20candidature")).toBe(true);
    expect(mail).toContain("body=Madame%2C%20Monsieur");

    await wrapper.find("[data-test=follow-up-done]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[1]![0]).toBe("/api/applications/{application_id}/follow-up");
    expect(wrapper.emitted("done")).toHaveLength(1);
  });

  it("sans e-mail du contact : seulement « Copier »", async () => {
    POST.mockResolvedValueOnce({ data: { subject: "S", text: "T", language: "fr", ai: true, reason: null } });
    const wrapper = mount(FollowUpPanel, { props: { application: { ...application, contact_email: null } as never } });
    await wrapper.find("[data-test=follow-up-write]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-mail]").exists()).toBe(false);
    expect(wrapper.find("[data-test=follow-up-copy]").exists()).toBe(true);
    expect(wrapper.find("[data-test=follow-up-template]").exists()).toBe(false);
  });
});
