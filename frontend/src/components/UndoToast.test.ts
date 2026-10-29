/// <reference types="node" />
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { offerUndo, useUndo } from "../composables/useUndo";
import UndoToast from "./UndoToast.vue";

const css = readFileSync(resolve(__dirname, "../style.css"), "utf8");

afterEach(async () => {
  await useUndo().flush();
});

describe("UndoToast", () => {
  it("le bandeau dans la page (inline) montre la même action et le même « Annuler »", async () => {
    void offerUndo({ message: "Écartée : Cloud Engineer", commit: () => {}, restore: () => {} });
    const app = mount(UndoToast);
    const page = mount(UndoToast, { props: { inline: true } });
    await flushPromises();
    expect(page.find("[data-test=undo-inline]").classes()).toContain("inline");
    expect(page.text()).toContain("Écartée : Cloud Engineer");
    expect(app.find("[data-test=undo-toast]").classes()).not.toContain("inline");
  });

  it("un seul des deux est affiché ; sous 600 px, le bandeau passe au-dessus du panneau de commande", () => {
    expect(css).toContain(":root:has(.undo-toast.inline) .undo-toast:not(.inline) { display: none; }");
    expect(css).toMatch(/max-width: 599px\)[^@]*\.undo-toast\.inline \{ display: none; \}/);
    expect(css).toMatch(/:root:has\(\.action-bar\) \.toast \{ bottom: calc\([^}]*var\(--action-bar-h/);
  });
});
