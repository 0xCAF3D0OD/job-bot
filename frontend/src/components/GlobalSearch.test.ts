import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import GlobalSearch from "./GlobalSearch.vue";

const GET = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const RESULTS = {
  q: "devops",
  offers: {
    total: 7,
    items: [
      { id: 1, title: "DevOps Engineer", company: "Prototype Fintech SA", location: "Genève", score: 90 },
      { id: 2, title: "Ingénieur·e DevOps", company: "Fictif Cloud SA", location: "Lausanne", score: 72 },
    ],
  },
  applications: {
    total: 1,
    items: [{ id: 5, company: "Démo Data SA", job_title: "Platform Engineer (DevOps)", status: "en_attente", sent_at: "2026-10-12", interview_at: null, orp_month: "2026-10" }],
  },
  companies: { total: 1, items: [{ name: "DevOps Partners SA", offers: 2, applications: 1 }] },
};
const EMPTY = { q: "zzz", offers: { total: 0, items: [] }, applications: { total: 0, items: [] }, companies: { total: 0, items: [] } };

async function mountSearch() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/");
  const wrapper = mount(GlobalSearch, { global: { plugins: [router] } });
  return { wrapper, router };
}

async function type(wrapper: Awaited<ReturnType<typeof mountSearch>>["wrapper"], text: string) {
  const input = wrapper.find("[data-test=search-input]");
  await input.trigger("focus");
  await input.setValue(text);
  // La recherche part 250 ms après la dernière frappe.
  await new Promise((resolve) => setTimeout(resolve, 300));
  await flushPromises();
  return input;
}

describe("recherche globale (série du 27.10, point 2)", () => {
  it("un champ nommé, trois groupes, le verdict en mot, « Tout voir (N) »", async () => {
    GET.mockResolvedValue({ data: RESULTS });
    const { wrapper } = await mountSearch();
    expect(wrapper.find("label[for=global-search-input]").text()).toBe("Rechercher");
    expect(wrapper.find("[data-test=search-input]").attributes("placeholder")).toBe("Offres, candidatures, entreprises");
    await type(wrapper, "devops");
    expect(GET).toHaveBeenCalledWith("/api/search", { params: { query: { q: "devops" } } });
    expect(wrapper.find("[role=listbox]").attributes("aria-label")).toBe("Résultats de la recherche");
    expect(wrapper.findAll(".gs-group-title").map((t) => t.text())).toEqual(["Offres", "Candidatures", "Entreprises"]);
    expect(wrapper.find("[data-test=search-offer] .gs-verdict").text()).toBe("Très proche");
    expect(wrapper.find("[data-test=search-all-offers]").text()).toBe("Tout voir (7)");
    expect(wrapper.find("[data-test=search-application]").text()).toContain("Démo Data SA · envoyée le 12 oct.");
    expect(wrapper.find("[data-test=search-company]").text()).toContain("2 offres, 1 candidature");
    expect(wrapper.find("[data-test=search-follow]").text()).toContain("Ajoute « devops » à tes alertes");
    wrapper.unmount();
  });

  it("le clavier : flèches, Entrée ouvre, Échap ferme", async () => {
    GET.mockResolvedValue({ data: RESULTS });
    const { wrapper, router } = await mountSearch();
    const input = await type(wrapper, "devops");
    await input.trigger("keydown", { key: "ArrowDown" });
    expect(input.attributes("aria-activedescendant")).toBe("gs-offer-1");
    await input.trigger("keydown", { key: "ArrowDown" });
    expect(input.attributes("aria-activedescendant")).toBe("gs-offer-2");
    await input.trigger("keydown", { key: "ArrowUp" });
    await input.trigger("keydown", { key: "Enter" });
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/candidatures/offres");
    expect(router.currentRoute.value.query.offre).toBe("1");
    expect(wrapper.find("[data-test=search-panel]").exists()).toBe(false);
    await input.trigger("focus");
    expect(wrapper.find("[data-test=search-panel]").exists()).toBe(true);
    await input.trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[data-test=search-panel]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("aucun résultat : la phrase, puis « Suivre cette recherche »", async () => {
    GET.mockResolvedValue({ data: EMPTY });
    const { wrapper } = await mountSearch();
    await type(wrapper, "zzz");
    expect(wrapper.find("[data-test=search-empty]").text()).toBe("Aucun résultat pour « zzz » dans tes offres, candidatures et entreprises.");
    expect(wrapper.find("[data-test=search-follow]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("suivre : des sites restent à créer, « ajoutée » et la phrase orange, puis Annuler retire", async () => {
    GET.mockResolvedValue({ data: EMPTY });
    POST.mockResolvedValue({
      data: { ids: [3, 4], created: [3, 4], terms: "kubernetes", locations: ["Zurich"], sites: ["jobup", "LinkedIn"], todo: ["LinkedIn"] },
    });
    DELETE.mockResolvedValue({ data: {} });
    const { wrapper } = await mountSearch();
    await type(wrapper, "kubernetes");
    await wrapper.find("[data-test=search-follow]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/alert-searches/follow", { body: { terms: "kubernetes" } });
    const done = wrapper.find("[data-test=search-followed]");
    expect(done.attributes("role")).toBe("status");
    expect(done.text()).toContain("Recherche ajoutée : kubernetes · Zurich · jobup, LinkedIn");
    expect(done.text()).not.toContain("Recherche suivie");
    expect(wrapper.find("[data-test=search-todo]").text()).toBe(
      "Il te reste à créer l'alerte sur LinkedIn. Tant qu'elle n'est pas créée, rien n'arrive.",
    );
    expect(wrapper.find(".gs-actions").findAll("button").map((b) => b.text())).toEqual(["Créer les alertes", "Modifier", "Annuler (6 s)"]);
    expect(wrapper.find("[data-test=search-create-alerts]").classes()).toContain("primary");
    await wrapper.find("[data-test=search-undo]").trigger("click");
    await flushPromises();
    expect(DELETE).toHaveBeenCalledTimes(2);
    expect(wrapper.find("[data-test=search-followed]").exists()).toBe(false);
    expect(wrapper.find("[role=status]").text()).toBe("Recherche retirée.");
    wrapper.unmount();
  });

  it("suivre : aucun site à créer, « suivie », sans phrase orange ni « Créer les alertes »", async () => {
    GET.mockResolvedValue({ data: EMPTY });
    POST.mockResolvedValue({ data: { ids: [3], created: [3], terms: "linux", locations: [], sites: ["jobup"], todo: [] } });
    const { wrapper } = await mountSearch();
    await type(wrapper, "linux");
    await wrapper.find("[data-test=search-follow]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=search-followed]").text()).toContain("Recherche suivie : linux · jobup");
    expect(wrapper.find("[data-test=search-todo]").exists()).toBe(false);
    expect(wrapper.find("[data-test=search-create-alerts]").exists()).toBe(false);
    wrapper.unmount();
  });
});
