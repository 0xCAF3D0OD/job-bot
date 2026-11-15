import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import JobupCodeBox from "./JobupCodeBox.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const NOW = new Date("2026-11-15T13:00:00Z");
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW);
  POST.mockResolvedValue({ data: { queued: true } });
});
afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
});

const code = (minutesAgo: number, value = "482913", valid = 10) => ({
  code: value,
  received_at: new Date(Date.now() - minutesAgo * 60_000).toISOString(),
  valid_minutes: valid,
});

describe("Recopie le code de jobup (section 15 du paquet du 15.11)", () => {
  it("attente, puis le code dès qu’il arrive ; la relecture s’arrête", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: "https://www.jobup.ch/?term=DevOps" } });
    await flushPromises();
    const box = wrapper.get("[data-test=code-box]");
    expect(box.attributes("role")).toBe("status");
    expect(box.attributes("aria-live")).toBe("polite");
    expect(box.text()).toBe("En attente du code de jobup…");
    GET.mockResolvedValue({ data: code(0, "482913", 15) });
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.get("[data-test=code-box-value]").text()).toBe("482 913");
    expect(wrapper.get("[data-test=code-box-received]").text()).toBe("Reçu à 14 h · valable 15 minutes");
    const calls = GET.mock.calls.length;
    await vi.advanceTimersByTimeAsync(30_000);
    expect(GET.mock.calls.length).toBe(calls);
    expect(GET).toHaveBeenCalledWith("/api/alert-searches/codes/last", { params: { query: { site: "jobup" } } });
  });

  it("le code à copier, puis expiré à la fin de sa validité ; « Renvoyer » rouvre jobup et attend le suivant", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    GET.mockResolvedValue({ data: code(2) });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: "https://www.jobup.ch/?term=DevOps" } });
    await flushPromises();
    await wrapper.get("[data-test=code-box-copy]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("482913");
    expect(wrapper.get("[data-test=code-box-copy]").text()).toBe("Copié");
    await vi.advanceTimersByTimeAsync(8 * 60_000);
    expect(wrapper.get("[data-test=code-box]").text()).toContain("Code expiré");
    const resend = wrapper.get("[data-test=code-box-resend]");
    expect(resend.attributes("href")).toBe("https://www.jobup.ch/?term=DevOps");
    expect(resend.attributes("aria-label")).toBe("Renvoyer le code depuis jobup");
    await resend.trigger("click");
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/expect-code");
    expect(wrapper.get("[data-test=code-box]").text()).toBe("En attente du code de jobup…");
    // L'ancien code ne revient pas : seul un nouveau le remplace.
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.find("[data-test=code-box-value]").exists()).toBe(false);
    GET.mockResolvedValue({ data: code(0, "731205") });
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.get("[data-test=code-box-value]").text()).toBe("731 205");
  });

  it("10 minutes sans code : expiré, et plus de relecture", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: "https://www.jobup.ch/" } });
    await flushPromises();
    await vi.advanceTimersByTimeAsync(10 * 60_000 + 5000);
    expect(wrapper.get("[data-test=code-box]").text()).toContain("Code expiré");
    const calls = GET.mock.calls.length;
    await vi.advanceTimersByTimeAsync(60_000);
    expect(GET.mock.calls.length).toBe(calls);
  });

  it("écran caché : pas de relecture ; elle reprend quand il revient", async () => {
    GET.mockResolvedValue({ data: null });
    let visibility = "hidden";
    vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility as DocumentVisibilityState);
    mount(JobupCodeBox, { props: { siteUrl: null } });
    await flushPromises();
    await vi.advanceTimersByTimeAsync(30_000);
    expect(GET).not.toHaveBeenCalled();
    visibility = "visible";
    document.dispatchEvent(new Event("visibilitychange"));
    await flushPromises();
    expect(GET).toHaveBeenCalledTimes(1);
  });
});
