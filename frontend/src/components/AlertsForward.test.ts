import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import AlertsForward from "./AlertsForward.vue";

describe("Les alertes existantes (docs/116 §1, 0.86.1)", () => {
  it("trois étapes par messagerie, une action de copie au plus par ligne, aucun mot de passe demandé", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const wrapper = mount(AlertsForward, { props: { address: "alertes+amy-32e6krri@joba1.ch" }, attachTo: document.body });
    await wrapper.find("[data-test=alerts-forward] button").trigger("click");
    const rows = wrapper.findAll("[data-test=forward-steps] li");
    expect(rows.map((r) => r.find("strong").text())).toEqual([
      "Ajouter l'adresse de transfert",
      "Recopier le code de Gmail",
      "Créer le filtre",
    ]);
    for (const row of rows) expect(row.findAll("button").length).toBeLessThanOrEqual(1);
    await wrapper.find("[data-test=forward-copy-address]").trigger("click");
    expect(writeText).toHaveBeenLastCalledWith("alertes+amy-32e6krri@joba1.ch");
    await wrapper.find("[data-test=forward-copy-senders]").trigger("click");
    expect(writeText).toHaveBeenLastCalledWith(
      "from:(candidat@jobup.ch OR candidat@my.jobup.ch OR alert@indeed.com OR donotreply@jobalert.indeed.com)",
    );
    await wrapper.find("[data-test=forward-outlook]").trigger("click");
    expect(wrapper.findAll("[data-test=forward-steps] strong")[0]!.text()).toBe("Créer une règle");
    await wrapper.find("[data-test=forward-copy-senders]").trigger("click");
    expect(writeText).toHaveBeenLastCalledWith(expect.stringContaining("candidat@jobup.ch; "));
    wrapper.unmount();
  });
});
