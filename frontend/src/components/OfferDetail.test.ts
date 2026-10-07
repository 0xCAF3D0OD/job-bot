import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OfferDetail from "./OfferDetail.vue";

const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: vi.fn(() => Promise.resolve({ data: undefined })), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

function offer(extra: Record<string, unknown> = {}) {
  return {
    id: 4,
    title: "Ingénieur DevOps",
    company: "Exemple SA",
    location: "Lausanne",
    status: "to_review",
    first_seen_at: "2026-10-05T08:00:00Z",
    last_seen_at: "2026-10-05T08:00:00Z",
    seen_count: 1,
    links: [{ source: "indeed", url: "https://ch.indeed.com/viewjob?jk=1" }],
    apply_url: null,
    apply_kind: null,
    employer_url: null,
    employer_url_source: null,
    employer_status: null,
    employer_checked_at: null,
    ...extra,
  };
}

async function mountDetail(value: Record<string, unknown>) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(OfferDetail, { props: { offer: value as never }, global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("OfferDetail, annonce chez l'employeur (docs/20 §2)", () => {
  it("lien vérifié affiché avec sa source", async () => {
    const wrapper = await mountDetail(
      offer({ employer_url: "https://exemple.ch/jobs/2", employer_url_source: "ats", employer_status: "found", employer_checked_at: "2026-10-07T08:00:00Z" }),
    );
    expect(wrapper.find("[data-test=employer]").attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(wrapper.find("[data-test=employer-line]").text()).toContain("via son outil de recrutement");
  });

  it("recherche à la demande, puis « pas trouvée »", async () => {
    POST.mockResolvedValue({ data: offer({ employer_status: "not_found", employer_checked_at: "2026-10-07T08:00:00Z" }) });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=find-employer]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/employer", { params: { path: { offer_id: 4 } } });
    expect(wrapper.text()).toContain("Pas trouvée chez l'employeur");
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("agence, ou lien employeur déjà donné par jobup", async () => {
    expect((await mountDetail(offer({ employer_status: "agency" }))).text()).toContain("employeur non indiqué");
    const known = await mountDetail(offer({ apply_kind: "external", apply_url: "https://exemple.ch/postuler" }));
    expect(known.find("[data-test=employer-line]").exists()).toBe(false);
  });
});
