import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import IdentityForm from "./IdentityForm.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn() },
}));
afterEach(() => vi.resetAllMocks());

describe("IdentityForm", () => {
  it("charge et enregistre les coordonnées", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/identity"
            ? { name: "Camille Exemple", street: null, postcode: null, city: null, phone: null, email: null }
            : path === "/api/notifications"
              ? { configured: false, server: "https://ntfy.sh" }
              : { orp_monthly_target: null, notify_score_threshold: 70, llm_monthly_budget_chf: 10 },
      }),
    );
    const { api } = await import("../api/client");
    const put = vi.mocked(api.PUT).mockResolvedValue({ data: {} } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    const name = wrapper.find<HTMLInputElement>("[data-test=identity-name]");
    expect(name.element.value).toBe("Camille Exemple");
    await wrapper.find("[data-test=identity-street]").setValue("Rue du Test 1");
    await wrapper.find("[data-test=identity-postcode]").setValue("1020");
    await wrapper.find("[data-test=identity-city]").setValue("Renens");
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/identity", {
      body: {
        name: "Camille Exemple",
        street: "Rue du Test 1",
        postcode: "1020",
        city: "Renens",
        phone: null,
        email: null,
      },
    });
    expect(wrapper.find("[data-test=identity-form] [role=status]").text()).toContain("enregistrées");
  });

  it("plateforme pas à jour : demande de la redémarrer", async () => {
    GET.mockResolvedValue({ data: undefined, response: { status: 404 } });
    const { api } = await import("../api/client");
    vi.mocked(api.PUT).mockResolvedValue({ data: undefined, response: { status: 404 } } as never);
    const wrapper = mount(IdentityForm);
    await flushPromises();
    await wrapper.find("[data-test=identity-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=identity-form] [role=status]").text()).toContain("redémarre-la");
  });
});

describe("IdentityForm, ce qui manque (docs/21 §6)", () => {
  it("annonce les champs manquants de l'en-tête", async () => {
    GET.mockResolvedValue({ data: { name: "Camille Exemple", street: null, postcode: null, city: "Lausanne", phone: null, email: null } });
    const wrapper = mount(IdentityForm);
    await flushPromises();
    expect(wrapper.find("[data-test=identity-missing]").text()).toBe("Il manque : ta rue, ton NPA.");
  });
});
