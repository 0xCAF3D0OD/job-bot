import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import JobupCodeBox from "./JobupCodeBox.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
enableAutoUnmount(afterEach);
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

const WATCH = ["/api/alert-searches/watch-code"] as const;
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
    expect(POST).toHaveBeenCalledWith(...WATCH);
    expect(wrapper.get("[data-test=code-box]").text()).toBe("En attente du code de jobup…");
    // L'ancien code ne revient pas : seul un nouveau le remplace.
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.find("[data-test=code-box-value]").exists()).toBe(false);
    GET.mockResolvedValue({ data: code(0, "731205") });
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.get("[data-test=code-box-value]").text()).toBe("731 205");
  });

  it("10 minutes sans code : pas d’« expiré » (aucun code reçu), toujours en attente, plus de relecture", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: "https://www.jobup.ch/" } });
    await flushPromises();
    await vi.advanceTimersByTimeAsync(10 * 60_000 + 5000);
    expect(wrapper.get("[data-test=code-box]").text()).toBe("En attente du code de jobup…");
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

  // Décision de Kevin du 15.11 : le serveur relève la boîte tant que l'étape attend, 10 minutes au plus.
  it.each([
    ["à 20 s", 20_000],
    ["à 4 min", 4 * 60_000],
    ["à 9 min", 9 * 60_000],
  ])("code reçu %s : relance chaque minute, puis plus rien", async (_label, at) => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: null } });
    await flushPromises();
    expect(POST).toHaveBeenCalledTimes(1);
    expect(POST).toHaveBeenCalledWith(...WATCH);
    await vi.advanceTimersByTimeAsync(at);
    expect(POST).toHaveBeenCalledTimes(1 + Math.floor(at / 60_000));
    GET.mockResolvedValue({ data: code(0) });
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.find("[data-test=code-box-value]").exists()).toBe(true);
    const asked = POST.mock.calls.length;
    await vi.advanceTimersByTimeAsync(5 * 60_000);
    expect(POST).toHaveBeenCalledTimes(asked);
  });

  it("jamais reçu : relance jusqu’à 10 minutes, puis arrêt", async () => {
    GET.mockResolvedValue({ data: null });
    mount(JobupCodeBox, { props: { siteUrl: null } });
    await flushPromises();
    await vi.advanceTimersByTimeAsync(10 * 60_000 + 5000);
    expect(POST).toHaveBeenCalledTimes(10);
    await vi.advanceTimersByTimeAsync(5 * 60_000);
    expect(POST).toHaveBeenCalledTimes(10);
  });

  it("onglet caché : plus de relance ; elle reprend au retour, et la fermeture l’arrête", async () => {
    GET.mockResolvedValue({ data: null });
    let visibility = "visible";
    vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility as DocumentVisibilityState);
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: null } });
    await flushPromises();
    visibility = "hidden";
    await vi.advanceTimersByTimeAsync(3 * 60_000);
    expect(POST).toHaveBeenCalledTimes(1);
    visibility = "visible";
    document.dispatchEvent(new Event("visibilitychange"));
    await flushPromises();
    expect(POST).toHaveBeenCalledTimes(2);
    wrapper.unmount();
    await vi.advanceTimersByTimeAsync(3 * 60_000);
    expect(POST).toHaveBeenCalledTimes(2);
  });

  it("la boîte jobA1 ne répond pas (3 échecs), puis répond : la ligne d’attente revient", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: null } });
    await flushPromises();
    // Les trois premières lectures ratent : à la relance suivante, le serveur dit que la boîte est muette.
    POST.mockResolvedValue({ data: { queued: true, mailbox_down: true } });
    await vi.advanceTimersByTimeAsync(60_000);
    const box = wrapper.get("[data-test=code-box]");
    expect(box.text()).toBe("La boîte jobA1 ne répond pas. On réessaie dans 1 minute.");
    expect(box.attributes("role")).toBe("status");
    expect(box.find("[data-icon=alert]").exists()).toBe(true);
    expect(box.text()).not.toMatch(/IMAP|Infomaniak|erreur/i);
    // Muette, l'étape demande l'état à chaque relecture ; la lecture suivante réussit.
    const asked = POST.mock.calls.length;
    POST.mockResolvedValue({ data: { queued: true, mailbox_down: false } });
    await vi.advanceTimersByTimeAsync(5000);
    expect(POST.mock.calls.length).toBe(asked + 1);
    expect(box.text()).toBe("En attente du code de jobup…");
    // Revenue à la normale, la relance reprend son rythme d'une par minute.
    await vi.advanceTimersByTimeAsync(30_000);
    expect(POST.mock.calls.length).toBe(asked + 1);
  });

  // Section 24 du paquet du 15.11 : le trajet du code en 3 points, sur l’étape des premiers pas.
  const notes = (w: ReturnType<typeof mount>) =>
    w.findAll(".code-trail-point").map((p) => [p.get("b").text(), p.get("span:last-child").text(), p.get(".code-trail-dot").classes()[1]]);

  it("trajet, ordinateur : attente, 2 actif, ligne d’état et « Toujours rien ? » à 2 minutes ; puis reçu, 3 coches", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: null, trail: "ordinateur" } });
    await flushPromises();
    const trail = wrapper.get("[data-test=code-trail]");
    expect(trail.attributes("role")).toBe("status");
    expect(trail.attributes("aria-live")).toBe("polite");
    expect(wrapper.find("[data-test=code-box]").exists()).toBe(false);
    expect(notes(wrapper)).toEqual([
      ["jobup", "envoie le code", "todo"],
      ["Ta boîte jobA1", "on écoute", "on"],
      ["Cette page", "le code s’affiche", "todo"],
    ]);
    expect(trail.text()).toContain("Rien reçu pour l’instant. Valide l’alerte sur jobup, on vérifie toutes les 15 s.");
    await vi.advanceTimersByTimeAsync(115_000);
    expect(wrapper.find("[data-test=code-trail-late]").exists()).toBe(false);
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.get("[data-test=code-trail-late]").text()).toBe("Toujours rien ? Vérifie que l’adresse est bien collée dans jobup.");
    GET.mockResolvedValue({ data: code(0) });
    await vi.advanceTimersByTimeAsync(5000);
    expect(notes(wrapper)).toEqual([
      ["jobup", "code envoyé", "ok"],
      ["Ta boîte jobA1", "code reçu", "ok"],
      ["Cette page", "code affiché", "ok"],
    ]);
    expect(wrapper.get("[data-test=code-trail]").attributes("role")).toBeUndefined();
    expect(wrapper.get("[data-test=code-box-value]").text()).toBe("482 913");
    expect(wrapper.find("[data-test=code-trail-late]").exists()).toBe(false);
  });

  it("trajet, téléphone : « Boîte jobA1 », sans la fréquence ; 10 min sans code : en attente ; code périmé : 3 en alerte", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: "https://www.jobup.ch/", trail: "telephone" } });
    await flushPromises();
    expect(notes(wrapper)[1]).toEqual(["Boîte jobA1", "on écoute", "on"]);
    expect(notes(wrapper)[2]).toEqual(["Cette page", "s’affiche ici", "todo"]);
    expect(wrapper.get(".code-trail-status").text()).toBe("Rien reçu pour l’instant. Valide l’alerte sur jobup.");
    await vi.advanceTimersByTimeAsync(10 * 60_000);
    // Aucun code reçu : pas d'état inventé, l'attente reste avec son aide (Kevin, 16.11).
    expect(notes(wrapper)).toEqual([
      ["jobup", "envoie le code", "todo"],
      ["Boîte jobA1", "on écoute", "on"],
      ["Cette page", "s’affiche ici", "todo"],
    ]);
    expect(wrapper.find("[data-test=code-trail-late]").exists()).toBe(true);
    expect(wrapper.find("[data-test=code-box]").exists()).toBe(false);
    // Un code reçu puis périmé : « Code expiré ».
    await wrapper.vm.restart();
    GET.mockResolvedValue({ data: code(0) });
    await vi.advanceTimersByTimeAsync(5000);
    await vi.advanceTimersByTimeAsync(10 * 60_000);
    expect(notes(wrapper)).toEqual([
      ["jobup", "code envoyé", "ok"],
      ["Boîte jobA1", "code reçu", "ok"],
      ["Cette page", "code expiré", "bad"],
    ]);
    expect(wrapper.get("[data-test=code-box]").text()).toContain("Code expiré");
  });

  it("trajet : la boîte jobA1 ne répond pas, la ligne d’état le dit, puis revient", async () => {
    GET.mockResolvedValue({ data: null });
    const wrapper = mount(JobupCodeBox, { props: { siteUrl: null, trail: "ordinateur" } });
    await flushPromises();
    POST.mockResolvedValue({ data: { queued: true, mailbox_down: true } });
    await vi.advanceTimersByTimeAsync(120_000);
    const line = wrapper.get(".code-trail-status");
    expect(line.text()).toBe("La boîte jobA1 ne répond pas. On réessaie dans 1 minute.");
    expect(line.find("[data-icon=alert]").exists()).toBe(true);
    expect(wrapper.find("[data-test=code-trail-late]").exists()).toBe(false);
    expect(wrapper.get("[data-test=code-trail]").attributes("role")).toBe("status");
    expect(notes(wrapper)[1]).toEqual(["Ta boîte jobA1", "ne répond pas", "bad"]);
    expect(wrapper.findAll(".code-trail-dot")[1]?.find("[data-icon=alert-circle]").exists()).toBe(true);
    POST.mockResolvedValue({ data: { queued: true, mailbox_down: false } });
    await vi.advanceTimersByTimeAsync(5000);
    expect(wrapper.get(".code-trail-status").text()).toContain("Rien reçu pour l’instant.");
    expect(notes(wrapper)[1]).toEqual(["Ta boîte jobA1", "on écoute", "on"]);
    expect(wrapper.find("[data-test=code-trail-late]").exists()).toBe(true);
  });
});
