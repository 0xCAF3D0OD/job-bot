import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ApplicationSent from "./ApplicationSent.vue";

function mountSent(props: Record<string, unknown>) {
  return mount(ApplicationSent, {
    props: { title: "DevOps Engineer", company: "Alpstack", followUpOn: "2026-11-21", ...props },
    global: { stubs: { RouterLink: RouterLinkStub, TroupeScene: true } },
  });
}

describe("Candidature envoyée : l’adresse de l’entreprise manquante (corrections du 13.11 au soir, §8)", () => {
  it("la ligne sous la relance, et « Ajouter » ouvre la candidature à modifier, sur l’adresse", () => {
    const wrapper = mountSent({ applicationId: 42, addressMissing: true });
    const row = wrapper.get("[data-test=sent-address]");
    expect(row.text()).toContain("Il manque l’adresse de l’entreprise");
    expect(row.text()).toContain("Il la faut pour ton suivi ORP");
    const link = wrapper.findAllComponents(RouterLinkStub).find((l) => l.attributes("data-test") === "sent-address-add")!;
    expect(link.props("to")).toEqual({ path: "/candidatures/suivi", query: { candidature: "42", modifier: "adresse" } });
  });

  it("rien quand l’adresse est là", () => {
    const wrapper = mountSent({ applicationId: 42, addressMissing: false });
    expect(wrapper.find("[data-test=sent-address]").exists()).toBe(false);
  });
});
