import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import ManualOfferForm from "./ManualOfferForm.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const phone = ref(false);
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone }) }));
afterEach(() => {
  vi.resetAllMocks();
  phone.value = false;
});

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
  it("la zone de saisie commune (maquette du 8 novembre), et le compte du jour", async () => {
    const wrapper = await mountForm();
    expect(wrapper.find("[data-test=composer-input]").attributes("placeholder")).toBe("Lien ou texte de l’annonce");
    expect(wrapper.find("[data-test=composer-input]").attributes("rows")).toBe("3");
    expect(wrapper.find("[data-test=composer-send]").attributes("aria-label")).toBe("Ajouter l’offre");
    // Pas d'import de fichier : rien ne part à l'IA sans règle (I-1, E-5).
    expect(wrapper.find("[data-test=composer-plus]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manual-count]").text()).toBe("2 offres ajoutées sur 20 ces 24 heures.");
  });

  it("4 lignes sur téléphone (maquette AjouterOffreTel)", async () => {
    phone.value = true;
    const wrapper = await mountForm();
    expect(wrapper.find("[data-test=composer-input]").attributes("rows")).toBe("4");
  });

  it("un texte collé est lu comme un texte", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ read_by: "ia" }) } });
    await wrapper.find("[data-test=composer-input]").setValue("Menuisier à Sion, 100 %");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]).toEqual(["/api/offers/manual/read", { body: { text: "Menuisier à Sion, 100 %" } }]);
  });

  it("lit le lien, montre la fiche, puis ajoute l’offre corrigée", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft(), problem: null, paste: false } });
    POST.mockResolvedValueOnce({ data: { id: 9, existing: false, status: "to_review", reasons: [] } });
    await wrapper.find("[data-test=composer-input]").setValue("https://bois.ch/emplois/1");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]).toEqual(["/api/offers/manual/read", { body: { url: "https://bois.ch/emplois/1" } }]);
    expect(wrapper.find("[data-test=manual-draft]").text()).toContain("Lue sur la page de l’annonce.");
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
      fill: false,
    });
    expect(wrapper.emitted("added")).toEqual([[{ id: 9, existing: false, status: "to_review", reasons: [] }]]);
  });

  it("une annonce hors du métier : la fiche le dit, sans bloquer", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ title: "Comptable", matches_trade: false, read_by: "ia" }) } });
    await wrapper.find("[data-test=composer-input]").setValue("https://x.ch/a");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-off-trade]").text()).toContain("ne parle pas de « Menuisier »");
    expect(wrapper.find("[data-test=manual-draft]").text()).toContain("Lue par l’IA.");
    expect(wrapper.find<HTMLButtonElement>("[data-test=manual-add]").element.disabled).toBe(false);
  });

  it("une page protégée : passe au texte collé, ou la fiche à la main", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({
      data: { draft: null, problem: "Ce site ne se laisse pas lire par un robot : colle le texte de l’annonce.", paste: true },
    });
    await wrapper.find("[data-test=composer-input]").setValue("https://ch.indeed.com/viewjob?jk=1");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-problem]").text()).toContain("colle le texte");
    expect(wrapper.find("[data-test=manual-text-hint]").exists()).toBe(true);

    await wrapper.find("[data-test=manual-by-hand]").trigger("click");
    expect((wrapper.find("[data-test=manual-draft-url]").element as HTMLInputElement).value).toBe("https://ch.indeed.com/viewjob?jk=1");
    // L’exemple est sous le champ, plus dans le champ (libellé flottant, PR 27).
    expect(wrapper.find("[data-test=manual-title]").element.closest(".form-field")?.querySelector(".form-field-hint")?.textContent).toContain("Ex.\u202f: Menuisier");
  });

  it("déjà dans les offres : propose de l’ouvrir", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4 }) } });
    await wrapper.find("[data-test=composer-input]").setValue("https://bois.ch/emplois/1");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    await wrapper.find("[data-test=manual-existing] button").trigger("click");
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "", reasons: [] }]]);
  });

  // Une offre de LinkedIn sans texte : la page de l'annonce la complète, sans rien remplacer.
  it("déjà là sans texte ni lien : « Compléter l’offre » les ajoute", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4, fillable: ["description", "url"] }) } });
    await wrapper.find("[data-test=composer-input]").setValue("https://bois.ch/emplois/1");
    await wrapper.find("[data-test=composer-send]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-existing]").text()).toContain(
      "sans le texte de l’annonce et le lien : « Compléter l’offre » les ajoute, sans rien remplacer.",
    );
    expect(wrapper.find("[data-test=manual-add]").text()).toMatch(/^Compléter l’offre/);
    POST.mockResolvedValueOnce({ data: { id: 4, existing: true, status: "to_review", reasons: [], filled: ["description", "url"] } });
    await wrapper.find("[data-test=manual-draft]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[1]![1].body).toMatchObject({ fill: true, description: "Tu fabriques nos meubles." });
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "to_review", reasons: [], filled: ["description", "url"] }]]);
  });

  it("au maximum du jour, la lecture est fermée", async () => {
    const wrapper = await mountForm({}, "Menuisier", 20);
    expect(wrapper.find<HTMLButtonElement>("[data-test=composer-send]").element.disabled).toBe(true);
    expect(wrapper.find("[data-test=manual-count]").text()).toContain("c’est le maximum");
  });

  it("partagé depuis Android : le texte est déjà dans la zone de saisie", async () => {
    const wrapper = await mountForm({ initialText: "Menuisier à Sion, 100 %" });
    expect((wrapper.find("[data-test=composer-input]").element as HTMLTextAreaElement).value).toBe("Menuisier à Sion, 100 %");
  });
});
