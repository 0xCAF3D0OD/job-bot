import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import TrainingsView from "./TrainingsView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const training = (id: number, extra: Record<string, unknown> = {}) => ({
  id,
  title: "Certified Kubernetes Administrator (CKA)",
  provider: "The Linux Foundation / CNCF",
  kind: "certification",
  format: "exam_online",
  language: "en",
  price: "paid",
  duration: null,
  level: "intermediate",
  url: `https://training.example/${id}`,
  tags: ["Kubernetes", "CKA"],
  description: "Certification de référence.",
  prep: "KodeKloud.",
  origin: "catalog",
  verified: true,
  matched: ["Kubernetes", "CKA"],
  mark: null,
  ...extra,
});

const page = (items: unknown[], extra: Record<string, unknown> = {}) => ({
  items,
  domain_keywords: ["Kubernetes", "CKA"],
  languages: ["en", "fr"],
  can_suggest: true,
  ...extra,
});

async function mountView(path = "/formations") {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: TrainingsView }] });
  await router.push(path);
  const wrapper = mount(TrainingsView, { global: { plugins: [router], stubs: { teleport: true } } });
  await flushPromises();
  return wrapper;
}

// Le suivi se fait dans le panneau latéral (docs/44 §2) : la carte entière l'ouvre (docs/93).
async function openPanel(wrapper: Awaited<ReturnType<typeof mountView>>): Promise<void> {
  await wrapper.find("[data-test=training-open]").trigger("click");
  await flushPromises();
}

describe("TrainingsView", () => {
  it("catalogue : l'encadré du financement, les puces, les lignes groupées (B16 à B18)", async () => {
    GET.mockResolvedValue({
      data: page([
        training(1),
        training(2, { title: "Microsoft Learn", price: "free", kind: "parcours", language: "fr", format: "self_paced" }),
        training(3, { title: "Killercoda", price: "free", kind: "atelier", format: "self_paced" }),
      ]),
    });
    const wrapper = await mountView();
    // Le catalogue de ton domaine, sans bouton « Domaine · Tout » (B17).
    expect(GET).toHaveBeenCalledWith("/api/trainings", { params: { query: { domain_only: true } } });
    expect(wrapper.find("[data-test=filter-all]").exists()).toBe(false);
    // Le financement : l'encadré, puis la feuille « Formation et chômage » (B16, formulation neutre B4).
    const note = wrapper.find("[data-test=orp-note]");
    expect(note.text()).toBe("Financement possible par l'ORPSeulement avec l'accord préalable de l'ORP");
    await note.trigger("click");
    const sheet = wrapper.find("[data-test=orp-sheet]");
    expect(sheet.text()).toContain("Il faut d'abord la demander à l'ORP et attendre son accord");
    expect(sheet.findAll("a")).toHaveLength(2);
    // Les groupes, avec leur nombre ; une ligne : titre, « éditeur · format · langue », le prix.
    expect(wrapper.find("[data-test=training-section-certifications] h2").text()).toBe("Certifications1");
    expect(wrapper.find("[data-test=training-section-courses] h2").text()).toBe("Cours et ateliers2");
    const first = wrapper.findAll("[data-test=training]")[0]!;
    expect(first.find("strong").text()).toBe("Certified Kubernetes Administrator (CKA)");
    expect(first.text()).toContain("The Linux Foundation / CNCF · Examen en ligne · anglais");
    expect(first.find("[data-test=training-price]").text()).toBe("Payant");
    // Les puces (B17) : un seul genre ; « Gratuites » et « En français » s'ajoutent.
    await wrapper.find("[data-test=chip-cours]").trigger("click");
    expect(wrapper.find("[data-test=chip-cours]").attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=chip-all]").attributes("aria-pressed")).toBe("false");
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(2);
    await wrapper.find("[data-test=chip-fr]").trigger("click");
    expect(wrapper.findAll("[data-test=training] strong").map((t) => t.text())).toEqual(["Microsoft Learn"]);
    await wrapper.find("[data-test=chip-free]").trigger("click");
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    await wrapper.find("[data-test=chip-cert]").trigger("click");
    expect(wrapper.find("[data-test=trainings-no-result]").exists()).toBe(true);
  });

  it("aucun résultat avec des filtres : une ligne grise et « Effacer les filtres » (règles §4)", async () => {
    GET.mockResolvedValue({ data: page([training(1)]) });
    const wrapper = await mountView();
    await wrapper.find("[data-test=chip-free]").trigger("click");
    const none = wrapper.find("[data-test=trainings-no-result]");
    expect(none.text()).toContain("Aucune formation avec ces filtres.");
    expect(none.find("[data-test=face-state]").exists()).toBe(false);
    await none.find("[data-test=trainings-reset]").trigger("click");
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    expect(wrapper.find("[data-test=chip-free]").attributes("aria-pressed")).toBe("false");
  });

  it("suivi : intéressé, en cours avec progression, retrait", async () => {
    GET.mockResolvedValue({ data: page([training(1)]) });
    PUT.mockImplementation((_p: string, { body }: { body: Record<string, unknown> }) =>
      Promise.resolve({ data: { progress: null, done_at: null, certified: null, ...body } }),
    );
    DELETE.mockResolvedValue({});
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=mark-in_progress]").exists()).toBe(false);
    await openPanel(wrapper);
    await wrapper.find("[data-test=mark-in_progress]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/trainings/{training_id}/mark", {
      params: { path: { training_id: 1 } },
      body: { status: "in_progress", progress: null, done_at: null, certified: null, modules_total: null, modules_done: null },
    });
    await wrapper.find("[data-test=progress]").setValue("module 4/12");
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body.progress).toBe("module 4/12");
    // Sur la ligne : l'avancement noté, en étiquette (B19).
    expect(wrapper.find("[data-test=training] [data-test=training-progress]").text()).toBe("En cours · module 4/12");
    expect(wrapper.find("[data-test=tab-mine]").text()).toContain("1");
    await wrapper.find("[data-test=mark-in_progress]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalled();
  });

  it("le signet : gardée, puis retirée ; en cours, il ouvre le panneau (docs/101)", async () => {
    const inProgress = { status: "in_progress", progress: "module 2/6", done_at: null, certified: null };
    GET.mockResolvedValue({ data: page([training(1), training(2, { title: "Autre", mark: inProgress })]) });
    PUT.mockImplementation((_p: string, { body }: { body: Record<string, unknown> }) =>
      Promise.resolve({ data: { progress: null, done_at: null, certified: null, ...body } }),
    );
    DELETE.mockResolvedValue({});
    const wrapper = await mountView();
    const heart = () => wrapper.findAll("[data-test=interest]")[0]!;
    expect(heart().attributes("aria-label")).toBe("Garder : Certified Kubernetes Administrator (CKA)");
    await heart().trigger("click");
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body.status).toBe("interested");
    expect(heart().attributes("aria-pressed")).toBe("true");
    await heart().trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledTimes(1);
    await wrapper.findAll("[data-test=interest]")[1]!.trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledTimes(1);
    expect(wrapper.find("[data-test=side-panel]").attributes("aria-label")).toBe("Autre");
  });

  it("suggestions de l'IA : recherche, garder, écarter", async () => {
    const ai = training(5, { title: "Kubernetes en français", origin: "ai", verified: false, price: "free" });
    GET.mockResolvedValue({ data: page([ai, training(6, { origin: "ai", verified: false, title: "Autre" })]) });
    POST.mockImplementation((path: string) =>
      Promise.resolve(path === "/api/trainings/suggest" ? { data: { added: 2 } } : {}),
    );
    const wrapper = await mountView();
    await wrapper.find("[data-test=suggest]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("2 formations proposées");
    expect(wrapper.findAll("[data-test=unverified]")).toHaveLength(2);
    await wrapper.findAll("[data-test=keep]")[0]!.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/trainings/{training_id}/review", { params: { path: { training_id: 5 } }, body: { keep: true } });
    await wrapper.find("[data-test=dismiss]").trigger("click");
    await flushPromises();
    expect(wrapper.findAll("[data-test=training]")).toHaveLength(1);
    expect(wrapper.findAll("[data-test=unverified]")).toHaveLength(0);
  });

  it("Suivies : en cours en carte avec l'avancement, puis les gardées et les terminées (B19)", async () => {
    const done = { status: "done", progress: null, done_at: "2026-09-30", certified: true };
    const current = { status: "in_progress", progress: "Module 3 sur 6", done_at: null, certified: null };
    const kept = { status: "interested", progress: null, done_at: null, certified: null };
    GET.mockResolvedValue({
      data: page([training(1, { mark: done }), training(2), training(3, { title: "CKAD", mark: current }), training(4, { title: "Terraform", mark: kept })]),
    });
    const wrapper = await mountView("/formations?onglet=miennes");
    expect(wrapper.find("[data-test=tab-mine]").classes()).toContain("active");
    expect(wrapper.find("[data-test=tab-mine]").text()).toBe("Suivies3");
    const card = wrapper.find("[data-test=training-current]");
    expect(card.text()).toContain("CKAD");
    expect(card.find(".training-current-progress").text()).toBe("Module 3 sur 6");
    expect(card.find("[data-test=training-continue]").attributes("href")).toBe("https://training.example/3");
    // Lot 18 (§10.5) : « Continuer le cours » au niveau 2, la ligne gardée finit par le cercle D29 de 36 px.
    expect(card.find("[data-test=training-continue]").classes()).toContain("action-2");
    expect(wrapper.find(".training-see .arrow-circle.small").attributes("aria-hidden")).toBe("true");
    expect(wrapper.findAll("[data-test=training-kept]").map((li) => li.text())).toEqual([
      "TerraformGardée · pas encore commencée",
      "Certified Kubernetes Administrator (CKA)Terminée",
    ]);
    await wrapper.findAll("[data-test=training-kept] button")[1]!.trigger("click");
    await flushPromises();
    expect((wrapper.find("[data-test=certified]").element as HTMLInputElement).checked).toBe(true);
    await card.find("[data-test=training-update]").trigger("click");
    expect(wrapper.find("[data-test=side-panel]").attributes("aria-label")).toBe("CKAD");
  });

  it("B19 : le compteur de modules, la barre, l'envoi unique et « Marquer comme terminée »", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const current = { status: "in_progress", progress: null, done_at: null, certified: null, modules_total: 12, modules_done: 6 };
    GET.mockResolvedValue({ data: page([training(3, { title: "CKAD", mark: current })]) });
    PUT.mockImplementation((_url: string, { body }: { body: Record<string, unknown> }) => Promise.resolve({ data: { ...current, ...body } }));
    const wrapper = await mountView("/formations?onglet=miennes");
    const card = wrapper.find("[data-test=training-current]");
    expect(card.find(".training-modules-line").text()).toBe("Module 6 sur 1250 %");
    const bar = card.find("[data-test=modules-bar]");
    expect([bar.attributes("aria-valuenow"), bar.attributes("aria-valuemin"), bar.attributes("aria-valuemax")]).toEqual(["6", "0", "12"]);
    expect(bar.attributes("aria-valuetext")).toBe("Module 6 sur 12");
    expect(card.find("[data-test=module-more]").attributes("aria-label")).toBe("Un module de plus");
    expect(card.find("[data-test=module-less]").attributes("aria-label")).toBe("Un module de moins");
    // Rien n'est annoncé au chargement.
    expect(card.find("[data-test=modules-status]").text()).toBe("");

    // Trois appuis : l'écran suit tout de suite, un seul envoi 500 ms après le dernier.
    for (let i = 0; i < 3; i++) await card.find("[data-test=module-more]").trigger("click");
    expect(card.find("[data-test=module-count]").text()).toBe("9");
    expect(card.find("[data-test=modules-status]").text()).toBe("Module 9 sur 12");
    expect(card.find("[data-test=modules-status]").attributes("role")).toBe("status");
    expect(PUT).not.toHaveBeenCalled();
    vi.advanceTimersByTime(499);
    expect(PUT).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    await flushPromises();
    expect(PUT).toHaveBeenCalledTimes(1);
    expect(PUT.mock.calls[0]![1].body).toMatchObject({ status: "in_progress", modules_total: 12, modules_done: 9 });

    // Au dernier module : + désactivé, « Marquer comme terminée » proposé ; le statut ne change pas seul.
    for (let i = 0; i < 4; i++) await wrapper.find("[data-test=module-more]").trigger("click");
    expect(wrapper.find("[data-test=module-count]").text()).toBe("12");
    expect(wrapper.find("[data-test=module-more]").attributes("disabled")).toBeDefined();
    vi.advanceTimersByTime(500);
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body).toMatchObject({ status: "in_progress", modules_done: 12 });
    await wrapper.find("[data-test=module-finish]").trigger("click");
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body).toMatchObject({ status: "done", modules_done: 12 });
    vi.useRealTimers();
  });

  it("B19 : − désactivé à 0 ; une formation gardée avec ses modules est une carte, + la passe « en cours »", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const kept = { status: "interested", progress: null, done_at: null, certified: null, modules_total: 4, modules_done: 0 };
    GET.mockResolvedValue({ data: page([training(5, { title: "Terraform", mark: kept })]) });
    PUT.mockResolvedValue({ data: { ...kept, status: "in_progress", modules_done: 1 } });
    const wrapper = await mountView("/formations?onglet=miennes");
    expect(wrapper.findAll("[data-test=training-kept]")).toHaveLength(0);
    expect(wrapper.find("[data-test=module-less]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=module-less]").trigger("click");
    expect(wrapper.find("[data-test=module-count]").text()).toBe("0");
    await wrapper.find("[data-test=module-more]").trigger("click");
    vi.advanceTimersByTime(500);
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body).toMatchObject({ status: "interested", modules_total: 4, modules_done: 1 });
    vi.useRealTimers();
  });

  it("B19 : le nombre de modules se note dans le panneau ; vide, on revient au texte libre", async () => {
    const current = { status: "in_progress", progress: "module 2", done_at: null, certified: null, modules_total: null, modules_done: null };
    GET.mockResolvedValue({ data: page([training(3, { title: "CKAD", mark: current })]) });
    PUT.mockImplementation((_url: string, { body }: { body: Record<string, unknown> }) => Promise.resolve({ data: { ...current, ...body } }));
    const wrapper = await mountView("/formations?onglet=miennes");
    await wrapper.find("[data-test=training-update]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=progress]").exists()).toBe(true);
    await wrapper.find("[data-test=modules-total]").setValue("12");
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body).toMatchObject({ modules_total: 12, modules_done: 0 });
    expect(wrapper.find("[data-test=progress]").exists()).toBe(false);
    expect(wrapper.find("[data-test=training-modules]").exists()).toBe(true);
    await wrapper.find("[data-test=modules-total]").setValue("");
    await flushPromises();
    expect(PUT.mock.calls.at(-1)![1].body).toMatchObject({ modules_total: null, modules_done: null });
    expect(wrapper.find("[data-test=progress]").exists()).toBe(true);
  });

  it("Suivies vide : l'invitation à garder une formation", async () => {
    GET.mockResolvedValue({ data: page([training(1)]) });
    const wrapper = await mountView("/formations?onglet=miennes");
    expect(wrapper.find("[data-test=trainings-none]").text()).toContain("Garde une formation du catalogue avec son signet.");
  });

  it("formation terminée : « Ajouter à mon profil », bloc prérempli, puis « Dans ton profil »", async () => {
    const done = { status: "done", progress: null, done_at: "2026-09-30", certified: true, chunk_id: null };
    GET.mockResolvedValue({ data: page([training(1, { mark: done })]) });
    POST.mockResolvedValue({ data: { ...done, chunk_id: 42 } });
    const wrapper = await mountView();
    await openPanel(wrapper);
    expect(wrapper.find("[data-test=section-profile] h3").text()).toBe("Profil");
    await wrapper.find("[data-test=add-to-profile]").trigger("click");
    expect((wrapper.find("[data-test=block-title]").element as HTMLInputElement).value).toBe(
      "Certified Kubernetes Administrator (CKA) (The Linux Foundation / CNCF)",
    );
    const content = (wrapper.find("[data-test=block-content]").element as HTMLTextAreaElement).value;
    expect(content).toBe("Formation terminée en septembre 2026, certificat obtenu. Certification de référence.");
    expect((wrapper.find("[data-test=block-tags]").element as HTMLInputElement).value).toBe("Kubernetes, CKA");
    await wrapper.find("[data-test=block-form]").trigger("submit");
    await flushPromises();
    expect(POST.mock.calls[0]![0]).toBe("/api/trainings/{training_id}/profile-block");
    expect(POST.mock.calls[0]![1].body.tags).toEqual(["Kubernetes", "CKA"]);
    expect(wrapper.find("[data-test=in-profile]").exists()).toBe(true);
  });

  it("financement ORP : texte avec l'argument tiré des offres, puis demandée et acceptée", async () => {
    const interested = { status: "interested", progress: null, done_at: null, certified: null, chunk_id: null, funding_status: null, funding_requested_at: null };
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/trainings/{training_id}/funding-request"
          ? { data: { offers: 12, matched: ["Kubernetes", "CKA"], examples: [{ title: "Ingénieur DevOps", company: "Consort Group" }], sender: "Camille Exemple" } }
          : { data: page([training(1, { mark: interested, duration: "2 h d'examen" })]) },
      ),
    );
    PUT.mockResolvedValueOnce({ data: { ...interested, funding_status: "requested", funding_requested_at: "2026-10-15" } });
    const wrapper = await mountView();
    await openPanel(wrapper);
    expect(wrapper.find("[data-test=section-funding] h3").text()).toBe("Financement ORP");
    await wrapper.find("[data-test=prepare-funding]").trigger("click");
    await flushPromises();
    const text = (wrapper.find("[data-test=funding-letter]").element as HTMLTextAreaElement).value;
    expect(text).toContain("« Certified Kubernetes Administrator (CKA) » (The Linux Foundation / CNCF");
    expect(text).toContain("12 offres que j'ai reçues demandaient Kubernetes ou CKA, par exemple « Ingénieur DevOps » chez Consort Group.");
    expect(text).toContain("Coût : [montant]. Durée : 2 h d'examen.");
    expect(text.trim().endsWith("Camille Exemple")).toBe(true);

    await wrapper.find("[data-test=funding-requested]").trigger("click");
    await flushPromises();
    expect(PUT.mock.calls[0]![1].body).toEqual({ status: "requested" });
    expect(wrapper.find("[data-test=funding-badge]").text()).toBe("Financement demandé");
    expect(wrapper.find("[data-test=training-funding]").text()).toContain("Demandée le 15 oct.");
  });

  it("« Chercher d'autres formations » sans domaine : le champ du domaine s'ouvre", async () => {
    GET.mockResolvedValue({ data: page([training(1)], { domain_keywords: [] }) });
    const wrapper = await mountView();
    expect(GET).toHaveBeenLastCalledWith("/api/trainings", { params: { query: { domain_only: false } } });
    await wrapper.find("[data-test=suggest]").trigger("click");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("Indique d'abord ton domaine");
    expect(wrapper.find("#domaine-champ").exists()).toBe(true);
  });
});
