import { afterEach, describe, expect, it } from "vitest";

import { dateInList, dateInSentence } from "./dates";
import { orpDueDay } from "./format";
import { addCatalog, setLang, t, tn } from "./i18n";
import { ACTIVE, formatLocale, lang } from "./lang";
import { LANGUAGES } from "./languages";

describe("i18n (docs/147)", () => {
  afterEach(() => {
    lang.value = "fr";
  });

  it("en français, le texte du code tel quel, avec ses variables", () => {
    expect(t("Écarter l’offre")).toBe("Écarter l’offre");
    expect(t("Bonjour {prenom}", { prenom: "Kevin" })).toBe("Bonjour Kevin");
  });

  it("les pluriels français : le singulier pour 0 et 1, comme plural() ; « aucune » quand zero est donné", () => {
    const forms = { one: "{n} offre", other: "{n} offres" };
    expect(tn(0, forms)).toBe("0 offre");
    expect(tn(1, forms)).toBe("1 offre");
    expect(tn(3, forms)).toBe("3 offres");
    expect(tn(0, { ...forms, zero: "Aucune offre" })).toBe("Aucune offre");
  });

  it("une autre langue : la traduction du catalogue, ses pluriels et le nombre écrit à la suisse", () => {
    lang.value = "de";
    addCatalog("de", "test", {
      "Écarter l’offre": "Stelle ausblenden",
      "{n} offres": { one: "{n} Stelle", other: "{n} Stellen" },
    });
    expect(t("Écarter l’offre")).toBe("Stelle ausblenden");
    expect(tn(1, { one: "{n} offre", other: "{n} offres" })).toBe("1 Stelle");
    expect(tn(1000, { one: "{n} offre", other: "{n} offres" })).toBe("1'000 Stellen");
    expect(formatLocale()).toBe("de-CH");
  });

  it("une traduction qui manque affiche le français, jamais un vide", () => {
    lang.value = "it";
    expect(t("Texte pas encore traduit")).toBe("Texte pas encore traduit");
  });

  it("les dates suivent la langue ; en français, rien ne change", () => {
    const now = new Date("2026-11-17T12:00:00Z");
    expect(dateInList("2026-10-12T10:00:00Z", now)).toBe("12 oct.");
    expect(dateInSentence("2026-10-12T10:00:00Z", now)).toBe("le 12 octobre");
    expect(orpDueDay("2026-11")).toBe("5 décembre");
    lang.value = "de";
    expect(orpDueDay("2026-11")).toBe("5. Dezember");
  });

  it("sept langues dans l'ordre de la planche ; seules les langues relues se choisissent", async () => {
    expect(LANGUAGES.map((l) => l.code)).toEqual(["fr", "de", "it", "en", "pt", "es", "sq"]);
    expect(ACTIVE).toEqual(["fr"]);
    await setLang("de");
    expect(lang.value).toBe("fr");
    expect(document.documentElement.lang).not.toBe("de");
  });
});
