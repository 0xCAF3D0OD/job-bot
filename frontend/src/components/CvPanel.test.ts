import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import CvPanel from "./CvPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const offer = { id: 7, title: "Ingénieur DevOps junior", company: "Acme SA", links: [] };

function cv(id: number, chunkIds: number[], extra: Record<string, unknown> = {}) {
  const all = [
    { id: 1, title: "Stage DevOps", section: "experience" },
    { id: 2, title: "Stage web", section: "experience" },
    { id: 3, title: "Kubernetes", section: "competence" },
  ];
  return {
    id,
    offer_id: 7,
    version: 1,
    language: "fr",
    headline: "Ingénieur DevOps junior",
    summary: "Stage DevOps sur AWS.",
    chunk_ids: chunkIds,
    keywords: ["Terraform"],
    instruction: null,
    model: "claude-opus-5",
    created_at: "2026-10-05T08:00:00Z",
    edited_at: null,
    blocks: [
      ...chunkIds.map((i) => ({ ...all.find((b) => b.id === i)!, selected: true })),
      ...all.filter((b) => !chunkIds.includes(b.id)).map((b) => ({ ...b, selected: false })),
    ],
    document: {
      language: "fr",
      name: "Camille Exemple",
      headline: "Ingénieur DevOps junior",
      contacts: ["Rue du Test 1, 1020 Renens"],
      summary_heading: "Profil",
      summary: "Stage DevOps sur AWS.",
      sections: [
        {
          key: "experience",
          heading: "Expériences",
          items: [
            {
              chunk_id: 1,
              title: "Stage DevOps",
              content: [
                { text: "Infrastructure ", strong: false },
                { text: "Terraform", strong: true },
                { text: " sur AWS.", strong: false },
              ],
            },
          ],
        },
      ],
      missing_identity: [],
    },
    ...extra,
  };
}

async function mountPanel() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(CvPanel, { props: { offer: offer as never }, global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("CvPanel", () => {
  it("prépare le CV et met les mots-clés en gras", async () => {
    GET.mockResolvedValue({ data: [] });
    POST.mockResolvedValue({ data: cv(21, [1, 3]) });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=no-cv]").exists()).toBe(true);
    await wrapper.find("[data-test=write-cv]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/cvs", {
      params: { path: { offer_id: 7 } },
      body: { language: null, instruction: null, base_draft_id: null },
    });
    const item = wrapper.find("[data-test=cv-item]");
    expect(item.find("p").text()).toBe("Infrastructure Terraform sur AWS.");
    expect(item.find(".kw").text()).toBe("Terraform");
    expect(wrapper.find("[data-test=cv-docx]").attributes("href")).toBe("/api/cvs/21/docx");
  });

  it("cocher un bloc et le monter enregistrent aussitôt", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    PUT.mockResolvedValueOnce({ data: cv(21, [1, 3, 2]) }).mockResolvedValueOnce({ data: cv(21, [2, 3, 1]) });
    const wrapper = await mountPanel();
    const toggles = wrapper.findAll("[data-test=block-toggle]");
    // Ordre de la liste : Stage DevOps, Stage web (non coché), Kubernetes.
    await toggles[1]!.setValue(true);
    await flushPromises();
    expect((PUT.mock.calls[0]![1] as { body: { chunk_ids: number[] } }).body.chunk_ids).toEqual([1, 3, 2]);

    const up = wrapper.findAll("[data-test=move-up]");
    // « Stage web » est le deuxième de sa rubrique : on peut le monter.
    await up[1]!.trigger("click");
    await flushPromises();
    expect((PUT.mock.calls[1]![1] as { body: { chunk_ids: number[] } }).body.chunk_ids).toEqual([2, 3, 1]);
  });

  it("refuse de décocher le dernier bloc", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1])] });
    const wrapper = await mountPanel();
    await wrapper.findAll("[data-test=block-toggle]")[0]!.setValue(false);
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.find("[role=alert]").text()).toContain("au moins un bloc");
  });

  it("titre et résumé modifiés : enregistrement explicite", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1])] });
    PUT.mockResolvedValue({ data: cv(21, [1], { headline: "Platform engineer junior" }) });
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=headline]").setValue("Platform engineer junior");
    expect(wrapper.find("[data-test=cv-docx]").exists()).toBe(false);
    await wrapper.find("[data-test=save-cv]").trigger("click");
    await flushPromises();
    expect((PUT.mock.calls[0]![1] as { body: { headline: string } }).body.headline).toBe("Platform engineer junior");
  });
});
