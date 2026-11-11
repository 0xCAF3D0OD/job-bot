import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import ApplicationSent from "./ApplicationSent.vue";

const phone = ref(false);
vi.mock("../composables/usePhone", () => ({ PHONE_QUERY: "", usePhone: () => ({ phone }) }));

const BASE = { title: "DevOps Engineer", company: "Alpstack", month: "2026-11", count: 8, target: 10, due: "2026-12-07", followUpOn: "2026-11-21", missing: [] as string[], savedAt: "2026-11-11T10:52:00Z", applicationId: 42 };
function sent(props: Record<string, unknown> = {}) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  return mount(ApplicationSent, { props: { ...BASE, ...props }, global: { plugins: [router] } });
}

describe("« Candidature envoyée. » (PR 51)", () => {
  it("ordinateur : le poste, puis la carte (barre ORP, preuve gardée, relance prévue)", () => {
    phone.value = false;
    const wrapper = sent();
    expect(wrapper.find("h1").text()).toBe("Candidature envoyée.");
    expect(wrapper.text()).toContain("DevOps Engineer chez Alpstack.");
    const card = wrapper.find("[data-test=sent-card]");
    expect(card.find("[data-test=orp-bar]").text()).toContain("Mois ORP · novembre");
    expect(card.find("[data-test=month-count]").text()).toBe("8 sur 10");
    expect(card.find("[data-test=month-left]").text()).toBe("Encore 2 d’ici le 7 décembre");
    const rows = card.findAll(".sent-rows > li");
    expect(rows.map((r) => r.find("b").text())).toEqual(["Preuve pour l’ORP gardée", expect.stringMatching(/^Relance prévue le 21 novembre( 2026)?$/)]);
    expect(rows[0]!.text()).toMatch(/Enregistrée .+ à 11 h 52$/);
    expect(rows[1]!.text()).toContain("jobA1 te la prépare");
    expect(wrapper.find("[data-test=sent-applications]").text()).toBe("Voir mes candidatures");
    expect(wrapper.find("[data-test=next-offer]").text()).toBe("Préparer la prochaine");
  });

  it("preuve incomplète : « Il manque la preuve pour l’ORP » et le lien qui ouvre la candidature", () => {
    phone.value = false;
    const wrapper = sent({ missing: ["adresse de l'entreprise"] });
    const row = wrapper.find("[data-test=sent-proof-missing]");
    expect(row.find("b").text()).toBe("Il manque la preuve pour l’ORP");
    expect(row.text()).toContain("À compléter : adresse de l’entreprise");
    expect(row.find("[data-test=sent-proof-add]").attributes("href")).toBe("/candidatures/suivi?candidature=42");
    expect(wrapper.find("[data-test=sent-proof]").exists()).toBe(false);
  });

  it("sans objectif, sans relance, sans ligne connue : ni barre, ni carte", () => {
    phone.value = false;
    const wrapper = sent({ target: null, followUpOn: null, missing: null });
    expect(wrapper.find("[data-test=sent-card]").exists()).toBe(false);
    expect(wrapper.text()).toContain("DevOps Engineer chez Alpstack.");
  });

  it("téléphone : « Envoyée ! », le poste, la barre, les lignes, « Préparer la suivante » puis « Voir mes candidatures »", async () => {
    phone.value = true;
    const wrapper = sent({ cancellable: true });
    expect(wrapper.find("h1").text()).toBe("Envoyée !");
    expect(wrapper.find(".sent-fin-offer").text()).toBe("DevOps Engineer · Alpstack");
    expect(wrapper.find("[data-test=month-count]").text()).toBe("8 sur 10");
    expect(wrapper.findAll(".sent-rows > li")).toHaveLength(2);
    const actions = wrapper.findAll(".sent-fin-foot > *").map((a) => a.text());
    expect(actions).toEqual(["Préparer la suivante", "Voir mes candidatures", "Je n’ai pas postulé"]);
    expect(wrapper.find("[data-test=next-offer]").attributes("href")).toBe("/candidatures/offres");
    await wrapper.find("[data-test=cancel-applied]").trigger("click");
    expect(wrapper.emitted("cancel")).toHaveLength(1);
  });
});
