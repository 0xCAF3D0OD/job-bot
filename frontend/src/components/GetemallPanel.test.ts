import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import GetemallPanel from "./GetemallPanel.vue";

const GET = vi.fn();
const PATCH = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const LINKED = {
  available: true,
  tester: true,
  linked: true,
  orp: false,
  authorized_at: "2026-11-05T10:00:00Z",
  last_used_at: null,
};
const UNLINKED = { ...LINKED, linked: false, authorized_at: null };

async function mountPanel(answer: unknown) {
  GET.mockResolvedValue({ data: answer });
  const wrapper = mount(GetemallPanel, { attachTo: document.body });
  await flushPromises();
  return wrapper;
}

describe("Réglages › Connexions, Get'emAll (docs/140)", () => {
  it("rien tant que la connexion n'est pas configurée", async () => {
    const wrapper = await mountPanel({ ...UNLINKED, available: false });
    expect(wrapper.find("[data-test=getemall-panel]").exists()).toBe(false);
    expect(wrapper.find("[data-test=getemall-empty]").exists()).toBe(false);
  });

  it("l'interrupteur ORP s'enregistre tout de suite", async () => {
    const wrapper = await mountPanel(LINKED);
    expect(wrapper.find("[data-test=getemall-last-read]").text()).toBe("Pas encore lu");
    PATCH.mockResolvedValue({ data: { ...LINKED, orp: true } });
    await wrapper.find("[data-test=getemall-orp]").trigger("change");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/partenaires/getemall", { body: { orp: true } });
    expect((wrapper.find("[data-test=getemall-orp]").element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find("[data-test=setting-saved]").text()).toBe("Enregistré");
    wrapper.unmount();
  });

  it("« Retirer l'accès » demande confirmation, puis la section dit qu'aucune app n'est reliée", async () => {
    const wrapper = await mountPanel(LINKED);
    await wrapper.find("[data-test=getemall-remove]").trigger("click");
    await flushPromises();
    const dialog = wrapper.find("[data-test=getemall-confirm]");
    expect(dialog.attributes("role")).toBe("alertdialog");
    // « Garder l'accès » ne retire rien.
    await wrapper.find("[data-test=getemall-keep]").trigger("click");
    expect(DELETE).not.toHaveBeenCalled();
    await wrapper.find("[data-test=getemall-remove]").trigger("click");
    await flushPromises();
    DELETE.mockResolvedValue({ response: { ok: true } });
    GET.mockResolvedValue({ data: UNLINKED });
    await wrapper.find("[data-test=getemall-confirm-remove]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledWith("/api/partenaires/getemall");
    expect(wrapper.find("[data-test=getemall-empty]").text()).toBe(
      "Aucune application reliée. Celles que tu autorises apparaissent ici.",
    );
    wrapper.unmount();
  });
});
