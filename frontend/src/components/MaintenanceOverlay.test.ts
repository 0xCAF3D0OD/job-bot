import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h } from "vue";

import { MAINTENANCE_EVENT, MAINTENANCE_READ_EVENT } from "../api/client";
import { POLL_MS, READ_POLL_MS, useMaintenance } from "../composables/useMaintenance";
import MaintenanceOverlay from "./MaintenanceOverlay.vue";

const GET = vi.fn();
vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()),
  api: { GET: (...a: unknown[]) => GET(...a) },
}));

// Une page avec une saisie en cours, et la page d'attente par-dessus.
const Host = defineComponent({
  setup() {
    const { waiting, message, bypass, reading, refused, nextAt, retry } = useMaintenance();
    return () => [
      h("button", { "data-test": "probe-retry", onClick: () => void retry() }),
      nextAt.value ? h("p", { "data-test": "probe-next" }) : null,
      h("textarea", { "data-test": "draft" }),
      bypass.value ? h("p", { "data-test": "bypass" }, "rappel") : null,
      reading.value ? h("p", { "data-test": "reading" }, message.value ?? "") : null,
      refused.value ? h("p", { "data-test": "refused" }, refused.value) : null,
      h(MaintenanceOverlay, { waiting: waiting.value, message: message.value }),
    ];
  },
});

function state(body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } });
}

beforeEach(() => {
  document.body.innerHTML = '<div id="app"></div>';
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("page de maintenance (docs/79)", () => {
  it("se pose par-dessus, sonde toutes les 10 s, puis rend la page telle quelle", async () => {
    GET.mockResolvedValue({ data: { active: false, reason: null, message: null, bypass: false } });
    const fetch = vi.fn().mockResolvedValueOnce(state({ active: true, message: "Dix minutes", bypass: false }));
    fetch.mockResolvedValue(state({ active: false, message: null, bypass: false }));
    vi.stubGlobal("fetch", fetch);
    const wrapper = mount(Host, { attachTo: "#app" });
    await flushPromises();
    await wrapper.find("[data-test=draft]").setValue("Ma lettre à moitié écrite");
    (wrapper.find("[data-test=draft]").element as HTMLTextAreaElement).focus();

    window.dispatchEvent(new CustomEvent(MAINTENANCE_EVENT, { detail: null }));
    await flushPromises();
    const overlay = document.querySelector("[data-test=maintenance]");
    expect(overlay?.querySelector("h1")?.textContent?.trim()).toBe("jobA1 se met à jour");
    expect(overlay?.textContent).toContain("Ça revient dans un instant. Ce que tu écrivais est gardé.");
    expect(document.getElementById("app")?.hasAttribute("inert")).toBe(true);
    expect(document.activeElement).toBe(overlay);

    await vi.advanceTimersByTimeAsync(POLL_MS);
    // Une maintenance annoncée : son titre, et le message de l'exploitant.
    expect(document.querySelector("[data-test=maintenance] h1")?.textContent?.trim()).toBe("Maintenance en cours");
    expect(document.querySelector("[data-test=maintenance]")?.textContent).toContain("Dix minutes");
    await vi.advanceTimersByTimeAsync(POLL_MS);
    expect(document.querySelector("[data-test=maintenance]")).toBeNull();
    expect(document.getElementById("app")?.hasAttribute("inert")).toBe(false);
    expect((wrapper.find("[data-test=draft]").element as HTMLTextAreaElement).value).toBe("Ma lettre à moitié écrite");
    // Le curseur revient dans la lettre (docs/81 §2).
    expect(document.activeElement).toBe(wrapper.find("[data-test=draft]").element);
    expect(fetch).toHaveBeenCalledTimes(2);
    wrapper.unmount();
  });

  it("l'exploitant qui passe pendant une maintenance annoncée la voit rappelée", async () => {
    GET.mockResolvedValue({ data: { active: true, reason: "announced", message: null, bypass: true } });
    const wrapper = mount(Host, { attachTo: "#app" });
    await flushPromises();
    expect(wrapper.find("[data-test=bypass]").exists()).toBe(true);
    expect(document.querySelector("[data-test=maintenance]")).toBeNull();
    wrapper.unmount();
  });
});

describe("maintenance en lecture seule (docs/80)", () => {
  it("un bandeau, un message si l'on enregistre, puis plus rien quand elle est levée", async () => {
    GET.mockResolvedValue({ data: { active: true, reason: "announced", mode: "lecture", message: "Sauvegarde", bypass: false } });
    const fetch = vi.fn().mockResolvedValue(state({ active: false, mode: "complete", message: null, bypass: false }));
    vi.stubGlobal("fetch", fetch);
    const wrapper = mount(Host, { attachTo: "#app" });
    await flushPromises();
    expect(wrapper.find("[data-test=reading]").text()).toBe("Sauvegarde");
    // Une écriture refusée : un message, pas de page d'attente ; la saisie reste.
    await wrapper.find("[data-test=draft]").setValue("Brouillon");
    window.dispatchEvent(new CustomEvent(MAINTENANCE_READ_EVENT, { detail: "Sauvegarde" }));
    await flushPromises();
    expect(wrapper.find("[data-test=refused]").text()).toContain("tu peux consulter, pas encore enregistrer");
    expect(document.querySelector("[data-test=maintenance]")).toBeNull();
    await vi.advanceTimersByTimeAsync(READ_POLL_MS);
    expect(wrapper.find("[data-test=reading]").exists()).toBe(false);
    expect((wrapper.find("[data-test=draft]").element as HTMLTextAreaElement).value).toBe("Brouillon");
    wrapper.unmount();
  });
});

describe("page de maintenance, mise en page (maquettes Maintenance du 2026-11-05)", () => {
  it("le compte à rebours du prochain essai, et « Réessayer maintenant »", async () => {
    const wrapper = mount(MaintenanceOverlay, {
      props: { waiting: true, message: null, nextAt: Date.now() + POLL_MS },
      attachTo: "#app",
    });
    await flushPromises();
    const next = () => document.querySelector("[data-test=maintenance-next]")?.textContent;
    expect(next()?.trim()).toBe("Nouvel essai dans 10 s");
    await vi.advanceTimersByTimeAsync(3000);
    expect(next()?.trim()).toBe("Nouvel essai dans 7 s");
    (document.querySelector("[data-test=maintenance-retry]") as HTMLButtonElement).click();
    await flushPromises();
    expect(wrapper.emitted("retry")).toHaveLength(1);
    expect(next()?.trim()).toBe("Nouvel essai en cours…");
    // La mise à jour (scène « mise-a-jour », §15) : 340 px, 409 sur ordinateur, décorative ; pas d'en-tête sur
    // téléphone (le logo seul n'apparaît que sur ordinateur, maquette du 8 novembre).
    const person = document.querySelector("[data-test=maintenance-person]");
    expect(person?.getAttribute("src")).toContain("/troupe/mise-a-jour-680");
    expect(person?.getAttribute("srcset")).toContain("/troupe/mise-a-jour-818");
    expect(person?.getAttribute("alt")).toBe("");
    expect(person?.getAttribute("width")).toBe("340");
    expect(document.querySelector(".maintenance header")).toBeNull();
    wrapper.unmount();
  });

  it("une maintenance annoncée : la scène « maintenance » (§15)", async () => {
    const wrapper = mount(MaintenanceOverlay, { props: { waiting: true, message: "De retour à 14 h.", nextAt: null }, attachTo: "#app" });
    await flushPromises();
    expect(document.querySelector("[data-test=maintenance] h1")?.textContent?.trim()).toBe("Maintenance en cours");
    expect(document.querySelector("[data-test=maintenance-person]")?.getAttribute("data-scene")).toBe("maintenance");
    wrapper.unmount();
  });

  it("hors ligne : « Pas de connexion », puis le titre de la mise à jour quand le réseau revient", async () => {
    const online = vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
    const wrapper = mount(MaintenanceOverlay, { props: { waiting: true, message: null, nextAt: null }, attachTo: "#app" });
    await flushPromises();
    const title = () => document.querySelector("[data-test=maintenance] h1")?.textContent?.trim();
    expect(title()).toBe("Pas de connexion");
    expect(document.querySelector("[data-test=maintenance]")?.textContent).toContain("Vérifie le Wi‑Fi ou les données mobiles.");
    // L'équipe rebranche la prise (scène « hors-ligne », §15), distincte de la mise à jour.
    const pose = () => document.querySelector("[data-test=maintenance-person]")?.getAttribute("data-scene");
    expect(pose()).toBe("hors-ligne");
    online.mockReturnValue(true);
    window.dispatchEvent(new Event("online"));
    await flushPromises();
    expect(title()).toBe("jobA1 se met à jour");
    expect(pose()).toBe("mise-a-jour");
    online.mockRestore();
    wrapper.unmount();
  });

  it("« Réessayer maintenant » sonde tout de suite, sans attendre les 10 s", async () => {
    GET.mockResolvedValue({ data: { active: false, reason: null, message: null, bypass: false } });
    const fetch = vi.fn().mockResolvedValue(state({ active: false, message: null, bypass: false }));
    vi.stubGlobal("fetch", fetch);
    const wrapper = mount(Host, { attachTo: "#app" });
    await flushPromises();
    window.dispatchEvent(new CustomEvent(MAINTENANCE_EVENT, { detail: null }));
    await flushPromises();
    expect(document.querySelector("[data-test=maintenance]")).not.toBeNull();
    expect(wrapper.find("[data-test=probe-next]").exists()).toBe(true);
    await wrapper.find("[data-test=probe-retry]").trigger("click");
    await flushPromises();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(document.querySelector("[data-test=maintenance]")).toBeNull();
    wrapper.unmount();
});
});
