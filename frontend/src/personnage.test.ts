/// <reference types="node" />
// La règle du personnage (docs/141 §1, Kevin, 6.11.2026) : sur un écran, un seul des trois — le logo
// transformé (où l'on est : transitions de page, en-têtes), le personnage (moments et écrans pleins) ou une
// petite mascotte d'humeur (état dans un petit espace : chargement, erreur dans la page, notifications).
// Jamais le personnage sur un écran de travail (fiche offre, lettre, CV, formulaires).
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import Illustration, { MAX_HEIGHT, POSE_WIDTH, type Pose } from "./components/Illustration.vue";

const SRC = resolve(process.cwd(), "src");

function vueFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return vueFiles(path);
    return name.endsWith(".vue") ? [path] : [];
  });
}
const FILES = vueFiles(SRC).map((path) => ({ path: relative(SRC, path), text: readFileSync(path, "utf8") }));
const template = (text: string) => text.slice(text.indexOf("<template>"), text.lastIndexOf("</template>"));

// Les écrans qui montrent le personnage (docs/141 §3). Un nouvel écran s'ajoute ici et dans docs/141.
export const SCREENS: Record<string, string> = {
  "views/WelcomeView.vue": "premiers pas : étape CV, « Tout est prêt. »",
  "components/AuthIllustration.vue": "connexion, téléphone et ordinateur",
  "views/NotFoundView.vue": "page introuvable",
};

// Les écrans de travail : jamais le personnage (docs/141 §1).
const WORK = [
  "views/PreparationView.vue",
  "components/OfferDetail.vue",
  "components/CvPanel.vue",
  "components/CertificateLetter.vue",
  "components/ApplicationForm.vue",
  "components/CriteriaForm.vue",
  "components/IdentityForm.vue",
  "components/InterviewForm.vue",
  "components/ManualOfferForm.vue",
  "components/OrpOutcomeForm.vue",
  "components/SpontaneousForm.vue",
  "components/FormSheet.vue",
];

// Ce qui ne va pas avec le personnage sur le même écran : le logo transformé, les mascottes d'humeur, le
// visage du 1 d'un état (FaceState, FaceMark), l'ancienne série d'illustrations.
const OTHERS = /<(MoodAnimation|FaceTransform|FaceState|FaceMark|NetworkError|SceneIllustration|AssistantMascot)\b/;

describe("Personnage : un seul des trois par écran (docs/141)", () => {
  const users = FILES.filter((f) => /<Illustration\b/.test(template(f.text)));

  it("seuls les écrans de la liste montrent le personnage", () => {
    expect(users.map((f) => f.path).sort()).toEqual(Object.keys(SCREENS).sort());
  });

  it("aucun écran de travail ne le montre", () => {
    for (const path of WORK) {
      const file = FILES.find((f) => f.path === path);
      expect(file, path).toBeDefined();
      expect(template(file?.text ?? ""), path).not.toMatch(/<Illustration\b/);
    }
  });

  it("aucune page n'affiche à la fois le personnage et une mascotte d'humeur ou le logo transformé", () => {
    for (const file of users) expect(template(file.text), file.path).not.toMatch(OTHERS);
  });
});

describe("Illustration (docs/141 §2)", () => {
  it("pose l'image 400 px, 800 px pour les écrans 2×, avec sa taille, décorative et chargée à l'affichage", async () => {
    const wrapper = mount(Illustration, { props: { pose: "loupe", height: 200 } });
    const img = wrapper.find("img");
    expect(img.attributes("src")).toMatch(/perso-11-loupe-400\.webp$/);
    expect(img.attributes("srcset")).toMatch(/perso-11-loupe-400\.webp 1x, .*perso-11-loupe-800\.webp 2x$/);
    expect(img.attributes("width")).toBe("100");
    expect(img.attributes("height")).toBe("200");
    expect(img.attributes("alt")).toBe("");
    expect(img.attributes("aria-hidden")).toBe("true");
    expect(img.attributes("loading")).toBe("lazy");
    // Le fondu attend que l'image soit là.
    expect(img.classes()).not.toContain("loaded");
    await img.trigger("load");
    expect(img.classes()).toContain("loaded");
  });

  it("un écran plein la charge tout de suite ; les hauteurs restent dans les limites", () => {
    const full = mount(Illustration, { props: { pose: "avion", height: 320, desktopHeight: 500, full: true } });
    expect(full.attributes("loading")).toBe("eager");
    expect(full.attributes("height")).toBe(String(MAX_HEIGHT.full));
    expect(full.attributes("style")).toContain(`--perso-h-wide: ${MAX_HEIGHT.desktop}px`);
    const list = mount(Illustration, { props: { pose: "debout", height: 260 } });
    expect(list.attributes("height")).toBe(String(MAX_HEIGHT.list));
  });

  it("chaque pose a ses deux fichiers ; plus de pose sans suffixe -400 ou -800", () => {
    const dir = join(SRC, "assets/personnage");
    const names = readdirSync(dir);
    for (const name of names) expect(name).toMatch(/^perso-\d\d-[a-z-]+-(400|800)\.webp$/);
    for (const pose of Object.keys(POSE_WIDTH) as Pose[]) {
      expect(names.some((n) => n.endsWith(`-${pose}-400.webp`)), pose).toBe(true);
      expect(names.some((n) => n.endsWith(`-${pose}-800.webp`)), pose).toBe(true);
    }
    expect(existsSync(join(SRC, "assets/personnage/perso-09-cables.webp"))).toBe(false);
  });
});
