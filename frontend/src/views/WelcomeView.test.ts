import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import WelcomeView from "./WelcomeView.vue";

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
}));
afterEach(() => vi.resetAllMocks());

const CRITERIA = {
  locations: ["VD"],
  remote_policy: "refuse",
  min_rate: 80,
  excluded_types: [],
  banned_words: [],
  unspoken_languages: [],
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

type State = { status: string; step: number; goal: string | null; trade: string | null; roles?: string[] };

async function mountWelcome(
  state: State = { status: "pending", step: 1, goal: null, trade: null },
  options: { offers?: unknown[]; realTransition?: boolean } = {},
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
                : {},
    }),
  );
  PUT.mockResolvedValue({ data: {} });
  PATCH.mockResolvedValue({ response: { ok: true }, data: {} });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }],
  });
  await router.push("/bienvenue");
  const wrapper = mount(WelcomeView, {
    attachTo: options.realTransition ? document.body : undefined,
    global: { plugins: [router], stubs: options.realTransition ? { transition: false } : {} },
  });
  await flushPromises();
  return { wrapper, router };
}

function calls(path: string): Record<string, unknown>[] {
  return PUT.mock.calls.filter((c) => c[0] === path).map((c) => (c[1] as { body: Record<string, unknown> }).body);
}

async function click(wrapper: Awaited<ReturnType<typeof mountWelcome>>["wrapper"], test: string): Promise<void> {
  await wrapper.find(`[data-test=${test}]`).trigger("click");
  await flushPromises();
}

describe("les premiers pas (OnboardingC, 11b)", () => {
  it("quatre étapes : la barre le dit, « Moins chercher plus vivre. » sur la page bleue", async () => {
    const { wrapper } = await mountWelcome();
    expect(wrapper.find(".welcome-blue").exists()).toBe(true);
    const bar = wrapper.find("[role=progressbar]");
    expect(bar.attributes("aria-label")).toBe("Étape 1 sur 4");
    expect(bar.findAll("span.done")).toHaveLength(1);
    // Le mot barré reste lu par les lecteurs d'écran ; le gribouillis est décoratif.
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Moins chercher plus vivre.");
    expect(wrapper.find("[data-test=welcome-back]").exists()).toBe(false);

    await click(wrapper, "welcome-start");
    expect(wrapper.find(".welcome-blue").exists()).toBe(false);
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Étape 2 sur 4");
    expect(calls("/api/welcome")).toContainEqual({ step: 2 });
    expect(wrapper.find("[data-test=welcome-back]").exists()).toBe(true);
  });

  it("le CV : sans fichier, « Continuer sans CV » ; la phrase de confidentialité et son lien", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 2, goal: null, trade: null });
    expect(wrapper.find("[data-test=cv-upload]").text()).toContain("PDF ou Word, 10 Mo maximum");
    expect(wrapper.find("[data-test=welcome-continue]").text()).toBe("Continuer sans CV");
    const privacy = wrapper.find("[data-test=cv-privacy]");
    expect(privacy.text()).toContain("L'IA n'en reçoit que les parties utiles, sans tes coordonnées.");
    expect(privacy.find("a").attributes("href")).toBe("/tes-donnees#ia");
    expect(wrapper.text()).not.toContain("L'Assistant t'aide");
  });

  it("le CV lu par l'IA : les compétences trouvées, les blocs ajoutés au profil, les postes pré-remplis", async () => {
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
    expect(wrapper.find("[data-test=cv-done]").text()).toContain("Importé et analysé");
    expect(wrapper.find("[data-test=cv-skills]").text()).toContain("Kubernetes");
    expect(wrapper.find("[data-test=welcome-continue]").text()).toBe("Continuer");

    await click(wrapper, "welcome-continue");
    // Le bloc déjà dans le profil n'est pas ajouté une deuxième fois.
    const added = POST.mock.calls.filter((c) => c[0] === "/api/profile-chunks");
    expect(added).toHaveLength(1);
    expect(added[0]![1]).toMatchObject({ body: { title: "Kubernetes", document_id: 3 } });
    const roles = wrapper.findAll("[data-test=roles] button");
    expect(roles.map((r) => r.text())).toEqual(["DevOps Engineer", "SRE"]);
    expect(roles.every((r) => r.attributes("aria-pressed") === "true")).toBe(true);

    // Les valeurs par défaut : les langues du CV.
    await click(wrapper, "welcome-continue");
    expect(calls("/api/criteria").at(-1)).toMatchObject({ unspoken_languages: ["allemand", "italien"] });
    expect(wrapper.find("[data-test=welcome-defaults]").text()).toContain("Langues : français, anglais");
  });

  it("les critères : postes (trois au plus), lieux en puces, l'ORP et ses recherches par mois", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null, roles: ["Infirmière"] });
    for (const role of ["Aide-soignante", "Sage-femme", "Ambulancière"]) {
      await wrapper.find("[data-test=role-input]").setValue(role);
      await click(wrapper, "role-add");
    }
    const roles = wrapper.findAll("[data-test=roles] button");
    expect(roles).toHaveLength(4);
    expect(roles.filter((r) => r.attributes("aria-pressed") === "true")).toHaveLength(3);
    expect(roles[3]!.attributes("aria-disabled")).toBe("true");
    expect(wrapper.text()).toContain("Trois postes au plus.");

    expect(wrapper.find(".tag").text()).toContain("VD");
    expect(wrapper.find("[data-test=target]").text()).toBe("10");
    await click(wrapper, "target-plus");
    await click(wrapper, "target-plus");
    expect(wrapper.find("[data-test=target]").text()).toBe("12");

    await click(wrapper, "welcome-continue");
    expect(calls("/api/criteria").at(-1)).toEqual({
      ...CRITERIA,
      locations: ["VD"],
      min_rate: null,
      remote_policy: "from_switzerland",
      unspoken_languages: ["allemand", "italien", "anglais"],
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

  it("sans ORP : pas d'objectif, pas de remise dans la ligne des valeurs par défaut", async () => {
    const { wrapper } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null });
    await wrapper.find("[data-test=orp-switch]").setValue(false);
    expect(wrapper.find("[data-test=target]").exists()).toBe(false);
    await click(wrapper, "welcome-continue");
    expect(calls("/api/settings").at(-1)).toMatchObject({ orp_monthly_target: null });
    expect(calls("/api/welcome").at(-1)).toMatchObject({ goal: "job" });
    const line = wrapper.find("[data-test=welcome-defaults]").text();
    expect(line).toBe("Taux : peu importe · Langues : français · Télétravail : accepté · Téléphone : désactivé");
  });

  it("le tri : les offres déjà notées, une à la fois ; Garder et Écarter comme dans Candidatures", async () => {
    const offers = [OFFER, { ...OFFER, id: 8, title: "SRE", score: 55 }];
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null }, { offers });
    await click(wrapper, "welcome-continue");
    expect(wrapper.text()).toContain("Garde ou écarte. Celles que tu gardes t'attendent dans Candidatures.");
    expect(wrapper.text()).not.toContain("apprend");
    expect(wrapper.find("[data-test=welcome-offer]").text()).toContain("D'après ton CV : Kubernetes et Terraform demandés.");
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

  it("sans offre notée : directement « Tout est prêt. », et « Modifier dans Compte » termine l'accueil", async () => {
    const { wrapper, router } = await mountWelcome({ status: "pending", step: 3, goal: null, trade: null });
    await click(wrapper, "welcome-continue");
    expect(wrapper.find("[data-test=welcome-offer]").exists()).toBe(false);
    expect(wrapper.find("[data-test=welcome-sorted]").text()).toBe("Tes premières offres arrivent après la prochaine collecte.");
    await click(wrapper, "welcome-account");
    expect(calls("/api/welcome").at(-1)).toEqual({ done: true, postponed: false });
    expect(router.currentRoute.value.path).toBe("/compte");
  });

  it("« Passer » remet à plus tard ; un accueil repris revient à son étape", async () => {
    const { wrapper, router } = await mountWelcome({ status: "postponed", step: 9, goal: null, trade: null });
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Étape 3 sur 4");
    await click(wrapper, "welcome-later");
    expect(calls("/api/welcome").at(-1)).toEqual({ postponed: true });
    expect(router.currentRoute.value.path).toBe("/aujourdhui");
  });

  it("en changeant d'étape, le focus va au titre de la nouvelle (docs/69 §4)", async () => {
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
