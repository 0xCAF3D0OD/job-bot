import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import AccessView from "./AccessView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

async function mountAccess() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/acces/:token", component: AccessView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/acces/jba_lien");
  const wrapper = mount(AccessView, { global: { plugins: [router], stubs: { IllustratedSide: { template: "<div><slot /></div>" } } } });
  await flushPromises();
  return { wrapper, router };
}

describe("lien d'accès (docs/65 §2)", () => {
  it("invitation : identifiant et mot de passe, puis la plateforme", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/auth/me"
          ? { data: { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: false } }
          : { data: { kind: "invite", username: null, expires_at: "2026-10-23T10:00:00Z" } },
      ),
    );
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountAccess();
    await wrapper.find("[data-test=access-username]").setValue("camille");
    await wrapper.find("[data-test=access-password]").setValue("un-mot-de-passe-solide");
    await wrapper.find("[data-test=access-again]").setValue("un-mot-de-passe-autre");
    await wrapper.find("[data-test=access-form]").trigger("submit");
    expect(wrapper.find("[data-test=access-error]").text()).toContain("diffèrent");
    expect(POST).not.toHaveBeenCalled();
    await wrapper.find("[data-test=access-again]").setValue("un-mot-de-passe-solide");
    await wrapper.find("[data-test=access-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/auth/links/{token}", {
      params: { path: { token: "jba_lien" } },
      body: { username: "camille", password: "un-mot-de-passe-solide" },
    });
    expect(router.currentRoute.value.fullPath).toBe("/aujourdhui");
  });

  it("réinitialisation : le compte, pas d'identifiant à choisir", async () => {
    GET.mockResolvedValue({ data: { kind: "reset", username: "camille", expires_at: "2026-10-17T10:00:00Z" } });
    const { wrapper } = await mountAccess();
    expect(wrapper.text()).toContain("Pour le compte camille");
    expect(wrapper.find("[data-test=access-username]").exists()).toBe(false);
  });

  it("lien expiré : le dit", async () => {
    GET.mockResolvedValue({ data: undefined, error: { detail: "ce lien a expiré : demande-en un nouveau" } });
    const { wrapper } = await mountAccess();
    expect(wrapper.find("[data-test=access-problem]").text()).toContain("Ce lien a expiré");
    expect(wrapper.find("[data-test=access-form]").exists()).toBe(false);
  });
});
