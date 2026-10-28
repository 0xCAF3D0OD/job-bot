import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormField from "./FormField.vue";

const input = `<template #default="{ id, describedby, invalid }"><input :id="id" :aria-describedby="describedby" :aria-invalid="invalid"></template>`;

describe("FormField (planche « Formulaires »)", () => {
  it("libellé relié au champ, « (facultatif) », aide reliée", () => {
    const wrapper = mount(FormField, { props: { label: "Date d'envoi", hint: "jj.mm.aaaa", optional: true, width: 10 }, slots: { default: input } });
    const field = wrapper.find("input");
    expect(wrapper.find("label").attributes("for")).toBe(field.attributes("id"));
    expect(wrapper.find("label").text()).toBe("Date d'envoi (facultatif)");
    expect(field.attributes("aria-describedby")).toBe(wrapper.find(".form-field-hint").attributes("id"));
    expect(field.attributes("aria-invalid")).toBeUndefined();
    expect(wrapper.classes()).toContain("field-w-10");
  });

  it("l'erreur sous le champ, reliée, le champ marqué invalide", () => {
    const wrapper = mount(FormField, { props: { label: "Entreprise", error: "Indique l'entreprise." }, slots: { default: input } });
    const field = wrapper.find("input");
    const error = wrapper.find(".field-error");
    expect(error.text()).toBe("Indique l'entreprise.");
    expect(field.attributes("aria-invalid")).toBe("true");
    expect(field.attributes("aria-describedby")).toBe(error.attributes("id"));
    // L'erreur vient après le champ, pas entre le libellé et le champ.
    const order = [...wrapper.element.children].map((e) => e.tagName.toLowerCase());
    expect(order.indexOf("p")).toBeGreaterThan(order.indexOf("input"));
  });
});
