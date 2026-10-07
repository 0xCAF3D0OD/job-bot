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
