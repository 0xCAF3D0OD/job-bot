// Remplissage de Job-Room par l'extension (extension/fill-job-room.js, docs/70 §4, §5). Le
// formulaire est reconstruit à partir du relevé du formulaire réel (extension/fixtures/).
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

import releve from "../../extension/fixtures/job-room-formulaire.json";

type Report = { form: boolean; filled: string[]; todo: { label: string; value: string }[] };
let fillJobRoom: (data: unknown) => Promise<Report>;
type Element = (typeof releve.elements)[number] & Record<string, unknown>;

// Les suggestions de « NPA / Lieu », comme Job-Room les propose après la saisie du NPA.
const PLACES = ["1000 Lausanne", "1003 Lausanne", "1211 Genève 3", "1212 Grand-Lancy"];

beforeAll(async () => {
  globalThis.CSS ??= { escape: (v: string) => v } as typeof CSS;
  // @ts-expect-error script de l'extension, sans types (passé tel quel aux pages)
  await import("../../extension/fill-job-room.js");
  fillJobRoom = (globalThis as unknown as { jobbotFillJobRoom: typeof fillJobRoom }).jobbotFillJobRoom;
});

function escape(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function control(el: Element): string {
  const attrs = ["id", "type", "role", "placeholder", "autocomplete"]
    .filter((a) => typeof el[a] === "string")
    .map((a) => `${a}="${escape(String(el[a]))}"`);
  // Comme Job-Room : required="true" ou required="false" (attribut présent dans les deux cas).
  if (typeof el.required === "string") attrs.push(`required="${el.required}"`);
  if (el["aria-required"]) attrs.push(`aria-required="${String(el["aria-required"])}"`);
  const label = escape(String(el.etiquette ?? ""));
  if (el.balise === "select") {
    const options = (el.options as string[]).map((o) => `<option value="${escape(o)}">${escape(o)}</option>`).join("");
    return `<label for="${escape(String(el.id))}">${label}</label><select ${attrs.join(" ")}>${options}</select>`;
  }
  if (el.balise === "button") return `<button type="${String(el.type)}">${escape(String(el.texte))}</button>`;
  if (el.type === "checkbox" || el.type === "radio") {
    const name = el.type === "radio" ? ` name="${String(el.id).replace(/-[^-]+$/, "")}"` : "";
    return `<label><input ${attrs.join(" ")}${name}> ${label}</label>`;
  }
  return `<label for="${escape(String(el.id))}">${label}</label><input ${attrs.join(" ")}>`;
}

function buildForm(): void {
  document.body.innerHTML = `<header>Connecté</header><form>${(releve.elements as Element[])
    .map((el) => ("titre" in el && el.titre ? `<h3>${escape(el.titre)}</h3>` : control(el)))
    .join("")}</form>`;
  const place = document.querySelector<HTMLInputElement>('[role="combobox"]')!;
  // Le champ à suggestions : la liste s'ouvre un peu après la saisie, le clic choisit.
  place.addEventListener("input", () => {
    setTimeout(() => {
      document.querySelector('[role="listbox"]')?.remove();
      const list = document.createElement("div");
      list.setAttribute("role", "listbox");
      for (const text of PLACES.filter((p) => p.startsWith(place.value))) {
        const option = document.createElement("div");
        option.setAttribute("role", "option");
        option.textContent = text;
        option.addEventListener("click", () => {
          place.value = text;
          list.remove();
        });
        list.append(option);
      }
      document.body.append(list);
    }, 150);
  });
  document.querySelector("form")!.addEventListener("submit", () => {
    throw new Error("le formulaire ne doit jamais être envoyé");
  });
}

const values = {
  date: "02.10.2026",
  channel: "electronic",
  company: "Acme SA",
  street: "Rue du Marché",
  number: "4b",
  po_box: "123",
  postcode_city: "1211 Genève 3",
  contact: "Camille Exemple",
  email: "rh@exemple.ch",
  phone: "022 000 00 00",
  job_title: "Ingénieur DevOps",
  url: "https://emploi.exemple.ch/1",
  assigned: false,
  rate: "PARTTIME",
  interview: true,
  result: "PENDING",
};

// La fonction ne laisse rien dans la page : elle se passe en entier à `executeScript`.
const jobRoom = () => ({ fill: fillJobRoom });
const input = (part: string): HTMLInputElement =>
  document.querySelector(`input[id*="${part}"], select[id*="${part}"]`)!;
const checked = (id: string): boolean => (document.getElementById(id) as HTMLInputElement).checked;

describe("remplissage de Job-Room", () => {
  beforeEach(buildForm);

  it("remplit toute la saisie et choisit les réponses, sans enregistrer", async () => {
    const report = await jobRoom().fill(values);
    expect(report.form).toBe(true);
    expect(input("global.date").value).toBe("02.10.2026");
    expect(input("company.name").value).toBe("Acme SA");
    expect([input("company.street").value, input("house-number").value, input("postbox-number").value]).toEqual([
      "Rue du Marché",
      "4b",
      "123",
    ]);
    expect(input("company.country").value).toBe("Suisse");
    expect(input("typeahead-npa").value).toBe("1211 Genève 3");
    expect([input("contact-person").value, input("contact.email").value, input("global.phone").value]).toEqual([
      "Camille Exemple",
      "rh@exemple.ch",
      "022 000 00 00",
    ]);
    expect(input("job-title").value).toBe("Ingénieur DevOps");
    expect(input("online-form-url").value).toBe("https://emploi.exemple.ch/1");
    expect(checked("alv-checkbox-portal.work-efforts.edit-form.apply-channel.electronic-0")).toBe(true);
    expect(checked("alv-checkbox-portal.work-efforts.edit-form.apply-channel.phone-0")).toBe(false);
    expect([checked("alv-radio-button-0-false"), checked("alv-radio-button-0-true")]).toEqual([true, false]);
    expect(checked("alv-radio-button-1-PARTTIME")).toBe(true);
    expect([checked("alv-checkbox-0"), checked("alv-radio-button-2-PENDING")]).toEqual([true, true]);
    expect(report.todo).toEqual([]);
    expect(report.filled).toContain("NPA / Lieu");
    expect(input("company.name").style.outline).toContain("solid");
  });

  it("garde ce qui est déjà saisi, sauf la date, et liste ce qui reste à faire", { timeout: 10_000 }, async () => {
    input("company.name").value = "Saisi à la main";
    input("global.date").value = "18.10.2026";
    const report = await jobRoom().fill({
      ...values,
      postcode_city: "9999 Nulle-part",
      rate: "",
      interview: false,
      result: "REJECTED",
    });
    expect(input("company.name").value).toBe("Saisi à la main");
    expect(input("global.date").value).toBe("02.10.2026");
    expect(checked("alv-checkbox-0")).toBe(false);
    expect(checked("alv-radio-button-2-REJECTED")).toBe(true);
    expect(report.todo).toEqual([
      { label: "NPA / Lieu", value: "9999 Nulle-part" },
      { label: "Taux d'occupation", value: "" },
    ]);
  });

  it("vise le champ, pas son cadre ni son étiquette au même identifiant", async () => {
    // Job-Room entoure ses champs de composants dont l'identifiant reprend celui du champ.
    for (const part of ["global.date", "company.name"]) {
      const field = input(part);
      const wrapper = document.createElement("div");
      wrapper.id = `${field.id}-wrapper`;
      field.before(wrapper);
      const hint = document.createElement("span");
      hint.id = `${field.id}-label`;
      wrapper.before(hint);
    }
    await jobRoom().fill(values);
    expect(input("global.date").value).toBe("02.10.2026");
    expect(input("company.name").value).toBe("Acme SA");
  });

  it("ne signale pas les champs facultatifs vides (required=\"false\")", async () => {
    const report = await jobRoom().fill({ ...values, po_box: "", contact: "", email: "", phone: "", url: "" });
    expect(report.todo).toEqual([]);
  });

  it("signale un champ obligatoire resté vide", async () => {
    const report = await jobRoom().fill({ ...values, job_title: "" });
    expect(report.todo).toEqual([{ label: "Désignation du poste", value: "" }]);
  });

  it("ne fait rien hors du formulaire de saisie", async () => {
    document.body.innerHTML = "<main><h1>Mes recherches d'emploi</h1></main>";
    expect(await jobRoom().fill(values)).toEqual({ form: false, filled: [], todo: [] });
  });

  it("se passe en entier à la page : rien d'autre, pas de variable globale (docs/76 §5)", async () => {
    // `executeScript({ func })` ne transmet que le texte de la fonction : on la recrée de même.
    const copy = new Function(`return (${fillJobRoom.toString()})`)() as typeof fillJobRoom;
    const report = await copy(values);
    expect(report.form).toBe(true);
    // L'ancienne porte d'entrée, qu'une page pouvait préparer, n'existe plus.
    expect((globalThis as Record<string, unknown>).jobbotJobRoom).toBeUndefined();
  });

  it("un champ devenu zone de texte se remplit ; un autre mode déjà coché est signalé", async () => {
    const company = input("company.name");
    const area = document.createElement("textarea");
    area.id = company.id;
    company.replaceWith(area);
    const mail = document.querySelector<HTMLInputElement>('input[id*="apply-channel.mail"]')!;
    mail.checked = true;
    const report = await jobRoom().fill(values);
    expect(area.value).toBe("Acme SA");
    expect(report.todo.map((t) => t.label)).toContain("Autre mode coché");
  });

  it("l'assignation ORP vise la question de l'ORP, pas le premier oui / non", async () => {
    const other = document.createElement("div");
    other.innerHTML = '<p>Autre question ?</p><input type="radio" id="autre-true"><input type="radio" id="autre-false">';
    document.querySelector("form")!.prepend(other);
    const orp = document.getElementById("alv-radio-button-0-false")!;
    const groupBox = document.createElement("div");
    groupBox.innerHTML = "<p>Assignation par l'ORP ?</p>";
    orp.closest("label")!.before(groupBox);
    groupBox.append(document.getElementById("alv-radio-button-0-true")!.closest("label")!, orp.closest("label")!);
    await jobRoom().fill(values);
    expect(checked("alv-radio-button-0-false")).toBe(true);
    expect(checked("autre-false")).toBe(false);
  });
});
