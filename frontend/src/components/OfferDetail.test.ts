import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import OfferDetail from "./OfferDetail.vue";

const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: vi.fn(() => Promise.resolve({ data: undefined })), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

function offer(extra: Record<string, unknown> = {}) {
  return {
    id: 4,
    title: "Ingénieur DevOps",
    company: "Exemple SA",
    location: "Lausanne",
    status: "to_review",
    first_seen_at: "2026-10-05T08:00:00Z",
    last_seen_at: "2026-10-05T08:00:00Z",
    seen_count: 1,
    links: [{ source: "indeed", url: "https://ch.indeed.com/viewjob?jk=1" }],
    apply_url: null,
    apply_kind: null,
    employer_url: null,
    employer_url_source: null,
    employer_status: null,
    employer_checked_at: null,
    ...extra,
  };
}

async function mountDetail(value: Record<string, unknown>) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  const wrapper = mount(OfferDetail, { props: { offer: value as never }, global: { plugins: [router], stubs: { teleport: true, ContactsPanel: true } } });
  await flushPromises();
  return wrapper;
}

describe("OfferDetail, annonce chez l'employeur (docs/20 §2)", () => {
  it("lien vérifié affiché avec sa source", async () => {
    const wrapper = await mountDetail(
      offer({ employer_url: "https://exemple.ch/jobs/2", employer_url_source: "ats", employer_status: "found", employer_checked_at: "2026-10-07T08:00:00Z" }),
    );
    expect(wrapper.find("[data-test=employer]").attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(wrapper.find("[data-test=employer-line]").text()).toContain("via son outil de recrutement");
  });

  it("recherche à la demande, puis « pas trouvée »", async () => {
    POST.mockResolvedValue({ data: offer({ employer_status: "not_found", employer_checked_at: "2026-10-07T08:00:00Z" }) });
    const wrapper = await mountDetail(offer());
    // Dans le « ⋯ » de la partie Entreprise (docs/74).
    await wrapper.find("[data-test=company-more]").trigger("click");
    await wrapper.find("[data-test=find-employer]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/employer", { params: { path: { offer_id: 4 } } });
    expect(wrapper.emitted("changed")).toHaveLength(1);
    // L'offre rechargée affiche l'état, une seule fois.
    await wrapper.setProps({ offer: offer({ employer_status: "not_found", employer_checked_at: "2026-10-07T08:00:00Z" }) as never });
    const line = wrapper.find("[data-test=employer-line]");
    expect(line.text().match(/Pas trouvée/g)).toHaveLength(1);
    await wrapper.find("[data-test=company-more]").trigger("click");
    expect(wrapper.find("[data-test=find-employer]").text()).toBe("Chercher à nouveau chez l'employeur");
  });

  it("agence, ou lien employeur déjà donné par jobup", async () => {
    expect((await mountDetail(offer({ employer_status: "agency" }))).text()).toContain("employeur non indiqué");
    const known = await mountDetail(offer({ apply_kind: "external", apply_url: "https://exemple.ch/postuler" }));
    expect(known.find("[data-test=employer-line]").exists()).toBe(false);
  });
});

describe("OfferDetail, l'essentiel en haut (docs/21 §5)", () => {
  it("deux boutons, le reste dans ⋯, sans doublon de l'annonce d'origine (docs/45)", async () => {
    const wrapper = await mountDetail(offer());
    const triage = wrapper.find("[data-test=triage]");
    expect(triage.findAll("a")).toHaveLength(2);
    expect(wrapper.find("[data-test=apply]").attributes("href")).toBe("https://ch.indeed.com/viewjob?jk=1");
    expect(wrapper.find("[data-test=apply]").text()).toContain("Postuler sur Indeed");
    // « Voir sur Indeed » serait le même lien que « Postuler sur Indeed » : il n'apparaît pas.
    expect(wrapper.text()).not.toContain("Voir sur Indeed");
    expect(wrapper.find("[data-test=mark-applied]").exists()).toBe(false);
    await wrapper.find("[data-test=more]").trigger("click");
    for (const key of ["mark-applied", "later", "ignore", "flag-expired"]) {
      expect(wrapper.find(`[data-test=${key}]`).exists()).toBe(true);
    }
    // Chercher chez l'employeur est rangé dans la partie Entreprise (docs/74).
    expect(wrapper.find("[data-test=find-employer]").exists()).toBe(false);
  });

  it("sections Pour toi, À savoir, Entreprise, Annonce, dans cet ordre", async () => {
    const wrapper = await mountDetail(
      offer({
        employer_url: "https://exemple.ch/jobs/2",
        employer_status: "found",
        score: 88,
        score_stale: true,
        summary_role: "Architecte cloud",
        summary_asks: "AWS",
        summary_offers: "80-100 %",
        rate_min: 80,
        rate_max: 100,
        doubts: [{ kind: "permanent", text: "Annonce permanente : vue depuis 38 jours", excerpt: null }],
        filter_reasons: ["Type : stage"],
        description: "Missions. ".repeat(60),
      }),
    );
    const titles = wrapper.findAll(".panel-section h3").map((h) => h.text());
    expect(titles).toEqual(["Pour toi", "À savoir", "Entreprise", "Annonce"]);
    expect(wrapper.find("[data-test=score-note]").text()).toBe("Ton profil a changé depuis : note à refaire.");
    const marks = wrapper.findAll("[data-test=facts] li").map((li) => li.find(".fact-mark").text());
    expect(marks).toEqual(["✓", "✓", "!", "✗"]);
    expect(wrapper.find("[data-test=facts]").text()).toContain("80–100 %");
    // L'annonce chez l'employeur est le bouton ; celle d'Indeed, seule autre, s'affiche
    // directement, sans « ⋯ » pour une seule action (docs/76 §3).
    expect(wrapper.find("[data-test=ad-more]").exists()).toBe(false);
    expect(wrapper.find("[data-test=source-indeed]").text()).toContain("Voir sur Indeed");
    expect(wrapper.find("[data-test=company-section] [data-test=address]").exists()).toBe(true);
    expect(wrapper.find("[data-test=description]").classes()).toContain("folded");
    await wrapper.find("[data-test=read-more]").trigger("click");
    expect(wrapper.find("[data-test=description]").classes()).not.toContain("folded");
    expect(wrapper.find("[data-test=read-more]").exists()).toBe(false);
  });

  it("annonce trouvée chez l'employeur : « Postuler chez l'employeur »", async () => {
    const wrapper = await mountDetail(offer({ employer_url: "https://exemple.ch/jobs/2", employer_status: "found" }));
    const button = wrapper.find("[data-test=employer]");
    expect(button.attributes("href")).toBe("https://exemple.ch/jobs/2");
    expect(button.text()).toContain("Postuler chez l'employeur");
  });
});

describe("OfferDetail, partie Entreprise rangée (docs/74)", () => {
  it("l'adresse visible, les actions dans « ⋯ », « Ajouter l'adresse » visible si elle manque", async () => {
    const known = await mountDetail(offer({ company_address: "Rue 1\n1201 Genève", company_address_source: "registry" }));
    const section = known.find("[data-test=company-section]");
    expect(section.find("[data-test=address]").text()).toContain("Rue 1, 1201 Genève");
    expect(section.findAll("button.link")).toHaveLength(0);
    await section.find("[data-test=company-more]").trigger("click");
    const labels = section.findAll("[role=menuitem]").map((item) => item.text());
    expect(labels).toEqual(["Modifier l'adresse", "Chercher l'adresse", "Chercher l'offre chez l'employeur", "Contacts"]);

    const missing = await mountDetail(offer());
    expect(missing.find("[data-test=add-address]").text()).toBe("Ajouter l'adresse");
  });
});
