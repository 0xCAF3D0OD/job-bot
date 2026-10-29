import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import SavedStatus from "./SavedStatus.vue";

describe("SavedStatus (planche « Champs »)", () => {
  afterEach(() => vi.useRealTimers());

  it("« Enregistré » annoncé après un enregistrement, puis effacé au bout de 3 s", async () => {
    vi.useFakeTimers();
    const wrapper = mount(SavedStatus, { props: { at: 0 } });
    expect(wrapper.attributes("role")).toBe("status");
    expect(wrapper.text()).toBe("");
    await wrapper.setProps({ at: Date.now() });
    expect(wrapper.text()).toBe("Enregistré");
    vi.advanceTimersByTime(3000);
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toBe("");
  });
});
