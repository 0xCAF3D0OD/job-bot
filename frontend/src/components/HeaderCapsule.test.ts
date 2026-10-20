import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { useCapsuleZone } from "../composables/useCapsule";
import HeaderCapsule from "./HeaderCapsule.vue";

const phone = ref(false);
vi.mock("../composables/usePhone", () => ({ usePhone: () => ({ phone }) }));

// Une zone de test : un bouton qui ouvre son contenu dans la capsule.
function zone(name: "bell" | "account" | "menu") {
  return defineComponent({
    setup() {
      const { open } = useCapsuleZone(name);
      return () =>
        h("div", [
          h("button", { "data-capsule-zone": name, "data-test": name, onClick: () => (open.value = !open.value) }, name),
          open.value ? h("p", { "data-test": `${name}-content` }, `contenu ${name}`) : null,
        ]);
    },
  });
}

const Bell = zone("bell");
const Account = zone("account");

async function mountCapsule() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/aujourdhui");
  const wrapper = mount(HeaderCapsule, {
    attachTo: document.body,
    slots: { default: () => [h(Bell), h(Account)] },
    global: { plugins: [router] },
  });
  await flushPromises();
  return { router, wrapper };
}

afterEach(() => {
  document.body.innerHTML = "";
  phone.value = false;
});

describe("La capsule qui se déroule (docs/91)", () => {
  it("une seule zone ouverte : passer de la cloche au compte change le contenu sans refermer", async () => {
    const { wrapper } = await mountCapsule();
    const capsule = wrapper.find("[data-test=capsule]");
    expect(capsule.classes()).not.toContain("open");
    await wrapper.find("[data-test=bell]").trigger("click");
    expect(capsule.classes()).toContain("open");
    expect(wrapper.find("[data-test=bell-content]").exists()).toBe(true);
    await wrapper.find("[data-test=account]").trigger("click");
    expect(capsule.classes()).toContain("open");
    expect(wrapper.find("[data-test=bell-content]").exists()).toBe(false);
    expect(wrapper.find("[data-test=account-content]").exists()).toBe(true);
    await wrapper.find("[data-test=account]").trigger("click");
    expect(capsule.classes()).not.toContain("open");
  });

  it("se ferme par Échap (le focus revient à la zone), un clic ailleurs ou une page choisie", async () => {
    const { router, wrapper } = await mountCapsule();
    await wrapper.find("[data-test=account]").trigger("click");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(wrapper.find("[data-test=account-content]").exists()).toBe(false);
    expect(document.activeElement).toBe(wrapper.find("[data-test=account]").element);

    await wrapper.find("[data-test=bell]").trigger("click");
    document.body.click();
    await flushPromises();
    expect(wrapper.find("[data-test=bell-content]").exists()).toBe(false);

    await wrapper.find("[data-test=bell]").trigger("click");
    await router.push("/candidatures/offres");
    await flushPromises();
    expect(wrapper.find("[data-test=bell-content]").exists()).toBe(false);
  });

  it("ordinateur (docs/109) : la même largeur, fermée et ouverte", async () => {
    const { wrapper } = await mountCapsule();
    const capsule = wrapper.find("[data-test=capsule]");
    const closedWidth = (capsule.element as HTMLElement).style.width;
    expect(closedWidth).toBe("320px");
    await wrapper.find("[data-test=account]").trigger("click");
    await new Promise((resolve) => requestAnimationFrame(() => resolve(null)));
    await flushPromises();
    expect((capsule.element as HTMLElement).style.width).toBe(closedWidth);
    expect(capsule.classes()).not.toContain("sheet");
  });

  it("téléphone (docs/109) : ce qu'on ouvre prend tout l'écran, la page derrière immobile", async () => {
    phone.value = true;
    const { wrapper } = await mountCapsule();
    await wrapper.find("[data-test=bell]").trigger("click");
    await flushPromises();
    const capsule = wrapper.find("[data-test=capsule]");
    expect(wrapper.find("[data-test=bell-content]").exists()).toBe(true);
    expect(capsule.classes()).toContain("sheet");
    expect(document.documentElement.classList.contains("capsule-sheet")).toBe(true);
    await wrapper.find("[data-test=account]").trigger("click");
    await flushPromises();
    expect(capsule.classes()).toContain("sheet");
    await wrapper.find("[data-test=account]").trigger("click");
    await flushPromises();
    expect(capsule.classes()).not.toContain("sheet");
    expect(document.documentElement.classList.contains("capsule-sheet")).toBe(false);
  });
});
