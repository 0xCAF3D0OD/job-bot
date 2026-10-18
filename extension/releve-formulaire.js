// Relevé du formulaire Job-Room (docs/70 §5). À coller dans la console du navigateur, sur le
// formulaire VIDE de saisie d'une recherche d'emploi. Il ne lit que la structure de la page :
// titres, étiquettes, types de champs, noms techniques et options des listes. Il ne lit jamais
// ce qui est saisi dans un champ, rien en dehors du formulaire (en-tête, menu, ton nom), et
// n'envoie rien : le résultat est seulement affiché et copié dans le presse-papiers.
(() => {
  const clip = (text) => (text || "").replace(/\s+/g, " ").trim().slice(0, 100);
  const forms = [...document.querySelectorAll("form")];
  const roots = forms.length ? forms : [document.querySelector("main") || document.body];
  const skip = "header, nav, footer, [role=banner], [role=navigation]";

  function labelOf(el) {
    const parts = [];
    if (el.id) {
      const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (label) parts.push(label.textContent);
    }
    const wrap = el.closest("label");
    if (wrap) parts.push(wrap.textContent);
    for (const id of (el.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean)) {
      parts.push(document.getElementById(id)?.textContent);
    }
    parts.push(el.getAttribute("aria-label"));
    return clip(parts.filter(Boolean).join(" | "));
  }

  // Le titre de la partie où se trouve le champ (« Comment avez-vous postulé ? »).
  function groupOf(el) {
    const set = el.closest("fieldset, [role=radiogroup], [role=group]");
    const legend = set?.querySelector("legend, [role=heading], h1, h2, h3, h4, h5, h6");
    if (legend) return clip(legend.textContent);
    return clip(set?.getAttribute("aria-label"));
  }

  const ATTRS = ["type", "name", "id", "formcontrolname", "autocomplete", "role", "placeholder", "aria-required", "required"];
  const CONTROLS = "input, select, textarea, button, [role=combobox], [role=listbox], [role=radio], [role=checkbox], [role=switch], [contenteditable=true]";

  const items = [];
  const seen = new Set();
  for (const root of roots) {
    for (const el of root.querySelectorAll(`h1, h2, h3, h4, h5, h6, legend, ${CONTROLS}`)) {
      if (seen.has(el) || el.closest(skip)) continue;
      seen.add(el);
      if (/^(H\d|LEGEND)$/.test(el.tagName)) {
        items.push({ titre: clip(el.textContent) });
        continue;
      }
      if (el.type === "hidden" || el.type === "password") continue;
      const item = { balise: el.tagName.toLowerCase() };
      for (const attr of ATTRS) {
        const value = el.getAttribute(attr);
        if (value !== null) item[attr] = attr === "placeholder" ? clip(value) : value;
      }
      // Le composant Angular autour du champ (mat-select, ng-select…), utile pour le remplir.
      const host = el.closest("[class*=mat-], [class*=ng-select], [class*=dropdown], [class*=select]");
      if (host && host !== el) item.composant = host.tagName.toLowerCase();
      item.etiquette = labelOf(el);
      const group = groupOf(el);
      if (group) item.partie = group;
      // Choix : l'intitulé du bouton et son code, jamais l'état coché.
      if (el.type === "radio" || el.type === "checkbox" || el.getAttribute("role") === "radio") {
        item.code = el.getAttribute("value") ?? undefined;
      }
      if (el.tagName === "BUTTON") item.texte = clip(el.textContent);
      if (el.tagName === "SELECT") {
        item.options = [...el.options].slice(0, 40).map((o) => clip(o.textContent));
      }
      items.push(item);
    }
  }

  const releve = {
    releve: "job-room, formulaire vide",
    langue: document.documentElement.lang || "",
    chemin: location.pathname,
    formulaires: forms.length,
    cadres: [...document.querySelectorAll("iframe")].map((f) => {
      try {
        return new URL(f.src, location.href).origin;
      } catch {
        return "";
      }
    }),
    elements: items,
  };
  const text = JSON.stringify(releve, null, 2);
  console.log(text);
  try {
    copy(text);
    console.log(`Relevé copié dans le presse-papiers (${items.length} éléments).`);
  } catch {
    console.log("Copie impossible : sélectionne le texte ci-dessus et copie-le.");
  }
})();
