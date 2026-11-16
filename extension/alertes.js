// Le formulaire « Créer une alerte » de la page (docs/142 §4), passé tel quel à l'onglet actif
// (`func`) à l'ouverture du panneau, sur jobup, jobs.ch ou LinkedIn seulement. Avec `address`, le
// champ e-mail du formulaire reçoit l'adresse jobA1, comme au clavier (événements input et
// change), pour que le site la prenne en compte. Le bouton d'envoi du site n'est jamais touché.
// Rien d'autre n'est lu : seulement si le formulaire est là, et si son champ e-mail est trouvé.
// Une seule fonction, sans rien autour : elle est copiée dans la page. Les sélecteurs viennent de
// alert-selectors.js (`rules`).

function jobA1AlertForm(rules, address) {
  const visible = (el) => {
    if (!el || el.hidden || el.closest("[hidden], [aria-hidden='true']")) return false;
    const style = getComputedStyle(el);
    return style.display !== "none" && style.visibility !== "hidden";
  };
  const marker = new RegExp(rules.marker, "i");
  const opener = new RegExp(`${rules.opener}|${rules.marker}`, "i");
  const usable = (input) => visible(input) && !input.disabled && !input.readOnly;

  let input = null;
  for (const selector of rules.forms) {
    for (const form of document.querySelectorAll(selector)) {
      if (!visible(form) || !marker.test(form.textContent || "")) continue;
      for (const emailSelector of rules.email) {
        input = [...form.querySelectorAll(emailSelector)].find(usable) || null;
        if (input) break;
      }
      if (input) break;
    }
    if (input) break;
  }
  // Pas de champ : le formulaire est-il ouvert quand même (sélecteurs cassés) ? Une fenêtre ou
  // un formulaire visible, avec des champs, qui parle de créer une alerte. Un simple bouton
  // « Créer une alerte » dans la page ne suffit pas.
  if (!input) {
    const open = [...document.querySelectorAll("[role='dialog'], dialog, form")].some(
      (box) => visible(box) && box.querySelector("input:not([type=hidden])") && opener.test(box.textContent || ""),
    );
    return { form: open, filled: false };
  }
  if (!address) return { form: true, filled: false };
  // Le setter natif : les sites en React ou Angular ne voient pas une valeur posée directement.
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  input.focus();
  setter.call(input, address);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  input.blur();
  return { form: true, filled: input.value === address };
}

globalThis.jobA1AlertForm = jobA1AlertForm;

// --- Le suivi de l'alerte jobup (section 42, docs/142 §4 bis) ---------------------------------
// Deux fonctions copiées telles quelles dans l'onglet de l'alerte, celui où la personne a ouvert
// la fenêtre, et seulement lui. Ni l'une ni l'autre ne clique : la personne crée et confirme
// l'alerte elle-même sur jobup. Le code n'est jamais écrit dans la console.

// Où en est la page : le formulaire d'alerte ouvert, le champ du code, une demande de code sans
// champ trouvé (sélecteurs cassés), l'alerte créée. Rien d'autre n'est lu ni renvoyé.
function jobA1AlertProbe(rules) {
  const visible = (el) => {
    if (!el || el.hidden || el.closest("[hidden], [aria-hidden='true']")) return false;
    const style = getComputedStyle(el);
    return style.display !== "none" && style.visibility !== "hidden";
  };
  const usable = (input) => visible(input) && !input.disabled && !input.readOnly;
  const text = [...document.querySelectorAll("[role='dialog'], dialog, form, main, [role='alert'], [role='status']")]
    .filter(visible)
    .map((box) => box.textContent || "")
    .join(" ");
  const marker = new RegExp(rules.marker, "i");
  const form = [...document.querySelectorAll(rules.forms.join(","))].some(
    (box) => visible(box) && marker.test(box.textContent || "") && rules.email.some((s) => [...box.querySelectorAll(s)].some(usable)),
  );
  let code = false;
  for (const selector of rules.code) {
    if ([...document.querySelectorAll(selector)].some((input) => usable(input) && input.type !== "email" && input.type !== "hidden")) {
      code = true;
      break;
    }
  }
  return {
    form,
    code,
    asks: new RegExp(rules.codeAsk, "i").test(text),
    done: new RegExp(rules.done, "i").test(text),
  };
}

// Le code dans son champ, comme au clavier (setter natif, input et change), ou chiffre par chiffre
// dans des cases d'un caractère. Vrai si le champ a pris le code. Aucun bouton n'est touché.
function jobA1PasteCode(rules, code) {
  const visible = (el) => {
    if (!el || el.hidden || el.closest("[hidden], [aria-hidden='true']")) return false;
    const style = getComputedStyle(el);
    return style.display !== "none" && style.visibility !== "hidden";
  };
  const usable = (input) => visible(input) && !input.disabled && !input.readOnly && input.type !== "email" && input.type !== "hidden";
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  const type = (input, value) => {
    input.focus();
    setter.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  };
  for (const selector of rules.code) {
    const inputs = [...document.querySelectorAll(selector)].filter(usable);
    if (!inputs.length) continue;
    const boxes = inputs.filter((input) => input.maxLength === 1);
    if (boxes.length === code.length) {
      boxes.forEach((input, i) => type(input, code[i]));
      boxes[boxes.length - 1].blur();
      return boxes.map((input) => input.value).join("") === code;
    }
    type(inputs[0], code);
    inputs[0].blur();
    return inputs[0].value === code;
  }
  return false;
}

globalThis.jobA1AlertProbe = jobA1AlertProbe;
globalThis.jobA1PasteCode = jobA1PasteCode;
