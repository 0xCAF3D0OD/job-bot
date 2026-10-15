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

describe("Section des Réglages (docs/34 §3)", () => {
  it("ordinateur : le titre et le contenu, comme avant", async () => {
    phone(false);
    const wrapper = await mountAt("/reglages");
    expect(wrapper.findAll("h2.section-title").map((h) => h.attributes("id"))).toEqual(["recherche", "actualites"]);
    expect(wrapper.find(".disclosure").exists()).toBe(false);
  });

  it("téléphone : une ligne dépliable avec résumé, le lien #actualites l'ouvre", async () => {
    phone(true);
    const wrapper = await mountAt("/reglages#actualites");
    const rows = wrapper.findAll(".settings-row");
    expect(rows).toHaveLength(2);
    expect(rows[0]!.find(".disclosure-value").text()).toBe("objectif 10 / mois");
    expect(rows[0]!.classes()).not.toContain("open");
    expect(rows[1]!.classes()).toContain("open");
  });
});
