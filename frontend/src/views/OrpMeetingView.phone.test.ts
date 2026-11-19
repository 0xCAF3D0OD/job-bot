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
  const wrapper = mount(OrpMeetingView, { global: { plugins: [router], stubs: { InterviewPreparation: true, teleport: true } } });
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
    // Deux lignes (demande de Kevin du 16.11) : le titre et « Feuille prête », puis l'heure, le délai et le lieu.
    expect(orp.get(".rdv-line").text()).toBe("Rendez-vous ORP Feuille prête");
    expect(orp.get(".rdv-meta").text()).toMatch(/^9 h 30 · dans \d+ jours\s·\sORP Renens$/);
    // Ni « Dans N jours » au-dessus du titre, ni rangée de pastilles à part (§39 du 16.11).
    expect(orp.find(".rdv-kicker").exists()).toBe(false);
    expect(orp.findAll(".rdv-body > *")).toHaveLength(2);
    // Toute la carte ouvre la feuille avec « Où tu en es » ; son nom dit titre, pastille, date, heure et délai.
    expect(orp.get("[data-test=rdv-prep-open]").attributes("aria-label")).toMatch(
      /^Rendez-vous ORP, feuille prête, mardi 10 novembre à 9 h 30, dans \d+ jours, ORP Renens$/,
    );
    expect(orp.find("[data-test=rdv-pdf]").exists()).toBe(false);
    // §46 du 17.11 : une page entière, la flèche « Retour » à la place de la croix.
    const prep = wrapper.get("[data-test=rdv-prep-sheet]");
    expect(prep.classes()).toContain("sheet-full");
    expect(prep.get("[data-test=sheet-close]").attributes("aria-label")).toBe("Retour");
    expect(wrapper.findAll("[data-test=rdv-prep-lines] li").map((li) => li.text())).toEqual([
      "Ton mois6 recherches sur 10",
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

  it("« Feuille prête » seulement avec au moins une ligne ; sinon « Feuille à compléter »", async () => {
    const empty = { ...PREP, blockers: [], missing: [], months: [] };
    serve({ meeting: MEETING, preparation: empty, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-prep-lines]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-ready]").exists()).toBe(false);
    expect(wrapper.get("[data-test=rdv-todo]").text()).toBe("Feuille à compléter");

    serve({ meeting: MEETING, preparation: { ...empty, blockers: ["Aucune réponse."] }, past: [], target: 10, trainings: [] });
    const again = await open();
    expect(again.wrapper.get("[data-test=rdv-ready]").text()).toBe("Feuille prête");
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
    expect(sheet.text()).toContain("Mardi 10 novembre, 9 h 30 · ORP Renens");
    expect(wrapper.get("[data-test=rdv-prep-questions] h3").text()).toBe("Tes questions au conseiller · 1 cochée");
    await wrapper.get("[data-test=rdv-question-intermediate]").setValue(true);
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/questions", {
      body: { questions: [PREP.questions[0], { ...PREP.questions[1], checked: true }] },
    });
    expect(wrapper.get("[data-test=rdv-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf");
  });

  describe("« + Ajouter une question » (Kevin, 18.11)", () => {
    const OWN = { key: "custom:1", text: "Combien de recherches en décembre ?", checked: false };
    function serveWith(questions: object[]): void {
      serve({ meeting: MEETING, preparation: { ...PREP, questions }, past: [], target: 10, trainings: [] });
      PUT.mockImplementation((_path: string, { body }: { body: { questions: object[] } }) =>
        Promise.resolve({ data: { meeting: MEETING, preparation: { ...PREP, questions: body.questions }, past: [], target: 10, trainings: [] } }),
      );
    }
    async function openPrep() {
      const opened = await open();
      await opened.wrapper.get("[data-test=rdv-prep-open]").trigger("click");
      return opened;
    }
    const sent = (): { key: string; text: string; checked: boolean }[] => PUT.mock.calls.at(-1)?.[1].body.questions;

    it("un toucher ouvre un champ en bas ; Entrée l’enregistre non cochée, puis « Enregistré »", async () => {
      serveWith(PREP.questions);
      const { wrapper } = await openPrep();
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      expect(wrapper.find("[data-test=rdv-question-add]").exists()).toBe(false);
      const field = wrapper.get("[data-test=rdv-question-field]");
      await field.setValue("  Puis-je suivre un cours en janvier ?  ");
      await field.trigger("keydown", { key: "Enter" });
      await field.trigger("blur");
      await flushPromises();
      expect(sent()).toHaveLength(3);
      expect(sent()[2]).toMatchObject({ text: "Puis-je suivre un cours en janvier ?", checked: false });
      expect(sent()[2]!.key).toMatch(/^custom:/);
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).toContain("Puis-je suivre un cours en janvier ?");
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).toContain("Enregistré");
      expect(wrapper.find("[data-test=rdv-question-add]").exists()).toBe(true);
    });

    it("vide, la ligne disparaît ; Échap annule ; rien ne part au serveur", async () => {
      serveWith(PREP.questions);
      const { wrapper } = await openPrep();
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      await wrapper.get("[data-test=rdv-question-field]").trigger("blur");
      expect(wrapper.find("[data-test=rdv-question-field]").exists()).toBe(false);
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      const field = wrapper.get("[data-test=rdv-question-field]");
      await field.setValue("Brouillon");
      await field.trigger("keydown", { key: "Escape" });
      await field.trigger("blur");
      await flushPromises();
      expect(wrapper.find("[data-test=rdv-question-field]").exists()).toBe(false);
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).not.toContain("Brouillon");
      expect(PUT).not.toHaveBeenCalled();
    });

    it("« ⋯ › Modifier » ouvre le champ d’une question à toi ; toucher le texte la coche ; les proposées n’ont que « Retirer »", async () => {
      serveWith([...PREP.questions, OWN]);
      const { wrapper } = await openPrep();
      expect(wrapper.find("[data-test=rdv-question-edit-intermediate]").exists()).toBe(false);
      await wrapper.get("[data-test=rdv-question-more-intermediate]").trigger("click");
      expect(wrapper.find("[data-test=rdv-question-retire-intermediate]").exists()).toBe(true);
      expect(wrapper.find("[data-test=rdv-question-edit-intermediate]").exists()).toBe(false);
      expect(wrapper.find("[data-test=rdv-question-delete-intermediate]").exists()).toBe(false);
      await wrapper.get("[data-test='rdv-question-custom:1']").setValue(true);
      expect(PUT).toHaveBeenCalledTimes(1);
      expect(sent()[2]).toMatchObject({ key: "custom:1", checked: true });
      await wrapper.get("[data-test='rdv-question-more-custom:1']").trigger("click");
      await wrapper.get("[data-test='rdv-question-edit-custom:1']").trigger("click");
      const field = wrapper.get("[data-test=rdv-question-field]");
      expect((field.element as HTMLInputElement).value).toBe(OWN.text);
      await field.setValue("Combien de recherches en janvier ?");
      await field.trigger("blur");
      await flushPromises();
      expect(sent()).toEqual([...PREP.questions, { ...OWN, checked: true, text: "Combien de recherches en janvier ?" }]);
    });

    it("échec : « Pas enregistré · Réessayer », le texte reste dans le champ", async () => {
      serveWith(PREP.questions);
      PUT.mockResolvedValueOnce({ error: { detail: "nope" } });
      const { wrapper } = await openPrep();
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      await wrapper.get("[data-test=rdv-question-field]").setValue("Ma question");
      await wrapper.get("[data-test=rdv-question-field]").trigger("blur");
      await flushPromises();
      expect((wrapper.get("[data-test=rdv-question-field]").element as HTMLInputElement).value).toBe("Ma question");
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).toContain("Pas enregistré");
      await wrapper.get("[data-test=rdv-prep-questions] [data-test=field-save-retry]").trigger("click");
      await flushPromises();
      expect(PUT).toHaveBeenCalledTimes(2);
      expect(wrapper.find("[data-test=rdv-question-field]").exists()).toBe(false);
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).toContain("Enregistré");
    });

    it("pendant la saisie : « Annuler » et « Ajouter » sous le champ, plus de « + Ajouter une question »", async () => {
      serveWith(PREP.questions);
      const { wrapper } = await openPrep();
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      expect(wrapper.find("[data-test=rdv-question-add]").exists()).toBe(false);
      expect(wrapper.get("[data-test=rdv-prep-questions]").text()).not.toContain("Entrée pour");
      await wrapper.get("[data-test=rdv-question-field]").setValue("Brouillon");
      await wrapper.get("[data-test=rdv-question-cancel]").trigger("pointerdown");
      await wrapper.get("[data-test=rdv-question-field]").trigger("blur");
      await wrapper.get("[data-test=rdv-question-cancel]").trigger("click");
      await flushPromises();
      expect(PUT).not.toHaveBeenCalled();
      expect(wrapper.find("[data-test=rdv-question-field]").exists()).toBe(false);
      await wrapper.get("[data-test=rdv-question-add]").trigger("click");
      await wrapper.get("[data-test=rdv-question-field]").setValue("Ma question");
      await wrapper.get("[data-test=rdv-question-submit]").trigger("click");
      await flushPromises();
      expect(PUT).toHaveBeenCalledTimes(1);
      expect(sent()[2]).toMatchObject({ text: "Ma question", checked: false });
    });

    it("« ⋯ › Retirer » une question proposée : « Question retirée » 5 s, puis le serveur la garde comme retirée", async () => {
      vi.useFakeTimers();
      try {
        serveWith(PREP.questions);
        const { wrapper } = await openPrep();
        await wrapper.get("[data-test=rdv-question-more-intermediate]").trigger("click");
        await wrapper.get("[data-test=rdv-question-retire-intermediate]").trigger("click");
        expect(wrapper.find("[data-test=rdv-question-intermediate]").exists()).toBe(false);
        expect(wrapper.get("[data-test=triage-toast]").text()).toContain("Question retirée");
        await vi.advanceTimersByTimeAsync(4900);
        expect(PUT).not.toHaveBeenCalled();
        await vi.advanceTimersByTimeAsync(200);
        await flushPromises();
        expect(sent()).toEqual([PREP.questions[0], { ...PREP.questions[1], checked: false, removed: true }]);
      } finally {
        vi.useRealTimers();
      }
    });

    it("« ⋯ › Supprimer » cache la ligne, « Annuler » la remet ; sans annuler, la liste part sans elle", async () => {
      vi.useFakeTimers();
      try {
        serveWith([...PREP.questions, OWN]);
        const { wrapper } = await openPrep();
        await wrapper.get("[data-test='rdv-question-more-custom:1']").trigger("click");
        await wrapper.get("[data-test='rdv-question-delete-custom:1']").trigger("click");
        expect(wrapper.get("[data-test=rdv-prep-questions]").text()).not.toContain(OWN.text);
        expect(wrapper.get("[data-test=triage-toast]").text()).toContain("Question supprimée");
        await wrapper.get("[data-test=undo]").trigger("click");
        await flushPromises();
        expect(wrapper.get("[data-test=rdv-prep-questions]").text()).toContain(OWN.text);
        expect(PUT).not.toHaveBeenCalled();
        await wrapper.get("[data-test='rdv-question-more-custom:1']").trigger("click");
        await wrapper.get("[data-test='rdv-question-delete-custom:1']").trigger("click");
        await vi.advanceTimersByTimeAsync(6000);
        await flushPromises();
        expect(sent()).toEqual(PREP.questions);
        expect(wrapper.get("[data-test=rdv-prep-questions]").text()).not.toContain(OWN.text);
      } finally {
        vi.useRealTimers();
      }
    });
  });

  it("« Ton nom sur la feuille » (§70) : ouverte depuis la préparation, trois champs gardés dans le compte, Retour y ramène", async () => {
    const page = { meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] };
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/orp-meeting/nom"
          ? { data: { name: "Camille Exemple", advisor: "M. Favre", office: null } }
          : path === "/api/orp-meeting" ? { data: page } : { data: [] },
      ),
    );
    PUT.mockResolvedValue({ data: { name: "Camille Exemple", advisor: "M. Favre", office: "ORP Lausanne" } });
    const { wrapper } = await open();
    await wrapper.get("[data-test=rdv-prep-open]").trigger("click");
    await wrapper.get("[data-test=rdv-name]").trigger("click");
    // La page est chargée à la première ouverture.
    await vi.waitFor(() => expect(wrapper.find("[data-test=feuille-nom]").exists()).toBe(true));
    await flushPromises();
    const prep = wrapper.findComponent({ name: "MeetingPrepSheet" });
    const name = wrapper.findComponent({ name: "FeuilleNomSheet" });
    expect(name.props("open")).toBe(true);
    // Une seule page à la fois : la préparation laisse la place.
    expect(prep.props("open")).toBe(false);
    // §72g (Kevin, 18.11) : plus de phrase « Tout est enregistré… » sous le titre.
    expect(name.text()).not.toContain("Tout est enregistré");
    expect(name.findAll("label").map((l) => l.text())).toEqual(["Prénom et nom", "Ton conseiller ORP", "Office régional"]);
    expect((name.get("[data-test=feuille-nom-name]").element as HTMLInputElement).value).toBe("Camille Exemple");
    expect((name.get("[data-test=feuille-nom-advisor]").element as HTMLInputElement).value).toBe("M. Favre");
    await name.get("[data-test=feuille-nom-office]").setValue("ORP Lausanne");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/nom", { body: { office: "ORP Lausanne" } });
    expect(name.findAll("[data-test=field-save]").map((s) => s.text())).toEqual(["", "", "Enregistré"]);
    // Retour : la préparation revient.
    await name.get(".sheet-close").trigger("click");
    await flushPromises();
    expect(prep.props("open")).toBe(true);
    expect(name.props("open")).toBe(false);
    // La ligne de la préparation suit ce qui est enregistré : nom · office.
    expect(wrapper.get("[data-test=rdv-name-line]").text()).toBe("Camille Exemple · ORP Lausanne");
  });

  it("carte « La feuille » (planche PreparerRendezVous, §71) : nom · office, « Voir la feuille » remplace la préparation", async () => {
    const page = { meeting: MEETING, preparation: PREP, past: [], target: 10, trainings: [] };
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/orp-meeting/nom"
          ? { data: { name: "Camille Exemple", advisor: null, office: "ORP Renens" } }
          : path === "/api/orp-meeting" ? { data: page } : { data: [] },
      ),
    );
    const { wrapper, router } = await open();
    await wrapper.get("[data-test=rdv-prep-open]").trigger("click");
    const prep = wrapper.findComponent({ name: "MeetingPrepSheet" });
    expect(prep.findAll(".prep-title").map((t) => t.text())).toContain("La feuille");
    expect(wrapper.get("[data-test=rdv-name-line]").text()).toBe("Camille Exemple · ORP Renens");
    expect(wrapper.get("[data-test=rdv-view-sheet]").text()).toContain("1 question");
    const replace = vi.spyOn(router, "replace");
    await wrapper.get("[data-test=rdv-view-sheet]").trigger("click");
    await flushPromises();
    expect(replace).toHaveBeenCalledWith({ query: { feuille: "1" } });
    expect(router.currentRoute.value.query.feuille).toBe("1");
  });

  it("une seule action dans la carte : « Préparer le rendez-vous », plus de « Voir ma feuille » (PR 7)", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [PAST], target: 10, trainings: [] });
    const { wrapper } = await open();
    const orp = wrapper.get("[data-test=rdv-orp]");
    // Le menu « Plus d'actions » (modifier, annuler) reste une icône dans le coin.
    expect(orp.findAll("button").map((b) => b.attributes("data-test")).filter((t) => t !== "rdv-more")).toEqual(["rdv-prep-open"]);
    expect(orp.get("[data-test=rdv-prep-open]").attributes("aria-haspopup")).toBe("dialog");
    expect(wrapper.find("[data-test=rdv-sheet]").exists()).toBe(false);
    expect(orp.find("[data-test=rdv-ready]").exists()).toBe(true);
  });

  it("aucun rendez-vous (RendezVousVide, §13 du 15 novembre) : l’état vide, « Ajouter un rendez-vous » ouvre le panneau", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=rdv-past]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-empty]").exists()).toBe(false);
    const empty = wrapper.get("[data-test=rdv-none-yet]");
    expect(empty.find("h2").text()).toBe("Aucun rendez-vous");
    expect(empty.get("[data-test=empty-pill]").text()).toBe("jobA1 prépare ta feuille la veille");
    // Rien encore : pas de recherche (§13).
    expect(wrapper.find(".rdv-search").exists()).toBe(false);
    await empty.get("[data-test=rdv-none-add]").trigger("click");
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
    expect(card.get(".rdv-meta").text()).toMatch(new RegExp(` · ${link.replace(/[.]/g, "\\.")}$`));
    // L'heure et le délai, à part : jamais coupés.
    expect(card.get(".rdv-when > span").text()).toMatch(/^\d+ h · dans \d+ jours$/);
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

  it("pas encore de candidature : l’état vide, puis le formulaire sur place après le bouton", async () => {
    serve({ meeting: null, preparation: { ...PREP, has_applications: false }, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-upcoming]").exists()).toBe(false);
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(false);
    await wrapper.get("[data-test=rdv-none-add]").trigger("click");
    expect(wrapper.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(wrapper.find("[data-test=sheet-none-yet]").exists()).toBe(true);
  });
});
