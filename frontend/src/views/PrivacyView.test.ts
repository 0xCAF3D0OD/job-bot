import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import PrivacyView from "./PrivacyView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

async function mountPage(contact: string | null, guestMailbox = false, billing = false, getemall = false) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/privacy"
          ? { contact, guest_mailbox: guestMailbox, billing, getemall }
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

  it("l'extension : ce qu'elle lit, quand, et ce qu'elle envoie (docs/142)", async () => {
    const text = (await mountPage("Kevin")).find("[data-test=privacy-extension]").text();
    expect(text).toContain("qu'au clic sur son icône");
    expect(text).toContain("seulement l'annonce et son adresse");
    expect(text).toContain("Jamais tes cookies");
    expect(text).toContain("Ton nom est retiré");
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

  it("Get'emAll, seulement une fois la connexion ouverte (docs/140)", async () => {
    const closed = await mountPage("Kevin, Lausanne");
    expect(closed.find("[data-test=privacy-getemall]").exists()).toBe(false);
    expect(closed.find("[data-test=privacy-revoke]").exists()).toBe(false);
    expect(closed.text()).not.toContain("apps reliées");
    const open = await mountPage("Kevin, Lausanne", false, false, true);
    const text = open.find("[data-test=privacy-getemall]").text();
    expect(text).toContain("seulement si tu l'as coché");
    expect(text).toContain("l'identifiant de ton compte jobA1");
    expect(open.find("[data-test=privacy-revoke]").text()).toContain("Réglages › Connexions");
    expect(open.text()).toContain("et l'accès des apps reliées est retiré");
    // La section vient juste après celle de l'IA.
    const titles = open.findAll("h2").map((h) => h.text());
    expect(titles[titles.indexOf("Ce qui part à l'IA (Anthropic)") + 1]).toBe("Get'emAll, si tu le relies");
  });

  it("sans mentions : le dit", async () => {
    const wrapper = await mountPage(null);
    expect(wrapper.find("[data-test=privacy-missing]").exists()).toBe(true);
  });
});
