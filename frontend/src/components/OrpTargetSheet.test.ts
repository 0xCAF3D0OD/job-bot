import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import OrpTargetSheet from "./OrpTargetSheet.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) } }));
afterEach(() => vi.resetAllMocks());

const SETTINGS = { orp_monthly_target: 10, orp_due_day: 5, notify_orp: true };
function sheet(target: number | null) {
  GET.mockResolvedValue({ data: SETTINGS });
  PUT.mockImplementation((_path: string, { body }: { body: typeof SETTINGS }) => Promise.resolve({ data: body }));
  return mount(OrpTargetSheet, { attachTo: document.body, props: { open: true, target } });
}

describe("« Objectif du mois » (PR 50)", () => {
  it("la phrase, le compteur nommé, la note du mois courant, « Annuler » et « Enregistrer »", () => {
    const wrapper = sheet(10);
    expect(wrapper.find(".sheet-title").text()).toBe("Objectif du mois");
    expect(wrapper.find("dialog").classes()).toContain("sheet-float");
    expect(wrapper.find(".goal-lead").text()).toBe("Le nombre de recherches que ton conseiller ORP te demande chaque mois.");
    const value = wrapper.find("[data-test=goal-value]");
    expect(value.attributes()).toMatchObject({ role: "spinbutton", tabindex: "0", "aria-label": "Recherches par mois", "aria-valuenow": "10", "aria-valuemin": "1", "aria-valuemax": "99" });
    expect(value.text()).toBe("10recherches par mois");
    expect(wrapper.find("[data-test=goal-less]").attributes("aria-label")).toBe("Une recherche de moins");
    expect(wrapper.find("[data-test=goal-more]").attributes("aria-label")).toBe("Une recherche de plus");
    const month = new Intl.DateTimeFormat("fr-CH", { month: "long", timeZone: "Europe/Zurich" }).format(new Date());
    expect(wrapper.find("[data-test=goal-note]").text()).toBe(`S’applique dès ${month}. Les mois déjà remis ne changent pas.`);
    expect(wrapper.findAll(".sheet-actions button").map((b) => b.text())).toEqual(["Annuler", "Enregistrer"]);
    wrapper.unmount();
  });

  it("deux fois « plus », puis « Enregistrer » : seul l’objectif change dans les réglages", async () => {
    const wrapper = sheet(10);
    await wrapper.find("[data-test=goal-more]").trigger("click");
    await wrapper.find("[data-test=goal-more]").trigger("click");
    expect(wrapper.find(".goal-number").text()).toBe("12");
    await wrapper.find("[data-test=goal-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/settings", { body: { ...SETTINGS, orp_monthly_target: 12 } });
    expect(wrapper.emitted("saved")).toEqual([[12]]);
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("flèches haut et bas, Début et Fin ; aux bornes, le bouton est désactivé et une phrase le dit", async () => {
    const wrapper = sheet(98);
    const value = wrapper.find("[data-test=goal-value]");
    await value.trigger("keydown", { key: "ArrowUp" });
    await value.trigger("keydown", { key: "ArrowUp" });
    expect(value.attributes("aria-valuenow")).toBe("99");
    expect(wrapper.find("[data-test=goal-more]").attributes("disabled")).toBeDefined();
    expect(wrapper.find("[data-test=goal-bound]").text()).toBe("99 est le maximum.");
    await value.trigger("keydown", { key: "ArrowDown" });
    expect(value.attributes("aria-valuenow")).toBe("98");
    expect(wrapper.find("[data-test=goal-bound]").text()).toBe("");
    await value.trigger("keydown", { key: "Home" });
    expect(value.attributes("aria-valuenow")).toBe("1");
    expect(wrapper.find("[data-test=goal-less]").attributes("disabled")).toBeDefined();
    expect(wrapper.find("[data-test=goal-bound]").text()).toBe("1 est le minimum.");
    await value.trigger("keydown", { key: "End" });
    expect(value.attributes("aria-valuenow")).toBe("99");
    wrapper.unmount();
  });

  it("sans objectif : part de 10 ; « Annuler » ferme sans rien écrire ; un refus reste dans le panneau", async () => {
    const wrapper = sheet(null);
    expect(wrapper.find(".goal-number").text()).toBe("10");
    await wrapper.find("[data-test=goal-cancel]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
    expect(PUT).not.toHaveBeenCalled();
    PUT.mockResolvedValue({ data: undefined });
    await wrapper.find("[data-test=goal-save]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=goal-error]").text()).toBe("L’enregistrement a échoué. Réessaie.");
    expect(wrapper.emitted("saved")).toBeUndefined();
    wrapper.unmount();
  });
});
