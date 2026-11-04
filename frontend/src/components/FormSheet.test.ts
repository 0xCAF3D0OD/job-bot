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
});
