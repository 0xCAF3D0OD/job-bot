import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { forgetProfileImage } from "../composables/useProfileImage";
import AccountView from "./AccountView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
const me = ref<Record<string, unknown>>({ username: "kevin", auth_enabled: true, demo: false, is_owner: false });
const logout = vi.fn();
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me, logout }) }));
const collectNow = vi.fn();
const running = ref(false);
const collectMessage = ref("");
vi.mock("../composables/useCollect", () => ({ useCollect: () => ({ running, message: collectMessage, collectNow }) }));
const phone = ref(true);
vi.mock("../composables/usePhone", () => ({ usePhone: () => ({ phone }) }));
vi.mock("../composables/usePlan", () => ({ usePlan: () => ({ plan: ref({ plan: "essentiel" }) }) }));
vi.mock("../composables/useProfiles", () => ({
  useProfiles: () => ({ list: ref(null), current: ref(null), load: vi.fn(), choose: vi.fn() }),
}));

const DATA: Record<string, unknown> = {
  "/api/identity": { name: "Kevin Di Nocera", email: "kevin@example.ch" },
  "/api/documents": [{ id: 1, kind: null }, { id: 2, kind: "certificate" }, { id: 3, kind: null }],
  "/api/privacy": { contact: "Kevin, aide@example.ch" },
};

async function mountPage() {
  GET.mockImplementation((path: string) => Promise.resolve({ data: DATA[path] ?? null }));
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/actualites", name: "news", component: { template: "<div />" } }, { path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/compte");
  const wrapper = mount(AccountView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}
const href = (wrapper: Awaited<ReturnType<typeof mountPage>>, test: string) =>
  wrapper.get(`[data-test=${test}] a, a[data-test=${test}]`).attributes("href");

afterEach(() => {
  vi.resetAllMocks();
  running.value = false;
  collectMessage.value = "";
  me.value = { username: "kevin", auth_enabled: true, demo: false, is_owner: false };
});

describe("AccountView (maquette Compte, étape 10a ; blocs du lot 18, §10.4)", () => {
  it("« Se déconnecter » dans sa carte, en rouge, l’adresse dessous ; pas sans connexion (§10.4, PR 8 du 9 novembre)", async () => {
    const wrapper = await mountPage();
    const button = wrapper.get("[data-test=logout]");
    expect(button.find(".block-row-title").text()).toBe("Se déconnecter");
    expect(button.get("[data-test=logout-email]").text()).toBe("kevin@example.ch");
    expect(button.classes()).toContain("account-logout-row");
    expect(button.element.closest(".account-group")).not.toBeNull();
    await button.trigger("click");
    await flushPromises();
    expect(logout).toHaveBeenCalledTimes(1);
    me.value = { ...me.value, auth_enabled: false };
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=logout]").exists()).toBe(false);
  });

  it("sur ordinateur, « Se déconnecter » reste le lien rouge sous les blocs (MODIFICATIONS_9 ordinateur, §4)", async () => {
    phone.value = false;
    const wrapper = await mountPage();
    const button = wrapper.get("[data-test=logout]");
    expect(button.text()).toBe("Se déconnecter");
    expect(button.classes()).toContain("account-logout");
    phone.value = true;
  });

  it("une carte par groupe (PR 8 du 9 novembre)", async () => {
    const wrapper = await mountPage();
    const groups = wrapper.findAll(".account-group");
    // Profil, Mon parcours, Préférences, Recherche et outils, Confidentialité et aide, Se déconnecter.
    expect(groups).toHaveLength(6);
    expect(groups[1]!.findAll(".block-row").map((r) => r.find(".block-row-name").text())).toEqual(["Formations", "CV et lettres"]);
  });

  it("la carte du profil, puis les quatre groupes et leurs liens", async () => {
    const wrapper = await mountPage();
    const card = wrapper.get("[data-test=account-profile-card]");
    expect(card.attributes("href")).toBe("/profil");
    // La ligne profil (CompteImage) : toute la ligne est le lien ; l'image (initiales) et sa pastille crayon décorative.
    expect(card.find("button").exists()).toBe(false);
    const image = card.get("[data-test=account-image]");
    expect(image.get("[data-test=profile-image]").text()).toBe("KD");
    expect(image.get(".account-image-badge").attributes("aria-hidden")).toBe("true");
    expect(image.find(".account-image-badge .icon").exists()).toBe(true);
    expect(card.text()).toContain("Kevin Di Nocera");
    expect(card.text()).toContain("CV, compétences, postes recherchés");
    expect(wrapper.findAll(".account-block .block-cap").map((t) => t.text())).toEqual([
      "Mon parcours",
      "Préférences",
      "Recherche et outils",
      "Confidentialité et aide",
    ]);
    expect(href(wrapper, "account-trainings")).toBe("/bilan/formations");
    // « Mes CV » compte les CV, pas les certificats (C5).
    expect(href(wrapper, "account-cv")).toBe("/profil?onglet=parcours");
    expect(wrapper.get("[data-test=account-cv] .block-row-line").text()).toBe(", 2 documents");
    // D29 : chaque ligne a son cercle à flèche, décoratif ; la carte du profil aussi.
    expect(card.get(".arrow-circle").attributes("aria-hidden")).toBe("true");
    expect(wrapper.get("[data-test=account-page]").element.closest(".blocks-page")).not.toBeNull();
    expect(href(wrapper, "account-criteria")).toBe("/profil");
    expect(href(wrapper, "account-notifications")).toBe("/reglages?rubrique=notifications");
    expect(wrapper.get("[data-test=account-appearance]").text()).toContain("Automatique");
    expect(href(wrapper, "account-ai-data")).toBe("/tes-donnees#ia");
    expect(wrapper.get("[data-test=account-ai-data]").text()).toBe("Ce qui part à l’IA");
    expect(href(wrapper, "account-help")).toBe("mailto:aide@example.ch");
    // L'administration et l'état du service, à l'exploitant seulement.
    expect(wrapper.find("[data-test=account-admin]").exists()).toBe(false);
    expect(wrapper.find("[data-test=account-diagnostic]").exists()).toBe(false);
    await wrapper.get("button[data-test=account-collect]").trigger("click");
    expect(collectNow).toHaveBeenCalled();
  });

  it("l’image choisie dans Profil s’affiche sur la ligne, la pastille reste dans le conteneur de 52 px", async () => {
    forgetProfileImage();
    DATA["/api/profile-image"] = { avatar: 3 };
    const wrapper = await mountPage();
    const image = wrapper.get("[data-test=account-profile-card] [data-test=account-image]");
    expect(image.get("img").attributes("src")).toContain("avatar-3");
    expect(image.find(".account-image-badge").exists()).toBe(true);
    expect(wrapper.findComponent({ name: "AvatarPicker" }).exists()).toBe(false);
    delete DATA["/api/profile-image"];
    forgetProfileImage();
    wrapper.unmount();
  });

  it("sans nom ni contact : « Ton profil », l’aide mène à À propos ; la démo ne collecte pas", async () => {
    DATA["/api/identity"] = { name: "" };
    DATA["/api/privacy"] = { contact: null };
    me.value = { username: "demo", auth_enabled: false, demo: true };
    const wrapper = await mountPage();
    expect(wrapper.get("[data-test=account-profile-card]").text()).toContain("Ton profil");
    expect(wrapper.find("[data-test=account-image] [data-test=profile-image]").exists()).toBe(true);
    expect(href(wrapper, "account-help")).toBe("/a-propos");
    expect(wrapper.find("[data-test=account-collect]").exists()).toBe(false);
  });
});

describe("Collecter maintenant (reprise de la 502)", () => {
  it("pendant la collecte : la ligne est aria-disabled et aria-busy, le clic ne relance rien, l’état est annoncé", async () => {
    const wrapper = await mountPage();
    const button = () => wrapper.get("button[data-test=account-collect]");
    const status = wrapper.get("[data-test=account-collect-status]");
    expect(status.attributes("role")).toBe("status");
    expect(button().attributes("aria-disabled")).toBeUndefined();
    running.value = true;
    await flushPromises();
    expect(button().attributes("aria-disabled")).toBe("true");
    expect(button().attributes("aria-busy")).toBe("true");
    expect(status.text()).toBe("Relève en cours…");
    await button().trigger("click");
    expect(collectNow).not.toHaveBeenCalled();
    running.value = false;
    collectMessage.value = "Collecte lancée. Le journal se met à jour d’ici une minute.";
    await flushPromises();
    expect(button().attributes("aria-busy")).toBeUndefined();
    expect(status.text()).toBe("Collecte lancée. Le journal se met à jour d’ici une minute.");
  });
});
