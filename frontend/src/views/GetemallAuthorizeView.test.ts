import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import GetemallAuthorizeView from "./GetemallAuthorizeView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const assign = vi.fn();
beforeEach(() => {
  vi.stubGlobal("location", { ...window.location, assign });
});
afterEach(() => {
  vi.resetAllMocks();
  vi.unstubAllGlobals();
});

const READY = { available: true, tester: true, linked: false, orp: false, authorized_at: null, last_used_at: null };
const CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM";
const QUERY = `redirect_uri=${encodeURIComponent("https://getthemall.ch/connexion")}&state=etat-123456&code_challenge=${CHALLENGE}&code_challenge_method=S256`;

async function mountView(query = QUERY, state: unknown = READY) {
  GET.mockResolvedValue({ data: state });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/connexion/getemall", component: GetemallAuthorizeView },
      { path: "/tes-donnees", name: "privacy", component: { template: "<div />" } },
      { path: "/aujourdhui", component: { template: "<div />" } },
    ],
  });
  await router.push(`/connexion/getemall?${query}`);
  const wrapper = mount(GetemallAuthorizeView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Relier Get’emAll (docs/140, maquette AutoriserGetemall)", () => {
  it("la case ORP est décochée, et ne part qu’avec « Autoriser »", async () => {
    const { wrapper } = await mountView();
    const box = wrapper.find("[data-test=partner-orp]");
    expect((box.element as HTMLInputElement).checked).toBe(false);
    expect(wrapper.text()).toContain("Tu reviendras ensuite sur getthemall.ch");
    await box.setValue(true);
    POST.mockResolvedValue({ data: { redirect_to: "https://getthemall.ch/connexion?code=jbc_x&state=etat-123456" } });
    await wrapper.find("[data-test=partner-allow]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/partenaires/getemall/autorisation", {
      body: {
        redirect_uri: "https://getthemall.ch/connexion",
        state: "etat-123456",
        code_challenge: CHALLENGE,
        code_challenge_method: "S256",
        orp: true,
      },
    });
    expect(assign).toHaveBeenCalledWith("https://getthemall.ch/connexion?code=jbc_x&state=etat-123456");
  });

  it("« Refuser » passe par le serveur, qui vérifie l’adresse de retour", async () => {
    const { wrapper } = await mountView();
    POST.mockResolvedValue({ data: { redirect_to: "https://getthemall.ch/connexion?error=access_denied&state=etat-123456" } });
    await wrapper.find("[data-test=partner-refuse]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/partenaires/getemall/refus", {
      body: { redirect_uri: "https://getthemall.ch/connexion", state: "etat-123456" },
    });
    expect(assign).toHaveBeenCalledWith("https://getthemall.ch/connexion?error=access_denied&state=etat-123456");
  });

  it("refusée sans adresse de retour : retour à l’accueil, jamais ailleurs", async () => {
    const { wrapper, router } = await mountView("state=etat-123456");
    expect(wrapper.find("[data-test=partner-blocked]").exists()).toBe(true);
    expect(wrapper.find("[data-test=partner-allow]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=partner-refuse]").trigger("click");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
    expect(router.currentRoute.value.path).toBe("/aujourdhui");
  });

  it("hors des testeurs invités : la page le dit et « Autoriser » reste grisé", async () => {
    const { wrapper } = await mountView(QUERY, { ...READY, tester: false });
    expect(wrapper.find("[data-test=partner-blocked]").text()).toContain("réservé aux testeurs invités");
    expect(wrapper.find("[data-test=partner-allow]").attributes("disabled")).toBeDefined();
  });
});
