import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter, type Router } from "vue-router";

import { useUndo } from "../composables/useUndo";
import { useOfferSelection } from "../composables/useOfferSelection";
import OffersView from "./OffersView.vue";

const GET = vi.fn();
const PATCH = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
const PUT = vi.fn();
// Aucune note corrigée (docs/114) : sans cette réponse, la fiche recevait une page d'offres
// à la place de la correction et ScoreCorrection lisait un sens inexistant.
const NO_CORRECTION = "/api/offers/{offer_id}/score-correction";
vi.mock("../api/client", () => ({
  api: {
    PUT: (...args: unknown[]) => PUT(...args),
    GET: (...args: unknown[]) => (args[0] === NO_CORRECTION ? Promise.resolve({ data: null }) : GET(...args)),
    PATCH: (...args: unknown[]) => PATCH(...args),
    POST: (...args: unknown[]) => POST(...args),
    DELETE: (...args: unknown[]) => DELETE(...args),
  },
}));

const offer = (id: number, title: string, extra: Record<string, unknown> = {}) => ({
  id,
  title,
  company: "Acme SA",
  location: "Lausanne, VD",
  rate_min: 80,
  rate_max: 100,
  snippet: "Gérer l’infrastructure.",
  status: "to_review",
  first_seen_at: "2026-10-02T08:00:00Z",
  last_seen_at: "2026-10-02T08:00:00Z",
  seen_count: 1,
  links: [{ source: "jobup", url: `https://www.jobup.ch/fr/emplois/detail/${id}/` }],
  filter_reasons: [],
  ...extra,
});

function page(items: unknown[]) {
  return {
    data: {
      items,
      total: items.length,
      counts: { to_review: 5, pending: 6, pending_all: 6, filtered_out: 2, later: 0, in_progress: 0, expired: 3, all: 7 },
      facets: {
        sources: [
          { value: "indeed", count: 3 },
          { value: "jobup", count: 4 },
        ],
        cantons: [
          { value: "VD", count: 4 },
          { value: "GE", count: 1 },
        ],
        sure: 104,
        provisional: 312,
      },
    },
  };
}

let router: Router;

function mockOffers(response: unknown): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/profile-chunks" ? { data: [{ id: 1, title: "Linux", active: true }] } : response),
  );
}

async function mountAt(path: string, provide: Record<string, unknown> = {}) {
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/offres", name: "offers", component: OffersView },
      { path: "/aujourdhui/tri", name: "triage", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(OffersView, { global: { plugins: [router], provide, stubs: { teleport: true, ContactsPanel: true } } });
  await flushPromises();
  return wrapper;
}

// L'en-tête de la sélection se charge à part (poids de Candidatures) : attendre l'import.
async function startSelection(wrapper: { get: (s: string) => { trigger: (e: string) => Promise<void> } }) {
  await wrapper.get("[data-test=select-start]").trigger("click");
  await flushPromises();
  await vi.dynamicImportSettled();
  await flushPromises();
}

beforeEach(() => {
  sessionStorage.clear();
  GET.mockImplementation((path: string) =>
    Promise.resolve(
      path === "/api/profile-chunks"
        ? { data: [{ id: 1, title: "Linux", active: true }] }
        : page([offer(1, "Ingénieur système")]),
    ),
  );
});
afterEach(async () => {
  await useUndo().flush();
  POST.mockReset();
  useOfferSelection().stop();
  GET.mockReset();
  vi.useRealTimers();
  sessionStorage.clear();
});

describe("sélection multiple (§72q, Kevin le 19.11)", () => {
  const expired = { expired_at: "2026-11-18T08:00:00Z", expiry_source: "age" };
  const list = () => page([offer(1, "Une"), offer(2, "Deux", expired), offer(3, "Trois", expired), offer(4, "Quatre", { status: "applied" })]);

  it("« Sélectionner » à droite du premier titre seulement ; les cartes deviennent des cases, « Retirée » devient « Offre expirée »", async () => {
    mockOffers(list());
    const wrapper = await mountAt("/offres");
    expect(wrapper.findAll("[data-test=select-start]")).toHaveLength(1);
    expect(wrapper.text()).toContain("Retirée");
    expect(wrapper.find("[role=checkbox]").exists()).toBe(false);
    await startSelection(wrapper);
    expect(wrapper.find("[data-test=select-start]").exists()).toBe(false);
    expect(wrapper.find("[data-test=offers-toolbar]").exists()).toBe(false);
    const boxes = wrapper.findAll("[role=checkbox]");
    // L'offre envoyée n'est pas cochable.
    expect(boxes).toHaveLength(3);
    expect(boxes.every((b) => b.attributes("aria-checked") === "false")).toBe(true);
    expect(wrapper.text()).toContain("Offre expirée");
    expect(wrapper.text()).not.toContain("Retirée");
    expect(wrapper.get("[data-test=multi-count]").text()).toBe("0 sélectionnée");
    await boxes[0]!.trigger("click");
    await boxes[1]!.trigger("keydown", { key: " " });
    expect(wrapper.get("[data-test=multi-count]").text()).toBe("2 sélectionnées");
    expect(wrapper.findAll("[role=checkbox]").map((b) => b.attributes("aria-checked"))).toEqual(["true", "true", "false"]);
    // Un clic ne fait que cocher : aucune fiche ne s'ouvre.
    expect(wrapper.find("[data-test=offer-detail]").exists()).toBe(false);
  });

  it("« Toutes les expirées · N » coche puis décoche les offres expirées ; masquée sans offre expirée", async () => {
    mockOffers(list());
    const wrapper = await mountAt("/offres");
    await startSelection(wrapper);
    const pill = wrapper.get("[data-test=multi-expired]");
    expect(pill.text()).toBe("Toutes les expirées · 2");
    expect(pill.attributes("aria-pressed")).toBe("false");
    await pill.trigger("click");
    expect(pill.attributes("aria-pressed")).toBe("true");
    expect(wrapper.findAll("[role=checkbox]").map((b) => b.attributes("aria-checked"))).toEqual(["false", "true", "true"]);
    await pill.trigger("click");
    expect(wrapper.get("[data-test=multi-count]").text()).toBe("0 sélectionnée");
    wrapper.unmount();
    mockOffers(page([offer(1, "Une"), offer(5, "Cinq")]));
    const plain = await mountAt("/offres");
    await startSelection(plain);
    expect(plain.find("[data-test=multi-expired]").exists()).toBe(false);
  });

  it("« Écarter N offres » : les cartes sortent tout de suite, un bandeau, un seul appel à la fin ; « Annuler » les remet à leur place", async () => {
    mockOffers(list());
    const wrapper = await mountAt("/offres");
    await startSelection(wrapper);
    const discard = wrapper.get("[data-test=multi-discard]");
    expect(discard.text()).toBe("Écarter 0 offre");
    expect(discard.attributes("aria-disabled")).toBe("true");
    await wrapper.get("[data-test=multi-expired]").trigger("click");
    expect(wrapper.get("[data-test=multi-discard]").text()).toBe("Écarter 2 offres");
    await wrapper.get("[data-test=multi-discard]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=multi-head]").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=offer]").map((c) => c.text())).toEqual([expect.stringContaining("Une"), expect.stringContaining("Quatre")]);
    expect(useUndo().pending.value?.message).toBe("2 offres écartées");
    expect(POST).not.toHaveBeenCalled();
    await useUndo().undo();
    await flushPromises();
    expect(wrapper.findAll("[data-test=offer]").map((c) => c.find("[data-test=list-card-title]").text())).toEqual(["Une", "Deux", "Trois", "Quatre"]);
    expect(POST).not.toHaveBeenCalled();
    // Écarter pour de bon : un seul appel, avec les deux offres.
    await startSelection(wrapper);
    await wrapper.get("[data-test=multi-expired]").trigger("click");
    await wrapper.get("[data-test=multi-discard]").trigger("click");
    POST.mockResolvedValue({ data: { ignored: [2, 3], skipped: [] } });
    mockOffers(page([offer(1, "Une"), offer(4, "Quatre", { status: "applied" })]));
    await useUndo().flush();
    await flushPromises();
    expect(POST).toHaveBeenCalledTimes(1);
    expect(POST.mock.calls[0]![0]).toBe("/api/offers/discard");
    expect((POST.mock.calls[0]![1] as { body: unknown }).body).toEqual({ ids: [2, 3] });
  });

  it("Échap, la croix et « Annuler » quittent sans rien écarter", async () => {
    mockOffers(list());
    const wrapper = await mountAt("/offres", {});
    for (const leave of ["escape", "multi-quit", "multi-cancel"]) {
      await startSelection(wrapper);
      await wrapper.findAll("[role=checkbox]")[0]!.trigger("click");
      if (leave === "escape") window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
      else await wrapper.get(`[data-test=${leave}]`).trigger("click");
      await flushPromises();
      expect(wrapper.find("[data-test=multi-head]").exists()).toBe(false);
      expect(wrapper.find("[role=checkbox]").exists()).toBe(false);
      expect(wrapper.findAll("[data-test=offer]")).toHaveLength(4);
    }
    expect(POST).not.toHaveBeenCalled();
    expect(useUndo().pending.value).toBeNull();
  });
});
