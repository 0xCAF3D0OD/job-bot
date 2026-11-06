import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OfferDetail from "./OfferDetail.vue";

const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: vi.fn(() => Promise.resolve({ data: undefined })),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const GAPS = [
  { text: "Exigences : non précisées dans l'extrait", chunk_ids: [] },
  { text: "Conseil : lire l'annonce complète", chunk_ids: [] },
];

function offer(extra: Record<string, unknown> = {}) {
  return {
    id: 7,
    title: "Ingénieur DevOps",
    company: "SpeciTec",
    location: "Lausanne",
    status: "to_review",
    first_seen_at: "2026-11-05T08:00:00Z",
    last_seen_at: "2026-11-05T08:00:00Z",
    seen_count: 1,
    links: [{ source: "linkedin", url: "https://www.linkedin.com/jobs/view/42" }],
    snippet: "Extrait de l'alerte",
    description: null,
    score: 61,
    summary_partial: true,
    strengths: [{ text: "Linux : 5 ans", chunk_ids: [1] }],
    gaps: GAPS,
    ...extra,
  };
}

async function mountDetail(value: Record<string, unknown>) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(OfferDetail, { props: { offer: value as never }, global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } } });
  await flushPromises();
  return wrapper;
}

describe("OfferDetail, note provisoire (offre venue d'une alerte)", () => {
  it("encadré à la place des manques génériques, seulement quand l'annonce manque", async () => {
    const partial = await mountDetail(offer());
    const notice = partial.find("[data-test=partial-notice]");
    expect(notice.text()).toContain("Note provisoire : l'annonce complète n'a pas pu être lue.");
    expect(notice.find("[data-test=read-offer-text]").text()).toContain("Lire l'annonce maintenant");
    expect(notice.find("[data-test=paste-offer-text]").text()).toBe("Coller le texte de l'annonce");
    expect(partial.find("[data-test=match-sub]").text()).toContain("sur l'extrait de l'alerte seulement");
    expect(partial.find("[data-test=match-lines]").text()).not.toContain("Exigences");
    expect(partial.find("[data-test=gaps]").exists()).toBe(false);

    const full = await mountDetail(offer({ description: "Texte complet de l'annonce", summary_partial: false }));
    expect(full.find("[data-test=partial-notice]").exists()).toBe(false);
    expect(full.find("[data-test=match-lines]").text()).toContain("Exigences");
    expect(full.find("[data-test=match-sub]").text()).not.toContain("extrait");

    const spontaneous = await mountDetail(offer({ spontaneous: true }));
    expect(spontaneous.find("[data-test=partial-notice]").exists()).toBe(false);
  });

  it("sans lien lisible, seulement « Coller le texte »", async () => {
    const wrapper = await mountDetail(offer({ links: [{ source: "manual", url: "https://annonce-collee.invalid/" }] }));
    expect(wrapper.find("[data-test=read-offer-text]").exists()).toBe(false);
    expect(wrapper.find("[data-test=paste-offer-text]").exists()).toBe(true);
  });

  it("« Lire l'annonce maintenant » : la fiche se recharge ; l'échec propose de coller", async () => {
    POST.mockResolvedValueOnce({ data: { saved: true, source: "page", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/read", { params: { path: { offer_id: 7 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);

    POST.mockResolvedValueOnce({ data: { saved: false, problem: "Ce site interdit la lecture par un robot : colle le texte de l'annonce.", paste: true } });
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=read-problem]").text()).toContain("colle le texte");
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("texte collé : trop court refusé, puis enregistré", async () => {
    PUT.mockResolvedValue({ data: { saved: true, source: "collé", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=paste-offer-text]").trigger("click");
    await wrapper.find("[data-test=paste-text]").setValue("Trop court.");
    await wrapper.find("[data-test=paste-save]").trigger("click");
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=paste-sheet]").text()).toContain("trop court");

    const text = "Tu administres nos serveurs Linux. ".repeat(8);
    await wrapper.find("[data-test=paste-text]").setValue(text);
    await wrapper.find("[data-test=paste-save]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/offers/{offer_id}/description", { params: { path: { offer_id: 7 } }, body: { text } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });
});
