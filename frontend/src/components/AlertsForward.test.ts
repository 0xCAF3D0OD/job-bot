import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import AlertsForward from "./AlertsForward.vue";

describe("Lier ses alertes existantes (docs/116 §1)", () => {
  it("Gmail : l'adresse, le code affiché par jobA1, le filtre des seuls expéditeurs d'alertes", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const wrapper = mount(AlertsForward, { props: { address: "alertes+amy-32e6krri@joba1.ch" }, attachTo: document.body });
    await wrapper.find("summary, button.disclosure-row, [data-test=alerts-forward] button").trigger("click");
    const steps = wrapper.find("[data-test=forward-steps]");
    expect(steps.text()).toContain("Ajouter une adresse de transfert");
    expect(steps.text()).toContain("alertes+amy-32e6krri@joba1.ch");
    expect(steps.text()).toContain("Les e-mails des sites");
    expect(wrapper.find("[data-test=forward-filter]").text()).toBe(
      "from:(candidat@jobup.ch OR candidat@my.jobup.ch OR alert@indeed.com OR donotreply@jobalert.indeed.com)",
    );
    await wrapper.find("[data-test=forward-copy]").trigger("click");
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("candidat@jobup.ch"));
    expect(wrapper.text()).not.toMatch(/mot de passe(?! d'un site)/);

    await wrapper.find("[data-test=forward-outlook]").trigger("click");
    expect(wrapper.find("[data-test=forward-steps]").text()).toContain("Ajouter une nouvelle règle");
    expect(wrapper.find("[data-test=forward-filter]").text()).toContain("candidat@jobup.ch; ");
    wrapper.unmount();
  });
});
