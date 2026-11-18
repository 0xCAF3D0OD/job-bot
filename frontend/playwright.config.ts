// Le test d'affichage (décision de Kevin du 18.11.2026, 9 h 25, point 3 ; docs/decisions/2026-11-18-0925-controle-visuel-pr.md) :
// les écrans principaux, sur téléphone et sur ordinateur, en clair et en sombre, comparés à leur capture de
// référence (toHaveScreenshot), puis passés au script de contrôle (e2e/controles.ts, règles a à h).
//
// La démo tourne à heure figée (E2E_TIME), côté serveur (scripts/serveur_fige.py) comme côté page : les dates
// (« il y a 3 j », « jeudi 20 nov. ») sont les mêmes à chaque passage. Mode d'emploi : e2e/LISEZMOI.md.
import { defineConfig } from "@playwright/test";

// Les options de rendu de frontend/scripts/captures.py : sans elles, l'anticrénelage du texte varie de quelques
// pixels entre deux captures identiques.
const STABLE = [
  "--disable-gpu",
  "--disable-partial-raster",
  "--disable-lcd-text",
  "--force-color-profile=srgb",
  "--font-render-hinting=none",
  "--disable-skia-runtime-opts",
  "--disable-threaded-scrolling",
  "--num-raster-threads=1",
];

const PHONE = { width: 390, height: 844 };
const DESKTOP = { width: 1440, height: 900 };

export default defineConfig({
  testDir: "e2e",
  testMatch: "*.e2e.ts",
  // Les captures de référence, rangées par format : e2e/references/telephone-clair/accueil.png, etc.
  snapshotPathTemplate: "{testDir}/references/{projectName}/{arg}{ext}",
  outputDir: "e2e/resultats",
  fullyParallel: true,
  workers: process.env.CI ? 2 : 4,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never", outputFolder: "e2e/rapport" }]] : "list",
  timeout: 60_000,
  expect: {
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      scale: "css",
      // Aucune marge sur les pixels : seul l'écart de teinte d'un pixel (anticrénelage) est toléré, au seuil
      // par défaut de Playwright (0,2). Un élément qui bouge, change de couleur ou apparaît fait échouer.
      maxDiffPixels: 0,
    },
  },
  use: {
    baseURL: process.env.E2E_URL ?? "http://localhost:5200",
    locale: "fr-CH",
    timezoneId: "Europe/Zurich",
    reducedMotion: "reduce",
    deviceScaleFactor: 1,
    launchOptions: {
      args: STABLE,
      ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}),
    },
  },
  projects: [
    { name: "telephone-clair", use: { viewport: PHONE, colorScheme: "light", hasTouch: true, isMobile: true } },
    { name: "telephone-sombre", use: { viewport: PHONE, colorScheme: "dark", hasTouch: true, isMobile: true } },
    { name: "ordinateur-clair", use: { viewport: DESKTOP, colorScheme: "light" } },
    { name: "ordinateur-sombre", use: { viewport: DESKTOP, colorScheme: "dark" } },
  ],
});
