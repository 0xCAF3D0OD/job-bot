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
