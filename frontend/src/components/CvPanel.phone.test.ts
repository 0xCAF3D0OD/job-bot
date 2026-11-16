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

  it("avec un CV (§37 du 16.11) : la rangée d’outils, le CV entier, la retouche et « J’ai relu, continuer »", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    PUT.mockResolvedValue({ data: cv(21, [1, 3], { read_at: "2026-11-05T10:00:00Z" }) });
    const wrapper = await mountPanel();
    // Plus d'aperçu à toucher : le CV entier tout de suite.
    expect(wrapper.find("[data-test=doc-preview]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv]").exists()).toBe(true);
    const tools = wrapper.get("[data-test=cv-phone-tools]");
    expect(tools.get("[data-test=cv-changes-show]").text()).toBe("Changements · 1");
    expect(tools.get("[data-test=cv-search-open]").attributes("aria-label")).toBe("Chercher dans le CV");
    // « Modèle » ouvre la feuille « Mise en page et langue » ; plus de FR / DE / EN à l'écran.
    const model = tools.get("[data-test=layout-change]");
    expect(model.text()).toBe("Modèle");
    expect(model.attributes("aria-label")).toBe("Changer le modèle ou la langue, Moderne · Français");
    expect(wrapper.find(".doc-language").exists()).toBe(false);
    await model.trigger("click");
    const sheet = wrapper.get("[data-test=layout-sheet]");
    expect(sheet.get("[data-test=cv-language-fr]").attributes("aria-checked")).toBe("true");
    const pills = sheet.findAll("[role=radiogroup][aria-label='Langue du titre et du résumé'] [role=radio]");
    expect(pills.map((b) => b.text())).toEqual(["Français", "Deutsch", "English"]);
    expect(wrapper.get("[data-test=composer] textarea").attributes("placeholder")).toBe("Demander une modification du CV");
    // « J’ai relu, continuer » note la relecture, puis passe à Postuler.
    const next = wrapper.get("[data-test=next-step]");
    expect(next.text()).toContain("J’ai relu, continuer");
    await next.trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/cvs/{draft_id}/read", { params: { path: { draft_id: 21 } }, body: { read: true } });
  });

  it("une autre langue propose de préparer le CV à nouveau ; « Blocs du CV » replié", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1, 3])] });
    const wrapper = await mountPanel();
    await wrapper.find("[data-test=cv-language-de]").trigger("click");
    expect(wrapper.find("[data-test=write-cv]").text()).toContain("Préparer à nouveau en allemand");
    const blocks = wrapper.find("[data-test=cv-blocks-card]");
    expect(blocks.find("h2").exists()).toBe(false);
    const row = blocks.find(".disclosure-row");
    expect(row.text()).toContain("Blocs du CV");
    expect(row.text()).toContain("2 sur 3");
    expect(row.attributes("aria-expanded")).toBe("false");
  });

  it("« Changements » surligne ; toucher un passage ouvre « Changement N sur M » avec le pourquoi, précédent et suivant", async () => {
    const shown = cv(21, [3, 1], {
      origin_ids: [1, 2, 3],
      reasons: [
        { target: "summary", origin: "ai", text: "L’annonce demande AWS dès sa première ligne.", quotes: ["aws"] },
        { target: 2, origin: "user", text: null, quotes: [] },
      ],
    });
    GET.mockResolvedValue({ data: [shown] });
    PUT.mockResolvedValue({ data: cv(21, [1, 2, 3]) });
    const wrapper = await mountPanel();
    expect(wrapper.find("[data-change]").exists()).toBe(false);
    const pill = wrapper.get("[data-test=cv-changes-show]");
    expect(pill.text()).toBe("Changements · 2");
    await pill.trigger("click");
    expect(pill.attributes("aria-pressed")).toBe("true");
    const passage = wrapper.get("[data-change=summary]");
    expect(passage.classes()).toContain("cv-changed");
    expect(passage.attributes("role")).toBe("button");
    await passage.trigger("click");
    const sheet = () => wrapper.get("[data-test=cv-change-sheet]");
    expect(sheet().get("[data-test=sheet-eyebrow]").text()).toBe("Changement 1 sur 2");
    expect(sheet().get(".sheet-title").text()).toBe("Profil");
    expect(sheet().get("[data-test=cv-why]").text()).toBe("Pourquoi : L’annonce demande AWS dès sa première ligne.");
    expect(sheet().findAll(".cv-why-quote").map((m) => m.text())).toEqual(["AWS"]);
    // Le résumé ne s'annule pas (pas d'« avant » gardé).
    expect(sheet().find("[data-test=cv-change-undo]").exists()).toBe(false);
    await sheet().get("[data-test=cv-change-next]").trigger("click");
    expect(sheet().get("[data-test=sheet-eyebrow]").text()).toBe("Changement 2 sur 2");
    expect(sheet().get(".sheet-title").text()).toBe("Stage web");
    expect(sheet().get("[data-test=cv-why]").text()).toBe("Pourquoi : Demandé par toi.");
    await sheet().get("[data-test=cv-change-undo]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/cvs/{draft_id}", expect.objectContaining({ body: expect.objectContaining({ chunk_ids: [3, 1, 2] }) }));
  });

  it("la loupe remplace la rangée d’outils par la recherche ; la fermer la rend", async () => {
    GET.mockResolvedValue({ data: [cv(21, [1])] });
    const wrapper = await mountPanel();
    await wrapper.get("[data-test=cv-search-open]").trigger("click");
    expect(wrapper.find("[data-test=cv-phone-tools]").exists()).toBe(false);
    expect(wrapper.find("[data-test=doc-search]").exists()).toBe(true);
    await wrapper.get("[data-test=doc-search-close]").trigger("click");
    expect(wrapper.find("[data-test=cv-phone-tools]").exists()).toBe(true);
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
