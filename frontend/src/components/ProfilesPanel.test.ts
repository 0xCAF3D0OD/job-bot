import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProfileSwitcher from "./ProfileSwitcher.vue";
import ProfilesPanel from "./ProfilesPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  PROFILE_KEY: "jobbot-profile",
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

const main = { id: 1, name: "Profil principal", occupation: null, is_main: true, domain_keywords: ["DevOps"], sources: 5 };
const nurse = { id: 2, name: "Infirmière", occupation: "infirmière", is_main: false, domain_keywords: ["soins"], sources: 3 };

describe("ProfilesPanel", () => {
  it("création d'un profil d'essai avec domaine, langues et pays", async () => {
    GET.mockResolvedValue({ data: { current_id: 1, items: [main] } });
    POST.mockResolvedValue({ data: { current_id: 1, items: [main, nurse] } });
    const wrapper = mount(ProfilesPanel);
    await flushPromises();
    await wrapper.find("[data-test=add-profile-open]").trigger("click");
    await wrapper.find("[data-test=profile-name]").setValue(" Infirmière ");
    await wrapper.find("[data-test=profile-keywords]").setValue("soins, infirmière ,");
    await wrapper.find("[data-test=add-profile]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/profiles", {
      body: { name: "Infirmière", occupation: null, domain_keywords: ["soins", "infirmière"], languages: ["fr"], countries: ["CH"] },
    });
    expect(wrapper.findAll("[data-test=profile]")).toHaveLength(2);
    expect(wrapper.findAll("[data-test=profile-delete]")).toHaveLength(1);
  });

  it("le sélecteur retient le profil choisi et recharge la page", async () => {
    GET.mockResolvedValue({ data: { current_id: 1, items: [main, nurse] } });
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload });
    const wrapper = mount(ProfileSwitcher);
    await flushPromises();
    await wrapper.find("[data-test=profile-switcher]").setValue("2");
    expect(localStorage.getItem("jobbot-profile")).toBe("2");
    expect(reload).toHaveBeenCalled();
    await wrapper.find("[data-test=profile-switcher]").setValue("1");
    expect(localStorage.getItem("jobbot-profile")).toBeNull();
    vi.unstubAllGlobals();
  });
});
