import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import MailboxAddress from "./MailboxAddress.vue";

describe("L'adresse des alertes (docs/104)", () => {
  it("invité sur la boîte de l'exploitant : son nom abrégé ; la copie donne l'adresse entière", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const wrapper = mount(MailboxAddress, { props: { address: "kevin.dinocera+k9dyqou7@gmail.com", personal: true } });
    expect(wrapper.find("[data-test=mailbox-address]").text()).toBe("k…+k9dyqou7@gmail.com");
    await wrapper.find("[data-test=mailbox-copy]").trigger("click");
    await flushPromises();
    expect(writeText).toHaveBeenCalledWith("kevin.dinocera+k9dyqou7@gmail.com");
    expect(wrapper.find("[data-test=mailbox-copy]").text()).toBe("Copié");
  });

  it("l'adresse du domaine des alertes, ou celle de l'exploitant : entière", () => {
    const domain = mount(MailboxAddress, { props: { address: "eliot-k9dyqou7@alertes.joba1.ch", personal: true } });
    expect(domain.find("[data-test=mailbox-address]").text()).toBe("eliot-k9dyqou7@alertes.joba1.ch");
    // Sans « catch-all » (0.82.3) : la boîte du domaine, entière elle aussi.
    const box = mount(MailboxAddress, { props: { address: "alertes+amy-32e6krri@joba1.ch", personal: true } });
    expect(box.find("[data-test=mailbox-address]").text()).toBe("alertes+amy-32e6krri@joba1.ch");
    const owner = mount(MailboxAddress, { props: { address: "kevin.dinocera@gmail.com" } });
    expect(owner.find("[data-test=mailbox-address]").text()).toBe("kevin.dinocera@gmail.com");
  });
});
