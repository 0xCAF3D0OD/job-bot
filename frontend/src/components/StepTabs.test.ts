import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import StepTabs from "./StepTabs.vue";

describe("StepTabs (maquette Preparer, C2)", () => {
  it("le numéro en pastille teintée, une coche pour l’étape faite, seule l’étape ouverte annoncée", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/");
    const wrapper = mount(StepTabs, {
      props: {
        label: "Étapes",
        current: "cv",
        steps: [
          { key: "letter", label: "Lettre", to: "/?", done: true },
          { key: "cv", label: "CV", to: "/?doc=cv" },
          { key: "apply", label: "Postuler", to: "/?doc=postuler" },
        ],
      },
      global: { plugins: [router] },
    });
    const links = wrapper.findAll("a");
    expect(links.map((a) => a.attributes("aria-current"))).toEqual([undefined, "step", undefined]);
    expect(links[0]!.find(".step-dot.done [data-icon=check]").exists()).toBe(true);
    expect(links[0]!.text()).toContain("(faite)");
    expect(links.slice(1).map((a) => a.find(".step-dot").text())).toEqual(["2", "3"]);
  });
});
