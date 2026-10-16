import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import WelcomeView from "./WelcomeView.vue";

const GET = vi.fn();
const PUT = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const CRITERIA = {
  locations: [],
  remote_policy: "refuse",
  min_rate: null,
  excluded_types: [],
  banned_words: [],
  unspoken_languages: [],
};
const SETTINGS = {
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 5,
  orp_due_day: 5,
  employer_search_threshold: 70,
};

type State = { status: string; step: number; goal: string | null; trade: string | null };

async function mountWelcome(state: State = { status: "pending", step: 1, goal: null, trade: null }) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/welcome"
          ? state
          : path === "/api/criteria"
            ? { criteria: CRITERIA, keywords: {}, saved_at: null }
            : path === "/api/settings"
              ? SETTINGS
              : { configured: false, server: "https://ntfy.sh", personal: true, topic: null },
    }),
  );
  PUT.mockImplementation((path: string, options: { body: Record<string, unknown> }) =>
    Promise.resolve({
      data:
        path === "/api/criteria"
          ? { criteria: { ...CRITERIA, ...options.body } }
          : path === "/api/settings"
            ? { ...SETTINGS, ...options.body }
            : path === "/api/notifications/phone"
              ? { configured: false, server: "https://ntfy.sh", personal: true, topic: null }
              : {},
    }),
  );
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }],
  });
  await router.push("/bienvenue");
  const wrapper = mount(WelcomeView, {
    global: { plugins: [router], stubs: { Illustration: true } },
  });
  await flushPromises();
  return { wrapper, router };
}

function calls(path: string): Record<string, unknown>[] {
  return PUT.mock.calls.filter((c) => c[0] === path).map((c) => (c[1] as { body: Record<string, unknown> }).body);
}

describe("l'accueil, façon Duolingo (docs/66)", () => {
  it("une question par écran ; chaque réponse remplit un vrai réglage", async () => {
    const { wrapper, router } = await mountWelcome();
    expect(wrapper.find("[data-test=welcome-goal]").exists()).toBe(true);

    await wrapper.find("[data-test=goal-orp]").trigger("click");
    await flushPromises();
    expect(calls("/api/welcome")).toContainEqual(expect.objectContaining({ goal: "orp" }));

    await wrapper.find("[data-test=trade-input]").setValue("Infirmière");
    await wrapper.find("[data-test=welcome-continue]").trigger("click");
    await flushPromises();
    expect(calls("/api/welcome")).toContainEqual(expect.objectContaining({ trade: "Infirmière" }));

    await wrapper.find("[data-test=place-VD]").trigger("click");
    await wrapper.find("[data-test=place-GE]").trigger("click");
    await wrapper.find("[data-test=welcome-continue]").trigger("click");
    await flushPromises();
    expect(calls("/api/criteria").at(-1)?.locations).toEqual(["VD", "GE"]);

    await wrapper.find("[data-test=rate-80]").trigger("click");
    await flushPromises();
    expect(calls("/api/criteria").at(-1)).toMatchObject({ locations: ["VD", "GE"], min_rate: 80 });

    // ORP seulement parce que le premier écran l'a dit.
    await wrapper.find("[data-test=target-10]").trigger("click");
    await wrapper.find("[data-test=welcome-continue]").trigger("click");
    await flushPromises();
    expect(calls("/api/settings").at(-1)).toMatchObject({ orp_monthly_target: 10, orp_due_day: 5 });

    expect(wrapper.find("[data-test=welcome-cv]").exists()).toBe(true);
    await wrapper.find("[data-test=welcome-skip]").trigger("click");
    await flushPromises();

    await wrapper.find("[data-test=phone-no]").trigger("click");
    await flushPromises();
    expect(calls("/api/notifications/phone")).toEqual([{ enabled: false }]);

    const recap = wrapper.find("[data-test=welcome-recap]").text();
    expect(recap).toContain("Infirmière");
    expect(recap).toContain("Vaud, Genève");
    expect(recap).toContain("10 recherches par mois");
    await wrapper.find("[data-test=welcome-alerts]").trigger("click");
    await flushPromises();
    expect(calls("/api/welcome").at(-1)).toEqual({ done: true, postponed: false });
    expect(router.currentRoute.value.path).toBe("/candidatures/alertes");
  });

  it("sans ORP, pas de question sur l'ORP ; « Plus tard » mène à Aujourd'hui", async () => {
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 4, goal: "job", trade: "DevOps" });
    // Reprise à l'écran atteint : le taux d'activité.
    expect(wrapper.find("[data-test=welcome-rate]").exists()).toBe(true);
    await wrapper.find("[data-test=rate-any]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=welcome-cv]").exists()).toBe(true);
    await wrapper.find("[data-test=welcome-later]").trigger("click");
    await flushPromises();
    expect(calls("/api/welcome")).toContainEqual({ postponed: true });
    expect(router.currentRoute.value.path).toBe("/aujourdhui");
  });
});
