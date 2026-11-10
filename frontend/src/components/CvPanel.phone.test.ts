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
  it("sans CV : le modèle, l’aperçu vide et « Préparer le CV » en bas", async () => {
    GET.mockResolvedValue({ data: [] });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=template-moderne]").exists()).toBe(true);
    expect(wrapper.find("[data-test=no-cv] [data-test=doc-preview-empty]").exists()).toBe(true);
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer le CV");
    expect(wrapper.find("[data-test=next-step]").exists()).toBe(false);
  });

  it("avec un CV : « Moderne · Français » et « Changer » en tête, l’aperçu, « J’ai relu le CV » et la suite vers Postuler", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    PUT.mockResolvedValue({ data: cv(21, [1, 3], { read_at: "2026-11-05T10:00:00Z" }) });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=doc-preview]").exists()).toBe(true);
    expect(wrapper.find("[data-test=doc-preview]").classes()).toContain("doc-preview-tall");
    expect(wrapper.find("[data-test=cv]").exists()).toBe(false);
    // La langue du CV affiché, dans la feuille « Mise en page et langue » (§9) ; plus de FR / DE / EN à l'écran.
    expect(wrapper.find("[data-test=cv-language]").exists()).toBe(false);
    const card = wrapper.find("[data-test=cv-card]");
    expect(card.find(".doc-language").exists()).toBe(false);
    expect(card.get("[data-test=layout-summary]").text()).toBe("Moderne · Français");
    await card.get("[data-test=layout-change]").trigger("click");
    const sheet = wrapper.get("[data-test=layout-sheet]");
    expect(sheet.get("[data-test=cv-language-fr]").attributes("aria-checked")).toBe("true");
    const pills = sheet.findAll("[role=radiogroup][aria-label='Langue du titre et du résumé'] [role=radio]");
    expect(pills.map((b) => b.text())).toEqual(["Français", "Deutsch", "English"]);
    expect(wrapper.find(".prep-side").text()).not.toContain("Nouvelle version");
    expect(wrapper.find("[data-test=next-step]").text()).toBe("Continuer vers Postuler");

    await wrapper.find("[data-test=cv-read]").setValue(true);
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/cvs/{draft_id}/read", { params: { path: { draft_id: 21 } }, body: { read: true } });
    expect((wrapper.find("[data-test=cv-read]").element as HTMLInputElement).checked).toBe(true);

    await wrapper.find("[data-test=doc-preview]").trigger("click");
    expect(wrapper.find("[data-test=cv]").exists()).toBe(true);
  });

  it("une autre langue propose de préparer le CV à nouveau ; les mots mis en avant sous l’aperçu ; « Blocs du CV » replié", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=cv-language-de]").trigger("click");
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer à nouveau en allemand");
    const card = wrapper.find("[data-test=cv-card]").element;
    const preview = wrapper.find("[data-test=doc-preview]").element;
    const tags = wrapper.find("[data-test=cv-highlights]");
    expect(tags.text()).toBe("Terraform");
    expect(preview.compareDocumentPosition(tags.element) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(card.contains(preview)).toBe(true);
    const blocks = wrapper.find("[data-test=cv-blocks-card]");
    expect(blocks.find("h2").exists()).toBe(false);
    const row = blocks.find(".disclosure-row");
    expect(row.text()).toContain("Blocs du CV");
    expect(row.text()).toContain("2 sur 3");
    expect(row.attributes("aria-expanded")).toBe("false");
  });

  it("« Modifier le texte avec l’Assistant » ouvre la consigne et change le bouton du bas", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1])] });
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=cv-edit-text]").trigger("click");
    await wrapper.find("[data-test=cv-instruction]").setValue("Mets Kubernetes en avant");
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer la nouvelle version");
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

});
