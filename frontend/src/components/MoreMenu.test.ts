import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import MoreMenu from "./MoreMenu.vue";

describe("MoreMenu (docs/50 §1)", () => {
  it("Échap ferme le seul menu et rend le focus ; les flèches passent d'une action à l'autre", async () => {
    const run = vi.fn();
    const outside = vi.fn();
    document.addEventListener("keydown", outside);
    const wrapper = mount(MoreMenu, {
      attachTo: document.body,
      props: {
        items: [
          { label: "Modifier", test: "edit", run },
          { label: "Supprimer", test: "remove", run: vi.fn(), danger: true },
        ],
      },
    });
    await wrapper.find("[data-test=more]").trigger("click");
    expect(document.activeElement?.getAttribute("data-test")).toBe("edit");
    await wrapper.find("[data-test=edit]").trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("remove");

    outside.mockClear();
    await wrapper.find("[data-test=remove]").trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    expect(document.activeElement?.getAttribute("data-test")).toBe("more");
    // Le panneau autour n'a rien reçu : il reste ouvert.
    expect(outside).not.toHaveBeenCalled();

    await wrapper.find("[data-test=more]").trigger("click");
    await wrapper.find("[data-test=edit]").trigger("click");
    expect(run).toHaveBeenCalledOnce();
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    document.removeEventListener("keydown", outside);
    wrapper.unmount();
  });

  it("liens, nombre, et un filet avant les suppressions (docs/74 §5)", async () => {
    const wrapper = mount(MoreMenu, {
      props: {
        items: [
          { label: "Lettre (Word)", test: "letter", href: "/api/letters/1/docx", download: true },
          { label: "Ouvrir l'annonce", test: "page", href: "https://exemple.ch/annonce" },
          { label: "Contacts", test: "contacts", count: 2, run: vi.fn() },
          { label: "Supprimer", test: "remove", danger: true, run: vi.fn() },
        ],
      },
    });
    await wrapper.find("[data-test=more]").trigger("click");
    const letter = wrapper.find("[data-test=letter]");
    expect(letter.attributes("download")).toBe("");
    expect(letter.attributes("target")).toBeUndefined();
    const page = wrapper.find("[data-test=page]");
    expect(page.attributes("target")).toBe("_blank");
    expect(page.attributes("rel")).toBe("noopener noreferrer");
    expect(page.text()).toContain("↗");
    expect(wrapper.find("[data-test=contacts]").text()).toBe("Contacts (2)");
    const roles = wrapper.findAll("[role=menu] > li").map((li) => li.attributes("role"));
    expect(roles).toEqual(["none", "none", "none", "separator", "none"]);
  });

  it("une seule action ordinaire s'affiche directement, sans menu (docs/76 §3)", async () => {
    const run = vi.fn();
    const single = mount(MoreMenu, { props: { items: [{ label: "Contacts", test: "contacts", count: 2, run }] } });
    expect(single.find("[data-test=more]").exists()).toBe(false);
    expect(single.find("[data-test=contacts]").text()).toBe("Contacts (2)");
    await single.find("[data-test=contacts]").trigger("click");
    expect(run).toHaveBeenCalledOnce();
    // Une suppression seule garde son menu ; `inline` faux aussi.
    const danger = mount(MoreMenu, { props: { items: [{ label: "Supprimer", test: "remove", danger: true, run }] } });
    expect(danger.find("[data-test=more]").exists()).toBe(true);
    const kept = mount(MoreMenu, { props: { items: [{ label: "CV", test: "cv", run }], inline: false } });
    expect(kept.find("[data-test=more]").exists()).toBe(true);
  });

  it("clavier : nom de la liste, Début / Fin, actions indisponibles sautées, Tab ferme", async () => {
    const wrapper = mount(MoreMenu, {
      attachTo: document.body,
      props: {
        label: "Actions sur l'entreprise",
        items: [
          { label: "Modifier", test: "edit", run: vi.fn() },
          { label: "Chercher", test: "search", run: vi.fn(), disabled: true },
          { label: "Contacts", test: "contacts", run: vi.fn() },
          { label: "Supprimer", test: "remove", run: vi.fn(), danger: true },
        ],
      },
    });
    await wrapper.find("[data-test=more]").trigger("click");
    const menu = wrapper.find("[role=menu]");
    expect(menu.attributes("aria-labelledby")).toBe(wrapper.find("[data-test=more]").attributes("id"));
    await wrapper.find("[data-test=edit]").trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("contacts");
    await wrapper.find("[data-test=contacts]").trigger("keydown", { key: "End" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("remove");
    await wrapper.find("[data-test=remove]").trigger("keydown", { key: "Home" });
    expect(document.activeElement?.getAttribute("data-test")).toBe("edit");
    await wrapper.find("[data-test=edit]").trigger("keydown", { key: "Tab" });
    expect(wrapper.find("[role=menu]").exists()).toBe(false);
    wrapper.unmount();
  });
});

