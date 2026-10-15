import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { defineComponent, h } from "vue";

import HelpTip from "./HelpTip.vue";
import SidePanel from "./SidePanel.vue";

function escape(target: Element): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true });
  target.dispatchEvent(event);
  return event;
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("SidePanel (docs/32 §2.2)", () => {
  it("Échap ferme la bulle « ? » ouverte dans le panneau, pas le panneau", async () => {
    const wrapper = mount(SidePanel, {
      props: { open: true, title: "Candidature spontanée" },
      slots: { default: () => h(HelpTip, { text: "Deux ou trois lignes.", label: "Aide : pourquoi elle" }) },
      attachTo: document.body,
    });
    await flushPromises();
    const button = document.querySelector<HTMLButtonElement>("[data-test=help-tip]")!;
    button.click();
    await flushPromises();
    expect(document.querySelector("[data-test=help-tip-text]")).not.toBeNull();

    const first = escape(button);
    await flushPromises();
    expect(document.querySelector("[data-test=help-tip-text]")).toBeNull();
    expect(first.defaultPrevented).toBe(true);
    expect(wrapper.emitted("close")).toBeUndefined();

    escape(button);
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("seul le panneau du dessus se ferme, et Échap ne va pas plus loin", async () => {
    let reachedWindow = false;
    const onWindow = (): void => {
      reachedWindow = true;
    };
    window.addEventListener("keydown", onWindow);
    const closed: string[] = [];
    const Two = defineComponent(() => () => [
      h(SidePanel, { open: true, title: "Offre", onClose: () => closed.push("offre") }),
      h(SidePanel, { open: true, title: "Contacts", onClose: () => closed.push("contacts") }),
    ]);
    const wrapper = mount(Two, { attachTo: document.body });
    await flushPromises();
    escape(document.body);
    expect(closed).toEqual(["contacts"]);
    expect(reachedWindow).toBe(false);
    expect(document.querySelector("[data-test=side-panel]")!.getAttribute("aria-modal")).toBe("true");
    wrapper.unmount();
    window.removeEventListener("keydown", onWindow);
    expect(document.documentElement.classList.contains("side-open")).toBe(false);
  });

  it("rend le focus à l'élément de départ quand le panneau est démonté", async () => {
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    const wrapper = mount(SidePanel, { props: { open: true, title: "Contacts" }, attachTo: document.body });
    await flushPromises();
    expect(document.activeElement).toBe(document.querySelector("[data-test=side-close]"));
    wrapper.unmount();
    expect(document.activeElement).toBe(opener);
  });

  it("garde le focus dans le panneau avec Tab et Maj+Tab", async () => {
    const wrapper = mount(SidePanel, {
      props: { open: true, title: "Contacts" },
      slots: { default: () => h("input", { "data-test": "last" }) },
      attachTo: document.body,
    });
    await flushPromises();
    const close = document.querySelector<HTMLElement>("[data-test=side-close]")!;
    const last = document.querySelector<HTMLElement>("[data-test=last]")!;
    last.focus();
    last.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(close);
    close.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(last);
    wrapper.unmount();
  });
});
