import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import LoginView from "./LoginView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(async () => {
  vi.resetAllMocks();
  useAuth().me.value = null;
});

const anonymous = { authenticated: false, username: null, setup_needed: false, auth_enabled: true };

async function mountLogin(path = "/connexion?suite=/candidatures") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/connexion", name: "login", component: LoginView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(LoginView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("LoginView", () => {
  it("sans compte : explique la commande à lancer", async () => {
    GET.mockResolvedValue({ data: { ...anonymous, setup_needed: true } });
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=setup-needed]").text()).toContain("jobbot set-password");
    expect(wrapper.find("[data-test=login-form]").exists()).toBe(false);
  });

  it("erreur, puis connexion qui ramène à la page demandée", async () => {
    GET.mockResolvedValueOnce({ data: anonymous }).mockResolvedValue({ data: { ...anonymous, authenticated: true, username: "camille" } });
    POST.mockResolvedValueOnce({ response: { ok: false }, error: { detail: "identifiant ou mot de passe incorrect" } }).mockResolvedValue({
      response: { ok: true },
    });
    const { wrapper, router } = await mountLogin();
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("faux");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=login-error]").text()).toBe("Identifiant ou mot de passe incorrect.");
    expect((wrapper.find("[data-test=password]").element as HTMLInputElement).value).toBe("");

    await wrapper.find("[data-test=password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/auth/login", { body: { username: "camille", password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.fullPath).toBe("/candidatures");
    expect(useAuth().loggedIn.value).toBe(true);
  });

  it("refuse une adresse de retour externe", async () => {
    GET.mockResolvedValueOnce({ data: anonymous }).mockResolvedValue({ data: { ...anonymous, authenticated: true } });
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountLogin("/connexion?suite=//piege.example");
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("x");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/aujourdhui");
  });
});

describe("LoginView, deux moitiés (docs/65, complément 0.53.1)", () => {
  it("Google, Apple, Microsoft présentés : un clic dit que ça arrive", async () => {
    GET.mockResolvedValue({ data: anonymous });
    const { wrapper } = await mountLogin();
    expect(wrapper.find(".auth-art").exists()).toBe(true);
    for (const id of ["google", "apple", "microsoft"]) {
      expect(wrapper.find(`[data-test=social-${id}]`).exists()).toBe(true);
    }
    await wrapper.find("[data-test=social-google]").trigger("click");
    expect(wrapper.find("[data-test=social-notice]").text()).toContain("Google arrive bientôt");
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=login-form]").exists()).toBe(true);
  });
});

describe("LoginView, demander un compte (docs/102)", () => {
  function answer(open: boolean) {
    GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/auth/signup" ? { open } : anonymous }));
  }

  it("demandes ouvertes : « Créer un compte » mène à /inscription", async () => {
    answer(true);
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=signup-link]").attributes("href")).toBe("/inscription");
    expect(wrapper.find(".auth-foot").text().replace(/\s+/g, " ")).toContain("Pas encore de compte ? Créer un compte");
    expect(wrapper.text()).not.toContain("sur invitation");
  });

  it("demandes fermées : l'invitation, sans lien", async () => {
    answer(false);
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=signup-link]").exists()).toBe(false);
    expect(wrapper.text()).toContain("L'accès se fait sur invitation.");
  });

  it("un compte qui attend la validation : le message du serveur, tel quel", async () => {
    answer(true);
    POST.mockResolvedValue({ response: { ok: false, status: 403 }, error: { detail: "ton compte attend encore la validation de l'exploitant" } });
    const { wrapper } = await mountLogin();
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("un-mot-de-passe-solide");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=login-error]").text()).toBe("Ton compte attend encore la validation de l'exploitant.");
  });
});
