import { describe, expect, it } from "vitest";

import { focusBody, suggestionsFor, useAssistant } from "./useAssistant";

describe("useAssistant", () => {
  it("envoie seulement les éléments choisis", () => {
    expect(focusBody(null)).toBeNull();
    expect(focusBody({ label: "rien" })).toBeNull();
    expect(focusBody({ offerId: 12, label: "offre SRE" })).toEqual({ offer_id: 12, application_id: null, day: null, month: null });
  });

  it("propose des suggestions selon la page et l'élément choisi", () => {
    expect(suggestionsFor("offers", null)[0]).toBe("Lesquelles postuler en priorité ?");
    expect(suggestionsFor("offers", { offerId: 1 })[0]).toBe("Explique-moi la note de cette offre");
    expect(suggestionsFor("applications", { month: "2026-10", day: "2026-10-02" })[0]).toBe("Qu'ai-je envoyé ce jour-là ?");
    expect(suggestionsFor("inconnue", null)).toHaveLength(3);
  });

  it("un raccourci ouvre le panneau sur l'élément", () => {
    const assistant = useAssistant();
    const before = assistant.fresh.value;
    assistant.askAbout({ applicationId: 3, label: "candidature DevOps" });
    expect(assistant.open.value).toBe(true);
    expect(assistant.focus.value?.applicationId).toBe(3);
    expect(assistant.fresh.value).toBe(before + 1);
  });
});
