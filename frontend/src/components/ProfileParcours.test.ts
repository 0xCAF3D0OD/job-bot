import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { resetCvReading } from "../composables/useCvReading";
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
  QUIET: {},
}));

afterEach(() => {
  vi.resetAllMocks();
  resetCvReading();
});

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
          : path === "/api/certificates"
            ? { certificates: [], summary: null }
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

    // Filtres sans les types vides (docs/49 §3).
    expect(wrapper.findAll(".kind-tabs [role=radio]").map((t) => t.text())).toEqual(["Tous 1", "Compétence 1"]);
    // Carte calme : le type et les mots-clés en bas, plus de Modifier / Supprimer sur la carte.
    const card = wrapper.find("[data-test=chunk]");
    expect(card.find(".chunk-foot").text()).toContain("Compétence · 1 mot-clé");
    expect(card.text()).not.toContain("Supprimer");
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

  it("crée un bloc à partir d’un passage sélectionné", async () => {
    mockApi();
    POST.mockResolvedValue({ data: { ...chunk, id: 10 }, response: { status: 201 } });
    const wrapper = mount(ProfileView, { attachTo: document.body, global: { stubs: { teleport: true } } });
    await flushPromises();

    await wrapper.find("[data-test=open-document-4]").trigger("click");
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

describe("« Proposer à partir du CV » : la même lecture que la carte Mon CV (PR 21)", () => {
  it("lance la lecture sur le serveur, montre « Lecture en cours » puis l’état « lu »", async () => {
    let documents: unknown[] = [doc];
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/documents"
            ? documents
            : path === "/api/certificates"
              ? { certificates: [], summary: null }
              : path === "/api/profile-chunks"
                ? [chunk]
                : path === "/api/documents/{document_id}/read"
                  ? [
                      { kind: "competence", title: "Kubernetes", content: "K3s", tags: ["k8s"], duplicate_of: 9 },
                      { kind: "experience", title: "Projets 42", content: "Cloud-1, Webserv", tags: [], duplicate_of: null },
                    ]
                  : null,
      }),
    );
    POST.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/documents/{document_id}/read"
          ? { data: { ...doc, read_state: "reading", read_at: null, found: null }, response: { status: 202 } }
          : { data: { id: 50 }, response: { status: 201 } },
      ),
    );
    DELETE.mockResolvedValue({ response: { status: 204 } });
    const wrapper = mount(ProfileView);
    await flushPromises();
    expect(wrapper.find(".doc-read-state").exists()).toBe(false);

    await wrapper.find("[data-test=propose-4]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/documents/{document_id}/read", { params: { path: { document_id: 4 } } });
    expect(wrapper.find("[data-test=propose-4]").attributes("aria-disabled")).toBe("true");
    expect(wrapper.find(".doc-read-state [data-test=cv-state-cours]").exists()).toBe(true);

    // La lecture finit sur le serveur : la carte passe à « lu » au passage suivant.
    documents = [{ ...doc, read_state: "done", read_at: "2026-11-10T10:00:00Z", found: { competence: 1, experience: 1 } }];
    const { useCvReading } = await import("../composables/useCvReading");
    await useCvReading().load();
    await flushPromises();
    expect(wrapper.find(".doc-read-state [data-test=cv-state-lu]").exists()).toBe(true);
  });

  it("explique un départ manqué", async () => {
    mockApi();
    POST.mockResolvedValue({ data: undefined, error: { detail: "x" }, response: { status: 500 } });
    const wrapper = mount(ProfileView);
    await flushPromises();
    await wrapper.find("[data-test=propose-4]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[role=status]").text()).toContain("La lecture n’a pas pu partir");
  });
});

describe("Mon parcours, panneaux (docs/49)", () => {
  it("sans document : un seul encart ; un bloc s’ouvre dans le panneau, Supprimer en bas", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/documents" ? [] : path === "/api/profile-chunks" ? [chunk] : null }),
    );
    PUT.mockResolvedValue({ data: chunk });
    const wrapper = mount(ProfileView, { global: { stubs: { teleport: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=profile-missing]").exists()).toBe(false);
    expect(wrapper.find("[data-test=drop-zone]").text()).toContain("Dépose ton CV");
    expect(wrapper.text()).not.toContain("Aucun document");

    await wrapper.find("[data-test=open-chunk-9]").trigger("click");
    expect((wrapper.find("#chunk-title").element as HTMLInputElement).value).toBe("Kubernetes");
    expect(wrapper.find("[data-test=remove-chunk]").exists()).toBe(true);
    await wrapper.find("[data-test=chunk-form]").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/profile-chunks/{chunk_id}", expect.objectContaining({ params: { path: { chunk_id: 9 } } }));
  });

  it("marquer un document comme certificat de travail (docs/87)", async () => {
    mockApi();
    PUT.mockResolvedValue({ data: { certificates: [], summary: null } });
    const wrapper = mount(ProfileView, { global: { stubs: { teleport: true } } });
    await flushPromises();
    expect(wrapper.find("[data-test=certificates-hint]").exists()).toBe(true);
    await wrapper.find("[data-test=open-document-4]").trigger("click");
    await flushPromises();
    await wrapper.find("[data-test=document-more]").trigger("click");
    await wrapper.find("[data-test=toggle-certificate]").trigger("click");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/documents/{document_id}/kind", {
      params: { path: { document_id: 4 } },
      body: { kind: "certificate" },
    });
    expect(GET.mock.calls.filter(([path]) => path === "/api/certificates")).toHaveLength(2);
  });
});

