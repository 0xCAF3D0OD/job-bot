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

describe("OfferDetail, note provisoire (maquette OffreProvisoire)", () => {
  it("en-tête : pastille « Provisoire », anneau pâli, sous-titre sur n lignes de l'alerte", async () => {
    const wrapper = await mountDetail(offer({ snippet: "Ligne un\nLigne deux\n\nLigne trois" }));
    expect(wrapper.find("[data-test=provisional]").text()).toBe("Provisoire");
    const ring = wrapper.find("[data-test=section-for-you] [data-test=score]");
    expect(ring.classes()).toContain("provisional");
    expect(ring.attributes("aria-label")).toBe("À creuser : 61 sur 100, note provisoire");
    expect(wrapper.find("[data-test=match-sub]").text()).toBe(
      "Calculée sur 3 lignes de l’alerte : les exigences n’ont pas pu être vérifiées.",
    );
    expect(wrapper.find("[data-test=match-lines]").text()).not.toContain("Exigences");
  });

  it("bande au repos : titre, phrase, « Lire l'annonce » et « Coller le texte », aucun bouton plein", async () => {
    const wrapper = await mountDetail(offer());
    const band = wrapper.find("[data-test=partial-notice]");
    expect(band.find("[data-test=partial-title]").text()).toBe("Il manque l’annonce complète");
    expect(band.find("[data-test=partial-text]").text()).toBe("Pour une note sûre, jobA1 doit lire le texte entier de l’annonce.");
    expect(band.find("[data-test=partial-text]").attributes("aria-live")).toBe("polite");
    expect(band.find("[data-test=read-offer-text]").text()).toBe("Lire l’annonce");
    expect(band.find("[data-test=paste-offer-text]").text()).toBe("Coller le texte");
    expect(band.find(".offer-text-actions .primary").exists()).toBe(false);
    expect(band.find("[data-test=open-offer]").exists()).toBe(false);
  });

  it("note complète ou candidature spontanée : ni bande ni pastille", async () => {
    const full = await mountDetail(offer({ description: "Texte complet de l'annonce", summary_partial: false }));
    expect(full.find("[data-test=partial-notice]").exists()).toBe(false);
    expect(full.find("[data-test=provisional]").exists()).toBe(false);
    expect(full.find("[data-test=match-lines]").text()).toContain("Exigences");
    expect(full.find("[data-test=match-sub]").text()).toBe("Selon ton profil et tes préférences");
    const spontaneous = await mountDetail(offer({ spontaneous: true }));
    expect(spontaneous.find("[data-test=partial-notice]").exists()).toBe(false);
  });

  it("lecture : « Lecture… » désactivé, la phrase change, rien ne s'empile", async () => {
    let finish: (v: unknown) => void = () => {};
    POST.mockReturnValueOnce(new Promise((resolve) => (finish = resolve)));
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    const read = wrapper.find("[data-test=read-offer-text]");
    expect(read.text()).toBe("Lecture…");
    expect(read.attributes("aria-disabled")).toBe("true");
    expect(wrapper.find("[data-test=partial-text]").text()).toBe("Lecture de l’annonce…");
    await read.trigger("click");
    expect(POST).toHaveBeenCalledTimes(1);
    finish({ data: { saved: true, source: "page", score: 72, problem: null, paste: false } });
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/read", { params: { path: { offer_id: 7 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("refus du site : nouveau titre, « Lire » disparaît, « Coller le texte » seul, lien pour ouvrir l'annonce", async () => {
    POST.mockResolvedValueOnce({ data: { saved: false, problem: "Ce site interdit la lecture par un robot : colle le texte de l'annonce.", paste: true } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    await flushPromises();
    const band = wrapper.find("[data-test=partial-notice]");
    expect(band.find("[data-test=partial-title]").text()).toBe("Ce site bloque la lecture automatique");
    expect(band.find("[data-test=partial-text]").text()).toBe("Copie le texte de l’annonce et colle-le ici : la note sera refaite tout de suite.");
    expect(band.find("[data-test=read-offer-text]").exists()).toBe(false);
    expect(band.findAll(".offer-text-actions button")).toHaveLength(1);
    const open = band.find("[data-test=open-offer]");
    expect(open.text()).toContain("Ouvrir l’annonce pour la copier");
    expect(open.attributes("href")).toBe("https://www.linkedin.com/jobs/view/42");
    expect(open.attributes("target")).toBe("_blank");
    expect(wrapper.emitted("changed")).toBeUndefined();
  });

  it("trop de lectures (429) : la phrase de la bande dit quand réessayer", async () => {
    POST.mockResolvedValueOnce({ data: undefined, error: { detail: "Réessaie dans 4 minutes." }, response: { status: 429 } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=partial-text]").text()).toBe("Réessaie dans 4 minutes.");
    expect(wrapper.find("[data-test=read-offer-text]").exists()).toBe(true);
    expect(wrapper.emitted("changed")).toBeUndefined();
  });

  it("sans lien lisible, seulement « Coller le texte »", async () => {
    const wrapper = await mountDetail(offer({ links: [{ source: "manual", url: "https://annonce-collee.invalid/" }] }));
    expect(wrapper.find("[data-test=read-offer-text]").exists()).toBe(false);
    expect(wrapper.find("[data-test=paste-offer-text]").exists()).toBe(true);
    expect(wrapper.find("[data-test=open-offer]").exists()).toBe(false);
  });

  it("feuille « Coller le texte » : compteur, bouton désactivé sous 200 caractères, puis enregistré", async () => {
    PUT.mockResolvedValue({ data: { saved: true, source: "collé", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=paste-offer-text]").trigger("click");
    const sheet = wrapper.find("[data-test=paste-sheet]");
    expect(sheet.text()).toContain("Coller le texte de l’annonce");
    expect(sheet.text()).toContain("Ouvre l’annonce, sélectionne tout le texte, copie-le et colle-le ici.");
    // Maquette du 8 novembre : le Composer de 5 lignes, sans +, la flèche enregistre (désactivée sous 200).
    const area = wrapper.find("[data-test=paste-text] [data-test=composer-input]");
    expect(area.attributes("rows")).toBe("5");
    expect(wrapper.find("[data-test=paste-text] [data-test=composer-plus]").exists()).toBe(false);
    await area.setValue("Trop court.");
    const count = wrapper.find("[data-test=paste-text] [data-test=composer-counter]");
    expect(count.text()).toBe("11 caractères, 200 au moins · la flèche enregistre et refait la note");
    expect(count.attributes("aria-live")).toBe("polite");
    const save = wrapper.find("[data-test=paste-text] [data-test=composer-send]");
    expect(save.attributes("aria-label")).toBe("Enregistrer et refaire la note");
    expect(save.attributes("disabled")).toBeDefined();
    await save.trigger("click");
    expect(PUT).not.toHaveBeenCalled();

    const text = "Tu administres nos serveurs Linux. ".repeat(8);
    await area.setValue(text);
    expect(wrapper.find("[data-test=paste-text] [data-test=composer-counter]").text()).toBe(`${text.trim().length} caractères · la flèche enregistre et refait la note`);
    expect(wrapper.find("[data-test=paste-text] [data-test=composer-send]").attributes("disabled")).toBeUndefined();
    await wrapper.find("[data-test=paste-text] [data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/offers/{offer_id}/description", { params: { path: { offer_id: 7 } }, body: { text: text } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("après succès : la bande disparaît, anneau plein, vrais manques, confirmation (role=status)", async () => {
    POST.mockResolvedValueOnce({ data: { saved: true, source: "page", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer());
    await wrapper.find("[data-test=read-offer-text]").trigger("click");
    await flushPromises();
    await wrapper.setProps({
      offer: offer({ description: "Texte complet", summary_partial: false, score: 76, gaps: [{ text: "Azure demandé, tu connais surtout AWS", chunk_ids: [3] }] }) as never,
    });
    expect(wrapper.find("[data-test=partial-notice]").exists()).toBe(false);
    expect(wrapper.find("[data-test=provisional]").exists()).toBe(false);
    expect(wrapper.find("[data-test=section-for-you] [data-test=score]").classes()).not.toContain("provisional");
    expect(wrapper.find("[data-test=match-lines]").text()).toContain("Azure demandé, tu connais surtout AWS");
    const done = wrapper.find("[data-test=redone]");
    expect(done.text()).toBe("Note refaite sur l’annonce complète.");
    expect(done.attributes("role")).toBe("status");
    await wrapper.setProps({ offer: offer({ id: 8, description: "Autre", summary_partial: false }) as never });
    expect(wrapper.find("[data-test=redone]").exists()).toBe(false);
  });

  it("« Le poste » : « Extrait de l'alerte » si provisoire, « Résumé par jobA1 » sinon", async () => {
    const partial = await mountDetail(offer({ summary_role: "Résumé tiré de l'extrait" }));
    expect(partial.find("[data-test=snippet-by]").text()).toBe("Extrait de l’alerte");
    expect(partial.find("[data-test=summary-by]").exists()).toBe(false);
    expect(partial.find(".detail-snippet").text()).toBe("Extrait de l'alerte");
    const full = await mountDetail(offer({ description: "Texte complet", summary_partial: false, summary_role: "Missions : CI/CD" }));
    expect(full.find("[data-test=snippet-by]").exists()).toBe(false);
    expect(full.find("[data-test=summary-by]").text()).toBe("Résumé par jobA1");
  });
});
