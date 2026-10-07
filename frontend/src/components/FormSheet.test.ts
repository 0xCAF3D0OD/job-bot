import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

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
  it("liste les valeurs remplies, prénom et nom séparés, et les PDF", async () => {
    const wrapper = mount(FormSheet, {
      props: { letterText: "Madame, Monsieur…", letterId: 11, cvId: 31 },
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
    expect(wrapper.find("[data-test=sheet-cv]").attributes("href")).toBe("/api/cvs/31/pdf");
    expect(wrapper.text()).toContain("compléter dans Profil"); // téléphone manquant
  });
});
