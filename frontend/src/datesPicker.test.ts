import { describe, expect, it } from "vitest";

import { addDays, addMonths, clockLabel, dayLabel, longDate, monthCaps, monthTitle, parseTypedDay, parseTypedTime, shortDate, typedDay } from "./dates";

describe("les dates du sélecteur (docs/143, D26)", () => {
  it("écrit le jour et l’heure en toutes lettres", () => {
    expect(longDate("2026-11-10")).toBe("Mardi 10 novembre 2026");
    expect(shortDate("2026-11-10")).toBe("Mar. 10 nov. 2026");
    expect(monthTitle("2026-11-10")).toBe("Novembre 2026");
    expect(dayLabel("2026-11-01")).toBe("1er novembre 2026");
    expect(clockLabel("09:30")).toBe("9 h 30");
    expect(clockLabel("14:00")).toBe("14 h");
  });

  it("abrège le mois de l’icône calendrier en capitales", () => {
    expect(monthCaps(11)).toBe("NOV");
    expect(monthCaps(9)).toBe("SEPT");
    expect(monthCaps(10)).toBe("OCT");
  });

  it("compte les jours et les mois", () => {
    expect(addDays("2026-10-31", 1)).toBe("2026-11-01");
    expect(addMonths("2026-01-31", 1)).toBe("2026-02-28");
  });

  it("lit une saisie libre et refuse une date impossible", () => {
    expect(parseTypedDay("10.11.2026")).toBe("2026-11-10");
    expect(parseTypedDay("31.02.2026")).toBeNull();
    expect(typedDay("2026-11-10")).toBe("10.11.2026");
    expect(parseTypedTime("9:30")).toBe("09:30");
    expect(parseTypedTime("14h")).toBe("14:00");
    expect(parseTypedTime("25:00")).toBeNull();
  });
});
