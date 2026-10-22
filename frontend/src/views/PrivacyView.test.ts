import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import PrivacyView from "./PrivacyView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

async function mountPage(contact: string | null, guestMailbox = false, billing = false) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/privacy"
          ? { contact, guest_mailbox: guestMailbox, billing }
          : { authenticated: false, username: null, setup_needed: false, auth_enabled: true, is_owner: false },
    }),
  );
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/tes-donnees");
  const wrapper = mount(PrivacyView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("page Tes données (docs/65 §6)", () => {
  it("dit ce qui part à l'IA, et jamais les coordonnées", async () => {
    const wrapper = await mountPage("Kevin, Lausanne");
    expect(wrapper.text()).toContain("Jamais tes coordonnées");
    expect(wrapper.text()).toContain("30 jours");
    expect(wrapper.find("[data-test=privacy-contact]").text()).toBe("Kevin, Lausanne");
  });

  it("les e-mails des sites : la boîte de jobA1 en Suisse, vidée ; sinon, celle de la plateforme (docs/113)", async () => {
    const guest = await mountPage("Kevin", true);
    const text = guest.find("[data-test=privacy-mailbox]").text();
    expect(text).toContain("hébergée en Suisse chez Infomaniak");
    expect(text).toContain("les efface de cette boîte");
    expect(text).toContain("30 minutes");
    const shared = await mountPage("Kevin", false);
    expect(shared.find("[data-test=privacy-mailbox]").text()).toContain("que l'exploitant administre");
  });

  it("le paiement de Plus, seulement une fois ouvert (docs/125 §6)", async () => {
    const closed = await mountPage("Kevin");
    expect(closed.find("[data-test=privacy-billing]").exists()).toBe(false);
    const open = await mountPage("Kevin", true, true);
    const text = open.find("[data-test=privacy-billing]").text();
    expect(text).toContain("Payrexx, un prestataire suisse");
    expect(text).toContain("10 ans");
    expect(open.find("[data-test=privacy-billing] a").attributes("href")).toBe("/conditions");
  });

  it("sans mentions : le dit", async () => {
    const wrapper = await mountPage(null);
    expect(wrapper.find("[data-test=privacy-missing]").exists()).toBe(true);
  });
});
