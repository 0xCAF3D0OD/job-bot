import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AuthScene from "./AuthScene.vue";

// Les préférences du système : thème sombre, réduire les animations.
function media(prefs: { dark: boolean; still?: boolean }) {
  const listeners: Array<() => void> = [];
  const state = { ...prefs };
  vi.stubGlobal("matchMedia", (query: string) => ({
    get matches() {
      return query.includes("dark") ? state.dark : !!state.still;
    },
    addEventListener: (_: string, fn: () => void) => listeners.push(fn),
    removeEventListener: vi.fn(),
  }));
  return {
    set(dark: boolean) {
      state.dark = dark;
      listeners.forEach((fn) => fn());
    },
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("AuthScene (docs/67, complément 0.55.3)", () => {
  it("en clair, le jour ; en sombre, la vidéo puis l'image du soir", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    const theme = media({ dark: false });
    const wrapper = mount(AuthScene);
    expect(wrapper.attributes("data-phase")).toBe("day");
    expect(wrapper.find(".night-image").exists()).toBe(false);

    theme.set(true);
    await wrapper.vm.$nextTick();
    expect(wrapper.attributes("data-phase")).toBe("dusk");
    expect(play).toHaveBeenCalled();
    await wrapper.find("video").trigger("ended");
    expect(wrapper.attributes("data-phase")).toBe("night");
    expect(wrapper.find(".night-image").exists()).toBe(true);

    theme.set(false);
    await wrapper.vm.$nextTick();
    expect(wrapper.attributes("data-phase")).toBe("day");
  });

  it("« réduire les animations » : l'image du soir sans la vidéo", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    media({ dark: true, still: true });
    const wrapper = mount(AuthScene);
    await wrapper.vm.$nextTick();
    expect(wrapper.attributes("data-phase")).toBe("night");
    expect(play).not.toHaveBeenCalled();
  });
});
