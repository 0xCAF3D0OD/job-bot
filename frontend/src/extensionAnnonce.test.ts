// Lecture de l'annonce par l'extension (extension/annonce.js, docs/142 §3), sur des pages types
// (extension/fixtures/annonces/) : JobPosting, LinkedIn (l'annonce ouverte seulement), texte
// principal, page ordinaire. Ouverture : titre, entreprise, lieu ; « Envoyer » : le texte en plus.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

type Annonce = { kind: string; url: string; title: string; company: string; location: string; text?: string } | null;
let read: (full: boolean) => Annonce;

const dir = resolve(__dirname, "../../extension/fixtures/annonces");

function open(file: string, url: string): void {
  const html = readFileSync(resolve(dir, file), "utf-8");
  document.documentElement.innerHTML = html.replace(/^<!doctype html>\s*<html[^>]*>|<\/html>\s*$/gi, "");
  window.history.replaceState(null, "", "/");
  Object.defineProperty(window, "location", { configurable: true, value: new URL(url) });
}

beforeAll(async () => {
  // @ts-expect-error script de l'extension, sans types (passé tel quel à la page)
  await import("../../extension/annonce.js");
  read = (globalThis as unknown as { jobA1Annonce: typeof read }).jobA1Annonce;
});

describe("l'annonce de la page", () => {
  it("JobPosting : titre, entreprise, lieu à l'ouverture, sans le texte", () => {
    open("jobposting.html", "https://careers.specitec.com/jobs/7?utm=x#postuler");
    expect(read(false)).toEqual({
      kind: "posting",
      url: "https://careers.specitec.com/jobs/7?utm=x",
      title: "DevOps Engineer",
      company: "Sword Services",
      location: "Genève",
    });
  });

  it("JobPosting : « Envoyer » lit la description, pas le reste de la page", () => {
    open("jobposting.html", "https://careers.specitec.com/jobs/7");
    const found = read(true)!;
    expect(found.text).toContain("Tu automatises nos déploiements avec Ansible et Terraform.");
    expect(found.text).toContain("Linux Kubernetes");
    expect(found.text).not.toContain("<");
    // Ni le profil connecté, ni les champs de la page.
    expect(found.text).not.toContain("Camille");
    expect(found.text).not.toContain("newsletter");
  });

  it("LinkedIn : l'annonce ouverte seulement, jamais le profil ni la liste", () => {
    open("linkedin.html", "https://www.linkedin.com/jobs/search/?currentJobId=3912345678&keywords=linux");
    const found = read(true)!;
    expect(found.kind).toBe("linkedin");
    expect(found.url).toBe("https://www.linkedin.com/jobs/view/3912345678/");
    expect(found.title).toBe("Ingénieur·e système Linux");
    expect(found.company).toBe("SpeciTec SA");
    expect(found.text).toContain("administrer nos serveurs Linux");
    expect(found.text).not.toContain("Camille");
    expect(found.text).not.toContain("Autre offre");
  });

  it("LinkedIn sans annonce ouverte (profil, fil, liste) : rien", () => {
    open("linkedin.html", "https://www.linkedin.com/in/camille-exemple/");
    expect(read(true)).toBeNull();
    open("linkedin.html", "https://www.linkedin.com/jobs/search/?keywords=linux");
    expect(read(true)).toBeNull();
  });

  it("sans balisage : le texte principal d'une page d'annonce, le titre lu par jobA1", () => {
    open("texte-principal.html", "https://www.exemple.ch/carriere/admin-systeme");
    expect(read(false)).toMatchObject({ kind: "text", title: "Administrateur système (80-100 %)" });
    const found = read(true)!;
    expect(found.text).toContain("infrastructure Linux de nos clients");
    expect(found.text).not.toContain("Accueil · Carrière");
  });

  it("une page ordinaire n'est pas une annonce", () => {
    open("page-ordinaire.html", "https://www.recettes.ch/tarte-aux-pommes");
    expect(read(false)).toBeNull();
  });
});
