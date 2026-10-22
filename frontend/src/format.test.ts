// Jours de la liste des offres (docs/73 §3), à l'heure suisse.
import { describe, expect, it } from "vitest";

import { dayKey, dayName, dayShort, gapSkill, orpPace } from "./format";

// Dimanche 18 octobre 2026, 10 h à Zurich.
const NOW = new Date("2026-10-18T08:00:00Z");

describe("jours des offres", () => {
  it("nomme la ligne du jour : aujourd'hui, hier, puis le jour en toutes lettres", () => {
    expect(dayName("2026-10-18T05:00:00Z", NOW)).toBe("Aujourd'hui");
    expect(dayName("2026-10-17T22:30:00Z", NOW)).toBe("Aujourd'hui"); // 0 h 30 à Zurich, le 18
    expect(dayName("2026-10-17T21:30:00Z", NOW)).toBe("Hier"); // 23 h 30 à Zurich, le 17
    expect(dayName("2026-10-15T12:00:00Z", NOW)).toBe("Jeudi 15 octobre");
    expect(dayName("2025-12-31T12:00:00Z", NOW)).toBe("Mercredi 31 décembre 2025");
  });

  it("donne le jour en bref dans une offre, hors du tri par jour", () => {
    expect(dayShort("2026-10-18T05:00:00Z", NOW)).toBe("aujourd'hui");
    expect(dayShort("2026-10-17T12:00:00Z", NOW)).toBe("hier");
    expect(dayShort("2026-10-15T12:00:00Z", NOW)).toBe("15 oct.");
  });

  it("range une offre dans le jour de Zurich, pas celui du navigateur", () => {
    expect(dayKey("2026-10-17T22:30:00Z")).toBe("2026-10-18");
    expect(dayKey("2026-10-17T21:30:00Z")).toBe("2026-10-17");
  });
});

describe("gapSkill (docs/121 §C.3)", () => {
  it("garde la compétence d'un manque, pas une phrase", () => {
    expect(gapSkill("Spark : pas d'expérience dans ton profil.")).toBe("Spark");
    expect(gapSkill("Pas d'Ansible.")).toBe("Ansible");
    expect(gapSkill("Allemand courant demandé")).toBe("Allemand courant");
    expect(gapSkill("Le poste demande plus de développement que ton profil.")).toBeNull();
  });
});

describe("orpPace (docs/123 §2, Q)", () => {
  // Jeudi 16 octobre 2026 : 11 jours ouvrables passés sur 22.
  const now = new Date(2026, 9, 16);
  it("dans les temps, à rattraper, atteint", () => {
    expect(orpPace(6, 10, "2026-10", now)).toMatchObject({ state: "on-track", mood: "content", line: "Encore 4 d'ici le 31 octobre." });
    // 11 jours ouvrables restent, du jeudi 16 au vendredi 30.
    expect(orpPace(3, 10, "2026-10", now)).toMatchObject({ state: "behind", line: "Il reste 7 candidatures en 11 jours ouvrables." });
    expect(orpPace(10, 10, "2026-10", now)).toMatchObject({ state: "reached", mood: "ravi" });
    expect(orpPace(4, null, "2026-10", now)).toBeNull();
  });
  it("le premier jour du mois, personne n'est en retard", () => {
    expect(orpPace(0, 10, "2026-10", new Date(2026, 9, 1))?.state).toBe("on-track");
  });
});
