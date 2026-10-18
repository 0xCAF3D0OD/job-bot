import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h } from "vue";

import { MAINTENANCE_EVENT } from "../api/client";
import { POLL_MS, useMaintenance } from "../composables/useMaintenance";
import MaintenanceOverlay from "./MaintenanceOverlay.vue";

const GET = vi.fn();
vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()),
  api: { GET: (...a: unknown[]) => GET(...a) },
}));

// Une page avec une saisie en cours, et la page d'attente par-dessus.
const Host = defineComponent({
  setup() {
    const { waiting, message, bypass } = useMaintenance();
    return () => [
      h("textarea", { "data-test": "draft" }),
      bypass.value ? h("p", { "data-test": "bypass" }, "rappel") : null,
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

    window.dispatchEvent(new CustomEvent(MAINTENANCE_EVENT, { detail: null }));
    await flushPromises();
    const overlay = document.querySelector("[data-test=maintenance]");
    expect(overlay?.textContent).toContain("jobA1 revient dans un instant");
    expect(document.getElementById("app")?.hasAttribute("inert")).toBe(true);
    expect(document.activeElement).toBe(overlay);

    await vi.advanceTimersByTimeAsync(POLL_MS);
    expect(document.querySelector("[data-test=maintenance]")?.textContent).toContain("Dix minutes");
    await vi.advanceTimersByTimeAsync(POLL_MS);
    expect(document.querySelector("[data-test=maintenance]")).toBeNull();
    expect(document.getElementById("app")?.hasAttribute("inert")).toBe(false);
    expect((wrapper.find("[data-test=draft]").element as HTMLTextAreaElement).value).toBe("Ma lettre à moitié écrite");
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
