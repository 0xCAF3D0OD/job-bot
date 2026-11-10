import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OfferCompatSheet from "./OfferCompatSheet.vue";

const base = {
  open: true,
  score: 76,
  verdict: "Proche de ton profil",
  tone: "close",
  subtitle: "Ingénieur DevOps · Exemple SA",
  how: ["La note compare l’annonce à ton profil."],
};

describe("OfferCompatSheet (§10.1, maquette OffreCompatibilite)", () => {
  it("deux familles avec leur nombre, libellé au-dessus de la valeur ; une famille vide n’est pas affichée", () => {
    const wrapper = mount(OfferCompatSheet, {
      attachTo: document.body,
      props: { ...base, strengths: [{ key: "Lieu", value: "Lausanne" }, { key: "", value: "Ton expérience correspond" }], gaps: [] },
    });
    expect(wrapper.find(".sheet-title").text()).toBe("Compatibilité");
    expect(wrapper.find(".compat-verdict").text()).toBe("Proche de ton profil");
    const strong = wrapper.find("[data-test=compat-ok]");
    expect(strong.find("h3").text()).toBe("Points forts · 2");
    expect(strong.attributes("aria-labelledby")).toBe(strong.find("h3").attributes("id"));
    const points = strong.findAll(".compat-point");
    expect(points[0]!.find(".compat-key").text()).toBe("Lieu");
    expect(points[0]!.find(".compat-value").text()).toBe("Lausanne");
    expect(points[1]!.find(".compat-key").exists()).toBe(false);
    expect(wrapper.find("[data-test=compat-gap]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("« Comment la note est calculée » se déplie sur place (pas de feuille depuis une feuille)", async () => {
    const wrapper = mount(OfferCompatSheet, {
      attachTo: document.body,
      props: { ...base, strengths: [], gaps: [{ key: "Langue", value: "allemand" }] },
    });
    expect(wrapper.find("[data-test=compat-gap] h3").text()).toBe("À vérifier · 1");
    const how = wrapper.find("[data-test=compat-how]");
    expect(how.attributes("aria-expanded")).toBe("false");
    await how.trigger("click");
    expect(how.attributes("aria-expanded")).toBe("true");
    expect(wrapper.find(`#${how.attributes("aria-controls")}`).text()).toContain("La note compare");
    expect(wrapper.findAll("dialog")).toHaveLength(1);
    wrapper.unmount();
  });
});

describe("OfferCompatSheet, comment la note est calculée (prompt du 10 novembre, PR 18)", () => {
  const parts = [
    { key: "skills", points: 37, max: 40, text: "Kubernetes est dans ton profil. Ansible n’y figure pas." },
    { key: "experience", points: 15, max: 20, text: "3 ans demandés, 2 dans ton profil.", check: true },
    { key: "location", points: 15, max: 15, text: "Lausanne." },
    { key: "languages", points: 15, max: 15, text: "Français demandé : indiqué." },
    { key: "terms", points: 10, max: 10, text: "80 à 100 %, CDI." },
  ] as const;

  it("les cinq parts avec leurs points, la barre décrite, la couleur selon l’état", async () => {
    const wrapper = mount(OfferCompatSheet, {
      attachTo: document.body,
      props: {
        ...base,
        score: 92,
        strengths: [],
        gaps: [],
        parts: [...parts],
        tip: { text: "Tu as déjà utilisé Ansible ?", action: "skills" },
        scoredAt: new Date().toISOString(),
      },
    });
    const how = wrapper.find("[data-test=compat-how]");
    expect(how.find("[data-icon]").attributes("data-icon")).toBe("chevron-down");
    await how.trigger("click");
    expect(how.find("[data-icon]").attributes("data-icon")).toBe("chevron-up");
    const rows = wrapper.findAll("[data-test=compat-parts] li");
    expect(rows.map((r) => r.find(".compat-part-head").text())).toEqual([
      "Compétences demandées37 / 40",
      "Expérience15 / 20",
      "Lieu et trajet15 / 15",
      "Langues15 / 15",
      "Taux et contrat10 / 10",
    ]);
    expect(rows[0]!.find("[role=img]").attributes("aria-label")).toBe("37 points sur 40");
    expect(rows.map((r) => r.classes().find((c) => c.startsWith("is-")))).toEqual(["is-partial", "is-check", "is-full", "is-full", "is-full"]);
    expect(wrapper.find("[data-test=compat-calc-foot]").text()).toContain("sur l’annonce complète");
    expect(wrapper.find("[data-test=compat-calc-foot]").text()).toContain("jobA1 ne lit pas d’informations personnelles");
    await wrapper.find("[data-test=compat-tip-action]").trigger("click");
    expect(wrapper.find("[data-test=compat-tip-action]").text()).toBe("Ajouter une compétence");
    expect(wrapper.emitted("tip")).toEqual([["skills"]]);
    wrapper.unmount();
  });

  it("une note plus ancienne, sans parts : l’explication d’avant, aucun point inventé", async () => {
    const wrapper = mount(OfferCompatSheet, { attachTo: document.body, props: { ...base, strengths: [], gaps: [] } });
    await wrapper.find("[data-test=compat-how]").trigger("click");
    expect(wrapper.find("[data-test=compat-parts]").exists()).toBe(false);
    expect(wrapper.find("[data-test=compat-calc-old]").exists()).toBe(true);
    wrapper.unmount();
  });
});
