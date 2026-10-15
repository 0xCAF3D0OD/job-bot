import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AiWriting from "./AiWriting.vue";

afterEach(() => vi.useRealTimers());

describe("AiWriting (docs/58 §3.2)", () => {
  it("une phrase qui change toutes les 4 secondes, la dernière reste", async () => {
    vi.useFakeTimers();
    const wrapper = mount(AiWriting, { props: { kind: "letter" } });
    expect(wrapper.text()).toContain("Je lis l'offre…");
    await vi.advanceTimersByTimeAsync(4000);
    expect(wrapper.text()).toContain("Je choisis tes expériences…");
    await vi.advanceTimersByTimeAsync(60000);
    expect(wrapper.text()).toContain("Je relis…");
    expect(wrapper.attributes("role")).toBe("status");
  });
});
