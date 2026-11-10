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
    // La carte « CV adapté » (§14) : FR / DE / EN en tête, plus de puces de mots-clés sur ordinateur.
    const card = wrapper.find("[data-test=cv-card]");
    expect(card.find("h2").text()).toBe("CV adapté");
    expect(card.find("[role=radiogroup], [aria-label='Langue du CV']").exists()).toBe(true);
    expect(card.find("[data-test=cv-highlights]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv-docx]").attributes("href")).toBe("/api/cvs/21/docx");
  });

  it("sans langue choisie, le CV prend celle de la lettre (§14)", async () => {
    GET.mockResolvedValue({ data: [] });
    POST.mockResolvedValue({ data: cv(21, [1, 3]) });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    const wrapper = mount(CvPanel, { props: { offer: offer as never, letterLanguage: "de" }, global: { plugins: [router] } });
    await flushPromises();
    await wrapper.find("[data-test=write-cv]").trigger("click");
    await flushPromises();
    expect((POST.mock.calls[0]![1] as { body: { language: string } }).body.language).toBe("de");
  });

  it("« Ce CV » : les changements à vérifier, et « Annuler ce changement » remet l’ordre d’origine", async () => {
    // L'adaptation a mis « Stage web » avant « Stage DevOps ».
    GET.mockResolvedValue({ data: [cv(21, [2, 1, 3], { origin_ids: [1, 2, 3] })] });
    PUT.mockResolvedValue({ data: cv(21, [1, 2, 3], { origin_ids: [1, 2, 3] }) });
    const wrapper = await mountPanel();
    const file = wrapper.find("[data-test=cv-file]");
    expect(file.find("h2").text()).toBe("Ce CV");
    expect(file.find("[data-test=cv-changes-open]").text()).toContain("2 changements, à vérifier");
    expect(file.find("[data-test=cv-versions-open]").text()).toContain("Versions · 1");
    expect(file.find("[data-test=cv-origin]").text()).toContain("Ne change pas, sert de base");
    const changes = wrapper.find("[data-test=cv-changes]");
    expect(changes.text()).toContain("pour l’annonce d’Acme SA");
    const items = changes.findAll("[data-test=cv-change]");
    expect(items.map((li) => li.find("b").text())).toEqual(["Profil", "Expériences"]);
    expect(items[1]!.text()).toContain("Avant : « Stage web » venait en 2e position.");
    // Le résumé n'a pas d'« avant » gardé : il ne s'annule pas.
    expect(items[0]!.find("[data-test=cv-change-undo]").exists()).toBe(false);
    await items[1]!.find("[data-test=cv-change-undo]").trigger("click");
    await flushPromises();
    expect((PUT.mock.calls[0]![1] as { body: { chunk_ids: number[] } }).body.chunk_ids).toEqual([1, 2, 3]);
    expect(wrapper.findAll("[data-test=cv-change]")).toHaveLength(1);
  });

  it("un bloc retiré revient à sa place d’origine", async () => {
    GET.mockResolvedValue({ data: [cv(21, [2, 3], { origin_ids: [1, 2, 3] })] });
    PUT.mockResolvedValue({ data: cv(21, [1, 2, 3], { origin_ids: [1, 2, 3] }) });
    const wrapper = await mountPanel();
    const removed = wrapper.findAll("[data-test=cv-change]").find((li) => li.find("b").text() === "Stage DevOps")!;
    expect(removed.text()).toContain("Maintenant : retiré pour cette offre.");
    await removed.find("[data-test=cv-change-undo]").trigger("click");
    await flushPromises();
    expect((PUT.mock.calls[0]![1] as { body: { chunk_ids: number[] } }).body.chunk_ids).toEqual([1, 2, 3]);
  });

  it("« J’ai relu, continuer » note la relecture puis passe à Postuler", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    PUT.mockResolvedValue({ data: cv(21, [1, 3], { read_at: "2026-11-09T20:00:00Z" }) });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    const wrapper = mount(CvPanel, { props: { offer: offer as never }, global: { plugins: [router] } });
    await flushPromises();
    await wrapper.find("[data-test=cv-read-next]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/cvs/{draft_id}/read", { params: { path: { draft_id: 21 } }, body: { read: true } });
    expect(router.currentRoute.value.query.doc).toBe("postuler");
  });

  it("une autre langue remplace le bouton par « Préparer à nouveau » ; une puce de retouche prépare une version", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    POST.mockResolvedValue({ data: cv(22, [1, 3], { version: 2, instruction: "Plus court" }) });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-test=cv-desk-bottom]").text()).toContain("Mettre Terraform en avant");
    await wrapper.find("[data-test=cv-language-en]").trigger("click");
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer à nouveau en anglais");
    expect(wrapper.find("[data-test=cv-read-next]").exists()).toBe(false);
    await wrapper.find("[data-test=cv-language-fr]").trigger("click");
    const chip = wrapper.findAll("[data-test=cv-desk-bottom] button").find((b) => b.text() === "Plus court")!;
    await chip.trigger("click");
    await flushPromises();
    expect((POST.mock.calls[0]![1] as { body: { instruction: string; base_draft_id: number } }).body).toMatchObject({ instruction: "Plus court", base_draft_id: 21 });
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
