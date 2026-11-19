import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import WelcomeAlertSteps from "./WelcomeAlertSteps.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
enableAutoUnmount(afterEach);
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-11-16T20:00:00Z"));
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
const PROPS = { desk: true, searchLabel: "DevOps · Lausanne", url: "https://www.jobup.ch/fr/emplois/?term=DevOps", mailbox: "alertes+lea@joba1.ch" };
const current = (w: ReturnType<typeof mount>) =>
  w.findAll("li.wa-step").findIndex((li) => li.attributes("aria-current") === "step") + 1;
const cells = (w: ReturnType<typeof mount>) => w.get("[data-test=welcome-code]").findAll("span").map((s) => s.text()).join("");

describe("Crée ton alerte sur jobup (section 41 du paquet du 16.11)", () => {
  it("4 étapes ; ouvrir jobup fait passer à l’étape 3, qui attend le code", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(WelcomeAlertSteps, { props: PROPS });
    await flushPromises();
    expect(wrapper.findAll("li.wa-step")).toHaveLength(4);
    expect(current(wrapper)).toBe(1);
    const open = wrapper.get("[data-test=wizard-open]");
    expect(open.attributes("target")).toBe("_blank");
    expect(open.text()).toContain("Ouvrir jobup");
    expect(open.text()).not.toContain("avec ma recherche");
    expect(open.classes()).not.toContain("primary-link");
    await open.trigger("click");
    expect(current(wrapper)).toBe(3);
    expect(wrapper.find("[data-test=wizard-reopen]").exists()).toBe(true);
    const waiting = wrapper.get("[data-test=code-waiting]");
    expect(waiting.attributes("role")).toBe("status");
    expect(waiting.text()).toContain("En attente du code de jobup");
  });

  it("le code s’affiche dans 6 cases en lecture seule ; l’étape 4 devient l’étape en cours", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    GET.mockResolvedValue({ data: code(1) });
    const wrapper = mount(WelcomeAlertSteps, { props: PROPS });
    await flushPromises();
    expect(cells(wrapper)).toBe("482913");
    expect(wrapper.find("input").exists()).toBe(false);
    expect(wrapper.find("[contenteditable]").exists()).toBe(false);
    expect(current(wrapper)).toBe(4);
    expect(wrapper.text()).toContain("Colle le code sur jobup et valide l’alerte");
    expect(wrapper.emitted("update:received")?.at(-1)).toEqual([true]);
    await wrapper.get("[data-test=code-box-copy]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("482913");
  });

  it("un code périmé : le texte orange, puis le nouveau code s’affiche tout seul", async () => {
    GET.mockResolvedValue({ data: code(9) });
    const wrapper = mount(WelcomeAlertSteps, { props: PROPS });
    await flushPromises();
    expect(cells(wrapper)).toBe("482913");
    await vi.advanceTimersByTimeAsync(60_000);
    expect(wrapper.get("[data-test=code-expired]").text()).toBe("Ce code a expiré. Sur jobup, demande un nouveau code : il s’affichera ici.");
    expect(cells(wrapper)).toBe("");
    expect(current(wrapper)).toBe(3);
    expect(wrapper.emitted("update:received")?.at(-1)).toEqual([false]);
    GET.mockResolvedValue({ data: code(0, "105277") });
    await vi.advanceTimersByTimeAsync(5000);
    expect(cells(wrapper)).toBe("105277");
    expect(current(wrapper)).toBe(4);
  });

  it("le code n’est jamais écrit dans la console", async () => {
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) => vi.spyOn(console, m).mockImplementation(() => undefined));
    GET.mockResolvedValue({ data: code(1, "731904") });
    mount(WelcomeAlertSteps, { props: PROPS });
    await flushPromises();
    await vi.advanceTimersByTimeAsync(20 * 60_000);
    for (const spy of spies) expect(JSON.stringify(spy.mock.calls)).not.toContain("731904");
  });
});
