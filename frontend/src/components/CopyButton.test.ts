import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CopyButton from "./CopyButton.vue";

describe("CopyButton (règles §4)", () => {
  afterEach(() => vi.useRealTimers());

  it("copie la valeur, annonce « Copié » pendant 2 s, puis revient à « Copier »", async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const wrapper = mount(CopyButton, { props: { value: "abc@joba1.ch", label: "Copier l'adresse" } });
    expect(wrapper.find("button").text()).toContain("Copier l'adresse");
    expect(wrapper.find("[role=status]").text()).toBe("");

    await wrapper.find("button").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("abc@joba1.ch");
    expect(wrapper.find("[role=status]").text()).toBe("Copié");
    expect(wrapper.find("button").text()).toContain("Copié");
    expect(wrapper.emitted("copied")).toHaveLength(1);

    vi.advanceTimersByTime(2000);
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toBe("");
    expect(wrapper.find("button").text()).toContain("Copier l'adresse");
  });

  it("n'annonce rien si la copie échoue", async () => {
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockRejectedValue(new Error("refusé")) } });
    const wrapper = mount(CopyButton, { props: { value: "x" } });
    await wrapper.find("button").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toBe("");
    expect(wrapper.emitted("copied")).toBeUndefined();
  });
});
