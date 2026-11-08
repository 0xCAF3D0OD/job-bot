import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import ApplicationSent from "../components/ApplicationSent.vue";
import MaintenanceOverlay from "../components/MaintenanceOverlay.vue";

// Ordinateur : la requête de 1 024 px répond oui, celle du téléphone non (maquette du 8 novembre, lot 8).
vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: (query?: string) => ({ phone: ref(query === "(min-width: 1024px)") }),
  useNarrow: () => ({ phone: ref(false) }),
}));
afterEach(() => vi.restoreAllMocks());

const router = () => createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

describe("Pages d'état sur ordinateur (maquette du 8 novembre)", () => {
  it("maintenance : le logo seul en haut, le personnage à 240 px, le prochain essai en toutes lettres", async () => {
    const app = document.createElement("div");
    app.id = "app";
    document.body.appendChild(app);
    const wrapper = mount(MaintenanceOverlay, { props: { waiting: true, message: null, nextAt: Date.now() + 30_000 }, attachTo: "#app" });
    await flushPromises();
    expect(document.querySelector(".maintenance-brand")?.textContent).toContain("jobA1");
    expect(document.querySelector("[data-test=maintenance-next]")?.textContent?.trim()).toMatch(/^Nouvel essai automatique dans \d+ secondes$/);
    wrapper.unmount();
    app.remove();
  });

  it("hors ligne : « le câble réseau » au lieu des données mobiles", async () => {
    vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
    const wrapper = mount(MaintenanceOverlay, { props: { waiting: true, message: null, nextAt: null }, attachTo: document.body });
    await flushPromises();
    expect(document.querySelector(".maintenance-message")?.textContent).toContain("le câble réseau");
    wrapper.unmount();
  });

  it("candidature envoyée : la fin du titre manuscrite", async () => {
    const r = router();
    await r.push("/");
    const wrapper = mount(ApplicationSent, { props: { title: "DevOps Engineer", company: "Alpstack" }, global: { plugins: [r] } });
    expect(wrapper.find("h1").text()).toBe("Candidature envoyée.");
    expect(wrapper.find(".sent-screen-hand").text()).toBe("envoyée.");
  });
});
