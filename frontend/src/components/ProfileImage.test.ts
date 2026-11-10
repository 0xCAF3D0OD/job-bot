import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProfileImage from "./ProfileImage.vue";
import { initialsOf } from "../composables/useProfileImage";

const put = vi.fn(async () => ({ data: { avatar: null } }));
vi.mock("../api/client", () => ({
  api: {
    GET: vi.fn(async (path: string) => ({ data: path === "/api/identity" ? { name: "Kevin Di Nocera" } : { avatar: null } })),
    PUT: (...args: unknown[]) => put(...(args as [])),
  },
}));

afterEach(() => {
  document.body.innerHTML = "";
  put.mockClear();
});

describe("ProfileImage (docs/143)", () => {
  it("les initiales par défaut, l’avatar ou la photo ; décorative", () => {
    expect(initialsOf("Kevin Di Nocera")).toBe("KD");
    expect(initialsOf("kevin")).toBe("K");
    const initials = mount(ProfileImage, { props: { choice: { kind: "initials" }, initials: "KD", size: 48 } });
    expect(initials.text()).toBe("KD");
    expect(initials.get("span").attributes("aria-hidden")).toBe("true");
    expect(initials.classes()).toContain("profile-image-48");
    const avatar = mount(ProfileImage, { props: { choice: { kind: "avatar", avatar: 3 }, initials: "KD", size: 72 } });
    expect(avatar.get("img").attributes("src")).toBe("/avatars/avatar-3-256.webp");
    expect(avatar.get("img").attributes("alt")).toBe("");
  });
});

describe("AvatarPicker (docs/143)", () => {
  it("la grille en aria-pressed, Annuler et Enregistrer ; seul le numéro part au serveur", async () => {
    const { default: AvatarPicker } = await import("./AvatarPicker.vue");
    const { useProfileImage } = await import("../composables/useProfileImage");
    await useProfileImage().load(true);
    const wrapper = mount(AvatarPicker, { attachTo: document.body, props: { open: true } });
    await flushPromises();
    expect(wrapper.text()).toContain("Elle s’affiche seulement dans jobA1. Elle n’est jamais envoyée aux employeurs.");
    const options = wrapper.findAll(".avatar-option");
    expect(options.map((o) => o.text())).toEqual(["KDInitiales", "Souriant", "Clin d'œil", "Casque", "Lunettes", "Bonnet", "Écharpe", "Café", "Étoile", "Ma photo"]);
    expect(wrapper.get("[data-test=avatar-initials]").attributes("aria-pressed")).toBe("true");
    await wrapper.get("[data-test=avatar-4]").trigger("click");
    expect(wrapper.get("[data-test=avatar-4]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.get("[data-test=avatar-initials]").attributes("aria-pressed")).toBe("false");
    await wrapper.get("[data-test=avatar-save]").trigger("click");
    await flushPromises();
    expect(put).toHaveBeenCalledWith("/api/profile-image", { body: { avatar: 4 } });
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});
