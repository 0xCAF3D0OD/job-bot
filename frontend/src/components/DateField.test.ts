import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent, h, ref } from "vue";

import DateField from "./DateField.vue";
import { pickDate } from "./DateField.testing";

// Lot 10 (maquette du 8 novembre, D26) : plus aucun champ de date natif ; la pilule et le sélecteur à sa place.
function host(props: Record<string, unknown>) {
  const value = ref<string | null>((props.modelValue as string | null) ?? null);
  const Host = defineComponent({
    setup: () => () =>
      h(DateField as never, { ...props, modelValue: value.value, "onUpdate:modelValue": (v: string | null) => (value.value = v), "data-test": "field" }),
  });
  return { wrapper: mount(Host, { attachTo: document.body }), value };
}

describe("DateField", () => {
  it("la pilule sans heure, le sélecteur à sa place, puis le curseur revient sur la pilule", async () => {
    const { wrapper, value } = host({ label: "Date d'envoi", min: null, max: "2026-11-08" });
    expect(wrapper.find("input[type=date]").exists()).toBe(false);
    expect(wrapper.find("[data-test=dt-time]").exists()).toBe(false);
    expect(wrapper.find("[data-test=dt-date]").attributes("aria-label")).toBe("Date d'envoi : Choisir une date");
    await pickDate(wrapper, "field", "2026-10-06");
    expect(value.value).toBe("2026-10-06");
    expect(wrapper.find("[data-test=date-time-panel]").exists()).toBe(false);
    expect(document.activeElement).toBe(wrapper.find("[data-test=dt-date]").element);
    wrapper.unmount();
  });

  it("une date passée : les raccourcis à venir disparaissent, un jour après `max` est refusé", async () => {
    const { wrapper, value } = host({ label: "Terminée le", min: null, max: "2026-11-08" });
    await wrapper.find("[data-test=dt-date]").trigger("click");
    expect(wrapper.find(".dt-shortcuts").exists()).toBe(false);
    expect(wrapper.find("[data-test=dt-next]").attributes("disabled")).toBeDefined();
    const typed = wrapper.find("[data-test=dt-typed-date]");
    await typed.setValue("20.11.2026");
    await typed.trigger("change");
    expect(wrapper.find("[role=alert]").text()).toMatch(/^(Ce jour n'est pas encore arrivé|Choisis un jour jusqu'au .+)\.$/);
    await wrapper.find("[data-test=date-time-panel]").trigger("keydown", { key: "Escape" });
    expect(value.value).toBeNull();
    wrapper.unmount();
  });

  it("facultatif : « Effacer la date »", async () => {
    const { wrapper, value } = host({ label: "Avant le", min: null, optional: true, modelValue: "2026-10-20" });
    await wrapper.find("[data-test=date-clear]").trigger("click");
    expect(value.value).toBeNull();
    expect(wrapper.find("[data-test=date-clear]").exists()).toBe(false);
    wrapper.unmount();
  });
});
