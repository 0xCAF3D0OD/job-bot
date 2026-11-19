// Le test d'affichage, bloquant en CI (décision de Kevin du 18.11.2026, point 3). Pour chaque écran principal et
// chaque format (téléphone, ordinateur ; clair, sombre) :
// 1. la capture de la page entière est comparée à sa référence (e2e/references/<format>/<écran>.png) ;
// 2. le script de contrôle (controles.ts, règles a à h) ne trouve aucun défaut, hors des écarts connus listés dans
//    ecarts-connus.json, chacun avec sa raison. Un défaut absent de la liste fait échouer ; on ne relève aucun seuil.
import { readFileSync, writeFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";
import { controler, REGLES, type Defaut, type Regle } from "./controles";

// L'heure de la démo (celle du serveur figé, scripts/serveur_fige.py) : les dates affichées ne bougent pas.
const HEURE = process.env.E2E_TIME ?? "2026-11-18T10:00:00+01:00";

interface Ecran {
  nom: string;
  chemin: string | ((page: Page) => Promise<string>);
}

// La première offre de la démo : son numéro dépend de la base, on le demande au serveur.
async function premiereOffre(page: Page): Promise<string> {
  const reponse = await page.request.get("/api/offers?limit=1");
  const { items } = (await reponse.json()) as { items: { id: number }[] };
  return `/candidatures/offres?offre=${items[0].id}`;
}

// Les écrans principaux nommés par Kevin le 18.11 : Accueil, Candidatures (Offres, Envoyées, Rendez-vous), fiche d'une
// offre, Bilan, Réglages, Profil.
const ECRANS: Ecran[] = [
  { nom: "accueil", chemin: "/aujourdhui" },
  { nom: "offres", chemin: "/candidatures/offres" },
  { nom: "envoyees", chemin: "/candidatures/suivi" },
  { nom: "rendez-vous", chemin: "/candidatures/rendez-vous-orp" },
  { nom: "fiche-offre", chemin: premiereOffre },
  { nom: "bilan", chemin: "/bilan" },
  { nom: "reglages", chemin: "/reglages" },
  { nom: "profil", chemin: "/profil" },
];

interface Ecart {
  ecran: string;
  /** telephone-clair, telephone-sombre, ordinateur-clair, ordinateur-sombre ; « telephone » ou « ordinateur » pour les deux thèmes ; absent : tous. */
  format?: string;
  regle: Regle;
  /** Un morceau de la description de l'élément (« span.sent-tel-pill « Relancée » »). */
  element: string;
  raison: string;
}

const ECARTS: Ecart[] = (JSON.parse(readFileSync(new URL("./ecarts-connus.json", import.meta.url), "utf8")) as { ecarts: Ecart[] }).ecarts;

const connu = (d: Defaut, ecran: string, format: string) =>
  ECARTS.some((x) => x.ecran === ecran && x.regle === d.regle && d.element.includes(x.element) && (!x.format || format.startsWith(x.format)));

// Remonte en haut et attend que rien ne bouge plus (frontend/scripts/captures.py) : un repliable ou une rubrique peut
// lancer un défilement qui finirait pendant la capture.
async function poser(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.locator(".page-veil").waitFor({ state: "detached", timeout: 15_000 });
  await page.evaluate(() => document.fonts.ready);
  // Les entrées des éléments (docs/mouvement.md) : finies avant les contrôles, pour lire les couleurs à opacité pleine.
  // Une animation en pause ou sans fin n'est pas attendue, et l'attente ne dépasse jamais 2 s.
  await page.evaluate(() =>
    Promise.race([
      Promise.all(
        document
          .getAnimations()
          .filter((a) => a.playState === "running" && a.effect?.getComputedTiming().iterations !== Infinity)
          .map((a) => a.finished.catch(() => undefined)),
      ),
      new Promise((r) => setTimeout(r, 2000)),
    ]),
  );
  await page.evaluate(async () => {
    let calme = 0;
    for (let i = 0; i < 100 && calme < 6; i++) {
      window.scrollTo(0, 0);
      await new Promise((r) => setTimeout(r, 50));
      calme = window.scrollY === 0 ? calme + 1 : 0;
    }
  });
}

// Règle g, fin : un bouton dont ni lui ni ses trois parents les plus proches n'écoutent un clic n'a pas d'action. Les
// écouteurs posés par Vue sont des écouteurs ordinaires : le protocole de Chromium les voit.
async function boutonsSansAction(page: Page, descriptions: string[]): Promise<Defaut[]> {
  const cdp = await page.context().newCDPSession(page);
  const defauts: Defaut[] = [];
  const ACTION = new Set(["click", "pointerdown", "pointerup", "mousedown", "mouseup", "touchstart", "touchend", "keydown"]);
  for (let i = 0; i < descriptions.length; i++) {
    let agit = false;
    for (let niveau = 0; niveau < 4 && !agit; niveau++) {
      const chemin = `window.__e2eBoutons[${i}]${".parentElement".repeat(niveau)}`;
      const { result } = await cdp.send("Runtime.evaluate", { expression: chemin });
      if (!result.objectId) break;
      const { listeners } = await cdp.send("DOMDebugger.getEventListeners", { objectId: result.objectId });
      agit = listeners.some((l) => ACTION.has(l.type));
    }
    if (!agit) defauts.push({ regle: "g", element: descriptions[i], detail: "bouton sans action (aucun écouteur de clic)" });
  }
  await cdp.detach();
  return defauts;
}

// Règle d, fin : la police qui dessine vraiment chaque texte. Chromium dit, pour un élément, quelles polices ont servi
// et pour combien de lettres ; toute autre que Figtree (ou une police dessinée sur la planche, voir ecarts-connus.json)
// est un défaut, même si la feuille de style demande Figtree.
async function policesUtilisees(page: Page): Promise<Defaut[]> {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const { root } = await cdp.send("DOM.getDocument", { depth: 0 });
  const { nodeIds } = await cdp.send("DOM.querySelectorAll", { nodeId: root.nodeId, selector: "[data-e2e-texte]" });
  const lus = new Map<string, { element: string; enfants: string[]; polices: Map<string, number> }>();
  for (const nodeId of nodeIds) {
    const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId });
    const { attributes } = await cdp.send("DOM.getAttributes", { nodeId });
    const attribut = (nom: string) => attributes[attributes.indexOf(nom) + 1];
    lus.set(attribut("data-e2e-id"), {
      element: attribut("data-e2e-texte"),
      enfants: attribut("data-e2e-enfants").split(",").filter(Boolean),
      polices: new Map(fonts.map((f) => [f.familyName, f.glyphCount])),
    });
  }
  const defauts: Defaut[] = [];
  for (const { element, enfants, polices } of lus.values()) {
    // Les lettres propres à l'élément : celles de ses enfants marqués en moins.
    const propres = new Map(polices);
    for (const id of enfants) for (const [famille, n] of lus.get(id)?.polices ?? []) propres.set(famille, (propres.get(famille) ?? 0) - n);
    const autres = [...propres].filter(([famille, n]) => n > 0 && !/^Figtree/i.test(famille));
    if (!autres.length) continue;
    const detail = autres.map(([famille, n]) => `${famille} (${n} lettre${n > 1 ? "s" : ""})`).join(", ");
    defauts.push({ regle: "d", element, detail: `dessiné en ${detail}` });
  }
  await cdp.detach();
  return defauts;
}

for (const ecran of ECRANS) {
  test.describe(ecran.nom, () => {
    test.beforeEach(async ({ page }) => {
      await page.clock.setFixedTime(new Date(HEURE));
      const chemin = typeof ecran.chemin === "string" ? ecran.chemin : await ecran.chemin(page);
      await page.goto(chemin);
      await poser(page);
    });

    test("capture de référence", async ({ page }) => {
      await expect(page).toHaveScreenshot(`${ecran.nom}.png`, { fullPage: true });
    });

    test("contrôles a à h", async ({ page }, info) => {
      const format = info.project.name;
      const { defauts, boutons } = await page.evaluate(controler, format.endsWith("sombre"));
      const tous = [...defauts, ...(await boutonsSansAction(page, boutons)), ...(await policesUtilisees(page))];
      const nouveaux = tous.filter((d) => !connu(d, ecran.nom, format));
      // Tous les défauts, connus ou non, à côté des résultats : e2e/resultats/<test>/defauts.json.
      writeFileSync(info.outputPath("defauts.json"), JSON.stringify({ ecran: ecran.nom, format, defauts: tous }, null, 2));
      // Un écart connu qui ne se produit plus : la liste se nettoie (avertissement seulement).
      for (const x of ECARTS.filter((x) => x.ecran === ecran.nom && (!x.format || format.startsWith(x.format)))) {
        if (!tous.some((d) => d.regle === x.regle && d.element.includes(x.element))) {
          info.annotations.push({ type: "écart connu disparu", description: `${x.regle} ${x.element} : à retirer de ecarts-connus.json` });
        }
      }
      const liste = nouveaux.map((d) => `  ${d.regle}. ${d.element} : ${d.detail}\n     (${REGLES[d.regle]})`).join("\n");
      expect(nouveaux, `${nouveaux.length} défaut(s) d'affichage sur « ${ecran.nom} » (${format}) :\n${liste}\n`).toEqual([]);
    });
  });
}
