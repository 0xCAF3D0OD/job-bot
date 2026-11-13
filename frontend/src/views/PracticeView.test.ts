// S'entraîner pour l'entretien, en page (docs/75 ; récapitulatif du 11 novembre, PR 42 ; maquettes Entrainement).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { reactive, ref } from "vue";

import { useFocusMode } from "../composables/useFocusMode";
import PracticeView from "./PracticeView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: vi.fn(() => Promise.resolve({})),
  },
}));
const route = reactive<{ params: Record<string, string>; query: Record<string, string> }>({ params: {}, query: {} });
const push = vi.fn();
const back = vi.fn();
const replace = vi.fn((to: { query: Record<string, string> }) => {
  route.query = to.query;
  return Promise.resolve();
});
vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => ({ push: (...a: unknown[]) => push(...a), back: () => back(), replace: (to: { query: Record<string, string> }) => replace(to) }),
}));
const phone = ref(false);
vi.mock("../composables/usePhone", () => ({ usePhone: () => ({ phone }) }));
vi.mock("../composables/usePlan", () => ({ usePlan: () => ({ refresh: vi.fn() }) }));
afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount();
  vi.resetAllMocks();
  replace.mockImplementation((to: { query: Record<string, string> }) => {
    route.query = to.query;
    return Promise.resolve();
  });
  route.params = {};
  route.query = {};
  phone.value = false;
});

function practice(extra: Record<string, unknown> = {}) {
  return {
    id: 5,
    application_id: 3,
    company: "Exemple SA",
    job_title: "Ingénieur DevOps",
    kind: "technique",
    tone: "bienveillant",
    language: "en",
    status: "en_cours",
    question: 1,
    questions: 5,
    waiting: false,
    turns: [{ role: "recruteur", text: "Tell me about yourself.", question: 1, relance: false, skipped: false, tip: "Présent, passé, puis pourquoi ce poste." }],
    feedback: null,
    cost_chf: 0.01,
    created_at: "2026-10-18T10:00:00Z",
    ...extra,
  };
}
const DEFAULTS = {
  kind: "technique",
  language: "en",
  can_practice: true,
  language_from_offer: true,
  company: "Exemple SA",
  job_title: "Ingénieur DevOps",
  interview_at: "2026-11-19T13:00:00Z",
};
const stubs = { MoreMenu: { props: ["items"], template: "<div data-test=\"more\"><button v-for=\"i in items\" :key=\"i.test\" :data-test=\"i.test\" @click=\"i.run()\">{{ i.label }}</button></div>" } };
const mounted: { unmount: () => void }[] = [];
function mountView() {
  const wrapper = mount(PracticeView, { global: { stubs } });
  mounted.push(wrapper);
  return wrapper;
}

describe("PracticeView", () => {
  it("les réglages : titre, poste · entreprise · date, un choix coché par groupe, la phrase d’aide et la langue de l’annonce", async () => {
    route.params = { candidatureId: "3" };
    GET.mockResolvedValue({ data: DEFAULTS });
    const wrapper = mountView();
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/interview-practices/defaults", { params: { query: { application_id: 3 } } });
    expect(wrapper.find("h1").text()).toBe("S’entraîner pour l’entretien");
    expect(wrapper.find("[data-test=practice-back]").text()).toBe("Rendez-vous");
    expect(wrapper.find("[data-test=practice-subtitle]").text()).toBe("Ingénieur DevOps · Exemple SA · jeudi 19 nov., 14 h");
    // Une seule option cochée par groupe, avec une coche (WCAG 1.4.1).
    for (const group of wrapper.findAll("[role=radiogroup]")) {
      const checked = group.findAll("[role=radio][aria-checked=true]");
      expect(checked).toHaveLength(1);
      expect(checked[0]!.find("[data-icon=tick]").exists()).toBe(true);
      expect(group.findAll("[role=radio][aria-checked=false] [data-icon=tick]")).toHaveLength(0);
    }
    expect(wrapper.find("[data-test=practice-kind-technique]").attributes("aria-checked")).toBe("true");
    expect(wrapper.find("[data-test=practice-kind-help]").text()).toBe("Questions sur tes projets et tes outils.");
    await wrapper.find("[data-test=practice-kind-rh]").trigger("click");
    expect(wrapper.find("[data-test=practice-kind-help]").text()).toBe("Questions sur ton parcours, ta motivation et tes attentes.");
    expect(wrapper.find("[data-test=practice-language-note]").text()).toBe("L’annonce est en anglais.");
    expect(wrapper.text()).toContain("5 questions · environ 10 minutes · tu peux en passer une.");
    const start = wrapper.find("[data-test=practice-start]");
    expect(start.text()).toBe("Commencer l’entraînement");
    expect(start.find("svg").exists()).toBe(false);
    // Sur ordinateur, les réglages gardent la navigation.
    expect(useFocusMode().focus.value).toBe(false);
  });

  it("la question : mode concentration, progression, conseil, compteur de mots, Entrée envoie", async () => {
    route.params = { candidatureId: "3" };
    GET.mockResolvedValue({ data: DEFAULTS });
    POST.mockResolvedValueOnce({ data: practice() });
    const wrapper = mountView();
    await flushPromises();
    await wrapper.find("[data-test=practice-tone-exigeant]").trigger("click");
    await wrapper.find("[data-test=practice-start]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interview-practices", {
      body: { application_id: 3, kind: "technique", tone: "exigeant", language: "en" },
    });
    // L'adresse garde la séance, sans ajouter d'entrée à l'historique.
    expect(replace).toHaveBeenCalledWith({ params: { candidatureId: "3" }, query: { seance: "5" } });
    expect(useFocusMode().focus.value).toBe(true);
    expect(wrapper.find("[data-test=practice-progress]").text()).toBe("Question 1 sur 5");
    const bar = wrapper.find("[role=progressbar]");
    expect([bar.attributes("aria-valuenow"), bar.attributes("aria-valuemax"), bar.attributes("aria-label")]).toEqual(["1", "5", "Question 1 sur 5"]);
    expect(bar.findAll("span").map((s) => s.classes("on"))).toEqual([true, false, false, false, false]);
    expect(wrapper.find("[data-test=practice-meta]").text()).toBe("Technique · anglais");
    expect(wrapper.find(".pv-who").text()).toContain("Le recruteur · Exemple SA");
    const question = wrapper.find("[data-test=practice-question-text]");
    expect([question.text(), question.attributes("lang")]).toEqual(["Tell me about yourself.", "en"]);
    const tip = wrapper.find("[data-test=practice-tip]");
    expect(tip.element.tagName).toBe("DETAILS");
    expect(tip.text()).toBe("ConseilPrésent, passé, puis pourquoi ce poste.");
    expect(wrapper.find("label[for=practice-answer]").text()).toBe("Ta réponse");
    expect(wrapper.find("#practice-answer-help").text()).toBe("Entrée pour envoyer · Maj+Entrée pour aller à la ligne");
    expect(wrapper.find("[data-test=practice-skip]").text()).toBe("Passer la question");
    expect(wrapper.find("[data-test=practice-send]").text()).toBe("Envoyer la réponse");
    expect(wrapper.find("[data-test=practice-words]").text()).toBe("0 mot");

    // Une réponse vide ne part pas : elle se dit.
    await wrapper.find("form").trigger("submit");
    expect(wrapper.find("[role=alert]").text()).toBe("Écris ta réponse, ou passe la question.");
    expect(POST).toHaveBeenCalledTimes(1);

    POST.mockResolvedValueOnce({
      data: practice({
        question: 2,
        turns: [
          ...practice().turns,
          { role: "candidat", text: "I am an engineer.", question: 1, relance: false, skipped: false },
          { role: "recruteur", text: "Why us?", question: 2, relance: false, skipped: false, tip: null },
        ],
      }),
    });
    await wrapper.find("[data-test=practice-input]").setValue("I am an engineer.");
    expect(wrapper.find("[data-test=practice-words]").text()).toBe("4 mots");
    await wrapper.find("[data-test=practice-input]").trigger("keydown", { key: "Enter" });
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/interview-practices/{practice_id}/answer", {
      params: { path: { practice_id: 5 } },
      body: { text: "I am an engineer." },
    });
    expect(wrapper.find("[data-test=practice-question-text]").text()).toBe("Why us?");
    expect(wrapper.find("[data-test=practice-progress]").text()).toBe("Question 2 sur 5");
    // Pas de conseil pour cette question : rien à déplier.
    expect(wrapper.find("[data-test=practice-tip]").exists()).toBe(false);
    // Après une réponse, le retour peut se demander à tout moment.
    expect(wrapper.find("[data-test=practice-finish]").exists()).toBe(true);
    for (const item of mounted.splice(0)) item.unmount();
    expect(useFocusMode().focus.value).toBe(false);
  });

  it("« Quitter » : tout de suite sans réponse en cours, après confirmation sinon", async () => {
    route.params = { candidatureId: "3" };
    route.query = { seance: "5" };
    GET.mockResolvedValue({ data: practice() });
    const wrapper = mountView();
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/interview-practices/{practice_id}", { params: { path: { practice_id: 5 } } });
    await wrapper.find("[data-test=practice-input]").setValue("Une réponse commencée");
    await wrapper.find("[data-test=practice-quit]").trigger("click");
    expect(push).not.toHaveBeenCalled();
    const confirm = wrapper.find("[data-test=inline-confirm]");
    expect(confirm.text()).toContain("Quitter l’entraînement ? Ta réponse en cours ne sera pas envoyée.");
    await confirm.find("[data-test=inline-confirm-yes]").trigger("click");
    // Sans page d'avant dans l'historique : les Rendez-vous.
    expect(push).toHaveBeenCalledWith("/candidatures/rendez-vous-orp");

    push.mockReset();
    const empty = mountView();
    await flushPromises();
    await empty.find("[data-test=practice-quit]").trigger("click");
    expect(empty.find("[data-test=inline-confirm]").exists()).toBe(false);
    expect(push).toHaveBeenCalledWith("/candidatures/rendez-vous-orp");
  });

  it("téléphone : sans navigation dès les réglages, « Passer », « Réponds comme à l’oral », Entrée va à la ligne", async () => {
    phone.value = true;
    route.query = { seance: "5" };
    GET.mockResolvedValue({ data: practice() });
    const wrapper = mountView();
    await flushPromises();
    expect(useFocusMode().focus.value).toBe(true);
    expect(wrapper.find("#practice-answer-help").text()).toBe("Réponds comme à l’oral");
    expect(wrapper.find("[data-test=practice-skip] .pv-wide").exists()).toBe(true);
    await wrapper.find("[data-test=practice-input]").setValue("Hello");
    await wrapper.find("[data-test=practice-input]").trigger("keydown", { key: "Enter" });
    expect(POST).not.toHaveBeenCalled();
  });

  it("sans IA : un message, pas de bouton Commencer ; sans candidature, un entretien type", async () => {
    GET.mockResolvedValue({ data: { kind: "rh", language: "fr", can_practice: false } });
    const wrapper = mountView();
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/api/interview-practices/defaults", { params: { query: {} } });
    expect(wrapper.find("[data-test=practice-subtitle]").text()).toBe("Un entretien type, sans candidature.");
    expect(wrapper.find("[data-test=practice-back]").text()).toBe("Retour");
    expect(wrapper.text()).toContain("n’est pas configurée");
    expect(wrapper.find("[data-test=practice-start]").exists()).toBe(false);
  });

  it("le retour : repères, meilleure réponse, « Ajouter à À préparer », pas de lien Get’emAll sans le drapeau", async () => {
    route.query = { seance: "5" };
    GET.mockResolvedValue({
      data: practice({
        status: "termine",
        feedback: {
          questions: [{ question: 1, level: "a_preciser", good: "Clair", missing: "Un chiffre", better: "I migrated…" }],
          strengths: ["Structure"],
          work_on: ["Préparer un exemple chiffré"],
        },
        turns: [...practice().turns, { role: "candidat", text: "I am an engineer.", question: 1, relance: false, skipped: false }],
      }),
    });
    POST.mockResolvedValue({ data: { to_prepare: [] } });
    const wrapper = mountView();
    await flushPromises();
    expect(wrapper.find("[data-test=practice-progress]").text()).toBe("Le retour");
    expect(wrapper.find("[role=progressbar]").exists()).toBe(false);
    const question = wrapper.find("[data-test=practice-question]");
    expect(question.text()).toContain("1. Tell me about yourself.");
    expect(question.find("[data-test=practice-level]").text()).toBe("À préciser");
    expect(question.text()).toContain("I migrated…");
    expect(question.text()).toContain("I am an engineer.");
    await wrapper.find("[data-test=practice-add-prepare]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/interviews/insights/to-prepare", { body: { text: "Préparer un exemple chiffré", done: false } });
    expect(wrapper.find("[data-test=practice-added]").text()).toBe("Ajouté à « À préparer »");
    expect(wrapper.find("[data-test=practice-getemall]").exists()).toBe(false);
    expect(wrapper.find("[data-test=practice-finish]").exists()).toBe(false);
  });

  it("dit l’erreur de l’IA et propose « Réessayer » quand le recruteur n’a pas répondu", async () => {
    route.query = { seance: "5" };
    GET.mockResolvedValue({
      data: practice({ waiting: true, turns: [...practice().turns, { role: "candidat", text: "Hello", question: 1, relance: false, skipped: false }] }),
    });
    POST.mockResolvedValue({ error: { detail: "plafond mensuel de l’IA atteint" } });
    const wrapper = mountView();
    await flushPromises();
    expect(wrapper.find("[data-test=practice-input]").exists()).toBe(false);
    await wrapper.find("[data-test=practice-retry]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Impossible : plafond mensuel de l’IA atteint.");
  });
});
