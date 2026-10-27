import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import SiteCodes from "./SiteCodes.vue";
import SiteMail from "./SiteMail.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
});

const code = { search_id: 1, site: "jobup", code: "482913", received_at: "2026-10-21T12:32:00Z" };

describe("Les codes des sites (docs/112)", () => {
  it("le code en grand, à copier", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const wrapper = mount(SiteCodes, { props: { codes: [code] } });
    expect(wrapper.find("[data-test=site-code]").text()).toContain("Code jobup · reçu à 14:32");
    expect(wrapper.find("[data-test=site-code-value]").text()).toBe("482 913");
    await wrapper.find("[data-test=site-code-copy]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("482913");
    expect(wrapper.find("[data-test=site-code-copy]").text()).toBe("Copié");
  });

  it("« J'attends un code » : la page se met à jour jusqu'à son arrivée", async () => {
    vi.useFakeTimers();
    POST.mockResolvedValueOnce({ data: { queued: true } });
    GET.mockResolvedValue({ data: [] });
    const wrapper = mount(SiteMail, { props: { codes: [], guestMailbox: true } });
    await flushPromises();
    await wrapper.find("[data-test=site-code-expect]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/expect-code");
    expect(wrapper.text()).toContain("J'attends le code, pendant 5 minutes.");
    await vi.advanceTimersByTimeAsync(10_000);
    expect(wrapper.emitted("refresh")).toHaveLength(1);
    await wrapper.setProps({ codes: [code] });
    await vi.advanceTimersByTimeAsync(20_000);
    expect(wrapper.emitted("refresh")).toHaveLength(1);
    // Le code prend la place de « J'attends un code », dans la carte (0.84.2).
    expect(wrapper.find("[data-test=site-code-value]").text()).toBe("482 913");
    expect(wrapper.find("[data-test=site-code-expect]").exists()).toBe(false);
  });

  it("trop de relevés rapides : il le dit", async () => {
    POST.mockResolvedValueOnce({ data: { queued: false } });
    GET.mockResolvedValue({ data: [] });
    const wrapper = mount(SiteMail, { props: { codes: [], guestMailbox: false } });
    await flushPromises();
    await wrapper.find("[data-test=site-code-expect]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Déjà six relevés rapides");
  });

  it("les messages des sites, le texte à l'ouverture", async () => {
    GET.mockResolvedValueOnce({ data: [{ id: 7, site: "jobup", subject: "Bienvenue sur jobup", received_at: "2026-10-21T08:00:00Z" }] });
    GET.mockResolvedValueOnce({ data: { text: "Ton compte est prêt." } });
    const wrapper = mount(SiteMail, { props: { codes: [], guestMailbox: true } });
    await flushPromises();
    // L'invité : le code arrive dans la boîte de jobA1, dit sur la ligne du code (1.6.70).
    expect(wrapper.find("[data-test=site-code-row]").text()).toContain("la boîte de jobA1");
    expect(wrapper.find("[data-test=site-message]").text()).toContain("Bienvenue sur jobup");
    await wrapper.find("[data-test=site-message] button").trigger("click");
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/api/alert-searches/messages/{search_id}", { params: { path: { search_id: 7 } } });
    expect(wrapper.text()).toContain("Ton compte est prêt.");
  });

  it("sans message, rien", async () => {
    GET.mockResolvedValueOnce({ data: [] });
    const wrapper = mount(SiteMail, { props: { codes: [], guestMailbox: false } });
    await flushPromises();
    expect(wrapper.find("[data-test=site-messages]").exists()).toBe(false);
    expect(wrapper.find("[data-test=site-code-row]").text()).not.toContain("jobA1");
    // La rubrique reste : « J'attends un code » sert même sans message.
    expect(wrapper.find("[data-test=site-code-expect]").exists()).toBe(true);
  });
});
