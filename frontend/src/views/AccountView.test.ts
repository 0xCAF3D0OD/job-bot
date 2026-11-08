import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountView from "./AccountView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
const me = ref<Record<string, unknown>>({ username: "kevin", auth_enabled: true, demo: false, is_owner: false });
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me }) }));
const collectNow = vi.fn();
const running = ref(false);
const collectMessage = ref("");
vi.mock("../composables/useCollect", () => ({ useCollect: () => ({ running, message: collectMessage, collectNow }) }));
vi.mock("../composables/usePlan", () => ({ usePlan: () => ({ plan: ref({ plan: "essentiel" }) }) }));
vi.mock("../composables/useProfiles", () => ({
  useProfiles: () => ({ list: ref(null), current: ref(null), load: vi.fn(), choose: vi.fn() }),
}));

const DATA: Record<string, unknown> = {
  "/api/identity": { name: "Kevin Di Nocera" },
  "/api/documents": [{ id: 1, kind: null }, { id: 2, kind: "certificate" }, { id: 3, kind: null }],
  "/api/privacy": { contact: "Kevin, aide@example.ch" },
};

async function mountPage() {
  GET.mockImplementation((path: string) => Promise.resolve({ data: DATA[path] ?? null }));
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
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

describe("AccountView (maquette Compte, étape 10a)", () => {
  it("la carte du profil, puis les quatre groupes et leurs liens", async () => {
    const wrapper = await mountPage();
    const card = wrapper.get("[data-test=account-profile-card]");
    expect(card.attributes("href")).toBe("/profil");
    // L'image de profil et sa pastille crayon, à côté du lien (pas dedans) : un toucher ouvre « Ton image ».
    expect(card.find("button").exists()).toBe(false);
    const image = wrapper.get("[data-test=account-image]");
    expect(image.attributes("aria-label")).toBe("Changer ton image");
    expect(image.get("[data-test=profile-image]").text()).toBe("KD");
    expect(image.find(".account-image-badge .icon").exists()).toBe(true);
    expect(card.text()).toContain("Kevin Di Nocera");
    expect(card.text()).toContain("CV, compétences, postes recherchés");
    expect(wrapper.findAll(".grouped-title").map((t) => t.text())).toEqual([
      "Mon parcours",
      "Préférences",
      "Recherche et outils",
      "Confidentialité et aide",
    ]);
    expect(href(wrapper, "account-trainings")).toBe("/bilan/formations");
    // « Mes CV » compte les CV, pas les certificats (C5).
    expect(href(wrapper, "account-cv")).toBe("/profil?onglet=parcours");
    expect(wrapper.get("[data-test=account-cv] .grouped-value").text()).toBe("2");
    expect(href(wrapper, "account-criteria")).toBe("/profil");
    expect(href(wrapper, "account-notifications")).toBe("/reglages?rubrique=notifications");
    expect(wrapper.get("[data-test=account-appearance]").text()).toContain("Automatique");
    expect(href(wrapper, "account-ai-data")).toBe("/tes-donnees#ia");
    expect(wrapper.get("[data-test=account-ai-data]").text()).toBe("Ce qui part à l'IA");
    expect(href(wrapper, "account-help")).toBe("mailto:aide@example.ch");
    // L'administration et l'état du service, à l'exploitant seulement.
    expect(wrapper.find("[data-test=account-admin]").exists()).toBe(false);
    expect(wrapper.find("[data-test=account-diagnostic]").exists()).toBe(false);
    await wrapper.get("[data-test=account-collect] button").trigger("click");
    expect(collectNow).toHaveBeenCalled();
  });

  it("toucher l'image ouvre la feuille « Ton image » (grille de 5 colonnes, AvatarPicker)", async () => {
    const wrapper = await mountPage();
    const picker = wrapper.findComponent({ name: "AvatarPicker" });
    expect(picker.props("open")).toBe(false);
    await wrapper.get("[data-test=account-image]").trigger("click");
    await flushPromises();
    expect(picker.props("open")).toBe(true);
    expect(wrapper.get("[data-test=avatar-grid]").classes()).toContain("avatar-grid");
    wrapper.unmount();
  });

  it("sans nom ni contact : « Ton profil », l'aide mène à À propos ; la démo ne collecte pas", async () => {
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
  it("pendant la collecte : la ligne est aria-disabled et aria-busy, le clic ne relance rien, l'état est annoncé", async () => {
    const wrapper = await mountPage();
    const button = () => wrapper.get("[data-test=account-collect] button");
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
    collectMessage.value = "Collecte lancée. Le journal se met à jour d'ici une minute.";
    await flushPromises();
    expect(button().attributes("aria-busy")).toBeUndefined();
    expect(status.text()).toBe("Collecte lancée. Le journal se met à jour d'ici une minute.");
  });
});
