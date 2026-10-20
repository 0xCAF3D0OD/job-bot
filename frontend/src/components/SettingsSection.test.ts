import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { defineComponent } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import SettingsSection from "./SettingsSection.vue";

const original = globalThis.matchMedia;
afterEach(() => {
  globalThis.matchMedia = original;
});

function phone(matches: boolean): void {
  globalThis.matchMedia = ((query: string) =>
    ({ matches, media: query, addEventListener: () => {}, removeEventListener: () => {} }) as unknown as MediaQueryList);
}

const Page = defineComponent({
  components: { SettingsSection },
  template: `<div>
    <SettingsSection id="recherche" title="Recherche d'emploi" value="objectif 10 / mois"><p>critères</p></SettingsSection>
    <SettingsSection id="actualites" title="Actualités"><p>sources</p></SettingsSection>
  </div>`,
});

async function mountAt(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: Page }] });
  await router.push(path);
  const wrapper = mount(Page, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("Section des Réglages (docs/110)", () => {
  it("ordinateur : le titre de la section au-dessus de sa carte", async () => {
    phone(false);
    const wrapper = await mountAt("/reglages");
    expect(wrapper.findAll("section.settings-section").map((s) => s.attributes("id"))).toEqual(["recherche", "actualites"]);
    expect(wrapper.findAll(".settings-section > h2.section-title").map((h) => h.text())).toEqual(["Recherche d'emploi", "Actualités"]);
    expect(wrapper.find(".settings-section > .settings-card").text()).toBe("critères");
    expect(wrapper.find(".disclosure").exists()).toBe(false);
  });

  it("téléphone : plus de lignes dépliables, toutes les sections l'une sous l'autre", async () => {
    phone(true);
    const wrapper = await mountAt("/reglages#actualites");
    expect(wrapper.find(".settings-row").exists()).toBe(false);
    expect(wrapper.findAll("section.settings-section")).toHaveLength(2);
    expect(wrapper.text()).toContain("critères");
    expect(wrapper.text()).toContain("sources");
  });
});
