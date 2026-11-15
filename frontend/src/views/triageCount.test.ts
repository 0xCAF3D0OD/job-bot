// Aujourd'hui et « Trier les offres » lisent la même source et le même filtre (useDailyDose : pickDose,
// isTriagePending) : si Aujourd'hui annonce « Trier N offres », Trier montre N offres, quel que soit le jour.
// Bug du 15 novembre : un dimanche, Aujourd'hui annonçait « Trier 3 offres » et Trier « Jour de repos ».
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import TodayView from "./TodayView.vue";
import TriageView from "./TriageView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: vi.fn(), POST: vi.fn(), PATCH: vi.fn() },
}));

const mounted: VueWrapper[] = [];
afterEach(async () => {
  await useUndo().flush();
  mounted.splice(0).forEach((w) => w.unmount());
  vi.useRealTimers();
  vi.resetAllMocks();
  localStorage.clear();
});

const offer = (id: number, score: number) => ({
  id,
  title: `Offre ${id}`,
  company: "Acme SA",
  location: "Lausanne",
  score,
  description: "",
  snippet: null,
  passages: [],
  strengths: [],
  gaps: [],
  keywords_asks: [],
  links: [],
  first_seen_at: "2026-11-14T08:00:00Z",
});

// `behind` : le mois ORP en retard, la dose passe à 5.
function day(restDay: boolean, behind: boolean) {
  return {
    first_steps: ["profile", "alerts", "keep", "prepare", "sent"].map((key) => ({ key, done: true })),
    first_steps_dismissed: false,
    has_offers: true,
    to_review: 8,
    month: "2026-11",
    month_count: behind ? 0 : 10,
    month_target: 10,
    to_follow_up: 0,
    follow_ups: [],
    week: [],
    orp_history: [],
    rhythm: { target: 3, count: 3, days: [], research_today: !restDay, pause_until: null },
  };
}

function mockApi(restDay: boolean, behind: boolean, offers: unknown[]): void {
  GET.mockImplementation((path: string, init?: { params?: { query?: { view?: string } } }) => {
    if (path === "/api/today") return Promise.resolve({ data: day(restDay, behind) });
    if (path === "/api/identity") return Promise.resolve({ data: { name: "Kevin" } });
    if (path === "/api/offers" && init?.params?.query?.view === "to_review") return Promise.resolve({ data: { items: offers } });
    return Promise.resolve({ data: { items: [] } });
  });
}

async function mountAt(component: unknown) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/aujourdhui", name: "today", component: { template: "<div />" } },
      { path: "/candidatures/trier", name: "triage", component: { template: "<div />" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  const wrapper = mount(component as never, { global: { plugins: [router] }, attachTo: document.body });
  mounted.push(wrapper);
  await flushPromises();
  await vi.dynamicImportSettled();
  await flushPromises();
  return wrapper;
}

// Le dimanche 15 et le mercredi 18 novembre 2026, 10 h.
const SUNDAY = new Date(2026, 10, 15, 10);
const WEDNESDAY = new Date(2026, 10, 18, 10);
const OFFERS = [offer(1, 92), offer(2, 86), offer(3, 80), offer(4, 75), offer(5, 72), offer(6, 70)];

describe("Aujourd’hui et Trier comptent les mêmes offres", () => {
  it.each([
    ["un dimanche (jour de repos)", SUNDAY, true, false, 3],
    ["un mercredi", WEDNESDAY, false, false, 3],
    ["un dimanche, mois ORP en retard", SUNDAY, true, true, 5],
    ["un mercredi, mois ORP en retard", WEDNESDAY, false, true, 5],
  ])("%s : « Trier N offres » sur Aujourd’hui, N offres sur Trier", async (_label, now, restDay, behind, expected) => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(now);
    mockApi(restDay, behind, OFFERS);

    const today = await mountAt(TodayView);
    const task = today.find("[data-test=triage] strong").text();
    const n = Number(task.match(/^Trier (\d+) offres?$/)?.[1]);
    expect(n).toBe(expected);

    const triage = await mountAt(TriageView);
    expect(triage.find("[data-test=triage-empty]").exists()).toBe(false);
    expect(triage.find("[data-test=triage-count]").text()).toBe(`${n} offres pour toi`);
    expect(triage.find("[data-test=triage-offer]").attributes("aria-label")).toBe(`Offre 1 sur ${n}`);
  });

  it("un jour de repos sans offre : Trier dit seulement qu’il n’y a rien à trier, jamais « Jour de repos »", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(SUNDAY);
    mockApi(true, false, []);
    const triage = await mountAt(TriageView);
    const empty = triage.find("[data-test=triage-empty]");
    expect(empty.text()).toContain("Rien à trier");
    expect(triage.text()).not.toContain("Jour de repos");
  });
});
