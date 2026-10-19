import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import PrepCertificates from "./PrepCertificates.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

const certificate = (id: number, filename: string, advice: string) => ({ document_id: id, filename, advice });

// Dans « Postuler » (docs/87 §4) : les certificats à joindre, ceux à faire corriger d'abord.
describe("Les certificats dans Préparer", () => {
  it("à joindre, les plus récents d'abord ; à corriger, à part", async () => {
    GET.mockResolvedValue({
      data: {
        certificates: [
          certificate(3, "Acme SA.pdf", "attach"),
          certificate(1, "Exemple Sàrl.pdf", "attach"),
          certificate(2, "Démo SA.pdf", "correct"),
          certificate(4, "Autre.pdf", "on_request"),
        ],
        summary: null,
      },
    });
    const wrapper = mount(PrepCertificates, { global: { stubs: { RouterLink: true } } });
    await flushPromises();
    expect(wrapper.text()).toContain("Certificats à joindre : Acme SA, Exemple Sàrl.");
    expect(wrapper.find("[data-test=prep-certificate-3]").attributes("href")).toBe("/api/documents/3/file");
    expect(wrapper.text()).toContain("Pas encore « Démo SA »");
    expect(wrapper.text()).not.toContain("Autre");
  });

  it("sans certificat : rien", async () => {
    GET.mockResolvedValue({ data: { certificates: [], summary: null } });
    const wrapper = mount(PrepCertificates);
    await flushPromises();
    expect(wrapper.find("[data-test=prep-certificates]").exists()).toBe(false);
  });
});
