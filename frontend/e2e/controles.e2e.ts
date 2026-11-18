// Le script de contrôle trouve ce qu'il doit trouver : une page faite exprès, avec un défaut par règle, et une page
// propre où il ne trouve rien. Sans ce test, un contrôle cassé laisserait passer tous les défauts sans bruit.
import { expect, test } from "@playwright/test";
import { controler, type Regle } from "./controles";

const BASE = `<style>
  body { margin: 0; font-family: "Figtree Variable", sans-serif; background: #fff; color: #1b1b1b; }
  .card { width: 300px; margin: 16px; padding: 16px; border: 1px solid #ddd; border-radius: 12px; background: #fff; }
  button { min-width: 44px; min-height: 44px; font: inherit; }
</style>`;

async function defauts(page: import("@playwright/test").Page, corps: string, sombre = false) {
  await page.setContent(`${BASE}${corps}`);
  const { defauts } = await page.evaluate(controler, sombre);
  return defauts;
}

const regles = (liste: { regle: Regle }[]) => [...new Set(liste.map((d) => d.regle))].sort();

test.describe("le script de contrôle", () => {
  test.beforeEach(({}, info) => test.skip(info.project.name !== "ordinateur-clair", "une fois suffit"));

  test("une page propre : aucun défaut hors police", async ({ page }) => {
    const liste = await defauts(page, `<div class="card"><p>Une carte</p><button onclick="1">Ouvrir</button></div>`);
    // La page de test n'a pas Figtree chargée : seule la règle d le dit.
    expect(regles(liste).filter((r) => r !== "d")).toEqual([]);
  });

  const CAS: [Regle, string, boolean?][] = [
    ["a", `<div class="card"><div style="width:400px">trop large</div></div>`],
    ["a", `<div class="card"><p style="overflow:hidden;white-space:nowrap;width:60px">un texte bien trop long</p></div>`],
    ["b", `<div class="card"><span class="pill" style="display:inline-block;height:40px">Relancée</span></div>`],
    ["b", `<div class="card" style="display:flex;align-items:stretch"><p style="height:80px">haut</p><span class="pill">Envoyée</span></div>`],
    ["c", `<div class="card"><h3>Pour l'ORP</h3><a href="/orp">Pour l’ORP ›</a></div>`],
    ["d", `<div class="card"><p style="font-family:Arial">Arial</p></div>`],
    ["e", `<div class="card"><p style="color:#bbb">pâle</p></div>`],
    ["f", `<div class="card"><button onclick="1" style="min-width:0;min-height:0;width:16px;height:16px;padding:0">x</button></div>`],
    ["g", `<div class="card"><a>sans destination</a></div>`],
    ["g", `<div class="card"><button onclick="1"><svg width="24" height="24"></svg></button></div>`],
    ["h", `<div class="card" style="background:#1b1b1b;color:#000">noir sur sombre</div>`],
    ["h", `<div class="card">fond blanc</div>`, true],
  ];
  for (const [regle, html, sombre] of CAS) {
    test(`règle ${regle} : ${html.replace(/<[^>]+>/g, " ").trim().slice(0, 30)}`, async ({ page }) => {
      expect(regles(await defauts(page, html, sombre))).toContain(regle);
    });
  }
});
