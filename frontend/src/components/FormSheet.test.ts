import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import FormSheet from "./FormSheet.vue";

vi.mock("../api/client", () => ({
  api: {
    GET: () =>
      Promise.resolve({
        data: {
          name: "Camille Di Exemple",
          street: "Rue du Test 1",
          postcode: "1020",
          city: "Renens",
          phone: null,
          email: "camille@example.ch",
          linkedin: "https://linkedin.com/in/camille",
          website: null,
          availability: null,
          salary: "CHF 90'000",
          permit: null,
        },
      }),
  },
}));

describe("FormSheet", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("liste les valeurs remplies, prénom et nom séparés", async () => {
    const wrapper = mount(FormSheet, {
      props: { letterText: "Madame, Monsieur…" },
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();
    const labels = wrapper.findAll("dt").map((d) => d.text());
    expect(labels).toEqual([
      "Prénom",
      "Nom",
      "E-mail",
      "Rue et numéro",
      "NPA",
      "Localité",
      "Pays",
      "LinkedIn",
      "Prétentions salariales",
      "Lettre de motivation (texte)",
    ]);
    expect(wrapper.findAll("dd")[1]?.text()).toContain("Di Exemple");
    expect(wrapper.text()).toContain("compléter dans Profil"); // téléphone manquant
  });

  it("« Copier » devient « Copié » ; le nom du champ est lu avec (maquette Preparer)", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    const wrapper = mount(FormSheet, { global: { stubs: { RouterLink: RouterLinkStub } } });
    await flushPromises();
    const button = wrapper.findAll("[data-test=sheet-copy]")[2]!;
    expect(button.text()).toBe("Copier : E-mail");
    await button.trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("camille@example.ch");
    expect(button.text()).toBe("Copié : E-mail");
    expect(button.classes()).toContain("copy-done");
  });

  it("sur téléphone : les cinq champs courants, les autres sous « Autres champs » replié (Kevin, 6.11)", async () => {
    vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener() {}, removeEventListener() {} }));
    const wrapper = mount(FormSheet, {
      props: { letterText: "Madame, Monsieur…" },
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();
    const first = wrapper.find(".form-sheet > dl").findAll("dt").map((d) => d.text());
    expect(first).toEqual(["Prénom", "Nom", "E-mail", "Localité"]); // pas de téléphone dans le profil
    const more = wrapper.find("[data-test=sheet-more]");
    expect(more.find(".disclosure-row").text()).toContain("Autres champs");
    expect(more.find(".disclosure-row").text()).toContain("6");
    expect(more.find(".disclosure-row").attributes("aria-expanded")).toBe("false");
    expect(more.findAll("dt").map((d) => d.text())).toEqual([
      "Rue et numéro",
      "NPA",
      "Pays",
      "LinkedIn",
      "Prétentions salariales",
      "Lettre de motivation (texte)",
    ]);
  });
});
