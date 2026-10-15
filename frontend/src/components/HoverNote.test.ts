import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import HoverNote from "./HoverNote.vue";

afterEach(() => vi.useRealTimers());

function pointer(type: string, pointerType: string): Event {
  const event = new Event(type);
  Object.defineProperty(event, "pointerType", { value: pointerType });
  return event;
}

describe("HoverNote (docs/53)", () => {
  it("bulle après 3 secondes de souris sur le libellé, rien au toucher", async () => {
    vi.useFakeTimers();
    const wrapper = mount(HoverNote, { props: { text: "Communes ou cantons." }, slots: { default: "Lieux" } });
    const note = wrapper.find("[data-test=hover-note]");
    // Lu avec le libellé, sans s'ajouter à son texte.
    expect(note.attributes("aria-description")).toBe("Communes ou cantons.");
    expect(wrapper.text()).toBe("Lieux");

    note.element.dispatchEvent(pointer("pointerenter", "mouse"));
    vi.advanceTimersByTime(2900);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);
    vi.advanceTimersByTime(200);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").text()).toBe("Communes ou cantons.");

    note.element.dispatchEvent(pointer("pointerleave", "mouse"));
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);

    note.element.dispatchEvent(pointer("pointerenter", "touch"));
    vi.advanceTimersByTime(4000);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);
  });

  it("sans description, le libellé reste simple", () => {
    const wrapper = mount(HoverNote, { props: { text: "" }, slots: { default: "Langues" } });
    expect(wrapper.find("[data-test=hover-note]").exists()).toBe(false);
    expect(wrapper.text()).toBe("Langues");
  });
});
