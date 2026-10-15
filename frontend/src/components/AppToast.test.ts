import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AppToast from "./AppToast.vue";

afterEach(() => vi.useRealTimers());

describe("Bulle temporaire (docs/32 §4)", () => {
  it("disparaît après 5 s, 8 s pour une erreur, et attend tant que la souris est dessus", async () => {
    vi.useFakeTimers();
    const info = mount(AppToast, { props: { message: "Collecte lancée." } });
    vi.advanceTimersByTime(4900);
    expect(info.emitted("close")).toBeUndefined();
    vi.advanceTimersByTime(200);
    expect(info.emitted("close")).toHaveLength(1);

    const error = mount(AppToast, { props: { message: "API injoignable.", error: true } });
    await error.trigger("mouseenter");
    vi.advanceTimersByTime(20000);
    expect(error.emitted("close")).toBeUndefined();
    await error.trigger("mouseleave");
    vi.advanceTimersByTime(7900);
    expect(error.emitted("close")).toBeUndefined();
    vi.advanceTimersByTime(200);
    expect(error.emitted("close")).toHaveLength(1);
  });

  it("se ferme tout de suite avec ×", async () => {
    const wrapper = mount(AppToast, { props: { message: "Collecte lancée." } });
    await wrapper.find("[data-test=toast-close]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});
