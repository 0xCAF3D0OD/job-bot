import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { resetCvReading } from "../composables/useCvReading";
import TodayView from "./TodayView.vue";

// La veille de rendez-vous par-dessus Aujourd'hui (lot du 11 novembre au soir, PR 52 ; maquette
// RendezVousFeuilleOrdinateurV2).
const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn() }, QUIET: {} }));
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone: ref(false) }) }));
afterEach(() => {
  vi.resetAllMocks();
  resetCvReading();
  localStorage.clear();
});

const DAY = {
  first_steps: ["profile", "alerts", "keep", "prepare", "sent"].map((key) => ({ key, done: true })),
  first_steps_dismissed: false,
  has_offers: true,
  to_review: 0,
  month: "2026-11",
  month_count: 7,
  month_target: 10,
  to_follow_up: 0,
  week: [],
  orp_history: [],
  orp_meeting_at: "2026-11-12T09:30:00+01:00",
};
const QUESTIONS = [
  { key: "training", text: "Financer la formation Terraform", checked: true },
  { key: "intermediate", text: "Déclarer mon gain intermédiaire", checked: false },
];
const PAGE = {
  meeting: { id: 1, starts_at: "2026-11-12T09:30:00+01:00", place: "ORP Renens", measures: [] },
  preparation: { summaries: [], works: null, blockers: ["Formulaires en ligne : 0 réponse sur 9."], missing: [], offers: 0, questions: QUESTIONS, obligations: [], has_applications: true, months: [{ month: "2026-11", count: 7, target: 10, answered: 0, interviews: 0 }] },
  past: [],
  target: 10,
  trainings: [],
};

async function mountView(page: unknown) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/today" ? DAY : path === "/api/orp-meeting" ? page : path === "/api/documents" ? [] : path === "/api/insights" ? { highlight: null } : { items: [] } }),
  );
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/candidatures/trier", name: "triage", component: { template: "<div />" } }, { path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(TodayView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}
async function openEve(wrapper: Awaited<ReturnType<typeof mountView>>["wrapper"]) {
  await wrapper.get("[data-test=orp-meeting-soon]").trigger("click");
  await vi.dynamicImportSettled();
  await flushPromises();
}

describe("Veille de rendez-vous sur ordinateur (PR 52)", () => {
  it("« Préparer le rendez-vous ORP » ouvre l’écran en panneau, sans quitter Aujourd’hui", async () => {
    const { wrapper, router } = await mountView(PAGE);
    const task = wrapper.get("[data-test=orp-meeting-soon]");
    expect(task.attributes("aria-haspopup")).toBe("dialog");
    await openEve(wrapper);
    expect(router.currentRoute.value.path).toBe("/");
    expect(wrapper.findComponent({ name: "BottomSheet" }).props()).toMatchObject({ title: "Rendez-vous ORP", screen: true, open: true });
    expect(wrapper.get("[data-test=rdv-prep-hand]").text()).toBe("ta feuille est prête");
    expect(wrapper.findAll("[data-test=rdv-prep-lines] li").map((li) => li.text())).toEqual(["7 recherches sur 10Ton mois", "Ce qui bloqueFormulaires en ligne : 0 réponse sur 9"]);
    expect(wrapper.get("[data-test=rdv-pdf]").attributes("href")).toBe("/api/orp-meeting/feuille.pdf");
  });

  it("cocher une question l’enregistre", async () => {
    const { wrapper } = await mountView(PAGE);
    PUT.mockResolvedValue({ data: PAGE });
    await openEve(wrapper);
    await wrapper.get("[data-test=rdv-question-intermediate]").setValue(true);
    expect(PUT).toHaveBeenCalledWith("/api/orp-meeting/questions", { body: { questions: [QUESTIONS[0], { ...QUESTIONS[1], checked: true }] } });
  });

  it("sans rendez-vous lisible, la page Rendez-vous s’ouvre comme avant", async () => {
    const { wrapper, router } = await mountView({ ...PAGE, meeting: null });
    await openEve(wrapper);
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/candidatures/rendez-vous-orp");
  });
});
