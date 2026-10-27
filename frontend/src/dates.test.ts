import { describe, expect, it } from "vitest";

import { dateInList, dateInSentence, dateWithTime, inDays, meetingDate, sinceDays, timeOfDay } from "./dates";

// Midi à Zurich le 27 octobre 2026 (heure d'hiver depuis le 25 : UTC+1).
const now = new Date("2026-10-27T11:00:00Z");

describe("Les dates de jobA1 (1.6.74, règle §5)", () => {
  it("dans une liste : aujourd'hui, hier, puis la date courte, l'année si elle diffère", () => {
    expect(dateInList("2026-10-27T06:00:00Z", now)).toBe("aujourd'hui");
    expect(dateInList("2026-10-26T23:30:00Z", now)).toBe("aujourd'hui"); // 0 h 30 le 27 à Zurich
    expect(dateInList("2026-10-26T08:00:00Z", now)).toBe("hier");
    expect(dateInList("2026-10-12T08:00:00Z", now)).toBe("12 oct.");
    expect(dateInList("2025-10-12T08:00:00Z", now)).toBe("12 oct. 2025");
  });

  it("dans une phrase : « le 12 octobre », « le 1er » ; jamais « il y a »", () => {
    expect(dateInSentence("2026-10-12T08:00:00Z", now)).toBe("le 12 octobre");
    expect(dateInSentence("2026-10-01T08:00:00Z", now)).toBe("le 1er octobre");
    expect(dateInSentence("2025-12-03T08:00:00Z", now)).toBe("le 3 décembre 2025");
  });

  it("l'heure, seulement quand elle compte", () => {
    expect(timeOfDay("2026-10-27T13:05:00Z")).toBe("14 h 05");
    expect(timeOfDay("2026-10-27T13:00:00Z")).toBe("14 h");
    expect(dateWithTime("2026-10-27T13:00:00Z", now)).toBe("aujourd'hui à 14 h");
    expect(dateWithTime("2026-10-26T08:30:00Z", now)).toBe("hier à 9 h 30");
  });

  it("un rendez-vous : jour, date et heure", () => {
    expect(meetingDate("2026-10-29T08:30:00Z")).toBe("jeudi 29 octobre à 9 h 30");
  });

  it("les durées : depuis, dans", () => {
    expect(sinceDays("2026-10-18T08:00:00Z", now)).toBe("depuis 9 jours");
    expect(sinceDays("2026-10-26T08:00:00Z", now)).toBe("depuis hier");
    expect(inDays("2026-10-30T08:00:00Z", now)).toBe("dans 3 jours");
    expect(inDays("2026-10-28T08:00:00Z", now)).toBe("demain");
  });
});
