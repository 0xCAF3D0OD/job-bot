import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AiWriting from "./AiWriting.vue";

afterEach(() => vi.useRealTimers());

describe("AiWriting (docs/59 §4)", () => {
  it("une barre d’étapes qui avance, la dernière reste en cours", async () => {
    vi.useFakeTimers();
    const wrapper = mount(AiWriting, { props: { kind: "cv" } });
    const current = () => wrapper.find("[aria-current=step]").text();
    expect(current()).toBe("Lire l’offre");
    await vi.advanceTimersByTimeAsync(6000);
    expect(current()).toBe("Choisir ce qui compte");
    expect(wrapper.find("li.done").text()).toBe("Lire l’offre");
    expect(wrapper.find("li.done [data-icon=done]").exists()).toBe(true);
    await vi.advanceTimersByTimeAsync(60000);
    expect(current()).toBe("Relire");
    expect(wrapper.attributes("role")).toBe("status");
  });

});
