// Remplissage de Job-Room par l'extension (extension/fill-job-room.js, docs/70 §4, §5). Le
// formulaire est reconstruit à partir du relevé du formulaire réel (extension/fixtures/).
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

import releve from "../../extension/fixtures/job-room-formulaire.json";

type Report = { form: boolean; filled: string[]; todo: { label: string; value: string }[] };
type JobRoom = { fill: (data: unknown) => Promise<Report> };
type Element = (typeof releve.elements)[number] & Record<string, unknown>;

// Les suggestions de « NPA / Lieu », comme Job-Room les propose après la saisie du NPA.
const PLACES = ["1000 Lausanne", "1003 Lausanne", "1211 Genève 3", "1212 Grand-Lancy"];

beforeAll(async () => {
  globalThis.CSS ??= { escape: (v: string) => v } as typeof CSS;
  // @ts-expect-error script de l'extension, sans types (injecté tel quel dans les pages)
  await import("../../extension/fill-job-room.js");
});

function escape(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function control(el: Element): string {
  const attrs = ["id", "type", "role", "placeholder", "autocomplete"]
    .filter((a) => typeof el[a] === "string")
    .map((a) => `${a}="${escape(String(el[a]))}"`);
  if (el.required === "true") attrs.push("required");
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

const jobRoom = (): JobRoom => (globalThis as unknown as { jobbotJobRoom: JobRoom }).jobbotJobRoom;
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

  it("ne fait rien hors du formulaire de saisie", async () => {
    document.body.innerHTML = "<main><h1>Mes recherches d'emploi</h1></main>";
    expect(await jobRoom().fill(values)).toEqual({ form: false, filled: [], todo: [] });
  });
});
