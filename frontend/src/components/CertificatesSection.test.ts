import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CertificatesSection from "./CertificatesSection.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

// Les certificats de travail, décodés (docs/87).
const weak = {
  document_id: 2,
  filename: "Démo SA.pdf",
  readable: true,
  language: "fr",
  grade: 1,
  grade_label: "à revoir",
  explanation: "À revoir : « dans l'ensemble à notre satisfaction ».",
  advice: "correct",
  advice_label: "à faire corriger d'abord",
  passages: [
    { text: "dans l'ensemble à notre satisfaction", meaning: "À revoir.", tone: "bad", category: "performance", level: 1 },
  ],
  notes: [{ text: "Pas de formule de fin.", tone: "bad" }],
  ai: null,
  ai_at: null,
};
const page = { certificates: [weak], summary: "Pour « Démo SA », demande d'abord une correction." };

describe("Certificats de travail", () => {
  it("la note, le conseil, le détail, puis la lecture de l'IA", async () => {
    GET.mockResolvedValue({ data: page });
    const wrapper = mount(CertificatesSection, { props: { version: 0 } });
    await flushPromises();
    expect(wrapper.find("[data-test=certificates-summary]").text()).toContain("demande d'abord une correction");
    const card = wrapper.find("[data-test=certificate-2]");
    expect(card.find("[data-test=certificate-grade]").text()).toBe("à revoir");
    expect(card.find("[data-test=certificate-advice]").text()).toBe("À faire corriger d'abord");
    await card.find("[data-test=certificate-details-2]").trigger("click");
    expect(card.find(".certificate-passages").text()).toContain("« dans l'ensemble à notre satisfaction »");
    expect(card.find(".certificate-notes").text()).toContain("Pas de formule de fin.");
    POST.mockResolvedValue({
      data: {
        ...page,
        certificates: [
          {
            ...weak,
            explanation: "Le travail est jugé insuffisant.",
            ai: { grade: 1, explanation: "Le travail est jugé insuffisant.", missing: ["Les tâches manquent."], order: null, advice: "correct", advice_text: "Demande une reformulation." },
            ai_at: "2026-10-19T10:00:00Z",
          },
        ],
      },
    });
    await card.find("[data-test=certificate-read-2]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/certificates/{document_id}/lecture", { params: { path: { document_id: 2 } } });
    const read = wrapper.find("[data-test=certificate-2]");
    expect(read.find("[data-test=certificate-advice]").text()).toContain("Demande une reformulation.");
    expect(read.find(".certificate-notes").text()).toContain("Les tâches manquent.");
    expect(read.find("[data-test=certificate-read-2]").text()).toBe("Relire en détail");
  });

  it("sans certificat : rien ; l'IA indisponible : le dit", async () => {
    GET.mockResolvedValue({ data: { certificates: [], summary: null } });
    const empty = mount(CertificatesSection, { props: { version: 0 } });
    await flushPromises();
    expect(empty.find("[data-test=certificates]").exists()).toBe(false);
    GET.mockResolvedValue({ data: page });
    POST.mockResolvedValue({ error: { detail: "plafond mensuel de l'IA atteint" } });
    const wrapper = mount(CertificatesSection, { props: { version: 0 } });
    await flushPromises();
    await wrapper.find("[data-test=certificate-read-2]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toBe("plafond mensuel de l'IA atteint");
  });
});
