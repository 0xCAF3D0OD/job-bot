import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { searchGroups } from "../alertsState";
import AlertsPhoneList from "./AlertsPhoneList.vue";

const NOW = new Date("2026-11-08T12:00:00Z");
const SITES = [
  { slug: "indeed", name: "Indeed", url: null },
  { slug: "jobup", name: "jobup", url: null },
];
const cell = (site: string, status: string, received_at: string | null = null, created_at: string | null = null) => ({
  site,
  url: `https://${site}.example/recherche`,
  status,
  received_at,
  created_at,
  remote_url: null,
});
const PAGE = {
  sites: SITES,
  searches: [
    { id: 1, terms: "Kubernetes", location: "Lausanne", active: true, cells: [cell("indeed", "created", null, "2026-11-07T08:00:00Z"), cell("jobup", "todo")] },
    { id: 2, terms: "Linux", location: "Vaud", active: true, cells: [cell("indeed", "received", "2026-11-05T08:00:00Z", "2026-11-01T08:00:00Z"), cell("jobup", "todo")] },
  ],
  to_confirm: [{ site: "indeed", url: "https://indeed.example/confirmer", search_id: 1 }],
  codes: [],
} as never;

function mountList() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  return mount(AlertsPhoneList, {
    attachTo: document.body,
    props: { page: PAGE, groups: searchGroups(PAGE, NOW) },
    global: { plugins: [router] },
  });
}

describe("AlertsPhoneList (§10.8, maquettes AlertesTel, AlertesTelConfirmer, AlertesTelAlerte)", () => {
  it("les recherches par famille, dans l’ordre À confirmer, Actives, À créer ; une carte par site", () => {
    const wrapper = mountList();
    const titles = wrapper.findAll(".alerts-family-title").map((t) => t.text());
    expect(titles).toEqual(["À confirmer · 1", "Actives · 1", "À créer · 2"]);
    expect(wrapper.get("[data-test=alerts-family-confirm]").text()).toContain("Indeed attend ta confirmation avant d’envoyer les offres.");
    const confirm = wrapper.get("[data-test=alert-card-1-indeed]");
    expect(confirm.text()).toContain("Kubernetes");
    expect(confirm.text()).toContain("Lausanne");
    expect(confirm.text()).toContain("Indeed · confirmation demandée");
    expect(wrapper.get("[data-test=alert-card-2-indeed]").text()).toContain("Indeed · reçue le 5 nov.");
    expect(wrapper.get("[data-test=alert-card-2-jobup]").text()).toContain("jobup · pas encore créée");
    wrapper.unmount();
  });

  it("feuille « Alerte » à confirmer : le lien du site, puis « Ne plus suivre »", async () => {
    const wrapper = mountList();
    await wrapper.get("[data-test=alert-card-1-indeed]").trigger("click");
    expect(wrapper.get("[data-test=alert-sheet-state]").text()).toBe("À confirmer sur Indeed");
    const link = wrapper.get("[data-test=alert-confirm]");
    expect(link.attributes("href")).toBe("https://indeed.example/confirmer");
    expect(link.attributes("target")).toBe("_blank");
    await link.trigger("click");
    expect(wrapper.emitted("confirmed")?.[0]).toEqual([1]);
    wrapper.unmount();
  });

  it("feuille « Alerte » active : les actions ; à créer : « Créer l’alerte sur jobup »", async () => {
    const wrapper = mountList();
    await wrapper.get("[data-test=alert-card-2-indeed]").trigger("click");
    expect(wrapper.get("[data-test=alert-sheet-state]").text()).toBe("Active · reçue le 5 nov.");
    expect(wrapper.get("[data-test=alert-offers]").attributes("href")).toBe("/candidatures/offres?site=indeed");
    expect(wrapper.get("[data-test=alert-edit]").text()).toContain("Modifier sur Indeed");
    await wrapper.get("[data-test=alert-remove]").trigger("click");
    expect((wrapper.emitted("remove")?.[0]?.[0] as { terms: string }).terms).toBe("Linux");

    await wrapper.get("[data-test=alert-card-2-jobup]").trigger("click");
    await wrapper.get("[data-test=alert-create]").trigger("click");
    expect(wrapper.emitted("create")?.[0]).toEqual(["jobup", "Linux"]);
    wrapper.unmount();
  });
});
