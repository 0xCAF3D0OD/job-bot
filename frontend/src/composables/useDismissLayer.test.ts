import { mount } from "@vue/test-utils";
import { defineComponent, h, nextTick } from "vue";
import { afterEach, describe, expect, it } from "vitest";

import DismissLayer from "../components/DismissLayer.vue";
import { closeAllLayers, openLayerKind, useDismissLayer } from "./useDismissLayer";

function host(kind: string) {
  let api!: ReturnType<typeof useDismissLayer>;
  const Comp = defineComponent({
    setup() {
      api = useDismissLayer(kind);
      return () => h("button", { "data-test": kind, onClick: (e: MouseEvent) => api.toggle(e.currentTarget as HTMLElement) }, kind);
    },
  });
  const wrapper = mount(Comp, { attachTo: document.body });
  return { wrapper, get api() { return api; } };
}

afterEach(() => {
  closeAllLayers();
  document.body.innerHTML = "";
});

describe("useDismissLayer (docs/143, D24)", () => {
  it("ouvrir A ferme B : un seul panneau à la fois", async () => {
    const a = host("notifications");
    const b = host("compte");
    await a.wrapper.get("button").trigger("click");
    expect(a.api.open.value).toBe(true);
    expect(openLayerKind.value).toBe("notifications");
    await b.wrapper.get("button").trigger("click");
    expect(b.api.open.value).toBe(true);
    expect(a.api.open.value).toBe(false);
    expect(openLayerKind.value).toBe("compte");
  });

  it("un clic sur la couche ferme tout", async () => {
    const a = host("compte");
    const layer = mount(DismissLayer, { attachTo: document.body });
    expect(layer.find('[data-test="dismiss-layer"]').exists()).toBe(false);
    a.api.show();
    await nextTick();
    await layer.get('[data-test="dismiss-layer"]').trigger("click");
    expect(a.api.open.value).toBe(false);
    expect(openLayerKind.value).toBeNull();
    await nextTick();
    expect(layer.find('[data-test="dismiss-layer"]').exists()).toBe(false);
  });

  it("Échap ferme et rend le focus au déclencheur", async () => {
    const a = host("filtres");
    const trigger = a.wrapper.get("button").element as HTMLButtonElement;
    trigger.focus();
    a.api.show(trigger);
    const other = document.createElement("input");
    document.body.appendChild(other);
    other.focus();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(a.api.open.value).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });
});
