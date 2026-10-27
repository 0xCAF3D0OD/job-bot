import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent } from "vue";

import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

const Field = defineComponent({
  components: { SettingCard, SettingRow },
  props: { saved: Boolean, error: { type: String, default: "" } },
  template: `<SettingCard>
    <SettingRow title="Objectif mensuel de l'ORP" description="Les candidatures demandées chaque mois." :saved="saved" :error="error" stack>
      <template #default="{ labelledby, describedby, invalid }">
        <input :aria-labelledby="labelledby" :aria-describedby="describedby" :aria-invalid="invalid" value="10">
      </template>
    </SettingRow>
  </SettingCard>`,
});

describe("Ligne de réglage (1.6.65)", () => {
  it("le titre nomme le contrôle, la phrase le décrit", () => {
    const wrapper = mount(Field);
    const input = wrapper.find("input");
    const title = wrapper.find(".setting-row-title");
    expect(input.attributes("aria-labelledby")).toBe(title.attributes("id"));
    expect(input.attributes("aria-describedby")).toBe(wrapper.find(".setting-row-description").attributes("id"));
    expect(input.attributes("aria-invalid")).toBeUndefined();
  });

  it("« Enregistré » dans un message d'état (WCAG 4.1.3), vide tant que rien n'est enregistré", async () => {
    const wrapper = mount(Field);
    const status = wrapper.find("[data-test=setting-saved]");
    expect(status.attributes("role")).toBe("status");
    expect(status.text()).toBe("");
    await wrapper.setProps({ saved: true });
    expect(wrapper.find("[data-test=setting-saved]").text()).toBe("Enregistré");
  });

  it("une erreur sous le champ, reliée à lui (WCAG 3.3.1) ; pas d'« Enregistré » en même temps", async () => {
    const wrapper = mount(Field, { props: { saved: true, error: "Entre 1 et 28." } });
    const error = wrapper.find("[data-test=setting-error]");
    expect(error.text()).toBe("Entre 1 et 28.");
    const input = wrapper.find("input");
    expect(input.attributes("aria-describedby")).toContain(error.attributes("id"));
    expect(input.attributes("aria-invalid")).toBe("true");
    expect(wrapper.find("[data-test=setting-saved]").text()).toBe("");
  });

  it("`wide` : la classe qui met le contrôle sous le texte à toutes les tailles", () => {
    const wrapper = mount(SettingRow, { props: { title: "Jeton", wide: true }, slots: { default: "<code>abc</code>" } });
    expect(wrapper.find(".setting-row").classes()).toContain("wide");
  });

  it("`inline` : la classe qui garde un état court à droite sur téléphone", () => {
    const wrapper = mount(SettingRow, { props: { title: "jobup", inline: true }, slots: { default: "<span>Reçue</span>" } });
    expect(wrapper.find(".setting-row").classes()).toContain("inline");
  });
});
