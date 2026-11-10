import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { routes } from "../router";
import NotFoundView from "./NotFoundView.vue";

describe("page introuvable (docs/59 §5)", () => {
  it("une adresse inconnue mène à une page qui le dit", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes });
    await router.push("/nulle-part");
    expect(router.currentRoute.value.name).toBe("not-found");
    const wrapper = mount(NotFoundView, { global: { plugins: [router] } });
    // Maquette PageIntrouvable : le titre, la phrase, « Retour à l'accueil » ; sans barre (meta.bare).
    expect(router.currentRoute.value.meta.bare).toBe(true);
    expect(wrapper.find("h1").text()).toBe("Cette page s’est perdue");
    expect(wrapper.text()).toContain("Le lien est peut-être ancien. Tout le reste est à sa place.");
    const home = wrapper.find("[data-test=not-found-home]");
    expect(home.text()).toBe("Retour à l’accueil");
    expect(home.attributes("href")).toBe("/aujourdhui");
    // Les 4 personnages du logo (scène « introuvable », §15) : 340 px, 392 sur ordinateur, décoratif.
    const person = wrapper.find("[data-test=not-found-person]");
    expect(person.attributes("src")).toContain("/troupe/introuvable-680");
    expect(person.attributes("srcset")).toContain("/troupe/introuvable-784");
    expect(person.attributes("width")).toBe("340");
    expect(person.attributes("alt")).toBe("");
    expect(wrapper.find("[data-test=not-found-scene]").attributes("aria-hidden")).toBe("true");
  });
});
