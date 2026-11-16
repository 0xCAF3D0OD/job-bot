import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent, h, ref } from "vue";

import { NOTCH_HALF, notchTop, PIN_GAP, PIN_HEIGHT, pinCenter, pinSide, useLinkedNotch } from "./useLinkedNotch";

// Liaison carte → détail (§18 du 15 novembre) : le milieu de la pointe du rail tombe sur le centre de la flèche.
describe("useLinkedNotch, place de la pointe du rail", () => {
  it("top = centre de la flèche − haut de la zone − 30", () => {
    expect(notchTop(400, 150)).toBe(400 - 150 - NOTCH_HALF);
    for (const [center, zone] of [[312.4, 193], [655.75, 193], [880.2, 210.5]] as const) {
      const middle = zone + notchTop(center, zone) + NOTCH_HALF;
      expect(Math.abs(middle - center)).toBeLessThanOrEqual(1);
    }
  });

  it("la carte s'épingle en haut ou en bas quand son centre passe celui de la carte compacte", () => {
    const half = PIN_GAP + PIN_HEIGHT / 2;
    expect(pinSide(400, 200, 900)).toBeNull();
    expect(pinSide(200 + half, 200, 900)).toBeNull();
    expect(pinSide(200 + half - 1, 200, 900)).toBe("top");
    expect(pinSide(900 - half + 1, 200, 900)).toBe("bottom");
    expect(pinCenter("top", 200, 900)).toBe(200 + half);
    expect(pinCenter("bottom", 200, 900)).toBe(900 - half);
  });
});

// Une seule flèche (Kevin, 15.11) : quand la carte compacte est montrée, la flèche de la vraie carte est masquée.
describe("useLinkedNotch, une seule flèche", () => {
  const rect = (top: number, height: number) => ({ top, bottom: top + height, height, left: 0, right: 0, width: 0, x: 0, y: top, toJSON: () => ({}) }) as DOMRect;

  it("masque la flèche de la vraie carte en haut et en bas, et la rend quand la carte revient", async () => {
    const list = document.createElement("div");
    list.innerHTML = '<div data-linked-tools><input></div><div class="linked-cards"><button class="list-card" aria-current="true"><svg data-arrow></svg></button></div>';
    const zone = document.createElement("div");
    document.body.append(list, zone);
    const tools = list.querySelector("input")!;
    const cards = list.querySelector<HTMLElement>(".linked-cards")!;
    const arrow = list.querySelector<SVGElement>("[data-arrow]")!;
    tools.getBoundingClientRect = () => rect(100, 48);
    cards.getBoundingClientRect = () => rect(160, 600);
    zone.getBoundingClientRect = () => rect(100, 700);
    let center = 400;
    arrow.getBoundingClientRect = () => rect(center - 30, 60);
    const host = defineComponent({
      setup() {
        const notch = useLinkedNotch(ref(list), ref(zone));
        return { notch };
      },
      render: () => h("div"),
    });
    const wrapper = mount(host);
    const frame = () => new Promise((done) => requestAnimationFrame(() => done(null)));
    const check = async (at: number, side: string | null) => {
      center = at;
      wrapper.vm.notch.refresh();
      await frame();
      expect(list.getAttribute("data-pinned")).toBe(side);
      expect(arrow.style.visibility).toBe(side ? "hidden" : "");
    };
    await check(400, null);
    await check(120, "top");
    await check(400, null);
    await check(758, "bottom");
    await check(400, null);
    wrapper.unmount();
    list.remove();
    zone.remove();
  });
});
