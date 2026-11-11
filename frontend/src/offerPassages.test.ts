import { describe, expect, it } from "vitest";

import { buildExcerpt, markSegments, matchedPassages, letterPoints, letterSegments, letterTerms } from "./offerPassages";

describe("passages de l'annonce retrouvés dans le profil", () => {
  it("lit les passages vérifiés par le serveur, rien pour une note plus ancienne", () => {
    expect(matchedPassages({ passages: ["clusters Kubernetes"] })).toEqual(["clusters Kubernetes"]);
    expect(matchedPassages({} as { passages: string[] })).toEqual([]);
  });

  it("retrouve un passage malgré un retour à la ligne, une insécable, la casse ou l'apostrophe", () => {
    const text = "Vous faites évoluer l’infrastructure avec Terraform et Ansible.";
    const marks = markSegments(text, ["l'infrastructure avec\nTerraform", "terraform et\u00a0ansible"]).filter((s) => s.mark);
    // Le texte affiché reste celui de l'annonce.
    expect(marks.map((m) => m.text)).toEqual(["l’infrastructure avec Terraform"]);
    expect(markSegments(text, ["Terraform et\u00a0Ansible"]).filter((s) => s.mark)[0]!.text).toBe("Terraform et Ansible");
  });

  it("garde un texte court en entier", () => {
    const excerpt = buildExcerpt("Vous gérez Kubernetes et Terraform.", ["Kubernetes", "Terraform"]);
    expect(excerpt.built).toBe(false);
    expect(excerpt.count).toBe(2);
    expect(excerpt.segments.map((s) => s.text).join("")).toBe("Vous gérez Kubernetes et Terraform.");
  });

  it("construit l'extrait d'un texte long autour des passages, reliés par (…)", () => {
    const filler = "Notre entreprise familiale existe depuis cinquante ans et grandit chaque année. ";
    const text = `${filler}Vous exploitez nos clusters Kubernetes multi-régions. ${filler}${filler}Vous écrivez l’infrastructure avec Terraform et Ansible. ${filler}`;
    const excerpt = buildExcerpt(text, ["Kubernetes", "Terraform", "Ansible"], 150);
    const shown = excerpt.segments.map((s) => s.text).join("");
    expect(excerpt.built).toBe(true);
    expect(shown.startsWith("(…) ")).toBe(true);
    expect(shown).toContain(" (…) ");
    expect(excerpt.count).toBe(3);
    expect(shown.length).toBeLessThanOrEqual(170);
  });

  it("retire en entier un fragment qui ne tient pas, sans couper un passage surligné", () => {
    const filler = "Un long paragraphe sans rapport avec le profil, qui parle de la cantine et du parking. ";
    const text = `Kubernetes au quotidien. ${filler}${filler}Terraform aussi. ${filler}${filler}Et enfin Ansible.`;
    const excerpt = buildExcerpt(text, ["Kubernetes", "Terraform", "Ansible"], 70);
    const marks = excerpt.segments.filter((s) => s.mark).map((s) => s.text);
    expect(marks.length).toBeLessThan(3);
    for (const mark of marks) expect(["Kubernetes", "Terraform", "Ansible"]).toContain(mark);
  });

  it("sans passage retrouvé, donne le début de l'annonce, que la page coupe", () => {
    const text = "Vous rejoignez une petite équipe. ".repeat(30).trim();
    const excerpt = buildExcerpt(text, []);
    expect(excerpt.count).toBe(0);
    expect(excerpt.built).toBe(true);
    expect(excerpt.segments).toHaveLength(1);
    expect(text.startsWith(excerpt.segments[0]!.text)).toBe(true);
    expect(excerpt.segments[0]!.text.length).toBeGreaterThan(300);
  });
});

describe("la lettre : « Repris de l’annonce » (PR 51)", () => {
  const offer = {
    description: "Vous travaillez avec Kubernetes, Terraform, CI/CD. Go est un plus.",
    snippet: null,
    passages: ["Vous travaillez avec Kubernetes, Terraform, CI/CD"],
    keywords_asks: [{ text: "Kubernetes" }, { text: "Terraform" }, { text: "Go" }, { text: "Ansible" }, { text: "kubernetes" }],
  };

  it("ne garde que les demandes et les passages qui se lisent dans l’annonce, sans doublon", () => {
    expect(letterTerms(offer)).toEqual(["Kubernetes", "Terraform", "Go", "Vous travaillez avec Kubernetes, Terraform, CI/CD"]);
    expect(letterTerms(null)).toEqual([]);
    // Sans texte d'annonce connu, les demandes relevées avec la note sont gardées telles quelles.
    expect(letterTerms({ description: null, snippet: null, passages: [], keywords_asks: [{ text: "Ansible" }] })).toEqual(["Ansible"]);
  });

  it("surligne en mots entiers, sans toucher au texte", () => {
    const text = "J’ai mis en place une plateforme Kubernetes chez Google, décrite en terraform.";
    const segments = letterSegments(text, letterTerms(offer));
    expect(segments.map((s) => s.text).join("")).toBe(text);
    // « Go » n'est pas surligné dans « Google ».
    expect(segments.filter((s) => s.mark).map((s) => s.text)).toEqual(["Kubernetes", "terraform"]);
  });

  it("compte les termes différents repris dans toute la lettre", () => {
    const paragraphs = ["Kubernetes au quotidien.", "Encore kubernetes, et Terraform.", "Rien ici."];
    expect(letterPoints(paragraphs, letterTerms(offer))).toBe(2);
    expect(letterPoints(paragraphs, [])).toBe(0);
  });
});
