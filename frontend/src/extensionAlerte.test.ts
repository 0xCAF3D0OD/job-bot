// Le formulaire « Créer une alerte » des sites (extension/alertes.js, alert-selectors.js,
// docs/142 §4), un test par site sur une page type (extension/fixtures/alertes/) : l'adresse dans le
// champ e-mail, avec les événements input et change ; jamais le bouton d'envoi ; le repli quand
// les sélecteurs ne trouvent plus le champ.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

type Rules = { name: string; hosts: string[]; forms: string[]; email: string[]; marker: string; opener: string };
type Result = { form: boolean; filled: boolean };
let fillForm: (rules: Rules, address: string | null) => Result;
type Probe = { form: boolean; code: boolean; asks: boolean; done: boolean };
let probe: (rules: Rules) => Probe;
let paste: (rules: Rules, code: string) => boolean;
let rules: Record<string, Rules>;

const ADDRESS = "kevin.k3x@alertes.joba1.ch";
const dir = resolve(__dirname, "../../extension/fixtures/alertes");
const manifest = JSON.parse(readFileSync(resolve(__dirname, "../../extension/manifest.json"), "utf-8"));

function open(file: string): { events: string[]; submitted: () => boolean } {
  document.body.innerHTML = readFileSync(resolve(dir, file), "utf-8");
  const events: string[] = [];
  for (const input of document.querySelectorAll("input")) {
    for (const type of ["input", "change"]) input.addEventListener(type, () => events.push(`${input.name}:${type}`));
  }
  let submitted = false;
  document.addEventListener("submit", (event) => {
    submitted = true;
    event.preventDefault();
  });
  for (const button of document.querySelectorAll("button")) button.addEventListener("click", () => (submitted = true));
  return { events, submitted: () => submitted };
}

const value = (selector: string) => document.querySelector<HTMLInputElement>(selector)!.value;

beforeAll(async () => {
  // @ts-expect-error script de l'extension, sans types
  await import("../../extension/alert-selectors.js");
  // @ts-expect-error script de l'extension, sans types (passé tel quel à la page)
  await import("../../extension/alertes.js");
  const g = globalThis as unknown as {
    jobA1AlertForm: typeof fillForm;
    jobA1AlertSelectors: typeof rules;
    jobA1AlertProbe: typeof probe;
    jobA1PasteCode: typeof paste;
  };
  fillForm = g.jobA1AlertForm;
  probe = g.jobA1AlertProbe;
  paste = g.jobA1PasteCode;
  rules = g.jobA1AlertSelectors;
});

describe("remplir le formulaire d’alerte, par site", () => {
  it("jobup : l’adresse dans le champ e-mail, input et change, sans envoyer", () => {
    const page = open("jobup.html");
    expect(fillForm(rules.jobup!, ADDRESS)).toEqual({ form: true, filled: true });
    expect(value("#alert-email")).toBe(ADDRESS);
    expect(page.events).toEqual(["email:input", "email:change"]);
    expect(page.submitted()).toBe(false);
    // Ni la recherche, ni la newsletter, ni la case de consentement.
    expect(value("input[name=newsletter]")).toBe("");
    expect(document.querySelector<HTMLInputElement>("input[name=consent]")!.checked).toBe(false);
  });

  it("jobs.ch : le champ e-mail de la fenêtre, pas le nom de l’alerte", () => {
    const page = open("jobsch.html");
    expect(fillForm(rules.jobsch!, ADDRESS)).toEqual({ form: true, filled: true });
    expect(value("input[name=email]")).toBe(ADDRESS);
    expect(value("input[name=name]")).toBe("DevOps Lausanne");
    expect(page.events).toEqual(["email:input", "email:change"]);
    expect(page.submitted()).toBe(false);
  });

  it("LinkedIn : le champ de la fenêtre d’alerte seulement", () => {
    const page = open("linkedin.html");
    expect(fillForm(rules.linkedin!, ADDRESS)).toEqual({ form: true, filled: true });
    expect(value("#job-alert-email")).toBe(ADDRESS);
    expect(page.submitted()).toBe(false);
  });

  it("à l’ouverture, sans adresse : le formulaire est reconnu, rien n’est rempli", () => {
    open("jobup.html");
    expect(fillForm(rules.jobup!, null)).toEqual({ form: true, filled: false });
    expect(value("#alert-email")).toBe("");
  });

  it("sélecteurs cassés : le formulaire est là, le champ pas trouvé → repli « Copier »", () => {
    const page = open("jobup-casse.html");
    expect(fillForm(rules.jobup!, ADDRESS)).toEqual({ form: true, filled: false });
    expect(value("input[name=x1]")).toBe("");
    expect(page.events).toEqual([]);
  });

  it("fenêtre d’alerte fermée : pas de formulaire, ni la recherche ni la newsletter remplies", () => {
    open("jobup-sans-fenetre.html");
    expect(fillForm(rules.jobup!, ADDRESS)).toEqual({ form: false, filled: false });
    expect(value("input[name=newsletter]")).toBe("");
  });
});

describe("les sites et leurs accès", () => {
  it("host_permissions : jobup.ch, jobs.ch, linkedin.com, rien d’autre", () => {
    const hosts = Object.values(rules).flatMap((r) => r.hosts.map((h) => `https://${h}/*`));
    expect([...manifest.host_permissions].sort()).toEqual(hosts.sort());
    expect(manifest.host_permissions.join(" ")).not.toMatch(/all_urls|\*\.|auth\./);
    expect(manifest.permissions).not.toContain("<all_urls>");
  });
});

// Le suivi de l'alerte jobup (section 42) : où en est la page, le code collé sans jamais cliquer,
// et l'état secours quand le champ du code n'est plus reconnu.
describe("le code de l’alerte jobup", () => {
  it("le formulaire d’alerte ouvert : ni code demandé, ni alerte créée", () => {
    open("jobup.html");
    expect(probe(rules.jobup!)).toEqual({ form: true, code: false, asks: false, done: false });
  });

  it("le champ du code : reconnu, rempli comme au clavier, sans « Confirmer »", () => {
    const page = open("jobup-code.html");
    expect(probe(rules.jobup!)).toEqual({ form: false, code: true, asks: true, done: false });
    expect(paste(rules.jobup!, "482913")).toBe(true);
    expect(value("#otp")).toBe("482913");
    expect(page.events).toEqual(["code:input", "code:change"]);
    expect(page.submitted()).toBe(false);
  });

  it("six cases d’un chiffre : un chiffre par case, sans « Confirmer »", () => {
    const page = open("jobup-code-cases.html");
    expect(probe(rules.jobup!).code).toBe(true);
    expect(paste(rules.jobup!, "482913")).toBe(true);
    expect([...document.querySelectorAll("input")].map((i) => i.value).join("")).toBe("482913");
    expect(page.submitted()).toBe(false);
  });

  it("champ du code introuvable : la demande est vue, rien n’est collé (état secours)", () => {
    const page = open("jobup-code-casse.html");
    expect(probe(rules.jobup!)).toEqual({ form: false, code: false, asks: true, done: false });
    expect(paste(rules.jobup!, "482913")).toBe(false);
    expect(page.submitted()).toBe(false);
  });

  it("l’alerte créée est reconnue", () => {
    open("jobup-alerte-creee.html");
    expect(probe(rules.jobup!).done).toBe(true);
  });
});
