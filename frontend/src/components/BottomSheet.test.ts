import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BottomSheet from "./BottomSheet.vue";

describe("BottomSheet (règles §4)", () => {
  it("titre à gauche, ✕ « Fermer », actions en bas ; ✕ et Échap ferment", async () => {
    const wrapper = mount(BottomSheet, {
      attachTo: document.body,
      props: { open: true, title: "Filtres" },
      slots: { default: "<p>Statut</p>", actions: '<button class="primary">Afficher 3 offres</button>' },
    });
    await wrapper.vm.$nextTick();
    const dialog = wrapper.find("dialog");
    expect(dialog.attributes("open")).toBeDefined();
    expect(dialog.attributes("aria-labelledby")).toBe(wrapper.find(".sheet-title").attributes("id"));
    expect(wrapper.find(".sheet-title").text()).toBe("Filtres");
    expect(wrapper.find(".sheet-actions").text()).toBe("Afficher 3 offres");
    await wrapper.find("[data-test=sheet-close]").trigger("click");
    await dialog.trigger("cancel");
    expect(wrapper.emitted("close")).toHaveLength(2);
    wrapper.unmount();
  });

  it("la tabulation tourne dans la feuille : du dernier contrôle au premier, et l’inverse avec Maj", async () => {
    const wrapper = mount(BottomSheet, {
      attachTo: document.body,
      props: { open: true, title: "Filtres" },
      slots: { default: '<input data-test="champ">', actions: '<button data-test="dernier">Afficher</button>' },
    });
    await wrapper.vm.$nextTick();
    const first = wrapper.find("[data-test=sheet-close]").element as HTMLElement;
    const last = wrapper.find("[data-test=dernier]").element as HTMLElement;
    last.focus();
    await wrapper.find("dialog").trigger("keydown", { key: "Tab" });
    expect(document.activeElement).toBe(first);
    await wrapper.find("dialog").trigger("keydown", { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
    (wrapper.find("[data-test=champ]").element as HTMLElement).focus();
    await wrapper.find("dialog").trigger("keydown", { key: "Tab" });
    expect(document.activeElement).toBe(wrapper.find("[data-test=champ]").element);
    wrapper.unmount();
  });

  it("plein écran avec `full` (la cloche)", () => {
    const wrapper = mount(BottomSheet, { props: { open: false, title: "Alertes", full: true } });
    expect(wrapper.find("dialog").classes()).toContain("sheet-full");
  });

  it("panneau à formulaire avec `icon` (PR 37) : pastille, titre, sous-titre, clic à l’extérieur", async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true, title: "Ajouter", subtitle: "Une offre ou une candidature spontanée", icon: "plus" },
      attachTo: document.body,
    });
    const dialog = wrapper.find("dialog");
    expect(dialog.classes()).toContain("sheet-panel");
    expect(wrapper.find(".sheet-badge").attributes("aria-hidden")).toBe("true");
    expect(dialog.attributes("aria-labelledby")).toBe(wrapper.find(".sheet-title").attributes("id"));
    expect(wrapper.find(".sheet-subtitle").text()).toBe("Une offre ou une candidature spontanée");
    // Un clic sur le voile (la <dialog> elle-même) ferme ; un clic dans le panneau, non.
    await wrapper.find(".sheet-body").trigger("click");
    expect(wrapper.emitted("close")).toBeUndefined();
    await dialog.trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });

  it("îlot du 17.11 : « fit » par défaut, sans poignée ; aria-modal à true", () => {
    const wrapper = mount(BottomSheet, { props: { open: false, title: "Autres exports" } });
    const dialog = wrapper.find("dialog");
    expect(dialog.classes()).toContain("sheet-fit");
    expect(dialog.attributes("aria-modal")).toBe("true");
    expect(wrapper.find("[data-test=sheet-handle]").exists()).toBe(false);
  });

  it("la poignée change la taille au clic et au clavier (« Agrandir » / « Réduire »)", async () => {
    const wrapper = mount(BottomSheet, { attachTo: document.body, props: { open: true, title: "Compatibilité", size: "medium" } });
    await wrapper.vm.$nextTick();
    const handle = wrapper.find("[data-test=sheet-handle]");
    const dialog = wrapper.find("dialog");
    expect(handle.attributes("aria-label")).toBe("Agrandir");
    expect(dialog.classes()).toContain("sheet-h-medium");
    await handle.trigger("keydown", { key: "ArrowUp" });
    expect(dialog.classes()).toContain("sheet-h-large");
    expect(handle.attributes("aria-label")).toBe("Réduire");
    await handle.trigger("keydown", { key: "ArrowDown" });
    expect(dialog.classes()).toContain("sheet-h-medium");
    await handle.trigger("click");
    expect(dialog.classes()).toContain("sheet-h-large");
    await handle.trigger("click");
    expect(handle.attributes("aria-label")).toBe("Agrandir");
    wrapper.unmount();
  });

  it("« large » (Filtres) commence grande, poignée « Réduire » ; la barre d’actions reste dans la feuille", async () => {
    const wrapper = mount(BottomSheet, {
      attachTo: document.body,
      props: { open: true, title: "Filtres", size: "large" },
      slots: { default: "<p>Statut</p>", actions: "<button>Tout effacer</button><button class=\"primary\">Afficher 60 offres</button>" },
    });
    await wrapper.vm.$nextTick();
    expect(wrapper.find("dialog").classes()).toEqual(expect.arrayContaining(["sheet-large", "sheet-h-large"]));
    expect(wrapper.find("[data-test=sheet-handle]").attributes("aria-label")).toBe("Réduire");
    // La barre est un enfant direct de la feuille, après le corps qui défile : elle ne part pas avec le défilement.
    const inner = wrapper.find(".sheet-inner").element;
    expect(inner.lastElementChild?.classList.contains("sheet-actions")).toBe(true);
    expect(wrapper.find(".sheet-body .sheet-actions").exists()).toBe(false);
    wrapper.unmount();
  });

  it("Échap ferme et le focus revient au bouton d’origine", async () => {
    const origin = document.createElement("button");
    document.body.append(origin);
    origin.focus();
    const wrapper = mount(BottomSheet, { attachTo: document.body, props: { open: false, title: "Langue" } });
    await wrapper.setProps({ open: true });
    await new Promise((resolve) => setTimeout(resolve));
    await wrapper.find("dialog").trigger("cancel");
    expect(wrapper.emitted("close")).toHaveLength(1);
    await wrapper.setProps({ open: false });
    await new Promise((resolve) => setTimeout(resolve));
    expect(document.activeElement).toBe(origin);
    wrapper.unmount();
    origin.remove();
  });

  it("une seule feuille ouverte à la fois : ouvrir la seconde ferme la première", async () => {
    const first = mount(BottomSheet, { attachTo: document.body, props: { open: false, title: "Actions" } });
    const second = mount(BottomSheet, { attachTo: document.body, props: { open: false, title: "Compatibilité" } });
    await first.setProps({ open: true });
    await new Promise((resolve) => setTimeout(resolve));
    await second.setProps({ open: true });
    await new Promise((resolve) => setTimeout(resolve));
    expect(first.emitted("close")).toHaveLength(1);
    expect(second.emitted("close")).toBeUndefined();
    first.unmount();
    second.unmount();
  });

  it("`modeless` (« Pourquoi » du CV) : sans voile, aria-modal à false, focus dedans, Échap ferme", async () => {
    const wrapper = mount(BottomSheet, { attachTo: document.body, props: { open: false, title: "Expérience", modeless: true } });
    await wrapper.setProps({ open: true });
    await new Promise((resolve) => setTimeout(resolve));
    const dialog = wrapper.find("dialog");
    expect(dialog.attributes("aria-modal")).toBe("false");
    expect(dialog.classes()).toContain("sheet-modeless");
    expect(dialog.element.contains(document.activeElement)).toBe(true);
    await dialog.trigger("click");
    expect(wrapper.emitted("close")).toBeUndefined();
    await dialog.trigger("keydown", { key: "Escape" });
    expect(wrapper.emitted("close")).toHaveLength(1);
    wrapper.unmount();
  });
});
