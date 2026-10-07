// Script de remplissage de l'extension (extension/fill.js, docs/25 §3.5).
import { beforeAll, describe, expect, it } from "vitest";

type Report = { filled: string[]; todo: string[]; questions: { key: string; label: string }[]; frames: string[] };
type Fill = {
  fill: (data: unknown) => Report;
  setAnswer: (key: string, text: string) => boolean;
};

class FakeTransfer {
  private list: File[] = [];
  items = { add: (file: File) => this.list.push(file) };
  get files(): File[] {
    return this.list;
  }
}

beforeAll(async () => {
  Object.assign(globalThis, { DataTransfer: FakeTransfer });
  // jsdom n'accepte qu'une vraie FileList : on garde les fichiers posés tels quels.
  Object.defineProperty(HTMLInputElement.prototype, "files", {
    configurable: true,
    get(this: { _files?: File[] }) {
      return this._files ?? [];
    },
    set(this: { _files?: File[] }, value: File[]) {
      this._files = value;
    },
  });
  globalThis.CSS ??= { escape: (v: string) => v } as typeof CSS;
  // @ts-expect-error script de l'extension, sans types (injecté tel quel dans les pages)
  await import("../../extension/fill.js");
});

const data = {
  identity: {
    name: "Camille Di Exemple",
    street: "Rue du Test 1",
    postcode: "1020",
    city: "Renens",
    phone: "+41 79 000 00 00",
    email: "camille@example.ch",
    linkedin: "https://linkedin.com/in/camille",
    website: null,
    availability: null,
    salary: "CHF 90'000",
    permit: "Permis C",
  },
  letterText: "Madame, Monsieur…",
  files: { cv: { name: "CV - Exemple SA.pdf", base64: btoa("%PDF-1.4") } },
};

function jobbot(): Fill {
  return (globalThis as unknown as { jobbotFill: Fill }).jobbotFill;
}

describe("remplissage du formulaire", () => {
  it("remplit les champs reconnus en français et en allemand, sans écraser ni cocher", () => {
    document.documentElement.lang = "fr";
    document.body.innerHTML = `
      <form>
        <label for="fn">Prénom *</label><input id="fn" required>
        <label>Nom <input name="lastname" required></label>
        <input type="email" name="x1" aria-label="Adresse e-mail">
        <label>Vorname / Telefon <input name="phone_number" autocomplete="tel"></label>
        <label>NPA <input name="zip"></label><label>Localité <input name="ort"></label>
        <label>Adresse <input name="address"></label>
        <label>Pays <select name="country"><option value="">—</option><option value="FR">France</option><option value="CH">Suisse</option></select></label>
        <label>Prétentions salariales <input name="salary"></label>
        <label>Profil LinkedIn <input name="li" value="déjà rempli"></label>
        <label>Lettre de motivation <textarea name="cover"></textarea></label>
        <label>Pourquoi souhaitez-vous nous rejoindre ? <textarea name="why"></textarea></label>
        <label>Date de naissance <input name="birth" required></label>
        <label><input type="checkbox" name="consent" required> J'accepte la politique de confidentialité</label>
        <label>CV <input type="file" name="resume"></label>
      </form>`;
    const report = jobbot().fill(data);
    const value = (name: string) => (document.querySelector(`[name="${name}"]`) as HTMLInputElement).value;
    expect((document.getElementById("fn") as HTMLInputElement).value).toBe("Camille");
    expect(value("lastname")).toBe("Di Exemple");
    expect(value("x1")).toBe("camille@example.ch");
    expect(value("phone_number")).toBe("+41 79 000 00 00");
    expect([value("zip"), value("ort"), value("address")]).toEqual(["1020", "Renens", "Rue du Test 1"]);
    expect(value("country")).toBe("CH");
    expect(value("salary")).toBe("CHF 90'000");
    expect(value("li")).toBe("déjà rempli");
    expect(value("cover")).toBe("Madame, Monsieur…");
    expect(value("why")).toBe("");
    expect((document.querySelector('[name="consent"]') as HTMLInputElement).checked).toBe(false);
    expect((document.querySelector('[name="resume"]') as HTMLInputElement).files).toHaveLength(1);
    expect(report.filled).toContain("CV (PDF)");
    expect(report.todo).toEqual(["Date de naissance"]);
    expect(report.questions).toEqual([{ key: "0", label: "Pourquoi souhaitez-vous nous rejoindre ?" }]);
    expect(jobbot().setAnswer("0", "Parce que…")).toBe(true);
    expect(value("why")).toBe("Parce que…");
  });

  it("met le nom complet dans un seul champ « Name », et signale un cadre d'un autre site", () => {
    document.documentElement.lang = "de";
    document.body.innerHTML = `
      <label>Name <input name="n"></label>
      <label>Land <input name="land"></label>
      <iframe src="https://boards.greenhouse.io/exemple/jobs/1"></iframe>`;
    const report = jobbot().fill(data);
    expect((document.querySelector('[name="n"]') as HTMLInputElement).value).toBe("Camille Di Exemple");
    expect((document.querySelector('[name="land"]') as HTMLInputElement).value).toBe("Schweiz");
    expect(report.frames).toEqual(["https://boards.greenhouse.io/exemple/jobs/1"]);
  });
});
