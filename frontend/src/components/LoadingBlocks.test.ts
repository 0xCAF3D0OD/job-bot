import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import LoadingBlocks from "./LoadingBlocks.vue";

describe("LoadingBlocks (planche « vide et chargement »)", () => {
  afterEach(() => vi.useRealTimers());

  it("rien avant 300 ms, puis les blocs et une seule annonce « Chargement… »", async () => {
    vi.useFakeTimers();
    const wrapper = mount(LoadingBlocks, { props: { heights: ["4rem", "4rem"] } });
    expect(wrapper.findAll(".loading-block")).toHaveLength(0);
    expect(wrapper.text()).toBe("");
    vi.advanceTimersByTime(300);
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll(".loading-block")).toHaveLength(2);
    expect(wrapper.findAll("[role=status]")).toHaveLength(1);
    expect(wrapper.text()).toBe("Chargement…");
  });
});
