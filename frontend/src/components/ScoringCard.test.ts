import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ScoringCard from "./ScoringCard.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const base = {
  configured: true,
  model: "claude-opus-5",
  month_spend_chf: "2.40",
  budget_chf: "10",
  budget_reached: false,
  active_chunks: 4,
  scored: 120,
  unscored: 3,
  stale: 0,
  failed: 1,
  pending_batches: 0,
  last_error: null,
};

describe("ScoringCard", () => {
  it("affiche la dépense et les compteurs", async () => {
    GET.mockResolvedValue({ data: base });
    const wrapper = mount(ScoringCard);
    await flushPromises();
    expect(wrapper.text()).toContain("2.40 / 10 CHF");
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("24");
    expect(wrapper.find("[data-test=rescore]").exists()).toBe(false);
    // Des lignes (1.6.67) : l'état écrit en mots, les notées à droite de leur ligne.
    const rows = wrapper.findAll("[data-test=setting-row]");
    expect(rows[0]?.find(".setting-row-title").text()).toBe("Intelligence artificielle");
    expect(rows[0]?.find(".setting-row-control").text()).toContain("Active");
    const counts = wrapper.find("[data-test=scoring-counts]");
    expect(counts.find(".setting-row-control").text()).toBe("120");
    expect(counts.find(".setting-row-description").text()).toBe("3 à noter · aucun lot en cours · 1 échec.");
  });

  it("erreur de compte, profil vide et renotation", async () => {
    GET.mockResolvedValue({
      data: {
        ...base,
        active_chunks: 0,
        stale: 12,
        last_error: "ScoringUnavailable: crédit API Anthropic épuisé : en racheter dans la console",
      },
    });
    POST.mockResolvedValue({ data: { result: "queued" }, response: { status: 202 } });
    const wrapper = mount(ScoringCard);
    await flushPromises();
    expect(wrapper.find("[data-test=scoring-error] .setting-row-description").text()).toBe(
      "crédit API Anthropic épuisé : en racheter dans la console",
    );
    expect(wrapper.text()).toContain("Aucun bloc de profil actif");
    await wrapper.find("[data-test=rescore]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/rescore");
    expect(wrapper.find("[data-test=scoring-message]").text()).toContain("Renotation lancée");
  });
});
