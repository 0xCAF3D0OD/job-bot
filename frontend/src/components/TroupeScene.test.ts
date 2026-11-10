/// <reference types="node" />
import { existsSync } from "node:fs";
import { resolve } from "node:path";

import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { useTheme } from "../composables/useTheme";
import { SCENES, sceneFile, type Scene } from "../troupe";
import TroupeScene from "./TroupeScene.vue";

// Les 4 personnages du logo (MODIFICATIONS du 9 novembre, §15).
describe("TroupeScene", () => {
  const original = globalThis.matchMedia;
  const system = (dark: boolean) =>
    (globalThis.matchMedia = ((query: string) =>
      ({ matches: dark && query.includes("dark"), addEventListener() {}, removeEventListener() {} }) as unknown as MediaQueryList));
  afterEach(() => {
    globalThis.matchMedia = original;
    useTheme().setTheme("auto");
  });

  it("pose la scène aux largeurs des maquettes, décorative, avec le fichier 2× de l'ordinateur", () => {
    const wrapper = mount(TroupeScene, { props: { scene: "envoyee" } });
    expect(wrapper.attributes("src")).toMatch(/\/troupe\/envoyee-680\.webp\?v=\d+$/);
    expect(wrapper.attributes("srcset")).toMatch(/envoyee-680\.webp\?v=\d+ 680w, .*envoyee-942\.webp\?v=\d+ 942w$/);
    expect(wrapper.attributes("sizes")).toBe("(min-width: 1024px) 471px, 340px");
    expect(wrapper.attributes("width")).toBe("340");
    expect(wrapper.attributes("height")).toBe("173");
    expect(wrapper.attributes("alt")).toBe("");
    expect(wrapper.attributes("aria-hidden")).toBe("true");
    expect(wrapper.attributes("loading")).toBe("lazy");
  });

  it("le « 1 » seul s'affiche par sa hauteur ; un écran plein charge tout de suite", () => {
    const one = mount(TroupeScene, { props: { scene: "un", height: 72, full: true } });
    expect(one.attributes("src")).toMatch(/\/troupe\/un-400\.webp/);
    expect(one.attributes("srcset")).toBeUndefined();
    expect(one.attributes("height")).toBe("72");
    expect(one.attributes("width")).toBe("35");
    expect(one.attributes("loading")).toBe("eager");
  });

  it("la variante sombre suit Réglages, ou le système en Auto", () => {
    system(true);
    expect(mount(TroupeScene, { props: { scene: "groupe" } }).attributes("src")).toMatch(/groupe-sombre-412\.webp/);
    useTheme().setTheme("light");
    expect(mount(TroupeScene, { props: { scene: "groupe" } }).attributes("src")).toMatch(/groupe-412\.webp/);
    system(false);
    useTheme().setTheme("dark");
    const dark = mount(TroupeScene, { props: { scene: "introuvable" } });
    expect(dark.attributes("src")).toMatch(/introuvable-sombre-680\.webp/);
    expect(dark.attributes("srcset")).toMatch(/introuvable-sombre-784\.webp/);
  });

  it("chaque scène a ses fichiers, en clair et en sombre", () => {
    for (const scene of Object.keys(SCENES) as Scene[]) {
      for (const dark of [false, true]) {
        for (const width of new Set([SCENES[scene].phone, SCENES[scene].desk])) {
          const path = sceneFile(scene, width, dark).split("?")[0];
          expect(existsSync(resolve(process.cwd(), `public${path}`)), path).toBe(true);
        }
      }
    }
  });
});
