import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import AiSpend from "./AiSpend.vue";
import FilterOutcome from "./FilterOutcome.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

describe("de l'information plutôt que du vide (docs/63 §2)", () => {
  it("ce que donnent les critères : retenues sur reçues, trois raisons au plus", async () => {
    GET.mockResolvedValue({
      data: {
        start: "2026-08-01",
        received: 412,
        retained: 96,
        reasons: [
          { rule: "locations", label: "lieu", count: 180 },
          { rule: "min_rate", label: "taux d'activité", count: 74 },
          { rule: "language", label: "langue", count: 31 },
          { rule: "contract", label: "type d'offre", count: 9 },
        ],
      },
    });
    const wrapper = mount(FilterOutcome);
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/insights/filter");
    expect(wrapper.text()).toContain("96 offres passent sur 412 reçues");
    expect(wrapper.text()).toContain("23 %");
    expect(wrapper.findAll("li")).toHaveLength(3);
    // Une largeur CSS valide (« 57% », sans espace), sinon toutes les barres sont pleines.
    expect(wrapper.find(".bilan-bar").attributes("style")).toContain("width: 57%");
  });

  it("la dépense du mois à côté du plafond", async () => {
    GET.mockResolvedValue({
      data: { configured: true, model: "claude", month_spend_chf: "3.2", budget_chf: "20", budget_reached: false },
    });
    const wrapper = mount(AiSpend);
    await flushPromises();
    expect(wrapper.text()).toContain("3,20 CHF");
    expect(wrapper.text()).toContain("sur 20,00");
    expect(wrapper.find(".bilan-bar").attributes("style")).toContain("width: 16%");
  });
});
