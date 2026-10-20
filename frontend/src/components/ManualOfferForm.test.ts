import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ManualOfferForm from "./ManualOfferForm.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const draft = (extra: Record<string, unknown> = {}) => ({
  title: "Menuisière CFC",
  company: "Bois & Fils",
  location: "Sion",
  description: "Tu fabriques nos meubles.",
  url: "https://bois.ch/emplois/1",
  read_by: "page",
  trade: "Menuisier",
  matches_trade: true,
  existing_offer_id: null,
  ...extra,
});

async function mountForm(props: Record<string, unknown> = {}, trade: string | null = "Menuisier", added = 2) {
  GET.mockResolvedValue({ data: { trade, added_today: added, daily_limit: 20 } });
  const wrapper = mount(ManualOfferForm, { props });
  await flushPromises();
  return wrapper;
}

describe("Ajouter une offre (docs/111)", () => {
  it("des exemples tirés du métier, et le compte du jour", async () => {
    const wrapper = await mountForm();
    expect(wrapper.find("[data-test=manual-url]").attributes("placeholder")).toBe("https://entreprise.ch/emplois/menuisier");
    expect(wrapper.find("[data-test=manual-count]").text()).toBe("2 offres ajoutées sur 20 ces 24 heures.");
    await wrapper.find("[data-test=manual-mode-text]").trigger("click");
    expect(wrapper.find("[data-test=manual-text]").attributes("placeholder")).toContain("« Menuisier (80-100 %)");
  });

  it("sans métier connu, des exemples neutres", async () => {
    const wrapper = await mountForm({}, null);
    expect(wrapper.find("[data-test=manual-url]").attributes("placeholder")).toBe("https://entreprise.ch/emplois/poste");
  });

  it("lit le lien, montre la fiche, puis ajoute l'offre corrigée", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft(), problem: null, paste: false } });
    POST.mockResolvedValueOnce({ data: { id: 9, existing: false, status: "to_review", reasons: [] } });
    await wrapper.find("[data-test=manual-url]").setValue("https://bois.ch/emplois/1");
    await wrapper.find("[data-test=manual-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]).toEqual(["/api/offers/manual/read", { body: { url: "https://bois.ch/emplois/1" } }]);
    expect(wrapper.find("[data-test=manual-draft]").text()).toContain("Lue sur la page de l'annonce.");
    expect(wrapper.find("[data-test=manual-off-trade]").exists()).toBe(false);

    await wrapper.find("[data-test=manual-location]").setValue("Sion 80-100 %");
    await wrapper.find("[data-test=manual-draft]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[1]![1].body).toEqual({
      title: "Menuisière CFC",
      company: "Bois & Fils",
      location: "Sion 80-100 %",
      description: "Tu fabriques nos meubles.",
      url: "https://bois.ch/emplois/1",
      read_by: "page",
    });
    expect(wrapper.emitted("added")).toEqual([[{ id: 9, existing: false, status: "to_review", reasons: [] }]]);
  });

  it("une annonce hors du métier : la fiche le dit, sans bloquer", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ title: "Comptable", matches_trade: false, read_by: "ia" }) } });
    await wrapper.find("[data-test=manual-url]").setValue("https://x.ch/a");
    await wrapper.find("[data-test=manual-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-off-trade]").text()).toContain("ne parle pas de « Menuisier », ton métier");
    expect(wrapper.find("[data-test=manual-draft]").text()).toContain("Lue par l'IA.");
    expect(wrapper.find<HTMLButtonElement>("[data-test=manual-add]").element.disabled).toBe(false);
  });

  it("une page protégée : passe au texte collé, ou la fiche à la main", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({
      data: { draft: null, problem: "Ce site ne se laisse pas lire par un robot : colle le texte de l'annonce.", paste: true },
    });
    await wrapper.find("[data-test=manual-url]").setValue("https://ch.indeed.com/viewjob?jk=1");
    await wrapper.find("[data-test=manual-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-problem]").text()).toContain("colle le texte");
    expect(wrapper.find("[data-test=manual-text]").exists()).toBe(true);

    await wrapper.find("[data-test=manual-by-hand]").trigger("click");
    expect((wrapper.find("[data-test=manual-draft-url]").element as HTMLInputElement).value).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(wrapper.find("[data-test=manual-title]").attributes("placeholder")).toBe("Menuisier");
  });

  it("déjà dans les offres : propose de l'ouvrir", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4 }) } });
    await wrapper.find("[data-test=manual-url]").setValue("https://bois.ch/emplois/1");
    await wrapper.find("[data-test=manual-form]").trigger("submit");
    await flushPromises();
    await wrapper.find("[data-test=manual-existing] button").trigger("click");
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "", reasons: [] }]]);
  });

  it("au maximum du jour, la lecture est fermée", async () => {
    const wrapper = await mountForm({}, "Menuisier", 20);
    expect(wrapper.find<HTMLButtonElement>("[data-test=manual-read]").element.disabled).toBe(true);
    expect(wrapper.find("[data-test=manual-count]").text()).toContain("c'est le maximum");
  });

  it("partagé depuis Android : le texte seul ouvre l'onglet Texte", async () => {
    const wrapper = await mountForm({ initialText: "Menuisier à Sion, 100 %" });
    expect((wrapper.find("[data-test=manual-text]").element as HTMLTextAreaElement).value).toBe("Menuisier à Sion, 100 %");
  });
});
