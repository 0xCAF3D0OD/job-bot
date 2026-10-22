// La formule (docs/125 §4) : la carte de Réglages › Compte, les descriptions au survol, la limite.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { usePlan } from "../composables/usePlan";
import PlanLimit from "./PlanLimit.vue";
import PlanPanel from "./PlanPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) } }));
afterEach(() => vi.resetAllMocks());

const LIMITS = {
  essentiel: { score: 150, letter: 10, cv: 10, chat: 30, practice: 1 },
  plus: { score: 600, letter: 60, cv: 60, chat: 300, practice: 8 },
};

function plan(over: Record<string, unknown> = {}, letters = 2) {
  return {
    plan: "essentiel",
    unlimited: false,
    resets_on: "2026-11-01",
    plus_price_chf: 7,
    limits: LIMITS,
    billing_available: false,
    plan_until: null,
    cancelled: false,
    payments: [],
    usage: [
      { key: "score", label: "offres notées", used: 37, limit: 150, limit_text: "Les 150 offres notées du mois sont utilisées : elles reviennent le 1er novembre." },
      { key: "letter", label: "lettres", used: letters, limit: 10, limit_text: "Les 10 lettres du mois sont utilisées : elles reviennent le 1er novembre." },
      { key: "cv", label: "CV adaptés", used: 0, limit: 10, limit_text: "x" },
      { key: "chat", label: "messages à l'assistant", used: 3, limit: 30, limit_text: "x" },
      { key: "practice", label: "entraînements à l'entretien", used: 0, limit: 1, limit_text: "x" },
    ],
    ...over,
  };
}

const router = () => createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

describe("la formule", () => {
  it("Essentiel : une ligne par usage, quand ça repart, ce que Plus ajoute", async () => {
    GET.mockResolvedValue({ data: plan() });
    await usePlan().refresh();
    const wrapper = mount(PlanPanel, { global: { plugins: [router()] } });
    await flushPromises();
    expect(wrapper.find("[data-test=plan-name]").text()).toContain("Essentiel, gratuite");
    expect(wrapper.find("[data-test=plan-score]").text()).toBe("Offres notées37 sur 150");
    expect(wrapper.find("[data-test=plan-letter] .plan-usage-gauge").attributes("style")).toContain("--p: 20");
    expect(wrapper.find("[data-test=plan-resets]").text()).toBe("Les compteurs repartent le 1er novembre.");
    expect(wrapper.find("[data-test=plan-plus]").text()).toContain("Plus · 7 CHF par mois");
    expect(wrapper.find("[data-test=plan-plus]").text()).toContain("60 lettres");
    // Le paiement pas encore ouvert : pas de bouton.
    expect(wrapper.find("[data-test=plan-plus]").text()).toContain("Le paiement arrive bientôt.");
    expect(wrapper.find("[data-test=plan-buy]").exists()).toBe(false);
  });

  it("les descriptions au survol : le compteur pour une personne invitée, le coût pour l'exploitant", async () => {
    GET.mockResolvedValue({ data: plan() });
    const { refresh, aiNote } = usePlan();
    await refresh();
    expect(aiNote("Environ 0,10 $.", "letter")).toBe("Lettres : 2 sur 10 ce mois-ci.");
    expect(aiNote("Environ 0,002 $.")).toBe("");
    expect(aiNote("Environ 0,003 $.", undefined, "L'offre est renotée.")).toBe("L'offre est renotée.");
    GET.mockResolvedValue({ data: plan({ unlimited: true }) });
    await refresh();
    expect(aiNote("Environ 0,10 $.", "letter")).toBe("Environ 0,10 $.");
  });

  it("à la limite : la ligne grise dit pourquoi et mène à la formule ; rien avant", async () => {
    GET.mockResolvedValue({ data: plan({}, 9) });
    await usePlan().refresh();
    const before = mount(PlanLimit, { props: { usage: "letter" }, global: { plugins: [router()] } });
    expect(before.find("[data-test=plan-limit-letter]").exists()).toBe(false);
    GET.mockResolvedValue({ data: plan({}, 10) });
    await usePlan().refresh();
    const line = mount(PlanLimit, { props: { usage: "letter" }, global: { plugins: [router()] } }).find("[data-test=plan-limit-letter]");
    expect(line.text()).toContain("Les 10 lettres du mois sont utilisées : elles reviennent le 1er novembre.");
    expect(line.find("a").attributes("href")).toBe("/reglages?rubrique=compte");
  });

  it("l'exploitant n'a pas de carte Formule", async () => {
    GET.mockResolvedValue({ data: plan({ unlimited: true }) });
    await usePlan().refresh();
    const wrapper = mount(PlanPanel, { global: { plugins: [router()] } });
    expect(wrapper.find("[data-test=plan-panel]").exists()).toBe(false);
  });
});

describe("le paiement de Plus (docs/125 §6)", () => {
  it("les conditions acceptées d'abord, puis la page de Payrexx", async () => {
    GET.mockResolvedValue({ data: plan({ billing_available: true }) });
    POST.mockResolvedValue({ data: { link: "https://jobA1.payrexx.com/?payment=abc" } });
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    await usePlan().refresh();
    const wrapper = mount(PlanPanel, { global: { plugins: [router()] } });
    await flushPromises();
    const buy = wrapper.find("[data-test=plan-buy]");
    expect(buy.text()).toBe("Passer à Plus");
    expect(buy.attributes("disabled")).toBeDefined();
    expect(wrapper.find(".plan-terms a").attributes("href")).toBe("/conditions");
    await wrapper.find("[data-test=plan-accept]").setValue(true);
    await buy.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/billing/checkout", { body: { accept_terms: true } });
    expect(assign).toHaveBeenCalledWith("https://jobA1.payrexx.com/?payment=abc");
    vi.unstubAllGlobals();
  });

  it("au retour, la confirmation demandée au serveur ; puis la date de fin et résilier", async () => {
    GET.mockResolvedValue({ data: plan({ plan: "plus", plan_until: "2026-11-25", billing_available: true, payments: [{ paid_on: "2026-10-22", amount_cents: 700, currency: "CHF" }] }) });
    POST.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/billing/sync" ? { confirmed: true, plan_until: "2026-11-25" } : { confirmed: false, plan_until: "2026-11-25" } }),
    );
    await usePlan().refresh();
    const r = router();
    await r.push("/reglages?rubrique=compte&paiement=ok");
    const wrapper = mount(PlanPanel, { global: { plugins: [r] } });
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/billing/sync");
    expect(wrapper.find("[data-test=plan-message]").text()).toBe("Merci : Plus est actif jusqu'au 25 novembre.");
    expect(r.currentRoute.value.query.paiement).toBeUndefined();
    expect(wrapper.find("[data-test=plan-paid]").text()).toBe("Plus jusqu'au 25 novembre, renouvelé chaque mois.");
    expect(wrapper.find("[data-test=plan-payments]").text()).toContain("22 octobre 2026");
    expect(wrapper.find("[data-test=plan-payments]").text()).toContain("7,00 CHF");
    await wrapper.find("[data-test=plan-cancel]").trigger("click");
    expect(wrapper.text()).toContain("Résilier Plus ? Il reste actif jusqu'au 25 novembre, sans nouveau paiement.");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/billing/cancel");
  });

  it("un paiement annulé : rien n'a été débité", async () => {
    GET.mockResolvedValue({ data: plan({ billing_available: true }) });
    await usePlan().refresh();
    const r = router();
    await r.push("/reglages?rubrique=compte&paiement=annule");
    const wrapper = mount(PlanPanel, { global: { plugins: [r] } });
    await flushPromises();
    expect(wrapper.find("[data-test=plan-message]").text()).toBe("Paiement annulé : rien n'a été débité.");
    expect(POST).not.toHaveBeenCalled();
  });
});
