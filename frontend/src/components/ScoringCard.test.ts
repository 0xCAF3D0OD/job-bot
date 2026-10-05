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
    expect(wrapper.find("[data-test=scoring-error]").text()).toBe(
      "crédit API Anthropic épuisé : en racheter dans la console",
    );
    expect(wrapper.text()).toContain("Aucun bloc de profil actif");
    await wrapper.find("[data-test=rescore]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/rescore");
    expect(wrapper.find("[role=status]").text()).toContain("Renotation lancée");
  });
});
