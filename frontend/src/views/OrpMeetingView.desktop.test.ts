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
  it("deux colonnes : le prochain rendez-vous ORP ouvert, un rendez-vous noté s'ouvre dans ?rdv=", async () => {
    serve({ meeting: MEETING, preparation: PREP, past: [NOTED], target: 10, trainings: [] });
    const { wrapper, router } = await open();
    expect(wrapper.find("[data-test=rdv-desktop]").exists()).toBe(true);
    expect(wrapper.get("[data-test=rdv-item-orp]").attributes("aria-current")).toBe("true");
    expect(wrapper.find("[data-test=rdv-detail-orp]").exists()).toBe(true);
    expect(wrapper.get("[data-test=rdv-last-agreed]").text()).toContain("8 recherches par mois");
    const past = wrapper.get("[data-test=rdv-item-passe-2]");
    expect(past.text()).toContain("Objectif 8 par mois · financement Terraform");
    await past.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.rdv).toBe("passe-2");
    expect(wrapper.find("[data-test=rdv-detail-past]").exists()).toBe(true);
  });

  it("un rendez-vous passé et non noté : « À noter » ouvre le dialogue « Ce qui a été convenu »", async () => {
    const held = { ...MEETING, starts_at: "2026-10-13T08:00:00Z" };
    serve({ meeting: held, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.find("[data-test=rdv-to-note-1]").exists()).toBe(true);
    const sheet = wrapper.findComponent({ name: "OrpOutcomeSheet" });
    expect(sheet.props("meeting")).toBeNull();
    await wrapper.get("[data-test=rdv-note]").trigger("click");
    expect(sheet.props("meeting")).toMatchObject({ id: 1 });
    // Le prochain rendez-vous saisi part avec ce qui a été convenu : le serveur crée l'entrée « À venir ».
    PUT.mockResolvedValue({ data: { meeting: MEETING, preparation: PREP, past: [{ ...held, outcome_at: "2026-10-13T10:00:00Z" }], target: 10, trainings: [] } });
    // Maquette du 8 novembre : la pilule ouvre le sélecteur, qui prend la place du formulaire.
    await sheet.get("[data-test=outcome-next] [data-test=dt-date]").trigger("click");
    expect(sheet.find("[data-test=outcome-form]").exists()).toBe(false);
    sheet.findComponent({ name: "DateTimePanel" }).vm.$emit("confirm", { date: "2099-11-10", time: "09:30" });
    await flushPromises();
    await sheet.get("[data-test=outcome-form]").trigger("submit");
    await flushPromises();
    const [path, options] = PUT.mock.calls[0] as [string, { body: { target: number; next_starts_at: string } }];
    expect(path).toBe("/api/orp-meeting/{meeting_id}/convenu");
    expect(options.body.target).toBe(10);
    expect(options.body.next_starts_at).toBe(new Date("2099-11-10T09:30").toISOString());
    expect(wrapper.find("[data-test=rdv-item-orp]").exists()).toBe(true);
    expect(wrapper.find("[data-test=rdv-to-note-1]").exists()).toBe(false);
  });

  it("aucun rendez-vous : une ligne et « Ajouter » en tête de liste, le formulaire dans le détail, sans personnage", async () => {
    serve({ meeting: null, preparation: PREP, past: [], target: 10, trainings: [] });
    const { wrapper } = await open();
    expect(wrapper.get("[data-test=rdv-list-empty]").text()).toContain("Aucun rendez-vous à venir");
    expect(wrapper.find("[data-test=rdv-add]").text()).toBe("Ajouter");
    const detail = wrapper.get("[data-test=rdv-detail]");
    expect(detail.find("[data-test=meeting-person]").exists()).toBe(false);
    expect(detail.find("[data-test=meeting-form]").exists()).toBe(true);
    expect(detail.find("input[type=date], input[type=time]").exists()).toBe(false);
  });
});
