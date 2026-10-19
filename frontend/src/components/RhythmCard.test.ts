import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import RhythmCard from "./RhythmCard.vue";

// Ta semaine (docs/86) : la part de l'objectif, un point par jour, une phrase sans reproche.
const days = [19, 20, 21, 22, 23, 24, 25].map((d, i) => ({
  day: `2026-10-${d}`,
  research: i < 5,
  sent: d === 19 ? 1 : d === 20 ? 2 : 0,
}));
const mountCard = (week: Record<string, unknown>) =>
  mount(RhythmCard, {
    props: { week: { target: 5, count: 3, days, research_today: true, ...week } as never },
    global: { stubs: { RouterLink: true } },
  });

describe("Ta semaine", () => {
  it("le compte, les jours, ce qui reste", () => {
    const wrapper = mountCard({});
    expect(wrapper.find("[data-test=rhythm-count]").text()).toBe("3 / 5 candidatures");
    const items = wrapper.findAll(".rhythm-days li");
    expect(items).toHaveLength(7);
    expect(items[0]!.classes()).toContain("sent");
    expect(items[1]!.attributes("aria-label")).toBe("mardi, 2 candidatures");
    expect(items[5]!.classes()).toContain("rest");
    expect(wrapper.find("[data-test=rhythm-sentence]").text()).toBe("Encore 2 cette semaine.");
  });

  it("semaine faite, jour sans recherche, sans objectif", () => {
    expect(mountCard({ count: 5 }).find("[data-test=rhythm-sentence]").text()).toBe(
      "Semaine faite. Le reste du temps est à toi.",
    );
    expect(mountCard({ research_today: false }).find("[data-test=rhythm-sentence]").text()).toContain(
      "Jour sans recherche",
    );
    const free = mountCard({ target: null });
    expect(free.find("[data-test=rhythm-count]").exists()).toBe(false);
    expect(free.text()).toContain("pour le répartir sur tes semaines");
  });
});
