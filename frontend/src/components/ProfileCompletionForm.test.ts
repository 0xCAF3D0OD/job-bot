import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

import ProfileCompletionForm from "./ProfileCompletionForm.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  QUIET: {},
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn() },
}));
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me: ref({ username: "compte-fictif" }) }) }));
afterEach(() => vi.resetAllMocks());

const FOUND = { name: "Diego Exemple", street: "Rue de l’Exemple 12", postcode: "1000", city: "Lausanne", phone: "079 000 00 00", email: null };
const EMPTY = { name: null, street: null, postcode: null, city: null, phone: null, email: null };

function server(saved: Record<string, string | null>, docs: unknown[] = [{ id: 3, kind: null, text_status: "ok" }]) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data: path === "/api/identity" ? saved : path === "/api/documents" ? docs : FOUND,
    }),
  );
}

async function mountForm() {
  const wrapper = mount(ProfileCompletionForm, { props: { sections: ["identity"] } });
  await flushPromises();
  return wrapper;
}

const input = (wrapper: Awaited<ReturnType<typeof mountForm>>, key: string) =>
  wrapper.get(`[data-test=completion-${key}]`).element as HTMLInputElement;

describe("ProfileCompletionForm, « Avant ta lettre » préremplie depuis le CV (Kevin, 16.11)", () => {
  it("sans document donné, cherche le CV et remplit les champs vides, marqués « Du CV »", async () => {
    server(EMPTY, [{ id: 2, kind: "certificate", text_status: "ok" }, { id: 3, kind: null, text_status: "ok" }]);
    const wrapper = await mountForm();
    expect(GET).toHaveBeenCalledWith("/api/identity/from-document/{document_id}", { params: { path: { document_id: 3 } } });
    expect(input(wrapper, "street").value).toBe("Rue de l’Exemple 12");
    expect(input(wrapper, "postcode").value).toBe("1000");
    const street = wrapper.get("[data-test=completion-street]").element.closest(".form-field")!;
    expect(street.textContent).toContain("Du CV");
    expect(input(wrapper, "street").getAttribute("aria-describedby")).toContain("pc-from-cv");
    expect(wrapper.get("#pc-from-cv").text()).toBe("Repris de ton CV, vérifie-le.");
    expect(PUT).not.toHaveBeenCalled();
  });

  it("un champ déjà rempli dans le profil ne change jamais ; un champ vide du CV reste vide", async () => {
    server({ ...EMPTY, name: "Diego E.", phone: "021 111 11 11" });
    const wrapper = await mountForm();
    expect(input(wrapper, "name").value).toBe("Diego E.");
    expect(input(wrapper, "phone").value).toBe("021 111 11 11");
    expect(input(wrapper, "phone").getAttribute("aria-describedby") ?? "").not.toContain("pc-from-cv");
    expect(input(wrapper, "email").value).toBe("");
  });

  it("la marque part dès qu’on modifie le champ ; « Enregistrer » met à jour le profil", async () => {
    server(EMPTY);
    const wrapper = await mountForm();
    await wrapper.get("[data-test=completion-city]").setValue("Lausanne 1");
    const city = wrapper.get("[data-test=completion-city]").element.closest(".form-field")!;
    expect(city.textContent).not.toContain("Du CV");
    expect(input(wrapper, "city").getAttribute("aria-describedby") ?? "").not.toContain("pc-from-cv");
    PUT.mockResolvedValue({ response: { ok: true } });
    expect(await (wrapper.vm as unknown as { save: () => Promise<boolean> }).save()).toBe(true);
    expect(PUT).toHaveBeenCalledWith("/api/identity", {
      body: expect.objectContaining({ name: "Diego Exemple", street: "Rue de l’Exemple 12", postcode: "1000", city: "Lausanne 1", phone: "079 000 00 00", email: null }),
    });
  });

  it("sans CV lisible, le formulaire reste vide", async () => {
    server(EMPTY, [{ id: 2, kind: "certificate", text_status: "ok" }]);
    const wrapper = await mountForm();
    expect(input(wrapper, "street").value).toBe("");
    expect(GET).not.toHaveBeenCalledWith("/api/identity/from-document/{document_id}", expect.anything());
  });
});
