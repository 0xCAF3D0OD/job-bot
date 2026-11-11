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
  contract: null,
  read_by: "page",
  trade: "Menuisier",
  matches_trade: true,
  existing_offer_id: null,
  ...extra,
});

async function mountForm(props: Record<string, unknown> = {}, trade: string | null = "Menuisier", added = 2) {
  GET.mockResolvedValue({ data: { trade, added_today: added, daily_limit: 20 } });
  const wrapper = mount(ManualOfferForm, { props, attachTo: document.body });
  await flushPromises();
  return wrapper;
}
// « Ajouter l'offre » est dans le pied du panneau : il envoie le formulaire.
async function send(wrapper: Awaited<ReturnType<typeof mountForm>>, value?: string) {
  if (value !== undefined) await wrapper.find("[data-test=manual-entry]").setValue(value);
  await wrapper.find("[data-test=manual-form]").trigger("submit");
  await flushPromises();
}

describe("Ajouter une offre (docs/111 ; panneau du 11 novembre, PR 38)", () => {
  it("un champ à libellé flottant, sans flèche d’envoi ; ce qu’il reste à ajouter aujourd’hui ; le PDF", async () => {
    const wrapper = await mountForm();
    const entry = wrapper.find("textarea[data-test=manual-entry]");
    expect(entry.attributes("rows")).toBe("3");
    expect(wrapper.find(`label[for=${entry.attributes("id")}]`).text()).toBe("Lien ou texte de l’annonce");
    expect(wrapper.find("[data-test=composer-send]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manual-restart]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manual-count]").text()).toBe("Tu peux encore en ajouter 18 aujourd’hui.");
    expect(wrapper.find("[data-test=manual-pdf]").text()).toBe("Importer le PDF de l’annonce");
    wrapper.unmount();
    const last = await mountForm({}, "Menuisier", 19);
    expect(last.find("[data-test=manual-count]").text()).toBe("Tu peux encore en ajouter une aujourd’hui.");
  });

  it("téléphone (maquette AjouterOffreTel) : la zone de saisie de 4 lignes, + pour le PDF", async () => {
    phone.value = true;
    const wrapper = await mountForm();
    expect(wrapper.find("[data-test=composer-input]").attributes("rows")).toBe("4");
    expect(wrapper.find("[data-test=composer-send]").attributes("aria-label")).toBe("Ajouter l’offre");
    expect(wrapper.find("[data-test=composer-plus]").exists()).toBe(true);
    expect(wrapper.find("[data-test=manual-pdf]").exists()).toBe(false);
  });

  it("un texte collé est lu comme un texte ; champ vide : l’erreur sous le champ", async () => {
    const wrapper = await mountForm();
    await send(wrapper);
    expect(wrapper.find("[data-test=field-error]").text()).toContain("Colle le lien ou le texte de l’annonce.");
    expect(POST).not.toHaveBeenCalled();
    POST.mockResolvedValueOnce({ data: { draft: draft({ read_by: "ia" }) } });
    await send(wrapper, "Menuisier à Sion, 100 %");
    expect(POST.mock.calls[0]).toEqual(["/api/offers/manual/read", { body: { text: "Menuisier à Sion, 100 %" } }]);
    // Un texte collé : pas de cookies ni de formulaire à retirer.
    expect(wrapper.find("[data-test=manual-text-line]").text()).toBe("25 caractères");
  });

  it("lit le lien, montre « Ce que jobA1 a lu » sous le champ, puis ajoute l’offre corrigée", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ contract: "Durée indéterminée" }), problem: null, paste: false } });
    POST.mockResolvedValueOnce({ data: { id: 9, existing: false, status: "to_review", reasons: [] } });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(POST.mock.calls[0]).toEqual(["/api/offers/manual/read", { body: { url: "https://bois.ch/emplois/1" } }]);
    // Le champ reste, le PDF disparaît.
    expect(wrapper.find("[data-test=manual-entry]").exists()).toBe(true);
    expect(wrapper.find("[data-test=manual-pdf]").exists()).toBe(false);
    const read = wrapper.find("[data-test=manual-draft]");
    expect(read.find("h3").text()).toBe("Ce que jobA1 a lu");
    expect(read.findAll(".form-field-text").map((l) => l.text())).toEqual(["Poste", "Entreprise", "Lieu", "Contrat"]);
    expect((read.find("[data-test=manual-contract]").element as HTMLInputElement).value).toBe("Durée indéterminée");
    expect(wrapper.find("[data-test=manual-off-trade]").exists()).toBe(false);
    // « Texte lu » : replié, il dit ce qui a été retiré ; déplié, le texte se corrige.
    const toggle = read.find("[data-test=manual-text-toggle]");
    expect(toggle.attributes("aria-expanded")).toBe("false");
    expect(toggle.text()).toBe("Texte lu25 caractères · cookies et formulaire retirés");
    await toggle.trigger("click");
    expect(toggle.attributes("aria-expanded")).toBe("true");
    expect(read.find("[data-test=manual-description]").isVisible()).toBe(true);

    await wrapper.find("[data-test=manual-location]").setValue("Sion 80-100 %");
    await send(wrapper);
    expect(POST.mock.calls[1]![1].body).toEqual({
      title: "Menuisière CFC",
      company: "Bois & Fils",
      location: "Sion 80-100 %",
      contract: "Durée indéterminée",
      description: "Tu fabriques nos meubles.",
      url: "https://bois.ch/emplois/1",
      read_by: "page",
      fill: false,
    });
    expect(wrapper.emitted("added")).toEqual([[{ id: 9, existing: false, status: "to_review", reasons: [] }]]);
  });

  it("contrat inconnu : « Non précisé » à l’écran, rien d’enregistré ; changer le champ fait relire", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft() } });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect((wrapper.find("[data-test=manual-contract]").element as HTMLInputElement).value).toBe("Non précisé");
    await wrapper.find("[data-test=manual-entry]").setValue("https://bois.ch/emplois/2");
    expect(wrapper.find("[data-test=manual-draft]").exists()).toBe(false);
    POST.mockResolvedValueOnce({ data: { draft: draft({ url: "https://bois.ch/emplois/2" }) } });
    await send(wrapper);
    expect(POST.mock.calls[1]).toEqual(["/api/offers/manual/read", { body: { url: "https://bois.ch/emplois/2" } }]);
    POST.mockResolvedValueOnce({ data: { id: 10, existing: false, status: "new", reasons: [] } });
    await send(wrapper);
    expect(POST.mock.calls[2]![1].body).toMatchObject({ contract: null, url: "https://bois.ch/emplois/2" });
  });

  it("une annonce hors du métier : la fiche le dit, sans bloquer", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ title: "Comptable", matches_trade: false, read_by: "ia" }) } });
    await send(wrapper, "https://x.ch/a");
    expect(wrapper.find("[data-test=manual-off-trade]").text()).toContain("ne parle pas de « Menuisier »");
    // Une page lue par l'IA : son texte principal, cookies et formulaire retirés.
    expect(wrapper.find("[data-test=manual-text-line]").text()).toContain("cookies et formulaire retirés");
  });

  it("une page protégée : passe au texte collé, ou la fiche à la main", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({
      data: { draft: null, problem: "Ce site ne se laisse pas lire par un robot : colle le texte de l’annonce.", paste: true },
    });
    await send(wrapper, "https://ch.indeed.com/viewjob?jk=1");
    expect(wrapper.find("[data-test=manual-problem]").text()).toContain("colle le texte");
    expect(wrapper.find("[data-test=manual-text-hint]").exists()).toBe(true);

    await wrapper.find("[data-test=manual-by-hand]").trigger("click");
    expect(wrapper.find("[data-test=manual-draft] h3").text()).toBe("À remplir toi-même");
    await send(wrapper);
    expect(wrapper.find("[data-test=manual-title]").attributes("aria-invalid")).toBe("true");
    POST.mockResolvedValueOnce({ data: { id: 11, existing: false, status: "new", reasons: [] } });
    await wrapper.find("[data-test=manual-title]").setValue("Menuisier");
    await send(wrapper);
    expect(POST.mock.calls[1]![1].body).toMatchObject({ title: "Menuisier", url: "https://ch.indeed.com/viewjob?jk=1", read_by: "main" });
  });

  it("déjà dans la liste : pas de fiche, l’offre existante s’ouvre tout de suite (PR 38)", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4 }) } });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(wrapper.find("[data-test=manual-draft]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("déjà");
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "", reasons: [] }]]);
  });

  // Une offre de LinkedIn sans texte : la page de l'annonce la complète, sans rien remplacer.
  it("déjà là sans texte ni lien : « Compléter l’offre » les ajoute", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4, fillable: ["description", "url"] }) } });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(wrapper.find("[data-test=manual-existing]").text()).toContain(
      "sans le texte de l’annonce et le lien\u202f: « Compléter l’offre » les ajoute, sans rien remplacer.",
    );
    expect((wrapper.vm as unknown as { label: string }).label).toBe("Compléter l’offre");
    POST.mockResolvedValueOnce({ data: { id: 4, existing: true, status: "to_review", reasons: [], filled: ["description", "url"] } });
    await send(wrapper);
    expect(POST.mock.calls[1]![1].body).toMatchObject({ fill: true, description: "Tu fabriques nos meubles." });
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "to_review", reasons: [], filled: ["description", "url"] }]]);
  });

  it("au maximum du jour, la lecture est fermée", async () => {
    const wrapper = await mountForm({}, "Menuisier", 20);
    expect(wrapper.find("[data-test=manual-count]").text()).toContain("c’est le maximum");
    expect(wrapper.find<HTMLButtonElement>("[data-test=manual-pdf]").element.disabled).toBe(true);
    expect((wrapper.vm as unknown as { full: boolean }).full).toBe(true);
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(POST).not.toHaveBeenCalled();
  });

  it("partagé depuis Android : le texte est déjà dans le champ", async () => {
    const wrapper = await mountForm({ initialText: "Menuisier à Sion, 100 %" });
    expect((wrapper.find("[data-test=manual-entry]").element as HTMLTextAreaElement).value).toBe("Menuisier à Sion, 100 %");
  });

  it("« Importer le PDF de l’annonce » : le texte lu par le serveur arrive dans le champ, à relire", async () => {
    const wrapper = await mountForm();
    const file = new File(["%PDF-1.4"], "annonce.pdf", { type: "application/pdf" });
    const input = wrapper.find("[data-test=manual-pdf-file]");
    expect(input.attributes("accept")).toBe("application/pdf,.pdf");
    POST.mockResolvedValueOnce({ data: { text: "Menuisier CFC\nBois & Fils, Sion", problem: null } });
    Object.defineProperty(input.element, "files", { value: [file], configurable: true });
    await input.trigger("change");
    await flushPromises();
    const [path, options] = POST.mock.calls[0] as [string, { bodySerializer: () => FormData }];
    expect(path).toBe("/api/offers/manual/pdf");
    expect(options.bodySerializer().get("file")).toBe(file);
    expect((wrapper.find("[data-test=manual-entry]").element as HTMLTextAreaElement).value).toBe("Menuisier CFC\nBois & Fils, Sion");
    expect(wrapper.find("[data-test=manual-pdf-done]").text()).toBe("Texte du PDF repris. Relis-le, puis ajoute l’offre.");
    // Rien n'est lu par l'IA avant « Ajouter l'offre » ; la phrase dit ce qui se passera.
    expect(POST).toHaveBeenCalledTimes(1);
    expect(wrapper.find("[data-test=manual-text-hint]").text()).toContain("Lu par l’IA");
  });

  it("un PDF sans texte, ou trop lourd : la phrase dit quoi faire", async () => {
    const wrapper = await mountForm();
    const input = wrapper.find("[data-test=manual-pdf-file]");
    POST.mockResolvedValueOnce({ data: { text: null, problem: "no-text" } });
    Object.defineProperty(input.element, "files", { value: [new File(["%PDF"], "scan.pdf")], configurable: true });
    await input.trigger("change");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-pdf-problem]").text()).toBe("Ce PDF ne contient pas de texte. Colle le texte de l’annonce.");
    const big = new File(["x"], "gros.pdf");
    Object.defineProperty(big, "size", { value: 6 * 1024 * 1024 });
    Object.defineProperty(input.element, "files", { value: [big], configurable: true });
    await input.trigger("change");
    await flushPromises();
    expect(wrapper.find("[data-test=manual-pdf-problem]").text()).toBe("Ce PDF est trop lourd (5 Mo au plus). Colle le texte de l’annonce.");
    expect(POST).toHaveBeenCalledTimes(1);
  });
});
