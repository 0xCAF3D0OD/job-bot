// L'écran de lancement (§53, index.html) s'efface quand la page s'affiche. La page Assistant du téléphone vit hors
// de <main id="contenu">, qui reste vide : sans règle pour elle, le logo jobA1 la couvrait (Kevin, 19.11.2026).
import { expect, test } from "@playwright/test";

test.describe("écran de lancement", () => {
  test.beforeEach(({}, info) => test.skip(!info.project.name.startsWith("telephone"), "la page Assistant est celle du téléphone"));

  test("la page Assistant du téléphone n'est pas cachée par le logo", async ({ page }) => {
    // La démo n'a pas d'IA : on simule sa présence, comme frontend/scripts/regles.py.
    await page.route("**/api/assistant/status", (route) => route.fulfill({ json: { available: true, model: "demo" } }));
    await page.goto("/assistant");
    await expect(page.locator("[data-test=assistant-panel]")).toBeVisible();
    await expect(page.locator("#lancement")).toBeHidden();
  });
});
