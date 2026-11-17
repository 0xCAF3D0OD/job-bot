// Jours de la liste des offres (docs/73 §3), à l'heure suisse.
import { describe, expect, it } from "vitest";

import { SCORE_CHOICES } from "./composables/useOfferFilters";
import { SCORE_CLOSE, SCORE_DIG, SCORE_VERY_CLOSE, cityOnly, collectWhen, dayKey, dayName, dayShort, gapSkill, initials, orpChannel, orpDueDay, orpLeftLine, orpPace, remoteText, scoreWord } from "./format";

// Dimanche 18 octobre 2026, 10 h à Zurich.
const NOW = new Date("2026-10-18T08:00:00Z");

describe("jours des offres", () => {
  it("nomme la ligne du jour : aujourd’hui, hier, puis le jour en toutes lettres", () => {
    expect(dayName("2026-10-18T05:00:00Z", NOW)).toBe("Aujourd’hui");
    expect(dayName("2026-10-17T22:30:00Z", NOW)).toBe("Aujourd’hui"); // 0 h 30 à Zurich, le 18
    expect(dayName("2026-10-17T21:30:00Z", NOW)).toBe("Hier"); // 23 h 30 à Zurich, le 17
    expect(dayName("2026-10-15T12:00:00Z", NOW)).toBe("Jeudi 15 octobre");
    expect(dayName("2025-12-31T12:00:00Z", NOW)).toBe("Mercredi 31 décembre 2025");
  });

  it("donne le jour en bref dans une offre, hors du tri par jour", () => {
    expect(dayShort("2026-10-18T05:00:00Z", NOW)).toBe("aujourd’hui");
    expect(dayShort("2026-10-17T12:00:00Z", NOW)).toBe("hier");
    expect(dayShort("2026-10-15T12:00:00Z", NOW)).toBe("15 oct.");
  });

  it("range une offre dans le jour de Zurich, pas celui du navigateur", () => {
    expect(dayKey("2026-10-17T22:30:00Z")).toBe("2026-10-18");
    expect(dayKey("2026-10-17T21:30:00Z")).toBe("2026-10-17");
  });
});

describe("gapSkill (docs/121 §C.3)", () => {
  it("garde la compétence d’un manque, pas une phrase", () => {
    expect(gapSkill("Spark : pas d’expérience dans ton profil.")).toBe("Spark");
    expect(gapSkill("Pas d’Ansible.")).toBe("Ansible");
    expect(gapSkill("Allemand courant demandé")).toBe("Allemand courant");
    expect(gapSkill("Le poste demande plus de développement que ton profil.")).toBeNull();
  });
});

describe("orpPace (docs/123 §2, Q)", () => {
  // Jeudi 16 octobre 2026 : 11 jours ouvrables passés sur 22.
  const now = new Date(2026, 9, 16);
  it("dans les temps, à rattraper, atteint", () => {
    expect(orpPace(6, 10, "2026-10", now)).toMatchObject({ state: "on-track", mood: "content", line: "Encore 4 d’ici le 5 novembre." });
    // L'échéance du serveur, reportée au jour ouvrable du canton (§11).
    expect(orpPace(6, 10, "2026-10", now, "2026-11-06")?.line).toBe("Encore 4 d’ici le 6 novembre.");
    // 11 jours ouvrables restent, du jeudi 16 au vendredi 30.
    expect(orpPace(3, 10, "2026-10", now)).toMatchObject({ state: "behind", line: "Il reste 7 candidatures en 11 jours ouvrables." });
    expect(orpPace(10, 10, "2026-10", now)).toMatchObject({ state: "reached", mood: "ravi" });
    expect(orpPace(4, null, "2026-10", now)).toBeNull();
  });
  it("le premier jour du mois, personne n’est en retard", () => {
    expect(orpPace(0, 10, "2026-10", new Date(2026, 9, 1))?.state).toBe("on-track");
  });
});

describe("initiales d’une entreprise (téléphone)", () => {
  it("deux mots sans la forme juridique, ou les deux premières lettres d’un seul mot", () => {
    expect(initials("Léman Data SA")).toBe("LD");
    expect(initials("Romandie Logistics")).toBe("RL");
    expect(initials("Alpstack")).toBe("AL");
    expect(initials("Maquette Médias Sàrl")).toBe("MM");
    expect(initials("  ")).toBe("?");
  });
});

describe("cityOnly et remoteText court (cartes du téléphone)", () => {
  it("retire le canton, garde le reste", () => {
    expect(cityOnly("Lausanne, VD")).toBe("Lausanne");
    expect(cityOnly("Zurich")).toBe("Zurich");
    expect(cityOnly(null)).toBeNull();
  });
  it("« Hybride » et « Télétravail » en pastille courte", () => {
    expect(remoteText({ remote: "hybrid", remote_days: 2 }, true)).toBe("Hybride");
    expect(remoteText({ remote: "full" }, true)).toBe("Télétravail");
    expect(remoteText({ remote: "hybrid", remote_days: 2 })).toBe("Télétravail 2 j");
  });
});

describe("L’échéance ORP en toutes lettres (MODIFICATIONS du 9 novembre, §11)", () => {
  it("celle du serveur, sinon le 5 du mois suivant ; « Objectif du mois atteint » une fois tenu", () => {
    expect(orpDueDay("2026-11")).toBe("5 décembre");
    expect(orpDueDay("2026-12")).toBe("5 janvier");
    expect(orpDueDay("2026-11", "2026-12-07")).toBe("7 décembre");
    expect(orpLeftLine(4, 13, "2026-11", "2026-12-07")).toBe("Encore 9 d’ici le 7 décembre");
    expect(orpLeftLine(13, 13, "2026-11")).toBe("Objectif du mois atteint");
    expect(orpChannel("Électronique")).toBe("formulaire en ligne");
    expect(orpChannel("LinkedIn")).toBe("LinkedIn");
  });
});

describe("collectWhen (§41 du 16.11)", () => {
  const now = new Date("2026-11-16T12:30:00Z"); // 13 h 30 en Suisse
  it("le jour même : ce matin, cet après-midi, ce soir", () => {
    expect(collectWhen("2026-11-16T14:00:00Z", now)).toBe("cet après-midi vers 15 h");
    expect(collectWhen("2026-11-16T18:00:00Z", now)).toBe("ce soir vers 19 h");
    expect(collectWhen("2026-11-16T06:00:00Z", new Date("2026-11-16T05:00:00Z"))).toBe("ce matin vers 7 h");
  });
  it("le lendemain : demain matin", () => {
    expect(collectWhen("2026-11-17T06:00:00Z", now)).toBe("demain matin vers 7 h");
  });
});

// L'échelle unique 50 / 75 / 85 (Kevin, 17.11, LISEZMOI §65) : les limites de chaque mot.
describe("scoreWord, échelle 50 / 75 / 85", () => {
  it.each([
    [49, "Loin", "far"],
    [50, "À creuser", "dig"],
    [74, "À creuser", "dig"],
    [75, "Proche", "close"],
    [84, "Proche", "close"],
    [85, "Très proche", "very-close"],
  ])("%i → %s", (score, word, tone) => {
    expect(scoreWord(score)).toMatchObject({ word, tone });
  });

  it("une seule constante pour le cercle, le filtre Note et « M'avertir dès »", () => {
    expect([SCORE_DIG, SCORE_CLOSE, SCORE_VERY_CLOSE]).toEqual([50, 75, 85]);
    expect(SCORE_CHOICES.map((c) => c.min)).toEqual([null, SCORE_DIG, SCORE_CLOSE, SCORE_VERY_CLOSE]);
  });
});
