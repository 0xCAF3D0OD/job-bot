import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

// Ordinateur : la requête de 1 024 px répond oui, celle du téléphone non.
vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: (query?: string) => ({ phone: ref(query === "(min-width: 1024px)") }),
  useNarrow: () => ({ phone: ref(false) }),
}));
const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn(), DELETE: vi.fn() },
}));

import OrpMeetingView from "./OrpMeetingView.vue";

// Candidatures › Rendez-vous sur ordinateur (maquette RendezVousOrdinateur, 7.11.2026) : la liste de 560 px
// à gauche (À venir, À noter, Derniers rendez-vous ORP), le détail à droite, la sélection dans ?rdv=.
const EMPTY = { outcome_at: null, agreed_target: null, measures: [], assignments: null, note: null, asked: [], next_starts_at: null, sheet_text: null };
const PREP = {
  summaries: [],
  works: null,
  blockers: ["Formulaires en ligne : 0 réponse sur 9."],
  missing: [],
  offers: 22,
  questions: [{ key: "intermediate", text: "Déclarer mon gain intermédiaire", checked: false }],
  obligations: [],
  months: [{ month: "2099-11", count: 6, target: 10, answered: 0, interviews: 0 }],
  has_applications: true,
};
const MEETING = { id: 1, starts_at: "2099-11-10T08:30:00Z", place: "ORP Renens", advisor: null, ...EMPTY };
const NOTED = {
  ...MEETING,
  id: 2,
  starts_at: "2026-10-13T08:00:00Z",
  outcome_at: "2026-10-13T10:00:00Z",
  agreed_target: 8,
  measures: [{ text: "Financement Terraform", training_id: null }],
};

function serve(page: object): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/applications" ? { data: [] } : path === "/api/orp-meeting" ? { data: page } : { data: null }),
  );
}

async function open(query = "") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/candidatures/rendez-vous-orp", component: OrpMeetingView }],
  });
  await router.push(`/candidatures/rendez-vous-orp${query}`);
  const wrapper = mount(OrpMeetingView, { global: { plugins: [router], stubs: { InterviewPreparation: true } } });
  await flushPromises();
  return { wrapper, router };
}

afterEach(() => {
  GET.mockReset();
  PUT.mockReset();
});

describe("Rendez-vous sur ordinateur", () => {
  it("deux colonnes : rien d’ouvert à l’arrivée (§36), puis le rendez-vous ORP et un rendez-vous noté s’ouvrent dans ?rdv=", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [NOTED], target: 10, trainings: [] });
    const { wrapper, router } = await open();
    expect(wrapper.find("[data-test=rdv-desktop]").exists()).toBe(true);
    // Rien d'ouvert (§36 du 16.11, décision de Kevin) : aucune carte choisie, « Choisis un rendez-vous » à droite.
    expect(wrapper.get("[data-test=rdv-item-orp]").attributes("aria-current")).toBeUndefined();
    expect(wrapper.find("[data-test=rdv-detail]").exists()).toBe(false);
    const choose = wrapper.get("[data-test=choose-detail]");
    expect(choose.get("h2").text()).toBe("Choisis un rendez-vous");
    expect(choose.get(".choose-hint").text()).toBe("Préparation et feuille ORP s’affichent ici");
    await wrapper.get("[data-test=rdv-item-orp]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.rdv).toBe("orp");
    expect(wrapper.get("[data-test=rdv-item-orp]").attributes("aria-current")).toBe("true");
    expect(wrapper.find("[data-test=choose-detail]").exists()).toBe(false);
    // Deux lignes (§39 du 16.11) : le titre et sa pastille, puis l'heure, le délai et le lieu ; ni surtitre ni rangée vide.
    const card = wrapper.get("[data-test=rdv-item-orp]");
    expect(card.findAll(".rdv-item-text > *").map((line) => line.classes()[0])).toEqual(["rdv-item-line", "rdv-item-sub"]);
    expect(card.get(".rdv-item-line").text()).toMatch(/^Rendez-vous ORP\s*Feuille (prête|à compléter)$/);
    expect(card.get(".rdv-item-sub").text()).toMatch(/· dans \d+ jours/);
    expect(card.attributes("aria-label")).toMatch(/^Rendez-vous ORP, feuille (prête|à compléter), \S+ \d+ \S+ à .+, dans \d+ jours/);
    expect(wrapper.find("[data-test=rdv-list-empty]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-detail-orp]").exists()).toBe(true);
    expect(wrapper.get("[data-test=rdv-last-agreed]").text()).toContain("8 recherches par mois");
    const past = wrapper.get("[data-test=rdv-item-passe-2]");
    expect(past.text()).toContain("Objectif 8 par mois · financement Terraform");
    await past.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.rdv).toBe("passe-2");
    expect(wrapper.find("[data-test=rdv-detail-past]").exists()).toBe(true);
  });

  it("un rendez-vous passé et non noté : « À noter » ouvre ce qui a été convenu dans le détail, en deux colonnes (lot 14)", async () => {
    const held = { ...MEETING, starts_at: "2026-10-13T08:00:00Z" };
    serve({ meeting: held, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open("?rdv=passe-1");
    const item = wrapper.get("[data-test=rdv-to-note-1]");
    // Sans pastille « Pas encore noté » : le groupe « À noter » le dit.
    expect(item.text()).not.toContain("noté");
    // Ouvert par l'adresse (?rdv=) : rien ne s'ouvre seul depuis le §36.
    expect(item.attributes("aria-current")).toBe("true");
    const detail = wrapper.get("[data-test=rdv-detail-past]");
    expect(detail.get("h2").text()).toMatch(/^Rendez-vous ORP du 13 octobre/);
    const inline = detail.get("[data-test=outcome-inline]");
    // Récapitulatif du 11 novembre, PR 31 : objectif et mesures côte à côte, plus de colonne « Le rendez-vous ».
    expect(inline.findAll(".outcome-pair fieldset legend").map((l) => l.text())).toEqual(["Objectif de recherches", "Mesures décidées (facultatif)"]);
    expect(inline.find("aside").exists()).toBe(false);
    expect(inline.get("label").text()).toBe("Cours, stage ou programme");
    // « Prochain rendez-vous » : une ligne et « Ajouter », plus de formulaire dans ce détail.
    const next = inline.get("[data-test=outcome-next]");
    expect(next.text()).toContain("Pas encore noté. jobA1 prépare ta fiche la veille.");
    expect(next.find("[data-test=dt-date]").exists()).toBe(false);
    expect(next.get("[data-test=outcome-next-add]").text()).toBe("Ajouter");
    // La barre du bas : « Enregistrer » et ce que ça met à jour.
    expect(inline.get(".outcome-inline-actions").text()).toBe("Enregistrer L’objectif et les mesures se mettent à jour partout.");
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, past: [{ ...held, outcome_at: "2026-10-13T10:00:00Z" }], target: 10, trainings: [] } });
    await inline.get("[data-test=outcome-more]").trigger("click");
    await inline.trigger("submit");
    await flushPromises();
    const [path, options] = PUT.mock.calls[0] as [string, { body: { target: number; next_starts_at: string | null } }];
    expect(path).toBe("/api/orp-meeting/{meeting_id}/convenu");
    expect(options.body.target).toBe(11);
    // Le prochain rendez-vous ne part plus d'ici : ce qui était noté est gardé tel quel.
    expect(options.body.next_starts_at).toBeNull();
    expect(wrapper.find("[data-test=rdv-item-orp]").exists()).toBe(true);
    expect(wrapper.find("[data-test=rdv-to-note-1]").exists()).toBe(false);
  });

  it("rien à venir : une ligne en tête de liste ; aucun rendez-vous : l’état vide ; le « + Ajouter » de l’en-tête (?ajouter=1) ouvre le panneau (maquette du 14 novembre, §6)", async () => {
    // Un rendez-vous passé, rien à venir : la pastille en tête de liste (§13 du 15 novembre, planches corrigées).
    serve({ meeting: null, preparation: PREP, past: [NOTED], target: 10, trainings: [] });
    const before = await open();
    expect(before.wrapper.get("[data-test=rdv-list-empty]").text()).toContain("Aucun rendez-vous à venir");
    // La pastille seule (maquette du 15 novembre, §14) : la phrase « jobA1 prépare ta fiche la veille. » n'y est plus.
    expect(before.wrapper.get("[data-test=rdv-list-empty]").text()).not.toContain("la veille");
    // Aucun rendez-vous du tout (RendezVousOrdinateurVide) : l’état vide commun, centré, et son bouton d’ajout.
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper, router } = await open();
    expect(wrapper.get("[data-test=rdv-none-yet] h2").text()).toBe("Aucun rendez-vous");
    expect(wrapper.find("[data-test=rdv-list-empty]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-add]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-detail]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(false);
    expect(wrapper.findComponent({ name: "NewMeetingSheet" }).props("open")).toBe(false);
    await router.push("/candidatures/rendez-vous-orp?ajouter=1");
    await flushPromises();
    expect(router.currentRoute.value.query.ajouter).toBeUndefined();
    expect(wrapper.findComponent({ name: "NewMeetingSheet" }).props("open")).toBe(true);
    const panel = wrapper.get("[data-test=new-meeting]");
    expect(panel.find(".sheet-title").text()).toBe("Nouveau rendez-vous");
    expect(panel.text()).toContain("jobA1 prépare ta fiche la veille");
    expect(panel.find("[role=radiogroup][aria-label='Avec qui ?']").exists()).toBe(true);
    expect(panel.find("input[type=date], input[type=time]").exists()).toBe(false);
  });
});
