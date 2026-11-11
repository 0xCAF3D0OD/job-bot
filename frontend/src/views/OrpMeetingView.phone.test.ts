import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("../composables/usePhone", () => ({
  PHONE_QUERY: "",
  usePhone: () => ({ phone: ref(true) }),
  useNarrow: () => ({ phone: ref(true) }),
}));
const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn(), DELETE: vi.fn() },
}));

import OrpMeetingView from "./OrpMeetingView.vue";

// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6.11.2026).
const EMPTY = { outcome_at: null, agreed_target: null, measures: [], assignments: null, note: null, asked: [], next_starts_at: null, sheet_text: null };
const PREP = {
  summaries: [],
  works: null,
  blockers: ["Formulaires en ligne : 0 réponse sur 9."],
  missing: [{ skill: "Terraform", count: 14, training_id: null, training_title: null }],
  offers: 22,
  questions: [
    { key: "funding:3", text: "Financer la formation Terraform", checked: true },
    { key: "intermediate", text: "Déclarer mon gain intermédiaire", checked: false },
  ],
  obligations: [],
  months: [{ month: "2099-11", count: 6, target: 10, answered: 0, interviews: 0 }],
  has_applications: true,
};
const MEETING = { id: 1, starts_at: "2099-11-10T08:30:00Z", place: "ORP Renens", advisor: null, ...EMPTY };
const PAST = {
  ...MEETING,
  id: 2,
  starts_at: "2026-10-13T08:00:00Z",
  outcome_at: "2026-10-13T10:00:00Z",
  agreed_target: 10,
  measures: [{ text: "Cours Terraform", training_id: null }],
  next_starts_at: "2099-11-10T08:30:00Z",
};
const interview = (id: number, at: string) => ({
  id,
  company: `Entreprise ${id}`,
  job_title: `Poste ${id}`,
  status: "entretien",
  interview_at: at,
  company_address: id === 7 ? "Avenue de la Gare 12, Lausanne" : null,
  interviews: [],
});

function serve(page: object, applications: object[] = []): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === "/api/applications" ? { data: applications } : path === "/api/orp-meeting" ? { data: page } : { data: null }),
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

describe("Rendez-vous sur téléphone", () => {
  it("« À venir » : l’ORP et les entretiens mêlés, par date ; puis « Derniers rendez-vous ORP »", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [PAST], target: 10, trainings: [] }, [
      interview(7, "2099-11-16T09:00:00Z"),
      interview(8, "2099-11-08T13:00:00Z"),
    ]);
    const { wrapper } = await open();
    const upcoming = wrapper.get("[data-test=rdv-upcoming]");
    expect(upcoming.get("h2").text()).toBe("À venir3 rendez-vous");
    const order = upcoming.findAll("article").map((a) => a.attributes("data-test"));
    expect(order).toEqual(["rdv-interview-8", "rdv-orp", "rdv-interview-7"]);
    // Le bloc date est décoratif ; la date est aussi dite en texte.
    const orp = wrapper.get("[data-test=rdv-orp]");
    expect(orp.get(".rdv-date").attributes("aria-hidden")).toBe("true");
    expect(orp.text()).toContain("Mardi 10 novembre, 9 h 30 · ORP Renens");
    expect(orp.text()).toContain("Ta feuille est prête");
    // §10.7 (9 novembre) : la carte garde « Préparer le rendez-vous », qui ouvre la feuille avec « Où tu en es ».
    expect(orp.get("[data-test=rdv-prep-open]").text()).toBe("Préparer le rendez-vous");
    expect(orp.find("[data-test=rdv-pdf]").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=rdv-prep-lines] li").map((li) => li.text())).toEqual([
      "6 recherches sur 10Ton mois",
      "Ce qui bloqueFormulaires en ligne : 0 réponse sur 9",
      "Ce qui te manqueTerraform, demandé dans 14 offres sur 22",
    ]);
    expect(wrapper.get("[data-test=rdv-interview-7]").text()).toContain("Avenue de la Gare 12, Lausanne");
    // La page de l'ordinateur ne s'affiche pas.
    expect(wrapper.find("[data-test=meeting-when]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-questions]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-facts]").exists()).toBe(false);
    const past = wrapper.get("[data-test=rdv-past]");
    expect(past.text()).toContain("Rendez-vous ORP du 13 octobre");
    expect(past.get("[data-test=rdv-agreed]").text()).toContain("Objectif10 recherches par mois");
    expect(past.get("[data-test=rdv-log]").text()).toContain("Carnet ORP1 rendez-vous");
  });

  it("« Ta feuille est prête » seulement avec au moins une ligne ; sinon « Feuille à compléter »", async () => {
    const empty = { ...PREP, blockers: [], missing: [], months: [] };
    serve({ meeting: MEETING, preparation: empty, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-prep-lines]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-ready]").exists()).toBe(false);
    expect(wrapper.get("[data-test=rdv-todo]").text()).toBe("Feuille à compléter");

    serve({ meeting: MEETING, preparation: { ...empty, blockers: ["Aucune réponse."] }, past: [], target: 10, trainings: [] });
    const again = await open();
    expect(again.wrapper.get("[data-test=rdv-ready]").text()).toBe("Ta feuille est prête");
    expect(again.wrapper.find("[data-test=rdv-todo]").exists()).toBe(false);
  });

  it("le « ⋯ » de la carte ORP : modifier le rendez-vous ou le supprimer", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    await wrapper.get("[data-test=rdv-more]").trigger("click");
    const items = wrapper.findAll("[data-test=rdv-orp] [role=menuitem]").map((i) => i.text());
    expect(items).toEqual(["Modifier le rendez-vous", "Supprimer"]);
    await wrapper.get("[data-test=rdv-edit]").trigger("click");
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=rdv-more]").exists()).toBe(false);
  });

  it("la feuille « Préparer le rendez-vous » : rappel, questions au conseiller avec les cases existantes, PDF", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] });
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] } });
    const { wrapper } = await open();
    const sheet = wrapper.findComponent({ name: "MeetingPrepSheet" });
    expect(sheet.props("open")).toBe(false);
    await wrapper.get("[data-test=rdv-prep-open]").trigger("click");
    expect(sheet.props("open")).toBe(true);
    // L'écran « Rendez-vous ORP » (lot du 11 novembre au soir, PR 52 ; RendezVousFeuilleV2).
    expect(sheet.findComponent({ name: "BottomSheet" }).props()).toMatchObject({ title: "Rendez-vous ORP", screen: true });
    expect(sheet.get("[data-test=rdv-prep-hand]").text()).toBe("ta feuille est prête");
    expect(sheet.get("[data-test=rdv-prep-when]").text()).toMatch(/, 9 h 30$/);
    expect(sheet.text()).toContain("ORP Renens");
    expect(wrapper.get("[data-test=rdv-prep-questions] h3").text()).toBe("Tes questions au conseiller");
    expect(wrapper.get("[data-test=rdv-pdf]").text()).toContain("Ouvrir la feuille (PDF)");
    await wrapper.get("[data-test=rdv-question-intermediate]").setValue(true);
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/questions", {
      body: { questions: [PREP.questions[0], { ...PREP.questions[1], checked: true }] },
    });
    expect(wrapper.get("[data-test=rdv-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf");
  });

  it("une seule action dans la carte : « Préparer le rendez-vous », plus de « Voir ma feuille » (PR 7)", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [PAST], target: 10, trainings: [] });
    const { wrapper } = await open();
    const orp = wrapper.get("[data-test=rdv-orp]");
    // Le menu « Plus d'actions » (modifier, annuler) reste une icône dans le coin.
    expect(orp.findAll("button").map((b) => b.text()).filter(Boolean)).toEqual(["Préparer le rendez-vous"]);
    expect(orp.get("[data-test=rdv-prep-open]").attributes("aria-haspopup")).toBe("dialog");
    expect(wrapper.find("[data-test=rdv-sheet]").exists()).toBe(false);
    expect(orp.find("[data-test=rdv-ready]").exists()).toBe(true);
  });

  it("aucun rendez-vous : la carte « Aucun rendez-vous à venir » et « Ajouter », sans personnage (PR 28)", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-past]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(false);
    expect(wrapper.get("[data-test=meeting-empty]").text()).toContain("Aucun rendez-vous à venir");
    expect(wrapper.find("[data-test=meeting-person]").exists()).toBe(false);
    await wrapper.get("[data-test=meeting-add]").trigger("click");
    expect(wrapper.find("[data-test=new-meeting] [data-test=new-meeting-form]").exists()).toBe(true);
  });

  it("un entretien sans rendez-vous ORP : l’entretien à venir, puis le formulaire du rendez-vous", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] }, [interview(8, "2099-11-08T13:00:00Z")]);
    const { wrapper } = await open();
    expect(wrapper.get("[data-test=rdv-upcoming] h2").text()).toBe("À venir1 rendez-vous");
    expect(wrapper.find("[data-test=meeting-add]").exists()).toBe(true);
  });

  it("le lieu ou lien de l’entretien, quand il est saisi, remplace l’adresse de l’entreprise", async () => {
    const link = "https://meet.example.ch/entretien-7-avec-un-lien-tres-long";
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] }, [
      { ...interview(7, "2099-11-16T09:00:00Z"), interview_place: link },
    ]);
    const { wrapper } = await open();
    const card = wrapper.get("[data-test=rdv-interview-7]");
    expect(card.get("[data-test=rdv-place]").text()).toBe(link);
    expect(card.text()).not.toContain("Avenue de la Gare 12");
  });

  it("le rendez-vous passé : « À noter », la feuille « Ce qui a été convenu »", async () => {
    const started = { ...MEETING, starts_at: "2026-10-13T08:00:00Z" };
    serve({ meeting: started, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-to-note]").exists()).toBe(true);
    expect(wrapper.findComponent({ name: "OrpOutcomeSheet" }).props("meeting")).toBeNull();
    await wrapper.get("[data-test=rdv-note]").trigger("click");
    expect(wrapper.findComponent({ name: "OrpOutcomeSheet" }).props("meeting")).toMatchObject({ id: 1 });
  });

  it("pas encore de candidature : l’écran d’avant", async () => {
    serve({ meeting: null, preparation: { ...PREP, has_applications: false }, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=sheet-none-yet]").exists()).toBe(true);
  });
});
