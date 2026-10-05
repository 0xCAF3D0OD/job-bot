import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import PreparationView from "./PreparationView.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const offer = {
  id: 7,
  title: "Ingénieur DevOps junior",
  company: "Acme SA",
  location: "Lausanne, VD",
  status: "to_review",
  apply_url: "https://acme.example/jobs/1",
  apply_kind: "external",
  links: [],
};

function letter(id: number, version: number, extra: Record<string, unknown> = {}) {
  return {
    id,
    offer_id: 7,
    version,
    language: "fr",
    subject: "Candidature au poste d'ingénieur DevOps junior",
    paragraphs: [
      { text: "Votre annonce a retenu mon attention.", chunk_ids: [] },
      { text: "J'administre un cluster K3s.", chunk_ids: [1] },
    ],
    employer: { address: null, contact_name: null, contact_phone: null },
    instruction: null,
    model: "claude-opus-5",
    created_at: `2026-10-05T0${version}:00:00Z`,
    edited_at: null,
    document: {
      language: "fr",
      sender: ["Camille Exemple", "Rue du Test 1", "1020 Renens"],
      place_date: "Renens, le 5 octobre 2026",
      recipient: ["Acme SA"],
      subject_line: "Objet : Candidature au poste d'ingénieur DevOps junior",
      salutation: "Madame, Monsieur,",
      paragraphs: [],
      closing: "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.",
      signature: "Camille Exemple",
      enclosure: "Annexe : curriculum vitae",
      missing_identity: [],
    },
    ...extra,
  };
}

function mockGet(letters: unknown[]): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/offers/{offer_id}"
          ? offer
          : path === "/api/offers/{offer_id}/letters"
            ? letters
            : [{ id: 1, title: "Kubernetes" }],
    }),
  );
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/offres/:id/preparer", component: PreparationView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push("/offres/7/preparer");
  const wrapper = mount(PreparationView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("PreparationView", () => {
  it("sans lettre : propose de la rédiger, puis affiche la lettre assemblée", async () => {
    mockGet([]);
    POST.mockResolvedValue({ data: letter(11, 1) });
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=no-letter]").exists()).toBe(true);
    expect(wrapper.find("[data-test=instruction]").exists()).toBe(false);

    await wrapper.find("[data-test=language]").setValue("fr");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/offers/{offer_id}/letters", {
      params: { path: { offer_id: 7 } },
      body: { language: "fr", instruction: null, base_draft_id: null },
    });
    const sheet = wrapper.find("[data-test=letter]");
    expect(sheet.text()).toContain("Renens, le 5 octobre 2026");
    expect(sheet.text()).toContain("Objet :");
    expect(sheet.text()).toContain("Blocs : Kubernetes");
    expect(wrapper.find<HTMLInputElement>("[data-test=subject]").element.value).toBe(
      "Candidature au poste d'ingénieur DevOps junior",
    );
    expect(wrapper.find("[data-test=docx]").attributes("href")).toBe("/api/letters/11/docx");
  });

  it("la version modifiée en dernier est celle affichée ; les corrections s'enregistrent", async () => {
    mockGet([letter(12, 2), letter(11, 1, { edited_at: "2026-10-05T09:00:00Z" })]);
    PUT.mockResolvedValue({ data: letter(11, 1, { subject: "Candidature", edited_at: "2026-10-05T10:00:00Z" }) });
    const wrapper = await mountView();
    expect(wrapper.findAll("[data-test=version]")).toHaveLength(2);
    expect(wrapper.find(".versions .active").text()).toContain("v1");

    await wrapper.find("[data-test=subject]").setValue("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(false);
    await wrapper.find("[data-test=save-letter]").trigger("click");
    await flushPromises();
    const [path, opts] = PUT.mock.calls[0] as [string, { params: unknown; body: { subject: string } }];
    expect(path).toBe("/api/letters/{draft_id}");
    expect(opts.body.subject).toBe("Candidature");
    expect(wrapper.find("[data-test=docx]").exists()).toBe(true);
  });

  it("nouvelle version avec consigne : part de la version affichée", async () => {
    mockGet([letter(11, 1)]);
    POST.mockResolvedValue({ data: letter(12, 2, { instruction: "plus court" }) });
    const wrapper = await mountView();
    await wrapper.find("[data-test=instruction]").setValue("plus court");
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    const [, opts] = POST.mock.calls[0] as [string, { body: Record<string, unknown> }];
    expect(opts.body).toEqual({ language: null, instruction: "plus court", base_draft_id: 11 });
    expect(wrapper.find(".versions .active").text()).toContain("plus court");
  });

  it("erreur de l'API : message lisible", async () => {
    mockGet([]);
    POST.mockResolvedValue({ data: undefined, error: { detail: "plafond mensuel de l'IA atteint" } });
    const wrapper = await mountView();
    await wrapper.find("[data-test=write]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toBe("Plafond mensuel de l'IA atteint.");
  });

  it("coordonnées manquantes : renvoie vers les Réglages", async () => {
    const incomplete = letter(11, 1);
    incomplete.document.missing_identity = ["NPA", "localité"] as never[];
    mockGet([incomplete]);
    const wrapper = await mountView();
    expect(wrapper.find("[data-test=missing-identity]").text()).toContain("NPA, localité");
  });
});
