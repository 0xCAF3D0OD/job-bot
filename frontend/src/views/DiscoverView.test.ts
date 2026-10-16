import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import DiscoverView from "./DiscoverView.vue";

describe("La plateforme (docs/67)", () => {
  it("présente les étapes et propose de se connecter à qui ne l'est pas", async () => {
    useAuth().me.value = null;
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/la-plateforme");
    const wrapper = mount(DiscoverView, { global: { plugins: [router] } });
    expect(wrapper.findAll(".discover-step")).toHaveLength(6);
    expect(wrapper.find("[data-test=discover-login]").attributes("href")).toBe("/connexion");
    expect(wrapper.text()).toContain("ne partent jamais à l'IA");
  });
});
