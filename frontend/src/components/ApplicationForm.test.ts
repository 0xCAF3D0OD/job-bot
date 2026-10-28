import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import ApplicationForm from "./ApplicationForm.vue";

const initial = { sent_at: "", method: "electronique", company: "", job_title: "", assigned_by_orp: false } as never;

function mountForm() {
  return mount(ApplicationForm, {
    props: { title: "Ajouter une candidature", initial, withStatus: false },
    attachTo: document.body,
  });
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("ApplicationForm (règles §4, Champ de formulaire et Formulaire)", () => {
  it("l'erreur apparaît sous le champ en le quittant, dit quoi faire, et part dès que c'est corrigé", async () => {
    const wrapper = mountForm();
    const company = wrapper.find("[data-test=company]");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    await company.trigger("blur");
    const error = wrapper.find("[data-test=field-error]");
    expect(error.text()).toBe("Indique l'entreprise.");
    expect(company.attributes("aria-invalid")).toBe("true");
    expect(company.attributes("aria-describedby")).toBe(error.attributes("id"));
    await company.setValue("Beta Sàrl");
    expect(wrapper.find("[data-test=field-error]").exists()).toBe(false);
    expect(company.attributes("aria-invalid")).toBeUndefined();
    wrapper.unmount();
  });

  it("à l'envoi : une erreur sous chaque champ manquant, le curseur dans le premier, rien d'envoyé", async () => {
    const wrapper = mountForm();
    await wrapper.find("[data-test=company]").setValue("Beta Sàrl");
    await wrapper.find("form").trigger("submit");
    await wrapper.vm.$nextTick();
    expect(wrapper.findAll("[data-test=field-error]").map((e) => e.text())).toEqual([
      "Indique la date d'envoi.",
      "Indique le poste.",
    ]);
    expect(document.activeElement).toBe(wrapper.find("[data-test=sent-at]").element);
    expect(wrapper.emitted("submit")).toBeUndefined();
    // Pas de message global à la place des messages sous les champs.
    expect(wrapper.find(".notice.error").exists()).toBe(false);
    wrapper.unmount();
  });

  it("libellés au-dessus, « (facultatif) » sur les champs facultatifs, un seul bouton principal nommé par l'action", () => {
    const wrapper = mountForm();
    const labels = wrapper.findAll(".form-field-label").map((l) => l.text());
    expect(labels).toContain("Entreprise");
    expect(labels).toContain("Lieu (facultatif)");
    expect(wrapper.findAll("[placeholder=facultatif]")).toHaveLength(0);
    const buttons = wrapper.findAll(".form-actions button");
    expect(buttons.map((b) => b.text())).toEqual(["Enregistrer la candidature", "Annuler"]);
    expect(wrapper.findAll("button.primary")).toHaveLength(1);
    wrapper.unmount();
  });
});
