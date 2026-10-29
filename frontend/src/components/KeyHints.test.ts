import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent, h } from "vue";

import { useArrowKeys } from "../composables/useArrowKeys";
import KeyHints from "./KeyHints.vue";

function press(key: string, init: KeyboardEventInit = {}, target: EventTarget = document.body): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...init });
  target.dispatchEvent(event);
  return event;
}

describe("KeyHints et useArrowKeys", () => {
  it("montre ← et → avec leurs actions, caché aux lecteurs d'écran", () => {
    const wrapper = mount(KeyHints, { props: { left: "Écarter", right: "Garder" } });
    expect(wrapper.text()).toBe("Écarter Garder");
    expect(wrapper.findAll("kbd svg")).toHaveLength(2);
    expect(wrapper.attributes("aria-hidden")).toBe("true");
  });

  it("← et → appellent les actions, sauf dans un champ, avec une touche tenue ou une fenêtre ouverte", () => {
    const calls: string[] = [];
    const Host = defineComponent({
      setup() {
        useArrowKeys({ left: () => calls.push("gauche"), right: () => calls.push("droite") });
        return () => h("input");
      },
    });
    const wrapper = mount(Host, { attachTo: document.body });
    expect(press("ArrowLeft").defaultPrevented).toBe(true);
    press("ArrowRight");
    expect(calls).toEqual(["gauche", "droite"]);

    press("ArrowLeft", {}, wrapper.find("input").element);
    press("ArrowRight", { shiftKey: true });
    press("ArrowRight", { repeat: true });
    const dialog = document.createElement("dialog");
    dialog.setAttribute("open", "");
    document.body.append(dialog);
    press("ArrowRight");
    dialog.remove();
    expect(calls).toEqual(["gauche", "droite"]);

    wrapper.unmount();
    press("ArrowLeft");
    expect(calls).toEqual(["gauche", "droite"]);
  });
});
