import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ProfileView from "./ProfileView.vue";

const original = globalThis.matchMedia;
afterEach(() => {
  globalThis.matchMedia = original;
});

async function mountAt(width: "narrow" | "wide") {
  globalThis.matchMedia = ((query: string) =>
    ({ matches: width === "narrow" && query.includes("599px"), addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList);
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/profil", component: ProfileView }] });
  await router.push("/profil?onglet=coordonnees");
  await router.isReady();
  return mount(ProfileView, {
    global: {
      plugins: [router],
      stubs: { CriteriaForm: true, IdentityForm: true, ProfileParcours: true, ProfileGauge: true },
    },
  });
}

describe("Profil, structure téléphone", () => {
  it("sous 600 px : un contrôle segmenté pleine largeur, « Coordonnées » en entier", async () => {
    const wrapper = await mountAt("narrow");
    const segmented = wrapper.find(".segmented.segmented-full");
    expect(segmented.exists()).toBe(true);
    expect(segmented.findAll(".segmented-label").map((s) => s.text())).toEqual(["Critères", "Parcours", "Coordonnées"]);
    expect(wrapper.find("[data-test=tab-coordonnees]").attributes("aria-current")).toBe("page");
    expect(wrapper.find(".prep-tabs").exists()).toBe(false);
  });

  it("au-delà : les onglets habituels", async () => {
    const wrapper = await mountAt("wide");
    expect(wrapper.find(".prep-tabs").exists()).toBe(true);
    expect(wrapper.find(".segmented").exists()).toBe(false);
  });
});
