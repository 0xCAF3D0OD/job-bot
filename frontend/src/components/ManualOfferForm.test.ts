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
    // Kevin, 18.11 : « Coller » et « Capture ou PDF » aussi sur ordinateur, à la place de « Importer le PDF ».
    expect(wrapper.find("[data-test=manual-paste]").text()).toBe("Coller");
    expect(wrapper.find("[data-test=manual-file]").text()).toBe("Capture ou PDF");
    wrapper.unmount();
    const last = await mountForm({}, "Menuisier", 19);
    expect(last.find("[data-test=manual-count]").text()).toBe("Tu peux encore en ajouter une aujourd’hui.");
  });

  it("téléphone (planche AjouterOffreTel, §72d) : « Coller » et « Capture ou PDF » dans la barre du champ, sans +, la pastille de la formule", async () => {
    phone.value = true;
    const wrapper = await mountForm();
    expect(wrapper.find("[data-test=manual-paste]").text()).toBe("Coller");
    expect(wrapper.find("[data-test=manual-file]").text()).toBe("Capture ou PDF");
    const input = wrapper.find("[data-test=composer-input]");
    expect(input.attributes("rows")).toBe("4");
    expect(input.attributes("placeholder")).toBe("Lien ou texte de l’annonce");
    expect(input.attributes("aria-label")).toBe("Lien ou texte de l’annonce");
    // Dans la barre du champ, avant la flèche d'envoi.
    const bar = wrapper.find(".composer-bar");
    expect(bar.findAll("button").map((b) => b.attributes("data-test"))).toEqual(["manual-paste", "manual-file", "composer-send"]);
    expect(wrapper.find("[data-test=composer-send]").attributes("aria-label")).toBe("Ajouter l’offre");
    expect(wrapper.find("[data-test=composer-plus]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manual-pdf-file]").attributes("accept")).toBe("application/pdf,.pdf,image/png,image/jpeg");
    // §17 du 15 novembre : flèche aria-disabled tant que le champ est vide ; les pastilles liées au champ.
    expect(wrapper.find("[data-test=composer-send]").attributes("aria-disabled")).toBe("true");
    const help = wrapper.find("[data-test=manual-help]");
    expect(help.text()).toBe("Capture ou PDF : compte dans ta formule");
    expect(input.attributes("aria-describedby")).toBe(help.attributes("id"));
    expect(wrapper.find("[data-test=manual-count]").exists()).toBe(false);
    wrapper.unmount();
    // À 5 ajouts ou moins, la pastille orange du quota rejoint celle de la formule.
    const low = await mountForm({}, "Menuisier", 17);
    expect(low.find("[data-test=manual-count]").text()).toBe("Plus que 3 ajouts aujourd’hui");
    expect(low.find("[data-test=manual-help]").text()).toContain("Capture ou PDF : compte dans ta formule");
  });

  describe("téléphone, « Coller » (Kevin, 18.11)", () => {
    afterEach(() => {
      Object.defineProperty(navigator, "clipboard", { configurable: true, value: undefined });
    });
    it("le texte copié arrive dans le champ", async () => {
      phone.value = true;
      Object.defineProperty(navigator, "clipboard", { configurable: true, value: { readText: vi.fn(async () => "  https://bois.ch/emplois/1 \n") } });
      const wrapper = await mountForm();
      await wrapper.find("[data-test=manual-paste]").trigger("click");
      await flushPromises();
      expect(wrapper.find<HTMLTextAreaElement>("[data-test=composer-input]").element.value).toBe("https://bois.ch/emplois/1");
      expect(document.activeElement).toBe(wrapper.find("[data-test=composer-input]").element);
      wrapper.unmount();
    });
    it("accès refusé : le champ reste vide et prend le curseur, pour coller à la main", async () => {
      phone.value = true;
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: { readText: vi.fn(async () => Promise.reject(new DOMException("refusé", "NotAllowedError"))) },
      });
      const wrapper = await mountForm();
      await wrapper.find("[data-test=manual-paste]").trigger("click");
      await flushPromises();
      expect(wrapper.find<HTMLTextAreaElement>("[data-test=composer-input]").element.value).toBe("");
      expect(document.activeElement).toBe(wrapper.find("[data-test=composer-input]").element);
      wrapper.unmount();
    });
  });

  it("téléphone, « Capture ou PDF » : le texte du fichier arrive dans le champ ; la formule épuisée le dit", async () => {
    phone.value = true;
    const wrapper = await mountForm();
    const input = wrapper.find("[data-test=manual-pdf-file]");
    const capture = new File(["\x89PNG"], "capture.png", { type: "image/png" });
    Object.defineProperty(input.element, "files", { value: [capture], configurable: true });
    POST.mockResolvedValueOnce({ data: { text: "Menuisière CFC\nBois & Fils, Sion", problem: null, limit: null } });
    await input.trigger("change");
    await vi.waitFor(() => expect(POST).toHaveBeenCalledTimes(1));
    await flushPromises();
    expect(POST.mock.calls[0]![0]).toBe("/api/offers/manual/file");
    expect(wrapper.find<HTMLTextAreaElement>("[data-test=composer-input]").element.value).toBe("Menuisière CFC\nBois & Fils, Sion");
    expect(wrapper.find("[data-test=manual-pdf-done]").text()).toBe("Texte du fichier repris. Relis-le, puis ajoute l’offre.");

    POST.mockResolvedValueOnce({ data: { text: null, problem: null, limit: "Les 30 offres notées du mois sont utilisées." } });
    Object.defineProperty(input.element, "files", { value: [capture], configurable: true });
    await input.trigger("change");
    await vi.waitFor(() => expect(POST).toHaveBeenCalledTimes(2));
    await flushPromises();
    expect(wrapper.find("[data-test=manual-pdf-problem]").text()).toBe("Les 30 offres notées du mois sont utilisées.");
    wrapper.unmount();
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
    // Le champ reste, « Coller » et « Capture ou PDF » disparaissent.
    expect(wrapper.find("[data-test=manual-entry]").exists()).toBe(true);
    expect(wrapper.find("[data-test=manual-file]").exists()).toBe(false);
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
      separate: false,
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

  it("même lien (Kevin, 16.11) : le message sous le champ, « Ouvrir l’offre » seul, à la place d’« Ajouter l’offre »", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({
      data: { draft: draft({ existing_offer_id: 4, existing_kind: "link", existing_title: "Menuisier", existing_company: "Bois & Fils", existing_added: "2026-11-03" }) },
    });
    await send(wrapper, "https://bois.ch/emplois/1");
    const message = wrapper.find("[data-test=manual-existing]");
    expect(message.attributes("role")).toBe("alert");
    expect(message.find("[data-icon]").exists()).toBe(true);
    expect(message.text()).toBe("Cette offre est déjà dans tes candidatures (ajoutée le 3 novembre).");
    expect(wrapper.find("[data-test=manual-separate]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manual-draft]").exists()).toBe(false);
    expect(message.find("[data-icon=info]").exists()).toBe(true);
    // Rien à compléter : pas de phrase.
    expect(wrapper.find("[data-test=manual-fillable]").exists()).toBe(false);
    expect((wrapper.vm as unknown as { duplicate: boolean }).duplicate).toBe(true);
    POST.mockResolvedValueOnce({ data: { id: 4, existing: true, status: "to_review", reasons: [], filled: ["url"] } });
    await wrapper.find("[data-test=manual-open-existing]").trigger("click");
    await flushPromises();
    // Ouvrir ajoute le lien et les champs vides que cette annonce remplit, sans rien remplacer.
    expect(POST.mock.calls[1]![1].body).toMatchObject({ fill: true, separate: false });
    expect(wrapper.emitted("added")).toEqual([[{ id: 4, existing: true, status: "to_review", reasons: [], filled: ["url"] }]]);
  });

  it("même poste ailleurs (Kevin, 16.11) : « Ouvrir l’offre » et « Ajouter quand même », une offre à part", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({
      data: { draft: draft({ existing_offer_id: 4, existing_kind: "post", existing_title: "Menuisier CFC", existing_company: "Bois & Fils SA", existing_added: "2026-11-03", fillable: ["description"] }) },
    });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(wrapper.find("[data-test=manual-existing]").text()).toBe(
      "Une offre très proche est déjà là : Menuisier CFC chez Bois & Fils SA, ajoutée le 3 novembre. Ouvrir l’offre complète aussi les informations qui lui manquent.",
    );
    expect(wrapper.find("[data-test=manual-open-existing]").text()).toContain("Ouvrir l’offre");
    expect(wrapper.find("[data-test=manual-separate]").text()).toContain("Ajouter quand même");
    POST.mockResolvedValueOnce({ data: { id: 12, existing: false, status: "new", reasons: [] } });
    await wrapper.find("[data-test=manual-separate]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[1]![1].body).toMatchObject({ fill: false, separate: true });
    expect(wrapper.emitted("added")).toEqual([[{ id: 12, existing: false, status: "new", reasons: [] }]]);
  });

  it("changer le champ fait disparaître le message et revenir « Ajouter l’offre »", async () => {
    const wrapper = await mountForm();
    POST.mockResolvedValueOnce({ data: { draft: draft({ existing_offer_id: 4, existing_kind: "post", existing_title: "Menuisier" }) } });
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(wrapper.find("[data-test=manual-existing]").exists()).toBe(true);
    await wrapper.find("[data-test=manual-entry]").setValue("https://bois.ch/emplois/2");
    expect(wrapper.find("[data-test=manual-existing]").exists()).toBe(false);
    expect((wrapper.vm as unknown as { duplicate: boolean; label: string }).duplicate).toBe(false);
    expect((wrapper.vm as unknown as { label: string }).label).toBe("Ajouter l’offre");
  });

  it("au maximum du jour, la lecture est fermée", async () => {
    const wrapper = await mountForm({}, "Menuisier", 20);
    expect(wrapper.find("[data-test=manual-count]").text()).toContain("c’est le maximum");
    expect(wrapper.find("[data-test=manual-file]").attributes("aria-disabled")).toBe("true");
    expect((wrapper.vm as unknown as { full: boolean }).full).toBe(true);
    await send(wrapper, "https://bois.ch/emplois/1");
    expect(POST).not.toHaveBeenCalled();
  });

  it("partagé depuis Android : le texte est déjà dans le champ", async () => {
    const wrapper = await mountForm({ initialText: "Menuisier à Sion, 100 %" });
    expect((wrapper.find("[data-test=manual-entry]").element as HTMLTextAreaElement).value).toBe("Menuisier à Sion, 100 %");
  });

  it("ordinateur, « Capture ou PDF » : le texte lu par le serveur arrive dans le champ, à relire", async () => {
    const wrapper = await mountForm();
    const file = new File(["%PDF-1.4"], "annonce.pdf", { type: "application/pdf" });
    const input = wrapper.find("[data-test=manual-pdf-file]");
    expect(input.attributes("accept")).toBe("application/pdf,.pdf,image/png,image/jpeg");
    POST.mockResolvedValueOnce({ data: { text: "Menuisier CFC\nBois & Fils, Sion", problem: null, limit: null } });
    Object.defineProperty(input.element, "files", { value: [file], configurable: true });
    await input.trigger("change");
    await vi.waitFor(() => expect(POST).toHaveBeenCalledTimes(1));
    await flushPromises();
    const [path, options] = POST.mock.calls[0] as [string, { bodySerializer: () => FormData }];
    expect(path).toBe("/api/offers/manual/file");
    expect(options.bodySerializer().get("file")).toBe(file);
    expect((wrapper.find("[data-test=manual-entry]").element as HTMLTextAreaElement).value).toBe("Menuisier CFC\nBois & Fils, Sion");
    expect(wrapper.find("[data-test=manual-pdf-done]").text()).toBe("Texte du fichier repris. Relis-le, puis ajoute l’offre.");
    // Rien n'est lu par l'IA avant « Ajouter l'offre » ; la phrase dit ce qui se passera.
    expect(POST).toHaveBeenCalledTimes(1);
    expect(wrapper.find("[data-test=manual-text-hint]").text()).toContain("Lu par l’IA");
  });

  it("un fichier sans texte, ou trop lourd : la phrase dit quoi faire", async () => {
    const wrapper = await mountForm();
    const input = wrapper.find("[data-test=manual-pdf-file]");
    POST.mockResolvedValueOnce({ data: { text: null, problem: "no-text", limit: null } });
    Object.defineProperty(input.element, "files", { value: [new File(["%PDF"], "scan.pdf")], configurable: true });
    await input.trigger("change");
    await vi.waitFor(() => expect(POST).toHaveBeenCalledTimes(1));
    await flushPromises();
    expect(wrapper.find("[data-test=manual-pdf-problem]").text()).toBe("Je ne trouve pas de texte d’annonce dans ce fichier. Colle le texte de l’annonce.");
    const big = new File(["x"], "gros.pdf");
    Object.defineProperty(big, "size", { value: 6 * 1024 * 1024 });
    Object.defineProperty(input.element, "files", { value: [big], configurable: true });
    await input.trigger("change");
    await vi.waitFor(() => expect(wrapper.find("[data-test=manual-pdf-problem]").text()).toBe("Ce fichier est trop lourd (5 Mo au plus). Colle le texte de l’annonce."));
    expect(POST).toHaveBeenCalledTimes(1);
  });
});
