import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProfileView from "./ProfileParcours.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));

afterEach(() => vi.resetAllMocks());

const doc = {
  id: 4,
  filename: "CV.pdf",
  doc_type: "pdf",
  size: 120_000,
  text_status: "ok",
  uploaded_at: "2026-10-05T08:00:00Z",
  chunk_count: 1,
};
const chunk = {
  id: 9,
  kind: "competence",
  title: "Kubernetes",
  content: "CKA en cours",
  tags: ["infra"],
  active: true,
  document_id: 4,
  created_at: "2026-10-05T08:00:00Z",
  updated_at: "2026-10-05T08:00:00Z",
};

function mockApi(): void {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/documents"
          ? [doc]
          : path === "/api/profile-chunks"
            ? [chunk]
            : { id: 4, text_status: "ok", text: "Expérience\nAdministrateur Linux chez Acme, 2022-2025" },
    }),
  );
}

describe("ProfileView", () => {
  it("affiche documents et blocs, filtre par type", async () => {
    mockApi();
    const wrapper = mount(ProfileView);
    await flushPromises();
    expect(wrapper.find("[data-test=document]").text()).toContain("CV.pdf");
    expect(wrapper.find("[data-test=document]").text()).toContain("117 Ko");
    expect(wrapper.findAll("[data-test=chunk]")).toHaveLength(1);

    const formationTab = wrapper.findAll("[role=tab]").find((t) => t.text().startsWith("Formation"));
    await formationTab?.trigger("click");
    expect(wrapper.findAll("[data-test=chunk]")).toHaveLength(0);
  });

  it("envoie un fichier en multipart", async () => {
    mockApi();
    POST.mockResolvedValue({ data: { ...doc, id: 5, text_status: "unreadable" }, response: { status: 201 } });
    const wrapper = mount(ProfileView);
    await flushPromises();

    const input = wrapper.find("[data-test=file-input]");
    const file = new File(["%PDF-1.4"], "scan.pdf", { type: "application/pdf" });
    Object.defineProperty(input.element, "files", { value: [file] });
    await input.trigger("change");
    await flushPromises();

    const [path, options] = POST.mock.calls[0] as [string, { bodySerializer: () => FormData }];
    expect(path).toBe("/api/documents");
    expect(options.bodySerializer().get("file")).toBe(file);
    expect(wrapper.find("[role=status]").text()).toContain("pas lisible");
  });

  it("crée un bloc à partir d'un passage sélectionné", async () => {
    mockApi();
    POST.mockResolvedValue({ data: { ...chunk, id: 10 }, response: { status: 201 } });
    const wrapper = mount(ProfileView, { attachTo: document.body });
    await flushPromises();

    await wrapper.find("[data-test=document] button").trigger("click");
    await flushPromises();
    const textNode = wrapper.find(".doc-text").element.firstChild as Text;
    const range = document.createRange();
    const start = textNode.data.indexOf("Administrateur");
    range.setStart(textNode, start);
    range.setEnd(textNode, start + "Administrateur Linux".length);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(range);

    await wrapper.find("[data-test=chunk-from-selection]").trigger("click");
    const content = wrapper.find("#chunk-content").element as HTMLTextAreaElement;
    expect(content.value).toBe("Administrateur Linux");

    await wrapper.find("#chunk-title").setValue("Admin chez Acme");
    await wrapper.find("[data-test=chunk-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/profile-chunks", {
      body: expect.objectContaining({
        kind: "experience",
        title: "Admin chez Acme",
        content: "Administrateur Linux",
        document_id: 4,
      }),
    });
    expect(wrapper.find("[data-test=chunk-form]").exists()).toBe(false);
    wrapper.unmount();
  });
});

describe("propositions de blocs", () => {
  it("propose, laisse décocher les doublons, ajoute la sélection", async () => {
    mockApi();
    POST.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/documents/{document_id}/propose-chunks"
          ? {
              data: [
                { kind: "competence", title: "Kubernetes", content: "K3s", tags: ["k8s"], duplicate_of: 9 },
                { kind: "experience", title: "Projets 42", content: "Cloud-1, Webserv", tags: [], duplicate_of: null },
              ],
              response: { status: 200 },
            }
          : { data: { id: 50 }, response: { status: 201 } },
      ),
    );
    const wrapper = mount(ProfileView);
    await flushPromises();
    await wrapper.find("[data-test=propose-4]").trigger("click");
    await flushPromises();

    const proposals = wrapper.findAll("[data-test=proposal]");
    expect(proposals).toHaveLength(2);
    expect(proposals[0]?.text()).toContain("ressemble à : Kubernetes");
    expect((proposals[0]?.find("input[type=checkbox]").element as HTMLInputElement).checked).toBe(false);
    expect(wrapper.find("[data-test=add-proposals]").text()).toContain("Ajouter 1 bloc(s)");

    await proposals[1]?.find("input[type=text]").setValue("Projets 42 Lausanne");
    await wrapper.find("[data-test=proposals]").trigger("submit");
    await flushPromises();
    const created = POST.mock.calls.filter((c) => c[0] === "/api/profile-chunks");
    expect(created).toHaveLength(1);
    expect(created[0]?.[1]).toEqual({
      body: expect.objectContaining({ title: "Projets 42 Lausanne", kind: "experience", document_id: 4 }),
    });
    expect(wrapper.find("[data-test=proposals]").exists()).toBe(false);
    expect(wrapper.find("[role=status]").text()).toContain("1 bloc(s) ajouté(s)");
  });

  it("explique un refus de l'API", async () => {
    mockApi();
    POST.mockResolvedValue({
      data: undefined,
      error: { detail: "plafond mensuel de l'IA atteint : le relever dans les Réglages" },
      response: { status: 409 },
    });
    const wrapper = mount(ProfileView);
    await flushPromises();
    await wrapper.find("[data-test=propose-4]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toContain("plafond mensuel");
  });
});
