import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ChunkProposals from "./ChunkProposals.vue";

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  QUIET: {},
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

const FOUND = {
  name: "Diego Exemple",
  street: "Rue de l’Exemple 12",
  postcode: "1000",
  city: "Lausanne",
  phone: "079 000 00 00",
  email: "diego@example.ch",
};
const PROPOSAL = { kind: "competence" as const, title: "Lecture de schémas", content: "Schémas électriques.", tags: [] as string[], duplicate_of: null };

function identities(saved: Record<string, string | null>, found: Record<string, string | null> = FOUND) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({ data: path === "/api/identity" ? saved : found }),
  );
}

async function mountPanel() {
  const wrapper = mount(ChunkProposals, {
    props: { documentId: 3, documentName: "cv-fictif.pdf", proposals: [PROPOSAL], existing: [] },
  });
  await flushPromises();
  return wrapper;
}

describe("ChunkProposals, « Tes coordonnées » (B, Kevin 16.11)", () => {
  it("propose seulement les champs vides du profil, et les compte comme un élément", async () => {
    identities({ name: "Diego E.", phone: "", street: null, postcode: null, city: null, email: null });
    const wrapper = await mountPanel();
    const block = wrapper.get("[data-test=proposal-contact]");
    expect(block.find("[data-test=contact-name]").exists()).toBe(false);
    expect((block.get("[data-test=contact-phone]").element as HTMLInputElement).value).toBe("079 000 00 00");
    expect((block.get("[data-test=contact-postcode]").element as HTMLInputElement).value).toBe("1000");
    expect(wrapper.get("[data-test=add-proposals]").text()).toContain("Ajouter 2 éléments");
    expect(PUT).not.toHaveBeenCalled();
  });

  it("rien enregistré avant « Ajouter » ; à l’ajout, seuls les champs encore vides partent, modifiés", async () => {
    identities({ name: null, street: null, postcode: null, city: null, phone: null, email: null });
    const wrapper = await mountPanel();
    await wrapper.get("[data-test=contact-city]").setValue("Lausanne 1");
    // Entre-temps, le téléphone a été rempli ailleurs : il n'est pas écrasé.
    identities({ name: null, street: null, postcode: null, city: null, phone: "021 000 00 00", email: null });
    PUT.mockResolvedValue({ data: {} });
    POST.mockResolvedValue({ data: { id: 1 } });
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith("/api/identity", {
      body: { name: "Diego Exemple", street: "Rue de l’Exemple 12", postcode: "1000", city: "Lausanne 1", email: "diego@example.ch" },
    });
    expect(wrapper.emitted("saved")?.[0]).toEqual([2]);
  });

  it("décoché, le bloc n’enregistre rien ; tout rempli, le bloc n’apparaît pas", async () => {
    identities({ name: null, street: null, postcode: null, city: null, phone: null, email: null });
    const wrapper = await mountPanel();
    await wrapper.get("[data-test=proposal-contact] input[type=checkbox]").setValue(false);
    POST.mockResolvedValue({ data: { id: 1 } });
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(PUT).not.toHaveBeenCalled();
    expect(wrapper.emitted("saved")?.[0]).toEqual([1]);

    identities(FOUND);
    const full = await mountPanel();
    expect(full.find("[data-test=proposal-contact]").exists()).toBe(false);
  });

  it("des coordonnées refusées (NPA) arrêtent l’ajout et le disent", async () => {
    identities({ name: null, street: null, postcode: null, city: null, phone: null, email: null });
    const wrapper = await mountPanel();
    PUT.mockResolvedValue({ data: undefined });
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(wrapper.text()).toContain("Coordonnées refusées");
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.emitted("saved")).toBeUndefined();
  });
});
