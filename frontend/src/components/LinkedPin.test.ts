import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import LinkedPin from "./LinkedPin.vue";

// La carte compacte épinglée (§18 du 15 novembre, CandidaturesOrdinateurEpinglee).
describe("LinkedPin", () => {
  it("un bouton nommé, sans aria-current : la vraie carte reste la seule sélection", () => {
    const wrapper = mount(LinkedPin, { props: { side: "top", title: "DevOps Engineer", sub: "Swisscom", name: "Swisscom" } });
    const button = wrapper.get("button");
    expect(button.attributes("aria-label")).toBe("Revenir à la candidature sélectionnée dans la liste");
    expect(button.attributes("aria-current")).toBeUndefined();
    expect(wrapper.text()).toContain("Swisscom · Sélection affichée");
    expect(wrapper.find("[data-arrow]").exists()).toBe(true);
  });

  it("au clic, la liste défile jusqu'à la vraie carte (block: nearest), qui reçoit le focus", async () => {
    const host = document.createElement("div");
    host.className = "linked-list";
    const card = document.createElement("a");
    card.setAttribute("aria-current", "true");
    card.href = "#";
    card.scrollIntoView = vi.fn();
    host.append(card);
    const slot = document.createElement("div");
    host.append(slot);
    document.body.append(host);
    const wrapper = mount(LinkedPin, { props: { side: "bottom", title: "SRE", sub: "CICR" }, attachTo: slot });
    await wrapper.get("button").trigger("click");
    expect(card.scrollIntoView).toHaveBeenCalledWith(expect.objectContaining({ block: "nearest" }));
    expect(document.activeElement).toBe(card);
    wrapper.unmount();
    host.remove();
  });
});

// La pointe de la flèche touche la pointe du rail (≤ 1 px) : calculé sur les tracés et les mesures des fichiers.
describe("flèche et pointe du rail, au contact", () => {
  const read = (file: string) => readFileSync(resolve(__dirname, file), "utf8");
  // Pointe d'une courbe « Qcx cy ex ey » qui part de (sx, sy) : le milieu de la courbe.
  const tip = (d: string): number => {
    const m = /([-\d.]+) [-\d.]+ Q([-\d.]+) [-\d.]+ ([-\d.]+) [-\d.]+ L/.exec(d.slice(d.indexOf("L16") >= 0 ? d.indexOf("L16") + 1 : d.indexOf("L-14") + 1));
    if (!m) throw new Error(`tracé illisible : ${d}`);
    return 0.25 * Number(m[1]) + 0.5 * Number(m[2]) + 0.25 * Number(m[3]);
  };
  const px = (css: string, name: string) => Number(new RegExp(`${name}: ([\\d.]+)px`).exec(css)![1]);

  it("écart ≤ 1 px entre le bord du trait de la flèche et celui de la pointe", () => {
    const arrow = read("LinkedArrow.vue");
    const detail = read("LinkedDetail.vue");
    const arrowLine = /class="list-card-arrow-line"[^>]*?\sd="([^"]+)"/.exec(arrow)![1]!;
    const notchLine = /class="linked-notch-line"[^>]*?\sd="([^"]+)"/.exec(detail)![1]!;
    const col = px(detail, "--linked-col");
    const gap = px(detail, "--linked-gap");
    const into = px(detail, "--linked-into");
    const cardRight = col - gap;
    // La flèche : à 22 px à droite du bord intérieur de la carte (contour de 2), trait de 2.
    const arrowEdge = cardRight - 2 + tip(arrowLine) + 1;
    // La pointe : le rail commence 9 px après la colonne, trait de 1,5.
    const notchEdge = col + into + tip(notchLine) - 0.75;
    expect(Math.abs(notchEdge - arrowEdge)).toBeLessThanOrEqual(1);
  });
});
