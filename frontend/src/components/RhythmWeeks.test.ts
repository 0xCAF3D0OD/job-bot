import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import RhythmWeeks from "./RhythmWeeks.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

// Tes semaines (docs/86, 0.68.1) : faites, en dessous, en pause, en cours, à venir.
describe("Tes semaines", () => {
  it("une ligne par semaine du mois", async () => {
    GET.mockResolvedValue({
      data: {
        month: "2026-10",
        weeks: [
          { start: "2026-10-01", end: "2026-10-04", target: 1, count: 2, state: "done" },
          { start: "2026-10-05", end: "2026-10-11", target: 3, count: 1, state: "missed" },
          { start: "2026-10-12", end: "2026-10-18", target: 0, count: 0, state: "pause" },
          { start: "2026-10-19", end: "2026-10-25", target: 3, count: 1, state: "current" },
        ],
      },
    });
    const wrapper = mount(RhythmWeeks, { props: { month: "2026-10" } });
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/rhythm/semaines", { params: { query: { month: "2026-10" } } });
    const rows = wrapper.findAll("li").map((li) => li.findAll("span").map((span) => span.text()));
    expect(rows[0]).toEqual(["1 oct. – 4 oct.", "2 / 1", "faite"]);
    expect(rows[1]).toEqual(["5 oct. – 11 oct.", "1 / 3", "en dessous"]);
    expect(rows[2]?.slice(1)).toEqual(["—", "en pause"]);
    expect(rows[3]?.[2]).toBe("en cours");
  });
});
