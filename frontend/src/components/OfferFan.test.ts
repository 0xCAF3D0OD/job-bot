// Les notes des cartes de l'éventail (Kevin, 15.11) : la forme courte de l'IA (score-v9) quand elle tient en 28
// caractères ; sinon le texte complet, que l'éventail coupe à 1 ligne avec « … » (16.11). La note entière reste
// dans le nom du bouton.
import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { Offer } from "../api/client";
import OfferFan from "./OfferFan.vue";

const FULL = "Kubernetes : plateforme de 40 services en production.";
const offer = (short: string | null | undefined): Offer =>
  ({
    id: 1,
    title: "SRE",
    company: "Acme SA",
    location: "Lausanne",
    score: 82,
    has_logo: false,
    strengths: [short === undefined ? { text: FULL, chunk_ids: [1] } : { text: FULL, chunk_ids: [1], short }],
    gaps: [{ text: "Allemand : niveau demandé non précisé.", chunk_ids: [], short: "Allemand courant ?" }],
  }) as unknown as Offer;

const notes = (short: string | null | undefined) => {
  const view = mount(OfferFan, { props: { offers: [offer(short)] }, global: { stubs: { RouterLink: RouterLinkStub } } });
  return {
    notes: view.findAll(".fan-notes span").map((s) => s.text()),
    label: view.find("[data-test=fan-flip]").attributes("aria-label"),
  };
};

describe("Notes de l’éventail : forme courte, sinon texte complet", () => {
  it("forme courte valide : elle est écrite sur la carte, le doute en « ? » ; le texte complet reste dans le nom", () => {
    const { notes: shown, label } = notes("Kubernetes en production");
    expect(shown).toEqual(["Kubernetes en production", "Allemand courant ?"]);
    expect(label).toContain("Kubernetes : plateforme de 40 services en production");
    expect(label).toContain("Allemand : niveau demandé non précisé");
  });

  it("28 caractères tout juste : la forme courte", () => {
    const short = "a".repeat(28);
    expect(notes(short).notes[0]).toBe(short);
  });

  it("forme courte absente (note d’avant score-v9) : le texte complet", () => {
    expect(notes(undefined).notes[0]).toBe(FULL);
  });

  it("forme courte vide : le texte complet", () => {
    expect(notes("").notes[0]).toBe(FULL);
    expect(notes(null).notes[0]).toBe(FULL);
  });

  it("forme courte de plus de 28 caractères : le texte complet", () => {
    expect(notes("a".repeat(29)).notes[0]).toBe(FULL);
  });
});
