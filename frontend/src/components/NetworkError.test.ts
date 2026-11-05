import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import { isNetworkError } from "../network";
import NetworkError from "./NetworkError.vue";

describe("Pas de connexion (planche « Illustrations »)", () => {
  it("l'illustration, le titre, la promesse tenue : « Réessayer » et le retour du réseau relancent", async () => {
    const wrapper = mount(NetworkError);
    expect(wrapper.find(".illu").exists()).toBe(true);
    expect(wrapper.find(".face-mark").exists()).toBe(false);
    expect(wrapper.find(".face-state-title").text()).toBe("Pas de connexion");
    expect(wrapper.text()).toContain("jobA1 réessaie dès que le réseau revient.");
    await wrapper.find("[data-test=network-retry]").trigger("click");
    expect(wrapper.emitted("retry")).toHaveLength(1);
    window.dispatchEvent(new Event("online"));
    const events = wrapper.emitted("retry")!;
    expect(events).toHaveLength(2);
    // Démonté, il n'écoute plus.
    wrapper.unmount();
    window.dispatchEvent(new Event("online"));
    expect(events).toHaveLength(2);
  });

  it("téléphone (maquette ErreurConnexion) : le triangle qui dit « non », pas l'illustration", async () => {
    const wrapper = mount(NetworkError, { props: { title: "Connexion perdue", line: "Vérifie ta connexion." } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.find(".illu").exists()).toBe(false);
    expect(wrapper.find("[data-mood-animation=hochement]").exists()).toBe(true);
  });

  it("une panne de réseau, pas une erreur du serveur", () => {
    expect(isNetworkError(new TypeError("Failed to fetch"))).toBe(true);
    expect(isNetworkError(new Error("500"))).toBe(false);
  });
});
