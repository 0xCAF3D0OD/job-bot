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

    // WCAG 1.4.13 : la souris peut passer du libellé à la bulle (un court délai), puis elle se ferme.
    note.element.dispatchEvent(pointer("pointerleave", "mouse"));
    vi.advanceTimersByTime(100);
    note.element.dispatchEvent(pointer("pointerenter", "mouse"));
    vi.advanceTimersByTime(400);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(true);
    note.element.dispatchEvent(pointer("pointerleave", "mouse"));
    vi.advanceTimersByTime(300);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);

    note.element.dispatchEvent(pointer("pointerenter", "touch"));
    vi.advanceTimersByTime(4000);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);
  });

  it("Échap la ferme sans bouger la souris (WCAG 1.4.13)", async () => {
    vi.useFakeTimers();
    const wrapper = mount(HoverNote, { attachTo: document.body, props: { text: "Communes ou cantons." }, slots: { default: "Lieux" } });
    const note = wrapper.find("[data-test=hover-note]");
    note.element.dispatchEvent(pointer("pointerenter", "mouse"));
    vi.advanceTimersByTime(3000);
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(true);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=hover-note-text]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("au focus clavier : tout de suite, sur le libellé ou sur le bouton qui le contient", async () => {
    // jsdom ne connaît pas :focus-visible : on simule un focus au clavier.
    const matches = Element.prototype.matches;
    vi.spyOn(Element.prototype, "matches").mockImplementation(function (this: Element, selector: string) {
      return selector === ":focus-visible" ? true : matches.call(this, selector);
    });
    const alone = mount(HoverNote, { attachTo: document.body, props: { text: "Communes ou cantons." }, slots: { default: "Lieux" } });
    expect(alone.find("[data-test=hover-note]").attributes("tabindex")).toBe("0");
    await alone.find("[data-test=hover-note]").trigger("focusin");
    expect(alone.find("[data-test=hover-note-text]").exists()).toBe(true);
    await alone.find("[data-test=hover-note]").trigger("focusout");
    expect(alone.find("[data-test=hover-note-text]").exists()).toBe(false);
    alone.unmount();

    const inButton = mount({ components: { HoverNote }, template: '<button type="button"><HoverNote text="Insiste sur Kubernetes.">Kubernetes</HoverNote></button>' }, { attachTo: document.body });
    await inButton.vm.$nextTick();
    expect(inButton.find("[data-test=hover-note]").attributes("tabindex")).toBeUndefined();
    inButton.find("button").element.dispatchEvent(new FocusEvent("focusin", { bubbles: true }));
    await inButton.vm.$nextTick();
    expect(inButton.find("[data-test=hover-note-text]").exists()).toBe(true);
    inButton.unmount();
    vi.restoreAllMocks();
  });

  it("sans description, le libellé reste simple", () => {
    const wrapper = mount(HoverNote, { props: { text: "" }, slots: { default: "Langues" } });
    expect(wrapper.find("[data-test=hover-note]").exists()).toBe(false);
    expect(wrapper.text()).toBe("Langues");
  });
});
