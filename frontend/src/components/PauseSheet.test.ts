import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import PauseSheet from "./PauseSheet.vue";

// La pause (planche ReglagesRythmePause du 18.11, §70) : un seul calendrier de plage.
describe("PauseSheet", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 11, 18, 10));
  });
  afterEach(() => vi.useRealTimers());

  const day = (w: ReturnType<typeof mount>, iso: string) => w.get(`[data-test=pause-day-${iso}]`);

  it("premier toucher = Du, second = Jusqu’au ; un toucher avant le début le déplace ; les jours passés ne se choisissent pas", async () => {
    const wrapper = mount(PauseSheet, { props: { open: true, from: null, until: null, meeting: "2026-12-29T09:00:00" } });
    expect(day(wrapper, "2026-12-18").attributes("aria-current")).toBe("date");
    expect(day(wrapper, "2026-12-17").attributes("aria-disabled")).toBe("true");
    await day(wrapper, "2026-12-17").trigger("click");
    expect(wrapper.get("[data-test=pause-summary]").text()).toContain("Touche le premier jour");
    await day(wrapper, "2026-12-24").trigger("click");
    await day(wrapper, "2026-12-22").trigger("click");
    expect(wrapper.get("[data-test=pause-summary]").text()).toContain("22 déc. → touche le dernier jour");
    await day(wrapper, "2027-01-04").trigger("click");
    expect(wrapper.get("[data-test=pause-summary]").text()).toMatch(/22 déc\. → 4 janv\..*14 jours/);
    // La bande : le début et la fin pleins, arrondie au bout de la ligne (dimanche) et du mois.
    expect(day(wrapper, "2026-12-22").element.parentElement!.className).toContain("pc-end");
    expect(day(wrapper, "2026-12-27").element.parentElement!.className).toContain("pc-r");
    expect(day(wrapper, "2026-12-31").element.parentElement!.className).toContain("pc-r");
    expect(day(wrapper, "2027-01-01").element.parentElement!.className).toContain("pc-l");
    expect(day(wrapper, "2026-12-29").element.parentElement!.className).toContain("pc-rdv");
    expect(wrapper.get("[data-test=pause-meeting]").text()).toContain("Ton rendez-vous ORP du 29 déc. tombe pendant la pause");
    await wrapper.get("[data-test=pause-save]").trigger("click");
    expect(wrapper.emitted("save")?.[0]).toEqual(["2026-12-22", "2027-01-04"]);
  });

  it("« Effacer » vide la plage ; enregistrée vide, elle retire la pause", async () => {
    const wrapper = mount(PauseSheet, { props: { open: true, from: "2026-12-22", until: "2027-01-04" } });
    expect(wrapper.find("[data-test=pause-meeting]").exists()).toBe(false);
    await wrapper.get("[data-test=pause-clear]").trigger("click");
    await wrapper.get("[data-test=pause-save]").trigger("click");
    expect(wrapper.emitted("save")?.[0]).toEqual([null, null]);
  });
});
