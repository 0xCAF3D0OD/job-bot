import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAssistant } from "../composables/useAssistant";
import { useUndo } from "../composables/useUndo";
import WelcomeView from "./WelcomeView.vue";

// Chaque étape des premiers pas est un fichier chargé à part (defineAsyncComponent) : chargées une fois d'avance, leur
// import() se résout dans le même tour que dans le navigateur.
await Promise.all([
  import("../components/WelcomeCriteria.vue"),
  import("../components/WelcomeQuestions.vue"),
  import("../components/WelcomeAlertSteps.vue"),
  import("../components/WelcomeAlertExtension.vue"),
  import("../components/WelcomeProfileStep.vue"),
]);

const GET = vi.fn();
const PUT = vi.fn();
const POST = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    POST: (...a: unknown[]) => POST(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
  },
  QUIET: { headers: { "X-Jobbot-Quiet": "1" } },
}));
afterEach(async () => {
  await useUndo().flush();
  vi.resetAllMocks();
});

const CRITERIA = {
  locations: ["VD"],
  remote_policy: "refuse",
  min_rate: 80,
  excluded_types: [],
  banned_words: [],
  language_levels: {},
};
const SETTINGS = {
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 5,
  orp_due_day: 12,
  employer_search_threshold: 70,
};
const OFFER = {
  id: 7,
  title: "DevOps Engineer",
  company: "Alpstack",
  location: "Lausanne",
  score: 88,
  why: "Kubernetes et Terraform demandés.",
  rate_min: 80,
  rate_max: 100,
  employment_type: "CDI",
  links: [],
  keywords_asks: [],
};

const ALERTS = {
  mailbox: "lea+0mwdr89t@alertes.joba1.ch",
  sites: [{ slug: "jobup", name: "jobup" }],
  searches: [
    { id: 5, active: true, terms: "DevOps", location: "Lausanne et 30 km", cells: [{ site: "jobup", url: "https://www.jobup.ch/fr/emplois/?term=DevOps" }] },
    { id: 6, active: true, terms: "SRE", location: "", cells: [{ site: "jobup", url: "https://www.jobup.ch/fr/emplois/?term=SRE" }] },
  ],
};

type State = { status: string; step: number; goal: string | null; trade: string | null; roles?: string[]; sources?: Record<string, string> };

async function mountWelcome(
  state: State = { status: "pending", step: 1, goal: null, trade: null },
  options: { offers?: unknown[]; realTransition?: boolean; path?: string } = {},
) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/welcome"
          ? state
          : path === "/api/criteria"
            ? { criteria: CRITERIA, keywords: {}, saved_at: null }
            : path === "/api/settings"
              ? SETTINGS
              : path === "/api/offers"
                ? { items: options.offers ?? [], total: (options.offers ?? []).length }
                : path === "/api/alert-searches"
                  ? ALERTS
                  : {},
    }),
  );
  PUT.mockResolvedValue({ data: {}, response: { ok: true } });
  PATCH.mockResolvedValue({ response: { ok: true }, data: {} });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assistant", name: "assistant", component: { template: "<div />" } },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(options.path ?? "/bienvenue");
  const wrapper = mount(WelcomeView, {
    attachTo: options.realTransition ? document.body : undefined,
    global: { plugins: [router], stubs: options.realTransition ? { transition: false, teleport: true } : { teleport: true } },
  });
  await flushPromises();
  return { wrapper, router };
}

function calls(path: string): Record<string, unknown>[] {
  return PUT.mock.calls.filter((c) => c[0] === path).map((c) => (c[1] as { body: Record<string, unknown> }).body);
}

// Des critères aux premières offres : « Continuer » (sur téléphone, à chaque question, §60), puis « Plus tard » à
// l'étape de l'alerte.
async function toOffers(wrapper: Awaited<ReturnType<typeof mountWelcome>>["wrapper"], from = "welcome-continue"): Promise<void> {
  if (wrapper.find(".wq").exists()) await throughQuestions(wrapper);
  else await click(wrapper, from);
  await click(wrapper, "welcome-alert-later");
}

// Sur téléphone, « Continuer » jusqu'au bout des questions (§60) : 6, ou 5 sans ORP.
async function throughQuestions(wrapper: Awaited<ReturnType<typeof mountWelcome>>["wrapper"]): Promise<void> {
  for (let i = 0; i < 6 && wrapper.find(".wq").exists(); i++) await click(wrapper, "welcome-continue");
}

const question = (wrapper: Awaited<ReturnType<typeof mountWelcome>>["wrapper"]): string => wrapper.get(".wq-count").text();

async function click(wrapper: Awaited<ReturnType<typeof mountWelcome>>["wrapper"], test: string): Promise<void> {
  await wrapper.find(`[data-test=${test}]`).trigger("click");
  await flushPromises();
}

describe("les premiers pas (OnboardingC, 11b)", () => {
  it("cinq étapes : la barre le dit, « Moins chercher plus vivre. » sur la page bleue", async () => {
    const { wrapper } = await mountWelcome();
    expect(wrapper.find(".welcome-blue").exists()).toBe(true);
    const bar = wrapper.find("[role=progressbar]");
    expect(bar.attributes("aria-label")).toBe("Étape 1 sur 5");
    expect(bar.findAll("span.done")).toHaveLength(1);
    // Le mot barré reste lu par les lecteurs d'écran ; le gribouillis est décoratif.
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Moins chercher plus vivre.");
    expect(wrapper.find("[data-test=welcome-back]").exists()).toBe(false);

    await click(wrapper, "welcome-start");
    expect(wrapper.find(".welcome-blue").exists()).toBe(false);
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Étape 2 sur 5");
    expect(calls("/api/welcome")).toContainEqual({ step: 2 });
    expect(wrapper.find("[data-test=welcome-back]").exists()).toBe(true);
  });

  it("le CV : sans fichier, « Continuer sans CV » ; la phrase de confidentialité et son lien", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    expect(wrapper.find("[data-test=cv-upload]").text()).toContain("PDF ou Word, 10 Mo maximum");
    expect(wrapper.find("[data-test=welcome-continue]").text()).toBe("Continuer sans CV");
    const privacy = wrapper.find("[data-test=cv-privacy]");
    expect(privacy.text()).toContain("L’IA n’en reçoit que les parties utiles, sans tes coordonnées.");
    expect(privacy.find("a").attributes("href")).toBe("/tes-donnees#ia");
    // Sans Assistant, pas de « Pas de CV à jour ? » ; le « 1 » seul, lui, est là (maquette OnboardingC, §15).
    expect(wrapper.find("[data-test=cv-assistant]").exists()).toBe(false);
    const person = wrapper.find("[data-test=cv-person]");
    expect(person.attributes("src")).toContain("/troupe/un-400");
    expect(person.attributes("height")).toBe("100");
    expect(person.attributes("alt")).toBe("");
    expect(wrapper.find("[data-test=cv-scene]").attributes("aria-hidden")).toBe("true");
  });

  it("« Pas de CV à jour ? » : les premiers pas mis de côté, la demande part à l’Assistant (décision du 2026-11-06)", async () => {
    const assistant = useAssistant();
    assistant.available.value = true;
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    const card = wrapper.find("[data-test=cv-assistant]");
    expect(card.text()).toContain("Pas de CV à jour ?");
    expect(card.text()).toContain("L’Assistant t’aide à en créer un");
    await click(wrapper, "cv-assistant");
    expect(calls("/api/welcome")).toContainEqual({ postponed: true });
    expect(assistant.pending.value).toBe("Je n’ai pas de CV à jour. Aide-moi à en créer un.");
    expect(router.currentRoute.value.path).toBe("/assistant");
    assistant.available.value = false;
    assistant.pending.value = null;
    assistant.open.value = false;
  });

  it("le CV lu par l’IA : les compétences trouvées, les blocs ajoutés au profil, les postes pré-remplis", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    POST.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/documents"
            ? { id: 3, filename: "cv.pdf" }
            : path === "/api/documents/{document_id}/understand"
              ? {
                  chunks: [
                    { kind: "competence", title: "Kubernetes", content: "…", tags: [], duplicate_of: null },
                    { kind: "experience", title: "Acme SA", content: "…", tags: [], duplicate_of: 4 },
                  ],
                  roles: ["DevOps Engineer", "SRE"],
                  min_rate: null,
                  languages: ["anglais"],
                  remote: null,
                }
              : {},
      }),
    );
    const input = wrapper.find("[data-test=cv-upload] input");
    Object.defineProperty(input.element, "files", { value: [new File(["x"], "cv.pdf")] });
    await input.trigger("change");
    await flushPromises();
    await new Promise((done) => setTimeout(done, 420)); // la fin de la lecture se montre 0,4 s (§53)
    await flushPromises();
    expect(wrapper.find("[data-test=cv-done]").text()).toContain("Importé et analysé");
    expect(wrapper.find("[data-test=cv-skills]").text()).toContain("Kubernetes");
    expect(wrapper.find("[data-test=welcome-continue]").text()).toBe("Continuer");

    await click(wrapper, "welcome-continue");
    // Le bloc déjà dans le profil n'est pas ajouté une deuxième fois.
    const added = POST.mock.calls.filter((c) => c[0] === "/api/profile-chunks");
    expect(added).toHaveLength(1);
    expect(added[0]![1]).toMatchObject({ body: { title: "Kubernetes", document_id: 3 } });
    // Question 1 sur 6 (§60) : les postes du CV en pastilles cochées, « Depuis ton CV » au-dessus ; « + Autre poste »
    // ouvre le champ.
    expect(question(wrapper)).toBe("Question 1 sur 6");
    expect(wrapper.get("h1").text()).toBe("Quels postes cherches-tu\u00A0?");
    expect(wrapper.find("[data-test=question-cv]").text()).toBe("Depuis ton CV");
    const roles = wrapper.findAll("[data-test=roles] button[aria-pressed]");
    expect(roles.map((r) => r.text())).toEqual(["DevOps Engineer", "SRE"]);
    expect(roles.every((r) => r.attributes("aria-pressed") === "true")).toBe(true);
    expect(wrapper.find("[data-test=role-input]").exists()).toBe(false);
    await click(wrapper, "role-other");
    expect(wrapper.find("[data-test=role-input]").exists()).toBe(true);

    // Question 6 : les langues, pré-remplies (PR 17) ; celle du CV en « Courant », placée d'abord, « Depuis ton CV ».
    for (let i = 0; i < 5; i++) await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 6 sur 6");
    const languages = wrapper.get("[data-test=languages]");
    expect(languages.findAll("b").map((b) => b.text())).toEqual(["Anglais", "Français", "Allemand", "Italien"]);
    expect(wrapper.text()).toContain("Depuis ton CV");
    expect((languages.get("[data-test=level-anglais]").element as HTMLSelectElement).value).toBe("fluent");
    await languages.get("[data-test=level-francais]").setValue("native");
    await toOffers(wrapper);
    expect(calls("/api/criteria").at(-1)).toMatchObject({
      language_levels: { francais: "native", allemand: "unknown", italien: "unknown", anglais: "fluent" },
    });
    expect(wrapper.find("[data-test=welcome-defaults]").text()).toContain("Langues : français, anglais");
  });

  it("téléphone : pendant la lecture du CV, l’écran plein de ChargementCV (§53), puis retour à l’étape", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    let answer: (value: unknown) => void = () => {};
    POST.mockImplementation((path: string) =>
      path === "/api/documents/{document_id}/understand"
        ? new Promise((resolve) => (answer = resolve))
        : Promise.resolve({ data: path === "/api/documents" ? { id: 3, filename: "cv.pdf" } : {} }),
    );
    const input = wrapper.find("[data-test=cv-upload] input");
    Object.defineProperty(input.element, "files", { value: [new File(["x"], "cv.pdf")] });
    await input.trigger("change");
    await flushPromises();
    await vi.dynamicImportSettled();
    await flushPromises();
    const screen = wrapper.find("[data-test=cv-reading-screen]");
    expect(screen.exists()).toBe(true);
    expect(screen.find(".loading-steps-title").text()).toBe("Je lis ton CV,environ 20 secondes");
    expect(screen.findAll("li").map((li) => li.text().replace(/ : .*/, ""))).toEqual(["Coordonnées", "Expériences", "Compétences", "Langues"]);
    expect(screen.find("[role=progressbar]").attributes("aria-label")).toBe("Lecture du CV");
    expect(wrapper.find("[data-test=welcome-continue]").exists()).toBe(false);
    answer({ data: { chunks: [{ kind: "competence", title: "Kubernetes", content: "…", tags: [], duplicate_of: null }], roles: [], min_rate: null, languages: [], remote: null }, response: { status: 200 } });
    await flushPromises();
    await new Promise((done) => setTimeout(done, 420)); // la fin de la lecture se montre 0,4 s (§53)
    await flushPromises();
    expect(wrapper.find("[data-test=cv-reading-screen]").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv-done]").text()).toContain("Importé et analysé");
  });

  it("le CV enregistré mais pas lu (502) : ni « Importé et analysé » ni « Pré-rempli depuis ton CV »", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    POST.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/documents"
          ? { data: { id: 3, filename: "cv.pdf" } }
          : path === "/api/documents/{document_id}/understand"
            ? { error: { detail: "lecture impossible" }, response: { status: 502 } }
            : { data: {} },
      ),
    );
    const input = wrapper.find("[data-test=cv-upload] input");
    Object.defineProperty(input.element, "files", { value: [new File(["x"], "cv.pdf")] });
    await input.trigger("change");
    await flushPromises();
    expect(wrapper.find("[data-test=cv-done]").text()).toContain("pas pu être lu");
    // « Complétons ton profil » (PR 17) : le fichier et la raison en clair ; « Plus tard » passe aux critères.
    await click(wrapper, "welcome-continue");
    const step = wrapper.get("[data-test=welcome-profile]");
    expect(step.get("h1").text()).toBe("Complétons ton profil");
    expect(step.get("[data-test=welcome-profile-file]").text()).toContain("cv.pdf");
    expect(step.get("[data-test=welcome-profile-file]").text()).toContain("La lecture a échoué.");
    await click(wrapper, "welcome-profile-later");
    // Les questions (§60), sans « Depuis ton CV ».
    expect(question(wrapper)).toBe("Question 1 sur 6");
    expect(wrapper.find("[data-test=question-cv]").exists()).toBe(false);
    // À la place, la pastille orange, même forme et même place (Kevin, 17.11, 15 h 07).
    expect(wrapper.get("[data-test=question-cv-unread]").text()).toBe("Ton CV n’a pas pu être lu");
    expect(wrapper.text()).not.toContain("Pré-rempli");
  });

  it("sans CV : « Complétons ton profil », une expérience, les langues et le nom, puis les critères", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null, roles: ["Employée de commerce"] });
    POST.mockResolvedValue({ data: {}, response: { ok: true } });
    await click(wrapper, "welcome-continue");
    const step = wrapper.get("[data-test=welcome-profile]");
    expect(step.find("[data-test=welcome-profile-file]").exists()).toBe(false);
    // Les exemples suivent le poste cherché.
    expect(step.text()).toContain("Ex.\u202F: accueil des clients, caisse, commandes, inventaire.");
    // Le nom est le seul champ obligatoire.
    await click(wrapper, "welcome-profile-continue");
    expect(wrapper.get("[data-test=completion-message]").text()).toBe("Indique ton prénom et ton nom.");
    expect(POST).not.toHaveBeenCalledWith("/api/profile-chunks", expect.anything());

    await step.get("[data-test=completion-title]").setValue("Employée de commerce");
    await step.get("[data-test=completion-employer]").setValue("Coop, Renens");
    await step.get("[data-test=completion-start]").setValue("Mars 2021");
    await step.get("[data-test=completion-current]").setValue(true);
    expect(step.get("[data-test=completion-end]").attributes("disabled")).toBeDefined();
    expect((step.get("[data-test=completion-end]").element as HTMLInputElement).value).toBe("Aujourd’hui");
    await step.get("[data-test=completion-tasks]").setValue("Caisse et mise en rayon.");
    await step.get("[data-test=completion-level-francais]").setValue("native");
    await step.get("[data-test=completion-level-allemand]").setValue("notions");
    await step.get("[data-test=completion-name]").setValue("Léa Martin");
    await click(wrapper, "welcome-profile-continue");

    expect(POST).toHaveBeenCalledWith("/api/profile-chunks", {
      body: { kind: "experience", title: "Employée de commerce, Coop, Renens", content: "Mars 2021 à aujourd’hui.\nCaisse et mise en rayon.", tags: [], active: true },
    });
    expect(calls("/api/identity").at(-1)).toMatchObject({ name: "Léa Martin", street: null });
    expect(calls("/api/criteria").at(-1)).toMatchObject({ language_levels: { francais: "native", allemand: "notions", italien: "unknown", anglais: "unknown" } });
    // Retour aux critères, sans redemander les langues ; elles partent avec les critères.
    expect(wrapper.find("[data-test=welcome-profile]").exists()).toBe(false);
    expect(wrapper.find("[data-test=completion-languages]").exists()).toBe(false);
    expect(question(wrapper)).toBe("Question 1 sur 6");
    await toOffers(wrapper);
    expect(calls("/api/criteria").at(-1)).toMatchObject({ language_levels: { francais: "native", allemand: "notions" } });
    expect(wrapper.find("[data-test=welcome-defaults]").text()).toContain("Langues : français");
  });

  it("un poste tapé sans le « + » part aussi avec « Continuer »", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["Infirmière"] });
    await click(wrapper, "role-other");
    await wrapper.find("[data-test=role-input]").setValue("Aide-soignante");
    await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 2 sur 6");
    await throughQuestions(wrapper);
    expect(calls("/api/welcome").at(-1)).toMatchObject({ step: 4, roles: ["Infirmière", "Aide-soignante"] });
  });

  it("les critères, une question par écran (§60) : postes (trois au plus), lieu, taux, ORP, objectif, langues", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["Infirmière"] });
    // La barre de 6 segments remplace celle des 5 étapes pendant les questions.
    const bar = wrapper.get("[role=progressbar]");
    expect(bar.attributes("aria-label")).toBe("Question 1 sur 6");
    expect(bar.findAll("span.done")).toHaveLength(1);
    await click(wrapper, "role-other");
    for (const role of ["Aide-soignante", "Sage-femme", "Ambulancière"]) {
      await wrapper.find("[data-test=role-input]").setValue(role);
      await wrapper.find("[data-test=role-input]").trigger("keydown", { key: "Enter" });
    }
    const roles = wrapper.findAll("[data-test=roles] button[aria-pressed]");
    expect(roles).toHaveLength(4);
    expect(roles.filter((r) => r.attributes("aria-pressed") === "true")).toHaveLength(3);
    expect(roles[3]!.attributes("aria-disabled")).toBe("true");

    // 2. Lieu : les villes enregistrées en pastilles cochées, « Toute la Suisse » décochée.
    await click(wrapper, "welcome-continue");
    expect(wrapper.get("h1").text()).toBe("Où veux-tu travailler\u00A0?");
    expect(wrapper.get("[data-test=place-all]").attributes("aria-pressed")).toBe("false");
    expect(wrapper.text()).toContain("VD");
    // 3. Taux : un seul choix parmi les 7 valeurs, 80 % enregistré, « Dès 80 % » coché.
    await click(wrapper, "welcome-continue");
    const rates = wrapper.findAll("[data-test=rates] button");
    expect(rates.map((r) => r.text())).toEqual(["Tous", "Dès 50\u00A0%", "Dès 60\u00A0%", "Dès 70\u00A0%", "Dès 80\u00A0%", "Dès 90\u00A0%", "100\u00A0%"]);
    expect(rates.filter((r) => r.attributes("aria-checked") === "true").map((r) => r.text())).toEqual(["Dès 80\u00A0%"]);
    // 4. ORP : « Oui » par défaut ; 5. l'objectif, de 1 à 99.
    await click(wrapper, "welcome-continue");
    expect(wrapper.get("[data-test=orp-yes]").attributes("aria-checked")).toBe("true");
    await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 5 sur 6");
    expect(wrapper.find("[data-test=target]").text()).toBe("10");
    await click(wrapper, "target-plus");
    await click(wrapper, "target-plus");
    expect(wrapper.find("[data-test=target]").text()).toBe("12");
    // 6. Langues, puis tout part ensemble.
    await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 6 sur 6");
    expect(PUT.mock.calls.some((c) => c[0] === "/api/criteria")).toBe(false);

    await click(wrapper, "welcome-continue");
    expect(calls("/api/criteria").at(-1)).toEqual({
      ...CRITERIA,
      locations: ["VD"],
      // Le taux enregistré est gardé tant qu'on ne touche pas aux pastilles.
      min_rate: 80,
      remote_policy: "from_switzerland",
      // « Non renseigné » n'écarte rien (PR 17).
      language_levels: { francais: "unknown", allemand: "unknown", italien: "unknown", anglais: "unknown" },
    });
    expect(calls("/api/settings").at(-1)).toMatchObject({ orp_monthly_target: 12, orp_due_day: 5 });
    expect(calls("/api/welcome").at(-1)).toMatchObject({
      step: 4,
      goal: "orp",
      roles: ["Infirmière", "Aide-soignante", "Sage-femme"],
      trade: "Infirmière",
    });
    // Le téléphone reste désactivé : rien n'est envoyé.
    expect(PUT.mock.calls.some((c) => c[0] === "/api/notifications/phone")).toBe(false);
  });

  it("le lieu et le taux (§60) : une ville tapée devient une pastille, « Toute la Suisse » efface ; le taux choisi", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["Infirmière"] });
    await click(wrapper, "welcome-continue");
    await click(wrapper, "place-all");
    expect(wrapper.get("[data-test=place-all]").attributes("aria-pressed")).toBe("true");
    await wrapper.get("[data-test=place-input]").setValue("Lausanne");
    await wrapper.get("[data-test=place-input]").trigger("keydown", { key: "Enter" });
    expect(wrapper.get("[data-test=place-all]").attributes("aria-pressed")).toBe("false");
    expect(wrapper.get("[aria-label='Retirer Lausanne']").attributes("aria-pressed")).toBe("true");
    await click(wrapper, "welcome-continue");
    const rate = (label: string) => wrapper.findAll("[data-test=rates] button").find((b) => b.text() === label)!;
    await rate("Dès 60\u00A0%").trigger("click");
    await throughQuestions(wrapper);
    expect(calls("/api/criteria").at(-1)).toMatchObject({ locations: ["Lausanne"], min_rate: 60 });
    expect(calls("/api/welcome").filter((c) => c.sources).at(-1)).toEqual({ sources: { roles: "default", places: "user", rate: "user" } });
  });

  it("« Tous » : peu importe ; le retour revient à la question d’avant, sans l’objectif si « Non »", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["Infirmière"] });
    await click(wrapper, "welcome-continue");
    await click(wrapper, "welcome-continue");
    const rate = (label: string) => wrapper.findAll("[data-test=rates] button").find((b) => b.text() === label)!;
    await rate("Tous").trigger("click");
    await click(wrapper, "welcome-continue");
    await click(wrapper, "orp-no");
    await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 6 sur 6");
    await click(wrapper, "welcome-back");
    expect(question(wrapper)).toBe("Question 4 sur 6");
    await click(wrapper, "welcome-back");
    expect(question(wrapper)).toBe("Question 3 sur 6");
    await throughQuestions(wrapper);
    expect(calls("/api/criteria").at(-1)).toMatchObject({ min_rate: null });
    // Retour depuis l'alerte : la dernière question.
    await click(wrapper, "welcome-back");
    expect(question(wrapper)).toBe("Question 6 sur 6");
    // Retour depuis la question 1 : le CV.
    for (let i = 0; i < 4; i++) await click(wrapper, "welcome-back");
    expect(question(wrapper)).toBe("Question 1 sur 6");
    await click(wrapper, "welcome-back");
    expect(wrapper.find(".wq").exists()).toBe(false);
    expect(wrapper.find("[data-test=cv-upload]").exists()).toBe(true);
  });

  it("sans ORP : pas d’objectif, pas de remise dans la ligne des valeurs par défaut", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null });
    for (let i = 0; i < 3; i++) await click(wrapper, "welcome-continue");
    await click(wrapper, "orp-no");
    await click(wrapper, "welcome-continue");
    expect(question(wrapper)).toBe("Question 6 sur 6");
    expect(wrapper.find("[data-test=target]").exists()).toBe(false);
    await toOffers(wrapper);
    expect(calls("/api/settings").at(-1)).toMatchObject({ orp_monthly_target: null });
    expect(calls("/api/welcome").at(-2)).toMatchObject({ step: 4, goal: "job" });
    expect(calls("/api/welcome").at(-1)).toEqual({ step: 5 });
    const line = wrapper.find("[data-test=welcome-defaults]").text();
    expect(line).toBe("Taux : peu importe · Langues : à renseigner dans Profil · Télétravail : accepté depuis la Suisse · Téléphone : désactivé");
  });

  it("le tri : les offres déjà notées, une à la fois ; Garder et Écarter comme dans Candidatures", async () => {
    const offers = [OFFER, { ...OFFER, id: 8, title: "SRE", score: 55 }];
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers });
    await toOffers(wrapper);
    expect(wrapper.text()).toContain("Garde ou écarte. Celles que tu gardes t’attendent dans Candidatures.");
    expect(wrapper.text()).not.toContain("apprend");
    expect(wrapper.find("[data-test=welcome-offer]").text()).toContain("D’après ton CV : Kubernetes et Terraform demandés.");
    // L'anneau sans chiffre, le mot dessous (D3, D5).
    expect(wrapper.find(".score-ring-worded").exists()).toBe(true);
    expect(wrapper.text()).toContain("Offre 1 sur 2");

    await click(wrapper, "welcome-keep");
    expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 7 } }, body: { status: "preparing" } });
    await click(wrapper, "welcome-dismiss");
    expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 8 } }, body: { status: "ignored" } });

    expect(wrapper.find("[data-test=welcome-sorted]").text()).toBe("1 offre gardée, 1 écartée.");
    expect(wrapper.find("[data-test=welcome-later]").exists()).toBe(false);
    await click(wrapper, "welcome-finish");
    expect(calls("/api/welcome").at(-1)).toEqual({ done: true, postponed: false });
    expect(router.currentRoute.value.path).toBe("/aujourdhui");
  });

  it("« Écarter » laisse « Annuler » 6 s : l’offre reprend son statut et le tri revient sur elle", async () => {
    const offers = [{ ...OFFER, status: "to_review" }, { ...OFFER, id: 8, title: "SRE", score: 55, status: "later" }];
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers });
    await toOffers(wrapper);
    await click(wrapper, "welcome-dismiss");
    // Le bandeau commun à trait (§23 du 15.11) : le statut est parti, « Annuler » remet celui d'avant.
    const { pending, undo } = useUndo();
    expect(pending.value?.message).toBe("Offre écartée.");
    expect(wrapper.text()).toContain("Offre 2 sur 2");

    await undo();
    await flushPromises();
    expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 7 } }, body: { status: "to_review" } });
    expect(pending.value).toBeNull();
    expect(wrapper.text()).toContain("Offre 1 sur 2");

    // Garder ne propose pas d'annuler ; écarter la dernière offre garde « Annuler » sur « Tout est prêt ».
    await click(wrapper, "welcome-keep");
    expect(pending.value).toBeNull();
    vi.useFakeTimers();
    try {
      await click(wrapper, "welcome-dismiss");
      expect(wrapper.find("[data-test=welcome-sorted]").text()).toBe("1 offre gardée, 1 écartée.");
      await undo();
      await flushPromises();
      expect(PATCH).toHaveBeenLastCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 8 } }, body: { status: "later" } });
      expect(wrapper.text()).toContain("Offre 2 sur 2");
      await click(wrapper, "welcome-dismiss");
      vi.advanceTimersByTime(6000);
      await flushPromises();
      expect(pending.value).toBeNull();
      expect(wrapper.find("[data-test=welcome-sorted]").text()).toBe("1 offre gardée, 1 écartée.");
    } finally {
      vi.useRealTimers();
    }
  });

  it("sans offre notée : directement « Tout est prêt. », et « Modifier dans Compte » termine l’accueil", async () => {
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null });
    await toOffers(wrapper);
    expect(wrapper.find("[data-test=welcome-offer]").exists()).toBe(false);
    expect(wrapper.find("[data-test=welcome-sorted]").text()).toBe("Tes premières offres arrivent après la prochaine collecte.");
    await click(wrapper, "welcome-account");
    expect(calls("/api/welcome").at(-1)).toEqual({ done: true, postponed: false });
    expect(router.currentRoute.value.path).toBe("/compte");
  });

  it("l’alerte (étape 4 sur 5) : 4 étapes, la première recherche, jobup, l’adresse, le code en lecture seule ; « J’ai créé l’alerte » note jobup", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    expect(wrapper.get("[data-test=welcome-continue]").text()).toBe("Continuer»");
    await throughQuestions(wrapper);
    expect(calls("/api/welcome").at(-1)).toMatchObject({ step: 4 });
    expect(wrapper.get("[role=progressbar]").attributes("aria-label")).toBe("Étape 4 sur 5");
    expect(wrapper.get("h1").text().replace(/\s+/g, " ")).toBe("Chercher Recevoir.");
    const alert = wrapper.get("[data-test=welcome-alert]");
    // Section 41 du paquet du 16.11 : la phrase sous le titre, puis 4 étapes ; une seule recherche, la première.
    expect(wrapper.text()).toContain("Pour recevoir les nouvelles offres, crée une alerte sur jobup.");
    expect(alert.findAll("li.wa-step")).toHaveLength(4);
    expect(alert.get("[data-test=welcome-alert-step-1]").attributes("aria-current")).toBe("step");
    expect(alert.text()).toContain("jobA1 a préparé ta recherche : DevOps · Lausanne et 30 km.");
    expect(alert.text()).not.toContain("SRE");
    const open = alert.get("[data-test=wizard-open]");
    expect(open.attributes("href")).toBe("https://www.jobup.ch/fr/emplois/?term=DevOps");
    expect(open.attributes("target")).toBe("_blank");
    expect(open.text()).toContain("Ouvrir jobup avec ma recherche");
    expect(alert.get("[data-test=wizard-address]").text()).toBe("lea+0mwdr89t@alertes.joba1.ch");
    expect(alert.get("[data-test=alert-site-copy]").attributes("aria-label")).toBe("Copier l’adresse");
    // Le code se lit dans 6 cases, jamais dans un champ de saisie.
    expect(alert.get("[data-test=welcome-code]").findAll("span")).toHaveLength(6);
    expect(alert.find("input").exists()).toBe(false);
    expect(alert.text()).toContain("Termine l’alerte sur jobup");
    expect(wrapper.get("[data-test=welcome-alert-later]").text()).toBe("Plus tard");

    await click(wrapper, "welcome-alert-done");
    expect(PUT).toHaveBeenCalledWith("/api/alert-searches/{search_id}/sites/{site}", { params: { path: { search_id: 5, site: "jobup" } } });
    expect(calls("/api/welcome").at(-1)).toEqual({ step: 5 });
    expect(wrapper.get("[data-test=welcome-offer]").text()).toContain("DevOps Engineer");
  });

  it("l’alerte : « Plus tard » ne note rien et mène aux premières offres ; le retour du tri y revient", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    await toOffers(wrapper);
    expect(PUT.mock.calls.some((c) => String(c[0]).startsWith("/api/alert-searches"))).toBe(false);
    expect(wrapper.find("[data-test=welcome-offer]").exists()).toBe(true);
    await click(wrapper, "welcome-back");
    expect(wrapper.find("[data-test=welcome-alert]").exists()).toBe(true);
  });

  it("l’alerte rouverte depuis Aujourd’hui : « Retour », « Plus tard » et « J’ai créé l’alerte » y ramènent", async () => {
    for (const test of ["welcome-back", "welcome-alert-later", "welcome-alert-done"]) {
      const { wrapper, router } = await mountWelcome({ status: "done", step: 9, goal: "job", trade: null }, { path: "/bienvenue?etape=alerte" });
      expect(wrapper.find("[data-test=welcome-alert]").exists()).toBe(true);
      await click(wrapper, test);
      expect(router.currentRoute.value.path).toBe("/aujourdhui");
      expect(calls("/api/welcome")).toEqual([]);
      wrapper.unmount();
    }
  });

  it("« Passer » remet à plus tard ; un accueil repris revient à son étape", async () => {
    const { wrapper, router } = await mountWelcome({ status: "postponed", step: 9, goal: null, trade: null });
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Étape 4 sur 5");
    await click(wrapper, "welcome-later");
    expect(calls("/api/welcome").at(-1)).toEqual({ postponed: true });
    expect(router.currentRoute.value.path).toBe("/aujourdhui");
  });

  it("en changeant d’étape, le focus va au titre de la nouvelle (docs/69 §4)", async () => {
    const { wrapper } = await mountWelcome(undefined, { realTransition: true });
    await click(wrapper, "welcome-start");
    await vi.waitFor(async () => {
      await flushPromises();
      expect(document.activeElement?.tagName).toBe("H1");
      expect(document.activeElement?.textContent?.replace(/\s+/g, " ").trim()).toBe("Tout réécrire Ton CV suffit.");
    });
    wrapper.unmount();
  });
});

describe("premiers pas sur ordinateur (MODIFICATIONS_9 §5, OnboardingOrdinateur…)", () => {
  const realMatch = globalThis.matchMedia;
  beforeEach(() => {
    globalThis.matchMedia = ((q: string) => ({ matches: q.includes("min-width: 1024px"), addEventListener() {}, removeEventListener() {} })) as unknown as typeof matchMedia;
  });
  afterEach(() => {
    globalThis.matchMedia = realMatch;
    vi.useRealTimers();
  });

  it("étape 1 : en-tête « Étape 1 sur 4 », plus de « Passer », zone de dépôt, scène offres-profils décorative ; un seul des trois (la scène, pas le personnage)", async () => {
    const { wrapper } = await mountWelcome();
    expect(wrapper.findComponent({ name: "Illustration" }).exists()).toBe(false);
    expect(wrapper.get("[data-test=welcome-eyebrow]").text()).toBe("Étape 1 sur 4");
    expect(wrapper.find("[data-test=welcome-later]").exists()).toBe(false);
    expect(wrapper.get("[data-test=cv-upload]").text()).toContain("Glisse ton CV ici");
    expect(wrapper.get("[data-test=welcome-continue]").text()).toBe("Continuer sans CV");
    const scene = wrapper.get("[data-illustration]");
    expect(scene.attributes("data-illustration")).toBe("offres-profils");
    expect(scene.attributes("aria-hidden")).toBe("true");
    expect(scene.get("img").attributes("alt")).toBe("");
  });

  it("CV lu : « Lu : 2 postes, 1 compétence trouvés » et la scène formations-vide", async () => {
    const { wrapper } = await mountWelcome();
    POST.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/documents"
            ? { id: 3, filename: "cv.pdf" }
            : { chunks: [{ kind: "competence", title: "Kubernetes", content: "…", tags: [], duplicate_of: null }], roles: ["DevOps", "SRE"], min_rate: 80, languages: [], remote: null },
      }),
    );
    const input = wrapper.find("[data-test=cv-upload] input");
    Object.defineProperty(input.element, "files", { value: [new File(["x"], "cv.pdf")] });
    await input.trigger("change");
    await flushPromises();
    await new Promise((done) => setTimeout(done, 420)); // la fin de la lecture se montre 0,4 s (§53)
    await flushPromises();
    expect(wrapper.get("[data-test=cv-summary]").text()).toBe("Lu : 2 postes, 1 compétence trouvés");
    expect(wrapper.get("[data-illustration]").attributes("data-illustration")).toBe("formations-vide");
    await click(wrapper, "welcome-continue");
    expect(wrapper.findAll("[data-test=criteria-roles] li").map((li) => li.text())).toEqual(["DevOps", "SRE"]);
    expect(wrapper.get("[data-test=criteria-roles]").text()).toContain("Depuis ton CV");
    expect(wrapper.get("[data-test=criteria-roles-edit]").text()).toBe("Modifier");
    expect(wrapper.get("[data-test=criteria-rate]").text()).toContain("80 à 100");
    expect(wrapper.get("[data-illustration]").attributes("data-illustration")).toBe("lieux-carte");
    // La provenance (Kevin, 16.11, #806) : enregistrée ; jamais de pastille sur Lieu.
    expect(calls("/api/welcome").some((b) => JSON.stringify(b.sources) === JSON.stringify({ roles: "cv", places: "default", rate: "cv" }))).toBe(true);
    expect(wrapper.get("[data-test=criteria-rate]").text()).toContain("Depuis ton CV");
    expect(wrapper.get("[data-test=criteria-places]").text()).not.toContain("Depuis ton CV");
    // Le taux modifié puis validé : « user », la pastille s'en va ; ouvrir sans rien changer ne touche à rien.
    await click(wrapper, "criteria-roles-edit");
    await click(wrapper, "criteria-done");
    expect(wrapper.get("[data-test=criteria-roles]").text()).toContain("Depuis ton CV");
    await click(wrapper, "criteria-rate-edit");
    await wrapper.findAll("input[name=welcome-rate]").at(-1)!.setValue();
    await click(wrapper, "criteria-done");
    expect(wrapper.get("[data-test=criteria-rate]").text()).not.toContain("Depuis ton CV");
    expect(calls("/api/welcome").at(-1)).toEqual({ sources: { roles: "cv", places: "default", rate: "user" } });
  });

  it("la provenance revient avec l’état des premiers pas : « user » reste sans pastille", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["DevOps"], sources: { roles: "user", places: "default", rate: "cv" } });
    expect(wrapper.get("[data-test=criteria-roles]").text()).not.toContain("Depuis ton CV");
    expect(wrapper.get("[data-test=criteria-rate]").text()).toContain("Depuis ton CV");
  });

  it("coupure pendant la lecture : « En pause », scène connexion-perdue, nouvel essai après 5 s", async () => {
    const { wrapper } = await mountWelcome();
    vi.useFakeTimers();
    let attempts = 0;
    POST.mockImplementation((path: string) => {
      if (path === "/api/documents") return Promise.resolve({ data: { id: 3, filename: "cv.pdf" } });
      attempts += 1;
      return attempts === 1 ? Promise.reject(new TypeError("Failed to fetch")) : Promise.resolve({ data: { chunks: [], roles: ["DevOps"], min_rate: null, languages: [], remote: null } });
    });
    const input = wrapper.find("[data-test=cv-upload] input");
    Object.defineProperty(input.element, "files", { value: [new File(["x"], "cv.pdf")] });
    await input.trigger("change");
    await flushPromises();
    expect(wrapper.get("[data-test=cv-reading]").text()).toBe("En pause");
    expect(wrapper.get("[data-test=cv-paused]").text()).toContain("Nouvel essai dans 5 secondes");
    expect(wrapper.get("[data-illustration]").attributes("data-illustration")).toBe("connexion-perdue");
    await vi.advanceTimersByTimeAsync(5000);
    await flushPromises();
    expect(attempts).toBe(2);
    expect(wrapper.find("[data-test=cv-paused]").exists()).toBe(false);
    await vi.advanceTimersByTimeAsync(400); // la fin de la lecture se montre 0,4 s (§53)
    await flushPromises();
    expect(wrapper.get("[data-test=cv-summary]").text()).toBe("Lu : 1 poste trouvé");
  });

  it("étape 2 : objectif ORP de 1 à 99 ; étape 3 : Garder sur une carte, puis Annuler", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    expect(wrapper.get("[data-test=target]").text()).toBe("10");
    await click(wrapper, "target-plus");
    expect(wrapper.get("[data-test=target]").text()).toBe("11");
    await toOffers(wrapper, "welcome-criteria");
    expect(wrapper.get("[data-test=welcome-offers-title]").text()).toBe("1 offre pour toi");
    expect(wrapper.get("[data-test=welcome-offer]").text()).toContain("Très proche · 88");
    await click(wrapper, "welcome-keep");
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/offers/{offer_id}/status", { params: { path: { offer_id: 7 } }, body: { status: "preparing" } });
    expect(wrapper.get("[data-test=welcome-offer]").text()).toContain("Gardée");
    await click(wrapper, "undo-status");
    await flushPromises();
    expect(wrapper.find("[data-test=welcome-keep]").exists()).toBe(true);
  });
  it("étape 3 sur 4 : « Crée ton alerte sur jobup », 4 étapes dans une carte, la scène de la boîte aux lettres à droite", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    await click(wrapper, "welcome-criteria");
    expect(wrapper.get("[data-test=welcome-eyebrow]").text()).toBe("Étape 3 sur 4");
    expect(wrapper.get("h1").text()).toBe("Crée ton alerte sur jobup");
    // Section 41 du paquet du 16.11 : la phrase sous le titre, sans durée, puis une carte de 4 étapes.
    expect(wrapper.get(".wdk-lead").text()).toBe("Pour recevoir les nouvelles offres, tu crées une alerte sur jobup. C’est ainsi que jobA1 reçoit tes offres.");
    const card = wrapper.get("[data-test=welcome-alert]");
    expect(card.classes()).toContain("wa-desk");
    expect(card.findAll("li.wa-step")).toHaveLength(4);
    expect(card.text()).toContain("Le code de confirmation s’affiche ici");
    expect(card.find("input").exists()).toBe(false);
    expect(wrapper.get("[data-test=welcome-alert-done]").text()).toBe("J’ai créé l’alerte");
    // Section 25 du paquet du 15.11 : la scène à la place d'Orange seul, 420 px, servie en WebP 840 px.
    const scene = wrapper.get("[data-test=welcome-mailbox]");
    expect(scene.attributes("src")).toBe("/illustrations/scene-boite-aux-lettres-840.webp");
    expect(scene.attributes("alt")).toBe("");
    expect(scene.attributes("aria-hidden")).toBe("true");
    expect([scene.attributes("width"), scene.attributes("height")]).toEqual(["420", "299"]);
    expect(wrapper.find("[data-illustration]").exists()).toBe(false);
    await click(wrapper, "welcome-back");
    expect(wrapper.get("[data-test=welcome-eyebrow]").text()).toBe("Étape 2 sur 4");
  });

  it("section 42 : hors Firefox et sans extension, pas de choix, le parcours à la main seul (Kevin, 16.11, 23 h 29)", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    await click(wrapper, "welcome-criteria");
    expect(wrapper.find("[data-test=welcome-alert-via]").exists()).toBe(false);
    expect(wrapper.get("[data-test=welcome-alert]").isVisible()).toBe(true);
    expect(wrapper.get("[data-test=welcome-alert-extension]").isVisible()).toBe(false);
    expect(wrapper.find("[data-test=welcome-alert-done]").exists()).toBe(true);
  });

  it("section 42 : sur Firefox, « Avec l’extension / À la main », à la main par défaut sans extension ; chaque parcours garde son avancée", async () => {
    const ua = vi.spyOn(navigator, "userAgent", "get").mockReturnValue("Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0");
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
    await click(wrapper, "welcome-criteria");
    const group = wrapper.get("[data-test=welcome-alert-via]");
    expect(group.attributes("role")).toBe("radiogroup");
    const radios = group.findAll("[role=radio]");
    expect(radios.map((r) => [`${r.get("b").text()} ${r.get("span").text()}`, r.attributes("aria-checked")])).toEqual([
      ["Avec l’extension environ 1 minute", "false"],
      ["À la main environ 2 minutes", "true"],
    ]);
    expect(GET.mock.calls.some((c) => String(c[0]).includes("extension"))).toBe(false);
    await wrapper.get("[data-test=wizard-open]").trigger("click");
    await click(wrapper, "welcome-alert-via-extension");
    expect(wrapper.get("[data-test=welcome-alert-extension]").isVisible()).toBe(true);
    expect(wrapper.find("[data-test=welcome-ext-install]").exists()).toBe(true);
    expect(wrapper.find("[data-test=welcome-alert-done]").exists()).toBe(false);
    await group.trigger("keydown", { key: "ArrowRight" });
    await flushPromises();
    expect(wrapper.get("[data-test=welcome-alert-via-main]").attributes("aria-checked")).toBe("true");
    // Le parcours à la main a gardé son avancée : jobup ouvert, l'étape 3 en cours.
    expect(wrapper.get("[data-test=welcome-alert-step-3]").attributes("aria-current")).toBe("step");
    ua.mockRestore();
  });

  it("section 42 : l’extension détectée (quel que soit le navigateur) est choisie par défaut ; à « created », la page passe aux offres toute seule", async () => {
    document.documentElement.dataset.joba1Extension = "0.64.0";
    try {
      const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers: [OFFER] });
      await click(wrapper, "welcome-criteria");
      const extension = wrapper.get("[data-test=welcome-alert-via-extension]");
      expect(extension.attributes("aria-checked")).toBe("true");
      expect(extension.text()).toContain("installée · environ 1 minute");
      expect(wrapper.findAll("[data-test=welcome-alert-extension] li.wa-step")).toHaveLength(2);
      expect(wrapper.find("[data-test=welcome-alert-done]").exists()).toBe(false);
      expect(wrapper.find("[data-test=welcome-alert-later]").exists()).toBe(true);
      window.dispatchEvent(new MessageEvent("message", {
        data: { source: "joba1-extension", type: "alert-progress", site: "jobup", step: "created" },
        source: window,
        origin: window.location.origin,
      }));
      await flushPromises();
      expect(calls("/api/welcome").at(-1)).toEqual({ step: 5 });
      expect(wrapper.find("[data-test=welcome-alert-via]").exists()).toBe(false);
    } finally {
      delete document.documentElement.dataset.joba1Extension;
    }
  });
});
