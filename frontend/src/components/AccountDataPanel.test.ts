import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountDataPanel from "./AccountDataPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const SUMMARY = {
  offers: 12,
  applications: 3,
  documents: 1,
  profile_blocks: 5,
  alert_emails: 20,
  conversations: 0,
  notifications: 2,
  can_delete: true,
};

async function mountPanel(summary = SUMMARY, path = "/reglages") {
  GET.mockResolvedValue({ data: summary });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push(path);
  const wrapper = mount(AccountDataPanel, { attachTo: document.body, global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("Tes données (docs/65 §6)", () => {
  it("le résumé, et l'export après le mot de passe (docs/regles-securite-donnees.md X-1)", async () => {
    POST.mockResolvedValueOnce({ error: { detail: "mot de passe incorrect" }, response: { ok: false, headers: new Headers() } });
    POST.mockResolvedValueOnce({
      data: new Blob(["zip"]),
      response: { ok: true, headers: new Headers({ "content-disposition": 'attachment; filename="jobA1-amy-2026-11-04.zip"' }) },
    });
    const createObjectURL = vi.fn().mockReturnValue("blob:x");
    Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const { wrapper } = await mountPanel();
    // Les compteurs en une phrase (1.6.67).
    expect(wrapper.find("[data-test=account-counts] .setting-row-description").text()).toBe(
      "12 offres · 3 candidatures · 1 document · 5 blocs de profil · 20 e-mails d'alerte",
    );
    // Plus de lien direct : une session seule ne télécharge rien.
    expect(wrapper.find("a[href='/api/account/export']").exists()).toBe(false);
    await wrapper.find("[data-test=export]").trigger("click");
    expect(wrapper.find("[data-test=export-form] [data-test=inline-confirm-yes]").text()).toBe("Télécharger");
    await wrapper.find("[data-test=export-password]").setValue("faux");
    await wrapper.find("[data-test=export-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=export-error]").text()).toBe("Mot de passe incorrect.");
    expect(click).not.toHaveBeenCalled();
    await wrapper.find("[data-test=export-password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=export-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/account/export", {
      body: { password: "le-bon-mot-de-passe" },
      parseAs: "blob",
    });
    expect(createObjectURL).toHaveBeenCalled();
    expect(click).toHaveBeenCalledOnce();
    // Le mot de passe ne reste pas dans la page, et la confirmation se referme.
    expect(wrapper.find("[data-test=export-form]").exists()).toBe(false);
    click.mockRestore();
    wrapper.unmount();
  });

  it("le modèle des Réglages (1.6.67) ; la suppression seule dans sa carte rouge (C13)", async () => {
    const { wrapper } = await mountPanel();
    const card = wrapper.find("[data-test=account-data]");
    expect(card.classes()).toContain("setting-card");
    expect(wrapper.find("fieldset").exists()).toBe(false);
    expect(card.findAll(".setting-row-title").map((t) => t.text())).toEqual(["Données personnelles", "Exporter mes données"]);
    // Plus de lien dans la phrase : « Voir les durées » est l'action de la ligne.
    expect(card.find(".setting-row-description a").exists()).toBe(false);
    const retention = card.find("[data-test=account-counts] .setting-row-control [data-test=data-retention]");
    expect(retention.text()).toBe("Voir les durées");
    expect(retention.attributes("href")).toBe("/tes-donnees");
    expect(card.find(".setting-row-control [data-test=export]").text()).toBe("Télécharger");
    const danger = wrapper.find("[data-test=account-delete-card]");
    expect(danger.classes()).toContain("account-delete-card");
    expect(danger.find(".setting-row-title").text()).toBe("Supprimer mon compte");
    expect(danger.find(".setting-row-control [data-test=delete-account]").exists()).toBe(true);
    // La confirmation sous sa ligne, dans la même carte ; le bouton s'efface pendant ce temps.
    await wrapper.find("[data-test=delete-account]").trigger("click");
    expect(danger.find("[data-test=delete-form].setting-row-form").exists()).toBe(true);
    expect(wrapper.find("[data-test=delete-account]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("supprimer : le texte de la maquette, l'export ORP, « Annuler » par défaut, puis le mot de passe", async () => {
    POST.mockResolvedValueOnce({ error: { detail: "mot de passe incorrect" }, response: { ok: false } });
    POST.mockResolvedValueOnce({ response: { ok: true } });
    const { wrapper, router } = await mountPanel();
    expect(wrapper.find("[data-test=delete-account]").text()).toBe("Supprimer mon compte");
    await wrapper.find("[data-test=delete-account]").trigger("click");
    const form = wrapper.find("[data-test=delete-form]");
    expect(form.text()).toContain("Supprimer ton compte ?");
    expect(form.text()).toContain("Ton CV, tes candidatures et ton suivi ORP seront effacés. Cette action est définitive.");
    expect(form.find("[data-test=delete-export-orp]").element.tagName).toBe("BUTTON");
    expect(form.find("[data-test=inline-confirm-yes]").text()).toBe("Supprimer définitivement");
    expect(form.find("[data-test=inline-confirm-no]").text()).toBe("Annuler");
    await wrapper.find("[data-test=delete-password]").setValue("faux");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=delete-error]").text()).toBe("Mot de passe incorrect.");
    await wrapper.find("[data-test=delete-password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/account/delete", { body: { password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.path).toBe("/connexion");
    wrapper.unmount();
  });

  it("Entrée dans le mot de passe ne supprime pas ; le focus reste sur le champ", async () => {
    const { wrapper } = await mountPanel();
    await wrapper.find("[data-test=delete-account]").trigger("click");
    const input = wrapper.find("[data-test=delete-password]");
    await input.setValue("le-bon-mot-de-passe");
    (input.element as HTMLInputElement).focus();
    await input.trigger("keydown", { key: "Enter" });
    await wrapper.find("[data-test=delete-form]").trigger("submit");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(true);
    expect(document.activeElement).toBe(input.element);
    wrapper.unmount();
  });

  it("« Exporter ma feuille ORP » : le PDF du mois sur place, la confirmation reste ouverte", async () => {
    const { wrapper, router } = await mountPanel();
    GET.mockResolvedValue({ data: { month: "2026-11", count: 0, holder: { name: "", address: "" }, applications: [], searches: [] } });
    await wrapper.find("[data-test=delete-account]").trigger("click");
    const before = router.currentRoute.value.fullPath;
    const print = vi.spyOn(await import("../composables/usePrint"), "printSheet").mockImplementation(() => {});
    POST.mockResolvedValue({ response: { ok: true } });
    await wrapper.find("[data-test=delete-export-orp]").trigger("click");
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/api/orp");
    expect(print).toHaveBeenCalledOnce();
    expect(print.mock.calls[0]![1]).toMatchObject({ title: "Preuves ORP - 2026-11" });
    expect(router.currentRoute.value.fullPath).toBe(before);
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(true);
    expect(POST).not.toHaveBeenCalledWith("/api/account/delete", expect.anything());
    print.mockRestore();
    wrapper.unmount();
  });

  it("l'exploitant ne ferme pas son compte ici, même venu du menu", async () => {
    const { wrapper } = await mountPanel({ ...SUMMARY, can_delete: false }, "/reglages?rubrique=donnees&fermer=1");
    expect(wrapper.find("[data-test=delete-account]").exists()).toBe(false);
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(false);
  });

  it("venu de « Supprimer mon compte » (docs/105) : la confirmation est ouverte, le mot de passe a le focus", async () => {
    const { wrapper } = await mountPanel(SUMMARY, "/reglages?rubrique=donnees&fermer=1");
    expect(wrapper.find("[data-test=delete-form]").exists()).toBe(true);
    expect(document.activeElement).toBe(wrapper.find("[data-test=delete-password]").element);
    wrapper.unmount();
  });

  it("téléphone (0.77.4) : « Supprimer définitivement » grisé sans mot de passe, puis il supprime", async () => {
    POST.mockResolvedValueOnce({ response: { ok: true } });
    const { wrapper, router } = await mountPanel(SUMMARY, "/reglages?rubrique=donnees&fermer=1");
    expect(wrapper.find("[data-test=inline-confirm-yes]").attributes("disabled")).toBeDefined();
    await wrapper.find("[data-test=delete-password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/account/delete", { body: { password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.path).toBe("/connexion");
    wrapper.unmount();
  });
});

