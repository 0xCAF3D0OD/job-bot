// Bilan › ORP sur ordinateur (maquette du 9 novembre, BilanOrdinateur et BilanOrdinateurFiche ; §2.5, §10.3, §11).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import BilanOrpView from "./BilanOrpView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn() } }));
vi.mock("../composables/usePhone", () => ({ usePhone: () => ({ phone: ref(false) }) }));
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-09T10:00:00"));
});
afterEach(() => {
  GET.mockReset();
  vi.useRealTimers();
});

const row = (id: number, date: string, company: string, extra: Record<string, unknown> = {}) => ({
  application_id: id,
  date,
  company,
  job_title: "DevOps Engineer",
  method: "électronique",
  missing: [],
  declared_at: null,
  ...extra,
});
const october = {
  month: "2026-10",
  state: "a_remettre",
  due_date: "2026-11-05",
  count: 5,
  target: 13,
  rows: [
    row(1, "07.10.2026", "CERN"),
    row(2, "12.10.2026", "SuisseCo"),
    row(3, "22.10.2026", "Qim info", { method: "e-mail", missing: ["adresse"] }),
    row(4, "24.10.2026", "Romandie Logistics"),
    row(5, "02.10.2026", "Déjà déclarée", { declared_at: "2026-10-30" }),
  ],
  holder: { name: "Kevin", address: null },
  searches: [],
  changed_after_submit: false,
};
const november = {
  ...october,
  month: "2026-11",
  state: "en_cours",
  due_date: "2026-12-07",
  count: 4,
  rows: [row(6, "03.11.2026", "EPFL Lausanne", { declared_at: "2026-11-04" }), row(7, "05.11.2026", "SpeciTec SA", { declared_at: "2026-11-06", missing: ["capture"] })],
};

function mountView() {
  GET.mockImplementation((path: string, init?: { params?: { query?: { month?: string } } }) => {
    if (path === "/api/orp") return Promise.resolve({ data: init?.params?.query?.month === "2026-11" ? november : october });
    return Promise.resolve({ data: null });
  });
  return mount(BilanOrpView, {
    global: {
      stubs: {
        RouterLink: { props: ["to"], template: "<a :data-to=\"JSON.stringify(to)\"><slot /></a>" },
        OrpSheet: true,
        OrpFiche: { props: ["applicationId", "month"], template: "<div data-test=\"fiche\">{{ applicationId }} {{ month }}</div>" },
        SidePanel: { props: ["open", "title"], template: "<div v-if=\"open\">{{ title }}<slot /></div>" },
      },
    },
  });
}

describe("Bilan › ORP sur ordinateur (maquette du 9 novembre)", () => {
  it("la carte du mois en cours : « Novembre », « 4 sur 13 », « Encore 9 d’ici le 7 décembre · dans les temps »", async () => {
    const wrapper = mountView();
    await flushPromises();
    // Le serveur donne octobre (à remettre) ; la carte montre le mois en cours.
    expect(GET).toHaveBeenCalledWith("/api/orp", { params: { query: { month: "2026-11" } } });
    const card = wrapper.find("[data-test=orp-goal]");
    expect(card.find(".orp-month-band-head").text()).toBe("Novembre4 sur 13");
    expect(card.find(".orp-month-band-line").text()).toBe("Encore 9 d’ici le 7 décembre · dans les temps");
    expect(card.attributes("aria-label")).toBe("Novembre : 4 recherches sur 13. Voir tout le mois");
  });

  it("« À déclarer à l’ORP » en cartes : « Prête » ou « Infos à compléter », trois montrées, puis le panneau « Pour l’ORP »", async () => {
    const wrapper = mountView();
    await flushPromises();
    const declare = wrapper.find("[data-test=orp-to-declare]");
    expect(declare.find("h2").text()).toBe("À déclarer à l’ORP · 4");
    expect(declare.find(".bilan-section-sub").text()).toBe("Envoyées en octobre, pas encore sur ta feuille de recherches.");
    const cards = declare.findAll("button.bilan-card");
    expect(cards).toHaveLength(3);
    expect(cards[0]!.find(".bilan-card-what").text()).toBe("CERNDevOps Engineer · formulaire en ligne");
    expect(cards[0]!.find(".bilan-card-state").text()).toBe("Prête");
    expect(cards[2]!.find(".bilan-card-what").text()).toBe("Qim infoDevOps Engineer · e-mail");
    expect(cards[2]!.find(".bilan-card-state").classes()).toContain("todo");
    expect(cards[2]!.find(".bilan-card-state").text()).toBe("Infos à compléter");
    expect(cards[0]!.attributes("aria-haspopup")).toBe("dialog");
    const more = declare.find("[data-test=orp-declare-more]");
    expect(more.text()).toBe("Voir l’autre");
    await more.trigger("click");
    expect(declare.findAll("button.bilan-card")).toHaveLength(4);
    await cards[2]!.trigger("click");
    const panel = wrapper.find("[data-test=orp-fiche-panel]");
    expect(panel.text()).toContain("Pour l’ORP");
    expect(panel.find("[data-test=fiche]").text()).toBe("3 2026-10");
  });

  it("« Recherches de novembre » : celles déjà déclarées, « Justificatif joint » ou « à joindre »", async () => {
    const wrapper = mountView();
    await flushPromises();
    const searches = wrapper.find("[data-test=orp-searches]");
    expect(searches.find("h2").text()).toBe("Recherches de novembre");
    expect(searches.find(".bilan-section-head span").text()).toBe("4 ce mois");
    expect(searches.find("[data-test=orp-proof-note]").text()).toBe(
      "Déjà déclarées. L’ORP peut demander un justificatif pour chaque recherche : l’e-mail de confirmation ou une capture de la candidature.",
    );
    const states = searches.findAll(".bilan-card-state").map((s) => s.text());
    expect(states).toEqual(["Justificatif à joindre", "Justificatif joint"]);
    expect(searches.find("[data-test=orp-all]").text()).toBe("Voir tout le mois et les justificatifs");
  });

  it("un mois passé déjà remis n’a plus rien à déclarer", async () => {
    GET.mockImplementation((path: string, init?: { params?: { query?: { month?: string } } }) => {
      if (path !== "/api/orp") return Promise.resolve({ data: null });
      return Promise.resolve({ data: init?.params?.query?.month === "2026-11" ? november : { ...october, state: "remis" } });
    });
    const wrapper = mount(BilanOrpView, { global: { stubs: { RouterLink: { template: "<a><slot /></a>" }, OrpSheet: true, SidePanel: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=orp-to-declare]").exists()).toBe(false);
  });
});
