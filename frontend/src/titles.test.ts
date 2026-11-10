import { describe, expect, it } from "vitest";

import { mainMenu, navigation } from "./router";

// Une interface qui s'affiche au lieu de parler (docs/88) : le titre d'une page reprend son
// entrée du menu, et aucun titre ne commence par « Ton », « Ta », « Tes »… Les prix sortent
// des boutons (0.70.1) : ils sont dans la description au survol.
const sources = import.meta.glob<string>(["./views/*.vue", "./components/**/*.vue"], {
  query: "?raw",
  import: "default",
  eager: true,
});
const VIEWS: Record<string, string> = {
  today: "TodayView",
  jobs: "JobsView",
  bilan: "BilanView",
  account: "AccountView",
  profile: "ProfileView",
  settings: "SettingsView",
};
// Les pages de présentation gardent leurs phrases : la connexion, la présentation, l'accueil.
const PRESENTATION = ["LoginView", "DiscoverView", "WelcomeView"];
const POSSESSIVE = /^(Ton|Ta|Tes|Toi|Mon|Ma|Mes)\b/;
// Titres repris tels quels des maquettes qui font foi (Mon compte ; Mes alertes e-mail, maquette du 8 novembre ;
// Mon parcours, maquette Compte, déjà là avant le lot 18 : le sur-titre est passé de GroupedList à un h2 ; Ta candidature,
// maquette PreparerOrdinateur du 9 novembre ; Mon CV, maquette ProfilOrdinateur, et Mon parcours, demandé par Kevin le
// 10 novembre pour le Profil ordinateur).
const MAQUETTE = new Set([
  "./components/AccountMenu.vue : Mon compte",
  "./views/AlertsView.vue : Mes alertes e-mail",
  "./views/AccountView.vue : Mon parcours",
  "./views/PreparationView.vue : Ta candidature",
  "./components/ProfileDesktop.vue : Mon CV",
  "./components/ProfileDesktop.vue : Mon parcours",
]);

function template(source: string): string {
  return source.slice(source.indexOf("<template>"));
}

describe("titres (docs/88)", () => {
  it("le menu principal : trois entrées, une question chacune (docs/126 §1)", () => {
    expect(mainMenu.map((entry) => entry.label)).toEqual(["Aujourd'hui", "Candidatures", "Bilan"]);
  });

  it("chaque page affiche comme titre son nom de page, Réglages à part", () => {
    for (const entry of navigation) {
      // Les Réglages (étape 10b) : une rubrique par page, son nom en titre (SettingsView.test.ts).
      if (entry.name === "settings") continue;
      // Aujourd'hui (maquette du 8 novembre, LISEZMOI : « H1 = action du jour ») : la date au-dessus, pas le nom de la page.
      if (entry.name === "today") continue;
      // Profil sur ordinateur (maquette ProfilOrdinateur) : le nom en titre ; « Profil » reste le titre du téléphone.
      const view = VIEWS[entry.name];
      expect(view, entry.name).toBeDefined();
      const html = template(sources[`./views/${view}.vue`]!);
      const title = /<PageHero[^>]*?\stitle="([^"]+)"/.exec(html)?.[1] ?? /<h1>([^<]+)<\/h1>/.exec(html)?.[1];
      expect(title, entry.name).toBe(entry.label);
      expect(/<PageHero[^>]*\ssubtitle=/.test(html), entry.name).toBe(false);
    }
  });

  it("aucun titre, onglet ou légende ne commence par un possessif", () => {
    const found: string[] = [];
    for (const [path, source] of Object.entries(sources)) {
      if (PRESENTATION.some((name) => path.endsWith(`/${name}.vue`))) continue;
      const html = template(source);
      const headings = [
        ...html.matchAll(/<(h[1-4]|legend)\b[^>]*>\s*([^<{]+?)\s*</g),
        ...html.matchAll(/<(PageHero|SidePanel)\b[^>]*?\stitle="([^"]+)"/g),
      ];
      for (const match of headings) {
        if (POSSESSIVE.test(match[2]!) && !MAQUETTE.has(`${path} : ${match[2]}`)) found.push(`${path} : ${match[2]}`);
      }
    }
    expect(found).toEqual([]);
  });

  it("aucun prix dans le libellé d'un bouton (0.70.1)", () => {
    const found: string[] = [];
    for (const [path, source] of Object.entries(sources)) {
      for (const match of template(source).matchAll(/<button\b[^>]*>([\s\S]*?)<\/button>/g)) {
        const label = match[1]!.replace(/<HoverNote\b[^>]*>/g, "");
        if (/CHF|\d\s?\$/.test(label.replace(/\{\{[\s\S]*?\}\}/g, (expr) => (/CHF/.test(expr) ? "CHF" : "")))) {
          found.push(`${path} : ${label.trim().slice(0, 60)}`);
        }
      }
    }
    expect(found).toEqual([]);
  });
});
