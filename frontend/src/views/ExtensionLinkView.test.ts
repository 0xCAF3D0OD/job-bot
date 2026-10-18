// « Relier ce navigateur » (docs/71 §4) : jeton posé dans la page, lu puis effacé par
// l'extension ; révoqué s'il n'est pas lu.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { browserName } from "../browserName";
import ExtensionLinkView from "./ExtensionLinkView.vue";

const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));

afterEach(() => {
  vi.resetAllMocks();
  vi.useRealTimers();
  document.body.innerHTML = "";
});

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/extension/relier", component: ExtensionLinkView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/extension/relier");
  const wrapper = mount(ExtensionLinkView, { global: { plugins: [router] }, attachTo: document.body });
  return { wrapper, router };
}

const token = () => document.getElementById("jobbot-extension-token") as HTMLOutputElement;

describe("relier ce navigateur", () => {
  it("pose le jeton dans la page, prévient par l'adresse, puis « C'est relié » une fois lu", async () => {
    POST.mockResolvedValue({ data: { id: 7, token: "jbx_secret", name: "Firefox" } });
    const { wrapper, router } = await mountView();
    expect(token().dataset.token).toBeUndefined();
    await wrapper.find("[data-test=link-browser]").trigger("click");
    await flushPromises();
    // Jeton de liaison : le serveur le refuse s'il n'est pas lu dans les 2 minutes (docs/76 §1).
    expect(POST).toHaveBeenCalledWith("/api/extension-tokens", { body: { name: browserName(), link: true } });
    expect(token().dataset.token).toBe("jbx_secret");
    expect(token().hidden).toBe(true);
    // Jamais dans l'adresse : seulement le signal.
    expect(router.currentRoute.value.fullPath).toBe("/extension/relier?etat=pret");
    expect(wrapper.find("[data-test=link-waiting]").exists()).toBe(true);

    // L'extension lit le jeton et l'efface.
    token().removeAttribute("data-token");
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await flushPromises();
    expect(wrapper.find("[data-test=link-done]").exists()).toBe(true);
    expect(DELETE).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it("sans extension pour le lire, le jeton est retiré et révoqué au bout de 2 minutes", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    POST.mockResolvedValue({ data: { id: 7, token: "jbx_secret", name: "Firefox" } });
    DELETE.mockResolvedValue({ response: { status: 204 } });
    const { wrapper } = await mountView();
    await wrapper.find("[data-test=link-browser]").trigger("click");
    await flushPromises();
    vi.advanceTimersByTime(120_000);
    await flushPromises();
    expect(token().dataset.token).toBeUndefined();
    expect(DELETE).toHaveBeenCalledWith("/api/extension-tokens/{token_id}", { params: { path: { token_id: 7 } } });
    expect(wrapper.find("[data-test=link-timeout]").exists()).toBe(true);
    wrapper.unmount();
  });
});

describe("nom du navigateur", () => {
  it("reconnaît Firefox, Edge et Chrome", () => {
    expect(browserName("Mozilla/5.0 (Macintosh) Gecko/20100101 Firefox/157.0")).toBe("Firefox");
    expect(browserName("Mozilla/5.0 Chrome/140.0 Safari/537.36 Edg/140.0")).toBe("Edge");
    expect(browserName("Mozilla/5.0 Chrome/140.0 Safari/537.36")).toBe("Chrome");
    expect(browserName("curl/8")).toBe("Mon navigateur");
  });
});
