import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OfferDetail from "./OfferDetail.vue";
import { resetRequested } from "./OfferTextNotice.vue";

const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: vi.fn(() => Promise.resolve({ data: undefined })),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => {
  vi.resetAllMocks();
  vi.unstubAllGlobals();
});
function onPhone(): void {
  vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener() {}, removeEventListener() {} }));
}

const GAPS = [
  { text: "Exigences : non précisées dans l’extrait", chunk_ids: [] },
  { text: "Conseil : lire l’annonce complète", chunk_ids: [] },
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
    snippet: "Extrait de l’alerte",
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

describe("OfferDetail, annonce complète lue automatiquement (prompt du 10 novembre, PR 13)", () => {
  beforeEach(() => {
    resetRequested();
    POST.mockResolvedValue({ data: { saved: false, problem: "lent", paste: false, retry: true } });
  });

  it("en lecture : pastille « Provisoire », anneau pâli, sous-titre « en attendant l’annonce complète »", async () => {
    const wrapper = await mountDetail(offer({ text_reading: "reading" }));
    expect(wrapper.find("[data-test=provisional]").text()).toBe("Provisoire");
    const ring = wrapper.find("[data-test=section-for-you] [data-test=score]");
    expect(ring.classes()).toContain("provisional");
    expect(ring.attributes("aria-label")).toBe("À creuser : 61 sur 100, note provisoire");
    expect(wrapper.find("[data-test=match-sub]").text()).toBe("Calculée sur l’extrait de l’alerte, en attendant l’annonce complète.");
    expect(wrapper.find("[data-test=match-lines]").text()).not.toContain("Exigences");
  });

  it("en lecture : « jobA1 lit l’annonce complète… » annoncé (role=status, aria-live), aucun bouton", async () => {
    vi.useFakeTimers();
    const wrapper = await mountDetail(offer({ text_reading: "reading" }));
    const line = wrapper.find("[data-test=text-reading]");
    expect(line.attributes("role")).toBe("status");
    expect(line.attributes("aria-live")).toBe("polite");
    expect(line.find("svg").attributes("aria-hidden")).toBe("true");
    // La phrase entre dans la région vivante après son ouverture, pour être annoncée.
    await vi.advanceTimersByTimeAsync(100);
    expect(line.text()).toBe("jobA1 lit l’annonce complète…");
    const card = wrapper.find("[data-test=section-for-you]");
    expect(card.find("[data-test=read-offer-text]").exists()).toBe(false);
    expect(card.find("[data-test=paste-offer-text]").exists()).toBe(false);
    expect(card.text()).not.toContain("Il manque l’annonce complète");
    vi.useRealTimers();
  });

  it("la fiche ouverte avant la tâche de fond demande la lecture, une fois ; réussie, la fiche se recharge", async () => {
    POST.mockResolvedValueOnce({ data: { saved: true, source: "page", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer({ text_reading: "reading" }));
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/read", { params: { path: { offer_id: 7 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
    await mountDetail(offer({ text_reading: "reading" }));
    expect(POST).toHaveBeenCalledTimes(1);
  });

  it("site lent : la lecture continue, la fiche se recharge toutes les 20 secondes", async () => {
    vi.useFakeTimers();
    const wrapper = await mountDetail(offer({ text_reading: "reading" }));
    await vi.advanceTimersByTimeAsync(0);
    expect(wrapper.find("[data-test=text-reading]").exists()).toBe(true);
    expect(wrapper.emitted("changed")).toBeUndefined();
    await vi.advanceTimersByTimeAsync(20_000);
    expect(wrapper.emitted("changed")).toHaveLength(1);
    vi.useRealTimers();
  });

  it("refus (état du serveur) : une ligne « Annonce illisible · LinkedIn bloque la lecture. », « Donner l’annonce », sans lien (PR 25)", async () => {
    const wrapper = await mountDetail(offer({ text_reading: "refused" }));
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=match-sub]").text()).toBe("Calculée sur l’extrait de l’alerte : les exigences n’ont pas pu être vérifiées.");
    const block = wrapper.find("[data-test=section-for-you] [data-test=text-refused]");
    expect(block.attributes("role")).toBe("group");
    expect(block.find("[data-test=refused-title]").text()).toBe("Annonce illisible");
    expect(block.find("[data-test=refused-text]").text()).toBe("LinkedIn bloque la lecture.");
    expect(block.find("[data-test=give-offer]").text()).toBe("Donner l’annonce");
    // Le seul lien vers l'annonce est « Voir l'annonce sur [source] » de la fiche : aucun dans l'encadré.
    expect(block.find("a").exists()).toBe(false);
    expect(block.text()).not.toContain("Ouvrir l’annonce");
    expect(wrapper.find("[data-test=text-reading]").exists()).toBe(false);
  });

  it("ordinateur : la carte se déplie sur place, « Lire » lit le lien de l’employeur et la fiche se recharge", async () => {
    const wrapper = await mountDetail(offer({ text_reading: "refused" }));
    const toggle = wrapper.find("[data-test=give-offer]");
    const zone = wrapper.find("[data-test=give-zone]");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    expect(toggle.attributes("aria-controls")).toBe(zone.attributes("id"));
    expect(zone.isVisible()).toBe(false);
    await toggle.trigger("click");
    expect(toggle.attributes("aria-expanded")).toBe("true");
    expect(wrapper.find("[data-test=give-sheet]").exists()).toBe(false);
    const field = zone.find("[data-test=give-url]");
    expect(field.attributes("type")).toBe("url");
    expect(zone.find(`label[for=${field.attributes("id")}]`).text()).toBe("Lien de l’annonce chez l’employeur");
    expect(zone.text()).toContain("Astuce : cherche le titre du poste sur le site carrière de l’entreprise.");
    expect(zone.find("[data-test=give-read]").text()).toBe("Lire");
    expect(zone.find("[data-test=paste-offer-text]").text()).toBe("Pas de lien ? Colle le texte");

    // Un lien incomplet n'est pas envoyé ; le message vient sous le champ, dans une région vivante.
    await field.setValue("emploi.exemple.ch");
    await zone.find("form").trigger("submit");
    expect(POST).not.toHaveBeenCalled();
    const problem = zone.find("[data-test=give-problem]");
    expect(problem.attributes("aria-live")).toBe("polite");
    expect(problem.text()).toBe("Colle un lien complet, qui commence par https://");
    expect(field.attributes("aria-describedby")).toContain(problem.attributes("id"));

    POST.mockResolvedValueOnce({ data: { saved: false, problem: "Cette page ne contient pas d'annonce lisible.", paste: true, retry: false } });
    await field.setValue("https://emploi.exemple.ch/postes/42");
    await zone.find("form").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/read-link", { params: { path: { offer_id: 7 } }, body: { url: "https://emploi.exemple.ch/postes/42" } });
    expect(problem.text()).toBe("Cette page ne contient pas d'annonce lisible.");
    expect(wrapper.emitted("changed")).toBeUndefined();

    POST.mockResolvedValueOnce({ data: { saved: true, source: "page", score: 78, problem: null, paste: false, retry: false } });
    await zone.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("trop de lectures : « Réessaie dans n minutes » sous le champ", async () => {
    const wrapper = await mountDetail(offer({ text_reading: "refused" }));
    await wrapper.find("[data-test=give-offer]").trigger("click");
    POST.mockResolvedValueOnce({ data: undefined, error: { detail: "Réessaie dans 4 minutes." } });
    await wrapper.find("[data-test=give-url]").setValue("https://emploi.exemple.ch/postes/42");
    await wrapper.find("[data-test=give-zone] form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=give-problem]").text()).toBe("Réessaie dans 4 minutes.");
  });

  it("téléphone : la fenêtre du bas « Donner l’annonce à jobA1 », puis « Coller le texte de l’annonce » ouvre le collage", async () => {
    onPhone();
    const wrapper = await mountDetail(offer({ text_reading: "refused", links: [{ source: "indeed", url: "https://ch.indeed.com/viewjob?jk=1" }] }));
    expect(wrapper.find("[data-test=refused-text]").text()).toBe("Indeed bloque la lecture.");
    const open = wrapper.find("[data-test=give-offer]");
    expect(open.attributes("aria-haspopup")).toBe("dialog");
    expect(open.attributes("aria-expanded")).toBeUndefined();
    expect(wrapper.find("[data-test=give-zone]").exists()).toBe(false);
    await open.trigger("click");
    const sheet = wrapper.find("[data-test=give-sheet]");
    expect(sheet.text()).toContain("Donner l’annonce à jobA1");
    expect(sheet.text()).toContain("Colle le lien de l’annonce chez l’employeur : jobA1 la lira directement.");
    const field = sheet.find("[data-test=give-url]");
    expect(field.attributes("type")).toBe("url");
    expect(sheet.find(`label[for=${field.attributes("id")}]`).text()).toBe("Lien chez l’employeur");
    expect(sheet.find("[data-test=give-read]").text()).toBe("Lire l’annonce");
    expect(sheet.find(".offer-give-or").attributes("aria-hidden")).toBe("true");
    const paste = sheet.find("[data-test=paste-offer-text]");
    expect(paste.text()).toBe("Coller le texte de l’annonce");
    await paste.trigger("click");
    // La première fenêtre se ferme, puis celle du collage s'ouvre (une seule fenêtre à la fois).
    await new Promise((done) => setTimeout(done, 350));
    await flushPromises();
    expect(wrapper.find("dialog[data-test=give-sheet]").attributes("open")).toBeUndefined();
    expect(wrapper.find("dialog[data-test=paste-sheet]").attributes("open")).toBeDefined();
    expect(wrapper.find("[data-test=paste-sheet]").text()).toContain("Tout le texte est accepté, même très long.");
  });

  it("refus dit par la lecture demandée d’ici : le bloc remplace la ligne de lecture", async () => {
    POST.mockResolvedValueOnce({ data: { saved: false, problem: "Ce site interdit la lecture par un robot.", paste: true, retry: false } });
    const wrapper = await mountDetail(offer({ text_reading: "reading" }));
    expect(wrapper.find("[data-test=text-refused]").exists()).toBe(true);
    expect(wrapper.find("[data-test=text-reading]").exists()).toBe(false);
    expect(wrapper.emitted("changed")).toBeUndefined();
  });

  it("refus sans site connu : « Ce site bloque la lecture. »", async () => {
    const wrapper = await mountDetail(offer({ text_reading: "refused", links: [{ source: "manual", url: "https://annonce-collee.invalid/" }] }));
    expect(wrapper.find("[data-test=refused-text]").text()).toBe("Ce site bloque la lecture.");
    expect(wrapper.find("[data-test=give-offer]").exists()).toBe(true);
    expect(wrapper.find("[data-test=open-offer]").exists()).toBe(false);
  });

  it("note complète ou candidature spontanée : ni lecture ni pastille", async () => {
    const full = await mountDetail(offer({ description: "Texte complet de l’annonce", summary_partial: false }));
    expect(full.find("[data-test=text-reading]").exists()).toBe(false);
    expect(full.find("[data-test=text-refused]").exists()).toBe(false);
    expect(full.find("[data-test=provisional]").exists()).toBe(false);
    expect(full.find("[data-test=redone]").exists()).toBe(false);
    expect(full.find("[data-test=match-lines]").text()).toContain("Exigences");
    expect(full.find("[data-test=match-sub]").text()).toBe("Selon ton profil et tes préférences");
    const spontaneous = await mountDetail(offer({ spontaneous: true }));
    expect(spontaneous.find("[data-test=text-reading]").exists()).toBe(false);
    expect(POST).not.toHaveBeenCalled();
  });

  it("feuille de collage : compteur, « Refaire la note » `aria-disabled` sous 200 caractères, puis enregistré", async () => {
    PUT.mockResolvedValue({ data: { saved: true, source: "collé", score: 72, problem: null, paste: false } });
    const wrapper = await mountDetail(offer({ text_reading: "refused" }));
    await wrapper.find("[data-test=give-offer]").trigger("click");
    await wrapper.find("[data-test=paste-offer-text]").trigger("click");
    const sheet = wrapper.find("[data-test=paste-sheet]");
    expect(sheet.text()).toContain("Coller le texte de l’annonce");
    expect(sheet.text()).toContain("Sur la page de l’annonce, sélectionne tout le texte, copie-le et colle-le ici. Tout le texte est accepté, même très long.");
    const area = wrapper.find("[data-test=paste-text] [data-test=composer-input]");
    expect(area.attributes("rows")).toBe("5");
    expect(area.attributes("maxlength")).toBeUndefined();
    await area.setValue("Trop court.");
    const count = wrapper.find("[data-test=paste-text] [data-test=composer-counter]");
    expect(count.text()).toBe("11 caractères · il en faut au moins 200");
    expect(count.attributes("aria-live")).toBe("polite");
    const save = wrapper.find("[data-test=paste-text] [data-test=composer-send]");
    expect(save.text()).toBe("Refaire la note");
    expect(save.attributes("aria-disabled")).toBe("true");
    await save.trigger("click");
    expect(PUT).not.toHaveBeenCalled();

    const text = "Tu administres nos serveurs Linux. ".repeat(8);
    await area.setValue(text);
    expect(count.text()).toBe(`${text.trim().length} caractères · assez pour noter`);
    expect(count.classes()).toContain("composer-counter-ok");
    expect(save.attributes("aria-disabled")).toBeUndefined();
    await save.trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/offers/{offer_id}/description", { params: { path: { offer_id: 7 } }, body: { text: text } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
  });

  it("done : la note recalculée, plus de « Provisoire », « Note refaite sur l’annonce complète. » (role=status)", async () => {
    const wrapper = await mountDetail(
      offer({ text_reading: "done", description: "Texte complet", summary_partial: false, score: 76, gaps: [{ text: "Azure demandé, tu connais surtout AWS", chunk_ids: [3] }] }),
    );
    expect(wrapper.find("[data-test=text-reading]").exists()).toBe(false);
    expect(wrapper.find("[data-test=provisional]").exists()).toBe(false);
    expect(wrapper.find("[data-test=section-for-you] [data-test=score]").classes()).not.toContain("provisional");
    expect(wrapper.find("[data-test=match-lines]").text()).toContain("Azure demandé, tu connais surtout AWS");
    const done = wrapper.find("[data-test=redone]");
    expect(done.text()).toBe("Note refaite sur l’annonce complète.");
    expect(done.attributes("role")).toBe("status");
    await wrapper.setProps({ offer: offer({ id: 8, description: "Autre", summary_partial: false }) as never });
    expect(wrapper.find("[data-test=redone]").exists()).toBe(false);
  });

  it("« Le poste » : « Extrait de l’alerte » si provisoire, « Résumé par jobA1 » sinon", async () => {
    const partial = await mountDetail(offer({ summary_role: "Résumé tiré de l’extrait" }));
    expect(partial.find("[data-test=snippet-by]").text()).toBe("Extrait de l’alerte");
    expect(partial.find("[data-test=summary-by]").exists()).toBe(false);
    expect(partial.find(".detail-snippet").text()).toBe("Extrait de l’alerte");
    const full = await mountDetail(offer({ description: "Texte complet", summary_partial: false, summary_role: "Missions : CI/CD" }));
    expect(full.find("[data-test=snippet-by]").exists()).toBe(false);
    expect(full.find("[data-test=summary-by]").text()).toBe("Résumé par jobA1");
  });
});
