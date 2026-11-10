import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import TroupeLoader from "./TroupeLoader.vue";

// L'attente (MODIFICATIONS du 9 novembre, §15) : rien sous 1 s, les 4 sautent jusqu'à 10 s, puis un texte.
describe("TroupeLoader", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("rien avant 1 s, puis les 4 morceaux du logo, puis le texte après 10 s", async () => {
    const wrapper = mount(TroupeLoader, { props: { slowText: "Les offres arrivent, encore un instant." } });
    expect(wrapper.attributes("data-stage")).toBe("hidden");
    expect(wrapper.find("svg").exists()).toBe(false);
    await vi.advanceTimersByTimeAsync(1000);
    expect(wrapper.attributes("data-stage")).toBe("jumping");
    expect(wrapper.findAll(".troupe-loader-part")).toHaveLength(4);
    expect(wrapper.find("svg").attributes("aria-hidden")).toBe("true");
    expect(wrapper.find("[data-test=troupe-loader-slow]").exists()).toBe(false);
    await vi.advanceTimersByTimeAsync(9000);
    expect(wrapper.attributes("data-stage")).toBe("slow");
    expect(wrapper.get("[data-test=troupe-loader-slow]").text()).toBe("Les offres arrivent, encore un instant.");
  });

  it("le nom de ce qui charge, tout de suite quand la page a déjà attendu", () => {
    const wrapper = mount(TroupeLoader, { props: { label: "Offres", delay: 0 } });
    expect(wrapper.attributes("role")).toBe("status");
    expect(wrapper.attributes("data-stage")).toBe("jumping");
    expect(wrapper.get(".troupe-loader-label").text()).toBe("Offres");
  });
});
