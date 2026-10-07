// Remplissage du formulaire de l'employeur (docs/25 §3). Injecté par l'extension dans l'onglet
// où tu as cliqué sur son icône, seulement à ce moment-là. Il remplit les champs reconnus,
// joint les PDF, n'écrase jamais un champ déjà rempli, ne coche aucune case et n'envoie rien.
(() => {
  if (globalThis.jobbotFill) return;

  const FILLED = "2px solid #635bff";
  const TODO = "2px solid #e08a2e";

  const norm = (value) =>
    (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[*:]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  // Étiquette visible du champ : <label for>, label englobant, aria, texte d'aide.
  function labelOf(el) {
    const doc = el.ownerDocument;
    const parts = [];
    if (el.id) {
      const label = doc.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (label) parts.push(label.textContent);
    }
    const wrap = el.closest("label");
    if (wrap) parts.push(wrap.textContent);
    for (const id of (el.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean)) {
      const node = doc.getElementById(id);
      if (node) parts.push(node.textContent);
    }
    parts.push(el.getAttribute("aria-label"), el.getAttribute("placeholder"), el.getAttribute("title"));
    if (!parts.some((p) => p && p.trim())) {
      // Formulaire sans étiquette reliée : le texte qui précède le champ dans son bloc.
      const block = el.closest("div, li, p, td, fieldset");
      const legend = block?.querySelector("label, legend, span, p, strong");
      if (legend && !legend.contains(el)) parts.push(legend.textContent);
    }
    return parts.filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
  }

  function visible(el) {
    if (el.type === "hidden" || el.disabled || el.readOnly || el.hidden) return false;
    const style = getComputedStyle(el);
    return style.display !== "none" && style.visibility !== "hidden";
  }

  // Ordre important : l'e-mail avant l'adresse (« e-mail address »), le NPA avant la rue.
  const RULES = [
    ["email", ["email"], /\b(e-?mail|courriel|mail)\b/],
    ["linkedin", [], /linkedin/],
    ["website", ["url"], /(website|site (web|internet|personnel)|portfolio|homepage|webseite)/],
    ["first", ["given-name"], /(first ?name|prenom|vorname|given name)/],
    ["last", ["family-name"], /(last ?name|surname|family name|nom de famille|nachname|familienname)/],
    ["phone", ["tel", "tel-national", "mobile"], /(phone|telephone|\btel\b|mobile|handy|portable|natel)/],
    ["postcode", ["postal-code"], /(\bzip\b|postal|\bnpa\b|\bplz\b|code postal|postleitzahl)/],
    ["city", ["address-level2"], /(\bcity\b|\bville\b|localite|\bort\b|wohnort|\btown\b)/],
    ["country", ["country", "country-name"], /(country|\bpays\b|\bland\b)/],
    ["street", ["street-address", "address-line1"], /(street|\brue\b|adresse|address|strasse|anschrift)/],
    ["availability", [], /(availab|disponib|verfugbar|start ?date|date d.entree|eintritt|notice period|preavis|kundigungsfrist)/],
    ["salary", [], /(salary|salaire|pretention|gehalt|lohn|remuneration)/],
    ["permit", [], /(work permit|permis|bewilligung|work authori|aufenthalt|\bvisa\b)/],
    ["letter", [], /(cover ?letter|lettre de motivation|motivation|anschreiben|motivationsschreiben)/],
  ];
  const FULL_NAME = /^(nom|name|nom et prenom|nom complet|prenom et nom|full ?name|vor- und nachname|vollstandiger name|your name|votre nom)$/;
  const COUNTRY = { fr: "Suisse", de: "Schweiz", it: "Svizzera", en: "Switzerland" };
  const COUNTRY_OPTIONS = ["suisse", "switzerland", "schweiz", "svizzera", "ch"];
  const LABELS = {
    email: "E-mail", linkedin: "LinkedIn", website: "Site personnel", first: "Prénom", last: "Nom",
    full: "Nom et prénom", phone: "Téléphone", postcode: "NPA", city: "Localité", country: "Pays",
    street: "Rue et numéro", availability: "Disponibilité", salary: "Prétentions salariales",
    permit: "Permis de travail", letter: "Lettre de motivation", cv: "CV (PDF)", letterFile: "Lettre (PDF)",
  };

  function kindOf(el, hasFirst) {
    const label = norm(labelOf(el));
    const auto = norm(el.getAttribute("autocomplete"));
    const text = norm([label, el.name, el.id].join(" "));
    if (el.type === "email") return "email";
    if (el.type === "tel") return "phone";
    if (FULL_NAME.test(label) || auto === "name") return hasFirst ? "last" : "full";
    // L'attribut d'autocomplétion, posé par le site, l'emporte sur l'étiquette.
    const byAuto = auto && RULES.find(([, autos]) => autos.includes(auto));
    if (byAuto) return byAuto[0];
    for (const [key, , pattern] of RULES) {
      if (key === "letter" && el.tagName !== "TEXTAREA") continue;
      if (pattern.test(text)) return key;
    }
    return null;
  }

  function split(name) {
    const words = (name || "").trim().split(/\s+/).filter(Boolean);
    return words.length > 1 ? [words[0], words.slice(1).join(" ")] : ["", words[0] || ""];
  }

  function valueFor(kind, data) {
    const who = data.identity || {};
    const [first, last] = split(who.name);
    const lang = (document.documentElement.lang || "fr").slice(0, 2).toLowerCase();
    return {
      email: who.email, linkedin: who.linkedin, website: who.website, first, last, full: who.name,
      phone: who.phone, postcode: who.postcode, city: who.city,
      country: who.city ? COUNTRY[lang] || COUNTRY.fr : null,
      street: who.street, availability: who.availability, salary: who.salary, permit: who.permit,
      letter: data.letterText,
    }[kind];
  }

  // Valeur posée comme une saisie : les formulaires React, Vue… la voient passer.
  function setValue(el, value) {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    for (const type of ["input", "change", "blur"]) el.dispatchEvent(new Event(type, { bubbles: true }));
  }

  function setSelect(el, kind, value) {
    const wanted = kind === "country" ? COUNTRY_OPTIONS : [norm(value)];
    const option = [...el.options].find((o) => {
      const text = norm(o.textContent);
      const code = norm(o.value);
      return wanted.some((w) => w && (text === w || code === w || (w.length > 3 && text.includes(w))));
    });
    if (!option) return false;
    el.value = option.value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function attach(input, file) {
    const bytes = Uint8Array.from(atob(file.base64), (c) => c.charCodeAt(0));
    const transfer = new DataTransfer();
    transfer.items.add(new File([bytes], file.name, { type: "application/pdf" }));
    input.files = transfer.files;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function mark(el, style) {
    el.style.outline = style;
    el.style.outlineOffset = "1px";
  }

  function fill(data) {
    const report = { filled: [], todo: [], questions: [], frames: [] };
    const fields = [...document.querySelectorAll("input, textarea, select")].filter(
      (el) => !["checkbox", "radio", "submit", "button", "reset", "image", "password", "file"].includes(el.type),
    );
    const shown = fields.filter(visible);
    const hasFirst = shown.some((el) => kindOf(el, false) === "first");
    let question = 0;
    for (const el of shown) {
      const kind = kindOf(el, hasFirst);
      const value = kind ? valueFor(kind, data) : null;
      const empty = !el.value || (el.tagName === "SELECT" && !el.value.trim());
      if (kind && value && empty) {
        const done = el.tagName === "SELECT" ? setSelect(el, kind, value) : (setValue(el, value), true);
        if (done) {
          mark(el, FILLED);
          el.dataset.jobbot = "filled";
          report.filled.push(LABELS[kind]);
          continue;
        }
      }
      if (!empty) continue;
      const label = labelOf(el).replace(/\s*\*\s*$/, "");
      if (!kind && el.tagName === "TEXTAREA" && label) {
        // Question libre : l'IA peut proposer une réponse, sur demande.
        el.dataset.jobbotQuestion = String(question);
        report.questions.push({ key: String(question), label: label.slice(0, 300) });
        question += 1;
      }
      if (el.required || el.getAttribute("aria-required") === "true") {
        mark(el, TODO);
        report.todo.push(label.slice(0, 80) || "champ sans nom");
      }
    }
    // Pièces jointes : le CV et la lettre d'après l'étiquette, sinon le CV dans le premier champ.
    const inputs = [...document.querySelectorAll('input[type="file"]')].filter((el) => !el.disabled && !el.files?.length);
    const files = data.files || {};
    const wanted = inputs.map((el) => {
      const text = norm([labelOf(el), el.name, el.id].join(" "));
      if (/(cover|lettre|motivation|anschreiben)/.test(text)) return "letter";
      if (/(\bcv\b|resume|curriculum|lebenslauf)/.test(text)) return "cv";
      return null;
    });
    const used = new Set(wanted.filter(Boolean));
    inputs.forEach((el, index) => {
      let kind = wanted[index];
      if (!kind) kind = !used.has("cv") ? "cv" : !used.has("letter") ? "letter" : null;
      if (!kind || !files[kind]) return;
      used.add(kind);
      try {
        attach(el, files[kind]);
        report.filled.push(kind === "cv" ? LABELS.cv : LABELS.letterFile);
        const target = el.closest("label, div") || el;
        mark(target, FILLED);
      } catch {
        report.todo.push(kind === "cv" ? LABELS.cv : LABELS.letterFile);
      }
    });
    // Formulaire intégré depuis un autre site : à ouvrir dans son propre onglet.
    for (const frame of document.querySelectorAll("iframe[src]")) {
      try {
        const url = new URL(frame.src, location.href);
        if (url.origin !== location.origin && /^https?:$/.test(url.protocol) &&
            /(greenhouse|lever|smartrecruiters|personio|workday|successfactors|umantis|recruitee|join\.com|apply|career|karriere|jobs?)/i.test(url.href)) {
          report.frames.push(url.href);
        }
      } catch {
        // adresse illisible : ignorée
      }
    }
    return report;
  }

  function setAnswer(key, text) {
    const el = document.querySelector(`[data-jobbot-question="${CSS.escape(key)}"]`);
    if (!el) return false;
    setValue(el, text);
    mark(el, FILLED);
    return true;
  }

  function questionText(key) {
    const el = document.querySelector(`[data-jobbot-question="${CSS.escape(key)}"]`);
    return el ? labelOf(el) : null;
  }

  globalThis.jobbotFill = { fill, setAnswer, questionText, kindOf, labelOf };
})();
