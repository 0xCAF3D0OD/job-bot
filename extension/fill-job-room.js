// Remplissage du formulaire Job-Room (docs/70 §4, §5). Injecté par l'extension dans l'onglet de
// Job-Room où tu as cliqué sur son icône, seulement à ce moment-là, et dans la page elle-même :
// depuis l'espace isolé de l'extension, Firefox cache la saisie à Job-Room. Il remplit la saisie d'une
// recherche d'emploi, choisit les réponses de la déclaration (mode, assignation, taux,
// résultat), et n'enregistre rien : « Sauvegarder » reste le tien. Il ne lit rien d'autre de la
// page que les champs qu'il remplit.
//
// Les champs sont reconnus par leur identifiant, qui porte les clés du formulaire (relevé du
// 2026-10-18, extension/fixtures/job-room-formulaire.json) : les mêmes dans toutes les langues.
(() => {
  if (globalThis.jobbotJobRoom) return;

  const FILLED = "2px solid #635bff";
  const TODO = "2px solid #e08a2e";
  const PLACE_WAIT_MS = 3000;

  const norm = (value) =>
    (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/\s+/g, " ")
      .trim();

  // Le champ lui-même : son cadre, son étiquette ou son message d'erreur peuvent porter un
  // identifiant voisin (« …company.name-0-label »), placé avant lui dans la page.
  const byId = (part) => document.querySelector(["input", "select", "textarea"].map((tag) => `${tag}[id*="${part}"]`).join(", "));
  const radio = (code) => document.querySelector(`input[type="radio"][id$="-${code}"]`);

  // Textes, dans l'ordre du formulaire. `always` : la valeur de la candidature remplace celle
  // que Job-Room propose (la date du jour) ; sinon, un champ déjà rempli n'est pas touché.
  const TEXTS = [
    ["date", "Date", "global.date", { always: true }],
    ["company", "Entreprise", "company.name"],
    ["street", "Rue", "company.street"],
    ["number", "N°", "company.house-number"],
    ["po_box", "Case postale", "company.postbox-number"],
    ["contact", "Personne contactée", "contact-person"],
    ["email", "Courriel", "contact.email"],
    ["phone", "Téléphone", "global.phone"],
    ["job_title", "Désignation du poste", "global.job-title"],
    ["url", "Lien vers le formulaire", "online-form-url"],
  ];
  const CHANNELS = {
    electronic: "Par voie électronique",
    mail: "Par lettre",
    personal: "Contact personnel",
    phone: "Par téléphone",
  };
  const RATES = { FULLTIME: "A plein temps", PARTTIME: "A temps partiel" };
  const RESULTS = { PENDING: "En suspens", EMPLOYED: "Engagement", REJECTED: "Réponse négative" };
  const SWISS = ["suisse", "schweiz", "svizzera", "switzerland"];
  const INTERVIEW = /(entretien d.embauche|vorstellungsgesprach|colloquio|job interview|interview)/;

  function mark(el, style) {
    const target = el.type === "checkbox" || el.type === "radio" ? el.closest("label") || el.parentElement || el : el;
    target.style.outline = style;
    target.style.outlineOffset = "1px";
  }

  // Valeur posée comme une saisie au clavier : Angular la voit passer.
  function setValue(el, value) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function leave(el) {
    el.dispatchEvent(new Event("blur"));
    el.dispatchEvent(new FocusEvent("focusout", { bubbles: true }));
  }

  // Coche (ou choisit) par un clic, comme toi : le formulaire suit son propre état.
  function choose(el) {
    if (!el.checked) el.click();
    return el.checked;
  }

  function labelOf(el) {
    const label = el.id ? document.querySelector(`label[for="${CSS.escape(el.id)}"]`) : null;
    return (label || el.closest("label"))?.textContent || el.getAttribute("aria-label") || "";
  }

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // « NPA / Lieu » : un champ à suggestions. On tape le NPA, puis on choisit la suggestion qui
  // porte aussi le lieu ; sans suggestion sûre, le champ reste à faire.
  async function pickPlace(el, text) {
    const postcode = (text.match(/\b\d{4}\b/) || [])[0];
    if (!postcode) return false;
    const city = norm(text.replace(postcode, "").replace(/\s+\d+$/, ""));
    el.focus();
    setValue(el, postcode);
    const deadline = Date.now() + PLACE_WAIT_MS;
    while (Date.now() < deadline) {
      await wait(100);
      const options = [...document.querySelectorAll('[role="option"]')].filter((o) => norm(o.textContent).includes(postcode));
      if (!options.length) continue;
      const exact = options.filter((o) => city && norm(o.textContent).includes(city));
      const found = exact[0] || (options.length === 1 ? options[0] : null);
      if (!found) return false;
      found.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
      found.click();
      leave(el);
      return true;
    }
    return false;
  }

  async function fill(data) {
    const report = { form: false, filled: [], todo: [] };
    if (!byId("company.name")) return report;
    report.form = true;
    const done = (el, label) => {
      mark(el, FILLED);
      report.filled.push(label);
    };
    const todo = (el, label, value) => {
      if (el) mark(el, TODO);
      report.todo.push({ label, value: value || "" });
    };

    for (const [key, label, part, options] of TEXTS) {
      const el = byId(part);
      const value = data[key] || "";
      if (!el) {
        if (value) todo(null, label, value);
        continue;
      }
      if (el.value && !options?.always) continue;
      if (!value) {
        if (el.required || el.getAttribute("aria-required") === "true") todo(el, label, "");
        continue;
      }
      setValue(el, value);
      leave(el);
      // Vérifié après coup : si la page n'a pas pris la valeur, le champ reste à faire.
      if (el.value === value) done(el, label);
      else todo(el, label, value);
    }

    // Pays, avant « NPA / Lieu » : les suggestions en dépendent.
    const country = byId("company.country");
    if (country?.tagName === "SELECT") {
      const option = [...country.options].find((o) => SWISS.includes(norm(o.textContent)));
      if (option) {
        if (country.value !== option.value) {
          country.value = option.value;
          country.dispatchEvent(new Event("change", { bubbles: true }));
        }
        done(country, "Pays");
      } else todo(country, "Pays", "Suisse");
    }

    const place = byId("typeahead-npa") || document.querySelector('input[role="combobox"]');
    if (place && !place.value) {
      if (data.postcode_city && (await pickPlace(place, data.postcode_city))) done(place, "NPA / Lieu");
      else todo(place, "NPA / Lieu", data.postcode_city);
    } else if (!place && data.postcode_city) todo(null, "NPA / Lieu", data.postcode_city);

    const channel = data.channel && byId(`apply-channel.${data.channel}`);
    if (channel && choose(channel)) done(channel, CHANNELS[data.channel]);
    else todo(null, "Comment avez-vous postulé ?", CHANNELS[data.channel] || "");

    const assigned = radio(data.assigned ? "true" : "false");
    if (assigned && choose(assigned)) done(assigned, `Assignation ORP : ${data.assigned ? "oui" : "non"}`);
    else todo(null, "Assignation par l'ORP", data.assigned ? "Oui" : "Non");

    const rate = data.rate && radio(data.rate);
    if (rate && choose(rate)) done(rate, RATES[data.rate]);
    else todo(null, "Taux d'occupation", "");

    if (data.interview) {
      const box = [...document.querySelectorAll('input[type="checkbox"]')].find((el) => INTERVIEW.test(norm(labelOf(el))));
      if (box && choose(box)) done(box, "Entretien d'embauche");
      else todo(null, "Entretien d'embauche", "à cocher");
    }
    const result = radio(data.result);
    if (result && choose(result)) done(result, RESULTS[data.result]);
    else todo(null, "Résultat", RESULTS[data.result] || "");

    return report;
  }

  globalThis.jobbotJobRoom = { fill };
})();
