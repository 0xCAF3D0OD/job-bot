import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import FormAnswerSheet from "./FormAnswerSheet.vue";

vi.mock("../api/client", () => ({ api: { PUT: vi.fn() } }));

// Motif « Radio Group » (ARIA APG ; Kevin, 17.11) : role="radio" et aria-checked, un seul arrêt de Tab, les flèches
// passent d'un choix à l'autre.
describe("Feuille Coordonnées : choix à cocher", () => {
  const radios = (w: ReturnType<typeof mount>) => w.findAll("[role=radio]");
  const checked = (w: ReturnType<typeof mount>) => radios(w).map((r) => r.attributes("aria-checked"));
  const stops = (w: ReturnType<typeof mount>) => radios(w).map((r) => r.attributes("tabindex"));

  it("un seul arrêt de Tab : le choix actif, sinon le premier", async () => {
    const w = mount(FormAnswerSheet, { props: { field: "permit", value: "", salaryMode: "auto" }, attachTo: document.body });
    expect(w.find("[role=radiogroup]").exists()).toBe(true);
    expect(stops(w)).toEqual(["0", "-1", "-1", "-1", "-1"]);
    expect(radios(w).every((r) => r.attributes("aria-pressed") === undefined)).toBe(true);
    w.unmount();
    const b = mount(FormAnswerSheet, { props: { field: "permit", value: "Permis B", salaryMode: "auto" }, attachTo: document.body });
    expect(stops(b)).toEqual(["-1", "-1", "0", "-1", "-1"]);
    b.unmount();
  });

  it("les flèches cochent le choix suivant ou précédent et y posent le focus, en boucle", async () => {
    const w = mount(FormAnswerSheet, { props: { field: "notice", value: "Aucun", salaryMode: "auto" }, attachTo: document.body });
    await radios(w)[0]!.trigger("keydown", { key: "ArrowRight" });
    expect(checked(w)).toEqual(["false", "true", "false", "false", "false"]);
    expect(document.activeElement).toBe(radios(w)[1]!.element);
    await radios(w)[1]!.trigger("keydown", { key: "ArrowUp" });
    await radios(w)[0]!.trigger("keydown", { key: "ArrowLeft" });
    expect(checked(w)).toEqual(["false", "false", "false", "false", "true"]);
    await radios(w)[4]!.trigger("keydown", { key: "Home" });
    expect(checked(w)[0]).toBe("true");
    expect(stops(w)).toEqual(["0", "-1", "-1", "-1", "-1"]);
    w.unmount();
  });
});
