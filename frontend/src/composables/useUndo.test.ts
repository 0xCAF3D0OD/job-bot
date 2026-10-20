import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import InlineConfirm from "../components/InlineConfirm.vue";
import UndoToast from "../components/UndoToast.vue";
import { offerUndo, UNDO_MS, useUndo } from "./useUndo";

afterEach(async () => {
  await useUndo().flush();
  vi.useRealTimers();
});

describe("Annuler plutôt que confirmer (docs/108 §1)", () => {
  it("l'action part au bout de 6 s ; « Annuler » la remet et rien ne part", async () => {
    vi.useFakeTimers();
    const commit = vi.fn();
    const restore = vi.fn();
    void offerUndo({ message: "Contact retiré", commit, restore });
    const toast = mount(UndoToast);
    await flushPromises();
    expect(toast.text()).toContain("Contact retiré");
    vi.advanceTimersByTime(UNDO_MS - 1);
    expect(commit).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    await flushPromises();
    expect(commit).toHaveBeenCalledWith(false);
    expect(toast.find("[data-test=undo-toast]").exists()).toBe(false);

    const commit2 = vi.fn();
    void offerUndo({ message: "Bloc supprimé", commit: commit2, restore });
    await flushPromises();
    await toast.find("[data-test=undo]").trigger("click");
    await flushPromises();
    expect(restore).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(UNDO_MS * 2);
    expect(commit2).not.toHaveBeenCalled();
  });

  it("un nouveau bandeau valide le précédent ; un échec remet ce qui était caché", async () => {
    const first = vi.fn();
    const restore = vi.fn();
    void offerUndo({ message: "A", commit: first, restore: vi.fn() });
    await offerUndo({ message: "B", commit: () => false, restore });
    expect(first).toHaveBeenCalledTimes(1);
    await useUndo().flush();
    expect(restore).toHaveBeenCalledTimes(1);
  });

  it("le compte s'arrête tant que la souris est sur le bandeau", async () => {
    vi.useFakeTimers();
    const commit = vi.fn();
    void offerUndo({ message: "Site retiré", commit, restore: vi.fn() });
    const toast = mount(UndoToast);
    await flushPromises();
    await toast.find("[data-test=undo-toast]").trigger("mouseenter");
    vi.advanceTimersByTime(UNDO_MS * 2);
    expect(commit).not.toHaveBeenCalled();
    await toast.find("[data-test=undo-toast]").trigger("mouseleave");
    vi.advanceTimersByTime(UNDO_MS);
    await flushPromises();
    expect(commit).toHaveBeenCalledTimes(1);
  });

  it("la confirmation dans la page : le focus sur « Garder », Échap annule", async () => {
    const wrapper = mount(InlineConfirm, { props: { message: "Refuser la demande ?" }, attachTo: document.body });
    expect(document.activeElement).toBe(wrapper.find("[data-test=inline-confirm-no]").element);
    await wrapper.find("[data-test=inline-confirm]").trigger("keydown", { key: "Escape" });
    expect(wrapper.emitted("cancel")).toHaveLength(1);
    await wrapper.find("[data-test=inline-confirm-yes]").trigger("click");
    expect(wrapper.emitted("confirm")).toHaveLength(1);
    wrapper.unmount();
  });

  it("plus aucune fenêtre window.confirm ni window.prompt dans l'interface (0.77.1)", () => {
    const found: string[] = [];
    const walk = (dir: string): void => {
      for (const name of readdirSync(dir)) {
        const path = join(dir, name);
        if (statSync(path).isDirectory()) walk(path);
        else if (/\.(vue|ts)$/.test(name) && !name.endsWith(".test.ts") && /window\.(confirm|prompt)\(/.test(readFileSync(path, "utf-8"))) found.push(path);
      }
    };
    walk(join(__dirname, ".."));
    expect(found).toEqual([]);
  });
});
