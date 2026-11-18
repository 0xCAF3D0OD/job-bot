// Le script de contrôle de l'affichage (décision de Kevin du 18.11.2026, point 3, règles a à h). La fonction
// `controler` tourne dans la page (page.evaluate) : elle ne doit rien importer. La règle g (bouton sans action)
// se termine dans affichage.e2e.ts, qui lit les écouteurs d'événements par le protocole de Chromium.

export type Regle = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h";

export interface Defaut {
  regle: Regle;
  /** « balise.classe « texte » », assez précis pour retrouver l'élément, stable d'un passage à l'autre. */
  element: string;
  detail: string;
}

export const REGLES: Record<Regle, string> = {
  a: "un élément dépasse de sa carte ou de l'écran, ou un texte est coupé sans « … »",
  b: "une pastille fait plus de 32 px de haut, ou un élément s'étire (align-self: stretch non voulu)",
  c: "le même texte d'état apparaît deux fois dans une même carte",
  d: "une police autre que Figtree apparaît",
  e: "un contraste de texte est sous 4,5:1 (3:1 dès 18 px)",
  f: "une zone cliquable fait moins de 24 × 24 px",
  g: "un bouton ou un lien n'a pas d'action, ou une icône cliquable n'a pas de nom",
  h: "un texte noir sur fond sombre, ou un fond blanc en mode sombre",
};

export interface Resultat {
  defauts: Defaut[];
  /** Les boutons à vérifier pour la règle g : leur indice dans window.__e2eBoutons et leur description. */
  boutons: string[];
}

export function controler(sombre: boolean): Resultat {
  const defauts: Defaut[] = [];
  const vw = document.documentElement.clientWidth;

  // Les éléments que personne ne voit : rien à contrôler (lecteur d'écran seul, replié, hors de la page).
  const visible = (e: Element): boolean => {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const s = getComputedStyle(e);
    if (s.visibility === "hidden" || s.display === "none" || s.opacity === "0") return false;
    if (s.clip === "rect(0px, 0px, 0px, 0px)" || s.clipPath === "inset(50%)") return false;
    if (e.closest("[aria-hidden=true], [inert], .visually-hidden, .sr-only")) return false;
    for (let p: Element | null = e; p; p = p.parentElement) {
      const ps = getComputedStyle(p);
      if (ps.opacity === "0" || ps.display === "none" || ps.visibility === "hidden") return false;
    }
    return true;
  };
  const texte = (e: Element) => ((e as HTMLElement).innerText ?? e.textContent ?? "").trim().replace(/\s+/g, " ");
  const decrire = (e: Element): string => {
    const classe = [...e.classList].filter((c) => !/^(router-link|v-|is-)/.test(c)).slice(0, 2).join(".");
    const test = e.getAttribute("data-test");
    const nom = e.getAttribute("aria-label") || texte(e);
    return `${e.tagName.toLowerCase()}${classe ? `.${classe}` : ""}${test ? `[${test}]` : ""}${nom ? ` « ${nom.slice(0, 40)} »` : ""}`;
  };
  const ajouter = (regle: Regle, e: Element, detail: string) => defauts.push({ regle, element: decrire(e), detail });
  const avecTexte = (e: Element) => [...e.childNodes].some((n) => n.nodeType === Node.TEXT_NODE && n.textContent!.trim().length > 0);

  const tous = [...document.body.querySelectorAll("*")].filter((e) => !["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "BR"].includes(e.tagName));
  const vus = tous.filter(visible);

  // Couleurs : le navigateur lit toute couleur CSS (oklch, color-mix…) ; on la passe par un pixel de canevas.
  const toile = document.createElement("canvas").getContext("2d", { willReadFrequently: true })!;
  const rgba = (c: string): [number, number, number, number] => {
    toile.clearRect(0, 0, 1, 1);
    toile.fillStyle = "rgba(0,0,0,0)";
    toile.fillStyle = c;
    toile.fillRect(0, 0, 1, 1);
    const d = toile.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3] / 255];
  };
  const melanger = (haut: number[], bas: number[]) => [0, 1, 2].map((i) => haut[i] * haut[3] + bas[i] * (1 - haut[3]));
  const lum = ([r, g, b]: number[]) => {
    const f = (v: number) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a: number[], b: number[]) => {
    const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  };
  // Le fond réel derrière un élément : les fonds des parents, superposés. null si une image ou un dégradé s'en mêle.
  const fond = (e: Element): number[] | null => {
    const couches: number[][] = [];
    for (let p: Element | null = e; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.backgroundImage !== "none") return null;
      const c = rgba(s.backgroundColor);
      if (c[3] > 0) couches.push(c);
      if (c[3] >= 1) break;
    }
    let base = rgba(getComputedStyle(document.documentElement).backgroundColor);
    if (base[3] === 0) base = sombre ? [0, 0, 0, 1] : [255, 255, 255, 1];
    let res = base.slice(0, 3);
    for (const c of couches.reverse()) res = melanger(c, res);
    return res;
  };

  // a. Débordements. La page ne défile pas de côté ; un élément ne sort ni de l'écran ni de sa carte ; un texte coupé
  // finit par « … ».
  if (document.documentElement.scrollWidth > vw + 1) {
    defauts.push({ regle: "a", element: "html", detail: `la page défile de côté : ${document.documentElement.scrollWidth} px pour ${vw} px d'écran` });
  }
  const CARTE = "[class*=card], [class*=carte], .panel-section, article, [data-test=application]";
  // Une carte se voit : un fond, un trait ou une ombre, et des coins arrondis. Un simple conteneur nommé « …-cards »
  // n'en est pas une.
  const estCarte = (e: Element): boolean => {
    if (!e.matches(CARTE)) return false;
    const s = getComputedStyle(e);
    const dessinee = rgba(s.backgroundColor)[3] > 0 || parseFloat(s.borderTopWidth) > 0 || s.boxShadow !== "none";
    return dessinee && parseFloat(s.borderTopLeftRadius) > 0;
  };
  const carteDe = (e: Element): Element | null => {
    for (let p = e.parentElement; p; p = p.parentElement) if (estCarte(p)) return p;
    return null;
  };
  for (const e of vus) {
    const r = e.getBoundingClientRect();
    const fixe = e.closest("[role=dialog], .tab-bar, .topbar");
    if (!fixe && (r.right > vw + 1 || r.left < -1) && !e.closest("[class*=scroll], [class*=rail], [class*=carousel]")) {
      // Seul le premier élément qui sort compte : ses enfants sortent avec lui.
      const parent = e.parentElement?.getBoundingClientRect();
      if (!parent || (parent.right <= vw + 1 && parent.left >= -1)) ajouter("a", e, `sort de l'écran (${Math.round(r.left)} à ${Math.round(r.right)} px pour ${vw} px)`);
    }
    const carte = carteDe(e);
    if (carte && carte !== e) {
      const c = carte.getBoundingClientRect();
      const cs = getComputedStyle(carte);
      const coupe = cs.overflow !== "visible";
      const dehors = r.right > c.right + 1 || r.left < c.left - 1 || r.bottom > c.bottom + 1 || r.top < c.top - 1;
      if (dehors && !coupe && !e.closest("[role=dialog], [role=menu], [role=listbox], [role=tooltip], .hover-note")) {
        const parent = e.parentElement!.getBoundingClientRect();
        const parentDehors = e.parentElement !== carte && (parent.right > c.right + 1 || parent.left < c.left - 1 || parent.bottom > c.bottom + 1 || parent.top < c.top - 1);
        if (!parentDehors) ajouter("a", e, `dépasse de sa carte ${decrire(carte)}`);
      }
    }
    if (avecTexte(e)) {
      const s = getComputedStyle(e);
      const he = e as HTMLElement;
      const cache = s.overflowX !== "visible" || s.overflow !== "visible";
      if (cache && he.scrollWidth > he.clientWidth + 1 && s.textOverflow !== "ellipsis" && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName)) {
        ajouter("a", e, `texte coupé sans « … » (${he.scrollWidth} px pour ${he.clientWidth} px)`);
      }
    }
  }

  // b. Pastilles et éléments étirés. Une pastille fait au plus 32 px de haut. Un élément que son parent (flex ou
  // grille) étire est plus haut qu'à sa taille naturelle : on le mesure une seconde fois, aligné en haut.
  const PASTILLE = "[class*=pill], [class*=chip], [class*=badge], [class*=pastille], [class*=tag]:not([class*=stage])";
  const pastilles = vus.filter((e) => e.matches(PASTILLE) && !e.matches("[class*=chips], [class*=pills], [class*=badges], [class*=tags], [class*=-list], [class*=-row], [class*=-group], [class*=-bar], [role=tablist], [role=radiogroup], fieldset"));
  for (const e of pastilles) {
    const h = e.getBoundingClientRect().height;
    if (h > 32.5) ajouter("b", e, `pastille de ${Math.round(h)} px de haut`);
  }
  const etirables = vus.filter((e) => e.matches(`${PASTILLE}, button, [role=button], a[class*=btn], a[class*=button], svg, img`));
  for (const e of etirables) {
    const parent = e.parentElement;
    if (!parent) continue;
    const ps = getComputedStyle(parent);
    if (!/flex|grid/.test(ps.display)) continue;
    const he = e as HTMLElement | SVGElement;
    const avant = he.getBoundingClientRect();
    const ancien = he.style.alignSelf;
    he.style.alignSelf = "start";
    const apres = he.getBoundingClientRect();
    he.style.alignSelf = ancien;
    const enLigne = !ps.flexDirection.startsWith("column") || /grid/.test(ps.display);
    // Une mesure à 0 px : l'élément n'a pas de taille propre (grille animée, contenu absolu) ; rien à comparer.
    if (apres.height < 4) continue;
    if (enLigne && avant.height - apres.height > 2) ajouter("b", e, `s'étire : ${Math.round(avant.height)} px au lieu de ${Math.round(apres.height)} px`);
    const enColonne = ps.flexDirection.startsWith("column") && /flex/.test(ps.display);
    if (enColonne && e.matches(PASTILLE) && avant.width - apres.width > 2) ajouter("b", e, `s'étire en largeur : ${Math.round(avant.width)} px au lieu de ${Math.round(apres.width)} px`);
  }

  // c. Une information une seule fois par carte : deux textes identiques dans la même carte (feuilles de texte d'au
  // moins 4 lettres, sans tenir compte de la casse ni des signes ›, ✓, …).
  const cartes = vus.filter((e) => estCarte(e) && ![...e.querySelectorAll(CARTE)].some(estCarte));
  for (const carte of cartes) {
    const vu = new Map<string, Element>();
    for (const e of carte.querySelectorAll("*")) {
      if (!visible(e) || !avecTexte(e) || e.closest("[role=dialog]") !== carte.closest("[role=dialog]")) continue;
      const t = texte(e).toLowerCase().replace(/[’‘`]/g, "'").replace(/[›‹✓·•…:!?.,()]/g, "").replace(/\s+/g, " ").trim();
      if (t.replace(/[^\p{L}]/gu, "").length < 4) continue;
      const deja = vu.get(t);
      if (deja && !deja.contains(e) && !e.contains(deja)) ajouter("c", e, `« ${t} » deux fois dans la carte ${decrire(carte)}`);
      else vu.set(t, e);
    }
  }

  // d. Figtree partout. La fiche ORP imprimable (Arial, document officiel) n'est pas un écran.
  for (const e of vus) {
    if (!avecTexte(e) || e.closest("#print-root")) continue;
    const famille = getComputedStyle(e).fontFamily.split(",")[0].replace(/["']/g, "").trim();
    if (!/^Figtree/i.test(famille)) ajouter("d", e, `police « ${famille} »`);
  }
  // Les éléments à texte, marqués pour la seconde moitié de la règle d (affichage.e2e.ts) : la police vraiment
  // utilisée pour dessiner chaque lettre, lue par le protocole de Chromium. Un caractère absent de Figtree (✓, →…)
  // est dessiné dans une police du système : c'est aussi une autre police.
  // Chromium compte aussi les lettres des éléments enfants : chaque élément marqué dit aussi qui sont ses enfants marqués
  // (data-e2e-enfants), dont on retire les lettres.
  const marques = vus.filter((e) => avecTexte(e) && !e.closest("#print-root"));
  marques.forEach((e, i) => {
    e.setAttribute("data-e2e-texte", decrire(e));
    e.setAttribute("data-e2e-id", String(i));
  });
  for (const e of marques) {
    const enfants = marques.filter((x) => x !== e && e.contains(x) && x.parentElement?.closest("[data-e2e-texte]") === e);
    e.setAttribute("data-e2e-enfants", enfants.map((x) => x.getAttribute("data-e2e-id")).join(","));
  }
  if (!document.fonts.check('16px "Figtree Variable"')) defauts.push({ regle: "d", element: "document", detail: "la police Figtree n'est pas chargée" });

  // e et h. Contrastes, texte noir sur fond sombre, fond blanc en mode sombre.
  for (const e of vus) {
    const s = getComputedStyle(e);
    const f = fond(e);
    if (avecTexte(e) && f && !e.closest("[disabled], [aria-disabled=true], .is-disabled")) {
      const c = rgba(s.color);
      const couleur = melanger(c, f);
      const taille = parseFloat(s.fontSize);
      const seuil = taille >= 18 ? 3 : 4.5;
      const r = ratio(couleur, f);
      if (r < seuil - 0.005) ajouter("e", e, `contraste ${r.toFixed(2)}:1 (minimum ${seuil}:1, ${Math.round(taille)} px) ; texte ${s.color}`);
      if (lum(couleur) < 0.02 && lum(f) < 0.18) ajouter("h", e, `texte noir sur fond sombre (${s.color})`);
    }
    if (sombre) {
      const b = rgba(s.backgroundColor);
      if (b[3] > 0.5 && lum(b.slice(0, 3)) > 0.85 && (e.getBoundingClientRect().width > 24 || avecTexte(e))) ajouter("h", e, `fond blanc en mode sombre (${s.backgroundColor})`);
    }
  }

  // f et g. Les zones cliquables : 24 × 24 px au moins (sauf un lien dans une phrase, WCAG 2.5.8), une action, un nom.
  const CLIC = "a, button, [role=button], [role=link], [role=tab], [role=menuitem], [role=switch], [role=checkbox], [role=radio], input:not([type=hidden]), select, textarea, summary";
  const cliquables = vus.filter((e) => e.matches(CLIC));
  const boutons: Element[] = [];
  for (const e of cliquables) {
    const r = e.getBoundingClientRect();
    const dansPhrase = e.tagName === "A" && getComputedStyle(e).display === "inline" && !!e.parentElement && avecTexte(e.parentElement);
    // Une case cachée sous son libellé : c'est le libellé qu'on touche.
    const id = e.getAttribute("id");
    const label = e.matches("input") ? e.closest("label") || (id ? document.querySelector(`label[for="${CSS.escape(id)}"]`) : null) : null;
    const zone = label ? label.getBoundingClientRect() : r;
    if (!dansPhrase && (zone.width < 23.5 || zone.height < 23.5)) ajouter("f", e, `zone cliquable de ${Math.round(zone.width)} × ${Math.round(zone.height)} px`);

    if (e.tagName === "A") {
      const href = e.getAttribute("href");
      if (href === null || href === "" || href === "#" || href.startsWith("javascript:")) {
        if (!e.matches("[role=button], [role=tab], [role=menuitem]")) ajouter("g", e, `lien sans destination (href ${href === null ? "absent" : `« ${href} »`})`);
        else boutons.push(e);
      }
    } else if (!e.matches("input, select, textarea") && e.matches("button, [role=button], [role=tab], [role=menuitem], [role=switch], summary")) {
      const enFormulaire = e.matches("button") && (e as HTMLButtonElement).type === "submit" && !!(e as HTMLButtonElement).form;
      if (!enFormulaire && !e.matches("summary") && !(e as HTMLButtonElement).disabled) boutons.push(e);
    }

    const etiquette = (x: Element): string => {
      const aria = x.getAttribute("aria-label")?.trim();
      if (aria) return aria;
      const par = x.getAttribute("aria-labelledby");
      if (par) return par.split(/\s+/).map((id) => document.getElementById(id)?.textContent ?? "").join(" ").trim();
      const t = texte(x);
      if (t) return t;
      if (x.getAttribute("title")) return x.getAttribute("title")!;
      const img = x.querySelector("img[alt]:not([alt=''])");
      if (img) return img.getAttribute("alt")!;
      const titre = x.querySelector("svg title");
      if (titre?.textContent) return titre.textContent;
      if (x.matches("input, select, textarea")) {
        const id = x.getAttribute("id");
        const lab = (id && document.querySelector(`label[for="${CSS.escape(id)}"]`)) || x.closest("label");
        if (lab && texte(lab)) return texte(lab);
        if ((x as HTMLInputElement).placeholder) return (x as HTMLInputElement).placeholder;
        if (["submit", "button", "reset"].includes((x as HTMLInputElement).type)) return (x as HTMLInputElement).value;
      }
      return "";
    };
    if (!etiquette(e)) ajouter("g", e, "zone cliquable sans nom (ni texte, ni aria-label)");
  }
  (window as unknown as { __e2eBoutons: Element[] }).__e2eBoutons = boutons;

  // Un défaut par élément et par règle : un élément qui dépasse ne compte qu'une fois.
  const uniques = new Map<string, Defaut>();
  for (const d of defauts) {
    const cle = `${d.regle}|${d.element}|${d.detail}`;
    if (!uniques.has(cle)) uniques.set(cle, d);
  }
  return { defauts: [...uniques.values()], boutons: boutons.map(decrire) };
}
