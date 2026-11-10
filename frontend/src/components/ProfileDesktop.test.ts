import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ProfileDesktop from "./ProfileDesktop.vue";

const GET = vi.fn();
const PUT = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    POST: vi.fn(),
  },
  PROFILE_KEY: "jobA1.profile",
}));
vi.mock("../composables/useAuth", async () => {
  const { ref } = await import("vue");
  return { useAuth: () => ({ me: ref({ authenticated: true, username: "kevin" }) }) };
});

const IDENTITY = { name: "Kevin Di Nocera", street: "Rue 1", postcode: "1020", city: "Renens", phone: "079 123 45 67", email: "k@example.ch", linkedin: null, website: null, availability: null, salary: null, permit: null };
const DATA: Record<string, unknown> = {
  "/api/identity": IDENTITY,
  "/api/profile-image": { avatar: null },
  "/api/profiles": { current_id: 1, items: [{ id: 1, name: "Principal", occupation: "Junior DevOps", is_main: true, domain_keywords: [] }] },
  "/api/documents": [
    { id: 1, filename: "ancien.pdf", doc_type: "pdf", size: 1000, text_status: "ok", uploaded_at: "2026-10-01T10:00:00Z", chunk_count: 2, kind: null },
    { id: 2, filename: "CV_Kevin.pdf", doc_type: "pdf", size: 1000, text_status: "ok", uploaded_at: "2026-11-02T10:00:00Z", chunk_count: 4, kind: null },
    { id: 3, filename: "certificat.pdf", doc_type: "pdf", size: 1000, text_status: "ok", uploaded_at: "2026-11-03T10:00:00Z", chunk_count: 0, kind: "certificate" },
  ],
  "/api/profile-chunks": [
    { id: 10, kind: "competence", title: "Kubernetes", content: "x", tags: [], active: true },
    { id: 11, kind: "competence", title: "Terraform", content: "x", tags: [], active: true },
    { id: 12, kind: "competence", title: "Ancien", content: "x", tags: [], active: false },
    { id: 13, kind: "experience", title: "Stage", content: "x", tags: [], active: true },
    { id: 14, kind: "formation", title: "CFC", content: "x", tags: [], active: true },
  ],
  "/api/criteria": { saved_at: null },
};

async function mountPage() {
  GET.mockImplementation((path: string) => Promise.resolve({ data: DATA[path] ?? null }));
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/profil", component: { template: "<div />" } }] });
  await router.push("/profil");
  const wrapper = mount(ProfileDesktop, { global: { plugins: [router], stubs: { CriteriaForm: { props: ["heading"], template: "<section data-test='criteria'><h2>{{ heading }}</h2></section>" }, ProfileGauge: true } } });
  await flushPromises();
  return wrapper;
}

afterEach(() => vi.resetAllMocks());

describe("Profil ordinateur, page unique (PR 9b, décision de Kevin du 10 novembre)", () => {
  it("l’ordre : en-tête, Mon CV, Compétences trouvées, Ce que je cherche, Mon parcours", async () => {
    const wrapper = await mountPage();
    expect(wrapper.findAll(".profile-desktop-body h2").map((h) => h.text())).toEqual(["Mon CV", "Compétences trouvées", "Ce que je cherche", "Mon parcours"]);
    expect(wrapper.get("[data-test=profile-head] h1").text()).toBe("Kevin Di Nocera");
    expect(wrapper.get("[data-test=profile-subline]").text()).toBe("Junior DevOps · Renens");
  });

  it("plus de « Changer d’image » : la pastille crayon de l’image ouvre « Ton image »", async () => {
    const wrapper = await mountPage();
    expect(wrapper.find("[data-test=change-image]").exists()).toBe(false);
    expect(wrapper.findAll(".profile-head-actions button").map((b) => b.text())).toEqual(["Modifier"]);
    const picker = wrapper.findComponent({ name: "AvatarPicker" });
    expect(picker.props("open")).toBe(false);
    await wrapper.get("[data-test=profile-image-edit]").trigger("click");
    expect(picker.props("open")).toBe(true);
  });

  it("« Modifier » ne change que le nom, le poste et le lieu", async () => {
    const wrapper = await mountPage();
    await wrapper.get("[data-test=profile-edit]").trigger("click");
    await flushPromises();
    const sheet = wrapper.findComponent({ name: "ProfileEditSheet" });
    expect(sheet.props("open")).toBe(true);
    const form = wrapper.get("[data-test=profile-edit-form]");
    expect(form.findAll("label").map((l) => l.text())).toEqual(["Nom", "Poste", "NPA", "Lieu"]);
    await wrapper.get("[data-test=profile-edit-city]").setValue("Lausanne");
    await wrapper.get("[data-test=profile-edit-occupation]").setValue("DevOps");
    PUT.mockResolvedValue({ data: {} });
    PATCH.mockResolvedValue({ data: {} });
    await form.trigger("submit");
    await flushPromises();
    // Les autres coordonnées repartent telles quelles.
    expect(PUT).toHaveBeenCalledWith("/api/identity", { body: { ...IDENTITY, city: "Lausanne" } });
    expect(PATCH).toHaveBeenCalledWith("/api/profiles/{profile_id}", { params: { path: { profile_id: 1 } }, body: { occupation: "DevOps" } });
  });

  it("Mon CV : le dernier document qui n’est pas un certificat, Voir et Remplacer", async () => {
    const wrapper = await mountPage();
    expect(wrapper.get("[data-test=profile-cv-name]").text()).toBe("CV_Kevin.pdf");
    expect(wrapper.get("[data-test=profile-cv-open]").attributes("href")).toBe("/api/documents/2/file");
    expect(wrapper.get("[data-test=profile-cv-replace]").text()).toContain("Remplacer");
  });

  it("Compétences trouvées : les blocs Compétence actifs ; « + Ajouter » ouvre un nouveau bloc", async () => {
    const wrapper = await mountPage();
    expect(wrapper.findAll(".profile-skill").map((s) => s.text())).toEqual(["Kubernetes", "Terraform"]);
    expect(wrapper.get("[data-test=profile-skill-10]").attributes("href")).toBe("/profil?onglet=competences&bloc=10");
    expect(wrapper.get("[data-test=profile-skill-add]").attributes("href")).toBe("/profil?onglet=competences&nouveau=1");
  });

  it("Mon parcours : quatre lignes, un résumé chacune, et leur page", async () => {
    const wrapper = await mountPage();
    const rows = wrapper.findAll("[data-test=profile-parcours] .criteria-row");
    expect(rows.map((r) => [r.find(".criteria-row-label").text(), r.find(".criteria-row-value").text()])).toEqual([
      ["Formations", "1 formation"],
      ["Expériences", "1 expérience"],
      ["Documents et certificats", "2 documents · 1 certificat"],
      ["Coordonnées", "Renens · 079…"],
    ]);
    expect(rows.map((r) => r.attributes("href"))).toEqual([
      "/profil?onglet=formations",
      "/profil?onglet=experiences",
      "/profil?onglet=documents",
      "/profil?onglet=coordonnees",
    ]);
    expect(rows[0]!.find(".arrow-circle").attributes("aria-hidden")).toBe("true");
  });
});
