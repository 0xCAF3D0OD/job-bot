import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ProfileView from "./ProfileView.vue";

const original = globalThis.matchMedia;
afterEach(() => {
  globalThis.matchMedia = original;
});

async function mountAt(width: "narrow" | "wide", at = "/profil?onglet=coordonnees") {
  globalThis.matchMedia = ((query: string) =>
    ({ matches: width === "narrow" && query.includes("599px"), addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList);
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/profil", component: ProfileView }] });
  await router.push(at);
  await router.isReady();
  return mount(ProfileView, {
    global: {
      plugins: [router],
      stubs: { ProfileDesktop: true, IdentityForm: true, ProfileParcours: true, ProfileGauge: true },
    },
  });
}

describe("Profil, page unique (prompt du 10 novembre, PR 20, décision B)", () => {
  it("sous 600 px : plus d’onglets ; « Mon profil » avec le retour au Compte, puis la page unique (ProfilTel)", async () => {
    const wrapper = await mountAt("narrow", "/profil");
    expect(wrapper.find(".segmented").exists()).toBe(false);
    expect(wrapper.get("[data-test=profile-topbar] h1").text()).toBe("Mon profil");
    expect(wrapper.get("[data-test=profile-topbar-back]").attributes("href")).toBe("/compte");
    expect(wrapper.find("profile-desktop-stub").exists()).toBe(true);
  });

  it("sous 600 px : ?onglet=coordonnees ouvre sa page avec un retour au Profil", async () => {
    const wrapper = await mountAt("narrow");
    expect(wrapper.find(".segmented").exists()).toBe(false);
    expect(wrapper.get("[data-test=profile-subhead] h1").text()).toBe("Coordonnées");
    expect(wrapper.get("[data-test=profile-back]").attributes("aria-label")).toBe("Retour au profil");
    expect(wrapper.find("identity-form-stub").exists()).toBe(true);
  });

  it("au-delà : plus d’onglets (PR 9b, page unique) ; ?onglet=coordonnees ouvre sa page avec un retour au Profil", async () => {
    const wrapper = await mountAt("wide");
    expect(wrapper.find(".prep-tabs").exists()).toBe(false);
    expect(wrapper.find(".segmented").exists()).toBe(false);
    expect(wrapper.get("[data-test=profile-subhead] h1").text()).toBe("Coordonnées");
    expect(wrapper.get("[data-test=profile-back]").attributes("href")).toBe("/profil");
  });
});
