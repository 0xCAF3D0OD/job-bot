// « C'est fait ! » (maquette ObjectifAtteint, docs/139 étape 8c ; B10 à B12, Kevin, 2026-11-04).
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import type { OrpMonth } from "../api/client";
import GoalReached from "./GoalReached.vue";

const POST = vi.fn().mockResolvedValue({});
vi.mock("../api/client", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));
const printSheet = vi.fn();
vi.mock("../composables/usePrint", () => ({ printSheet: (...a: unknown[]) => printSheet(...a) }));

const month = {
  month: "2026-11",
  count: 10,
  target: 10,
  rows: [],
  holder: { name: "Kevin", address: null },
  searches: [],
  changed_after_submit: false,
};

async function mountIt() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<p />" } }] });
  await router.push("/");
  return mount(GoalReached, { props: { data: month as unknown as OrpMonth }, global: { plugins: [router] }, attachTo: document.body });
}

describe("GoalReached", () => {
  it("dit l'objectif atteint, comme la maquette : barré, « C'est fait ! », la phrase, l'export, l'accueil", async () => {
    const wrapper = await mountIt();
    expect(wrapper.find(".goal-reached-todo s").text()).toBe("10 recherches à faire");
    expect(wrapper.find("h1").text()).toBe("C'est fait !");
    expect(wrapper.find("[role=status]").text()).toContain(
      "Objectif ORP de novembre atteint, 10 recherches sur 10. Ta feuille est prête pour le rendez-vous.",
    );
    // Le personnage qui fête, 240 px, à la place du logo ravi et du soleil (docs/141, 9) ; rien d'autre.
    const person = wrapper.find("[data-illustration=personnage]");
    expect(person.attributes("data-pose")).toBe("celebration");
    expect(person.attributes("height")).toBe("240");
    expect(wrapper.find("[data-mood-animation]").exists()).toBe(false);
    expect(wrapper.find(".confetti").exists()).toBe(false);
    expect(wrapper.find("[data-test=goal-close]").attributes("aria-label")).toBe("Fermer");
    expect(wrapper.find("[data-test=goal-close]").attributes("href")).toBe("/");
    expect(wrapper.find("[data-test=goal-home]").text()).toBe("Retour à l'accueil");
    // Un seul bouton plein, l'export.
    expect(wrapper.findAll(".primary")).toHaveLength(1);
    expect(wrapper.find("[data-test=goal-export]").text()).toBe("Exporter ma feuille ORP");
    wrapper.unmount();
  });

  it("« Exporter ma feuille ORP » imprime la feuille du mois ; « Je n'ai pas postulé » reste", async () => {
    const wrapper = await mountIt();
    await wrapper.find("[data-test=goal-export]").trigger("click");
    await new Promise((resolve) => setTimeout(resolve));
    expect(printSheet).toHaveBeenCalledWith(expect.any(HTMLElement), expect.objectContaining({ title: "Preuves ORP - 2026-11" }));
    expect(POST).toHaveBeenCalledWith("/api/orp/{month}/exported", { params: { path: { month: "2026-11" } } });
    await wrapper.find("[data-test=cancel-applied]").trigger("click");
    expect(wrapper.emitted("cancel")).toHaveLength(1);
    wrapper.unmount();
  });
});
