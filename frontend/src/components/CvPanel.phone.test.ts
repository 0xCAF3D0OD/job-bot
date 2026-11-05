import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import CvPanel from "./CvPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", useNarrow: () => ({ phone: ref(true) }), usePhone: () => ({ phone: ref(true) }) }));
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

describe("CvPanel sur téléphone (maquette Preparer)", () => {
  it("sans CV : le modèle, l'aperçu vide et « Préparer le CV » en bas", async () => {
    GET.mockResolvedValue({ data: [] });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=template-moderne]").exists()).toBe(true);
    expect(wrapper.find("[data-test=no-cv] [data-test=doc-preview-empty]").exists()).toBe(true);
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer le CV");
    expect(wrapper.find("[data-test=next-step]").exists()).toBe(false);
  });

  it("avec un CV : l'aperçu, la langue dessous, « J'ai relu le CV » et la suite vers Postuler", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    PUT.mockResolvedValue({ data: cv(21, [1, 3], { read_at: "2026-11-05T10:00:00Z" }) });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=doc-preview]").exists()).toBe(true);
    expect(wrapper.find("[data-test=cv]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv-language]").exists()).toBe(true);
    expect(wrapper.find(".prep-side").text()).not.toContain("Nouvelle version");
    expect(wrapper.find("[data-test=next-step]").text()).toBe("Continuer vers Postuler");

    await wrapper.find("[data-test=cv-read]").setValue(true);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/cvs/{draft_id}/read", { params: { path: { draft_id: 21 } }, body: { read: true } });
    expect((wrapper.find("[data-test=cv-read]").element as HTMLInputElement).checked).toBe(true);

    await wrapper.find("[data-test=doc-preview]").trigger("click");
    expect(wrapper.find("[data-test=cv]").exists()).toBe(true);
  });

  it("« Modifier le texte avec l'Assistant » ouvre la consigne et change le bouton du bas", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1])] });
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=cv-edit-text]").trigger("click");
    await wrapper.find("[data-test=cv-instruction]").setValue("Mets Kubernetes en avant");
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer la nouvelle version");
  });
});
