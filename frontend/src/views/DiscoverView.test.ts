import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import DiscoverView from "./DiscoverView.vue";

describe("La plateforme, en parcours (docs/67)", () => {
  it("présente les étapes et propose de se connecter à qui ne l'est pas", async () => {
    useAuth().me.value = null;
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/la-plateforme");
    const wrapper = mount(DiscoverView, { global: { plugins: [router] } });
    expect(wrapper.findAll(".discover-scene:not(.discover-end)")).toHaveLength(6);
    // Chaque scène : un bout de la plateforme, le personnage, sa bulle.
    expect(wrapper.findAll(".dmock")).toHaveLength(6);
    expect(wrapper.findAll(".discover-bubble")).toHaveLength(6);
    expect(wrapper.find("[data-test=discover-login]").attributes("href")).toBe("/connexion");
    expect(wrapper.text()).toContain("ne partent jamais à l'IA");
  });

  it("propose la démo quand son adresse est réglée, mais pas dans la démo elle-même (docs/72)", async () => {
    const me = { authenticated: false, username: null, setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done" as const, demo: false, demo_url: "https://demo.exemple.ch" };
    useAuth().me.value = me;
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/la-plateforme");
    const wrapper = mount(DiscoverView, { global: { plugins: [router] } });
    expect(wrapper.find("[data-test=discover-demo]").attributes("href")).toBe("https://demo.exemple.ch");
    useAuth().me.value = { ...me, authenticated: true, demo: true };
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[data-test=discover-demo]").exists()).toBe(false);
    useAuth().me.value = null;
  });

  it("en bas de la page, le chemin va jusqu'à la dernière pastille ; les notes en cercle (0.79.1)", async () => {
    useAuth().me.value = null;
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
    await router.push("/la-plateforme");
    const wrapper = mount(DiscoverView, { global: { plugins: [router] } });
    Object.defineProperty(document.documentElement, "scrollHeight", { configurable: true, value: 3000 });
    Object.defineProperty(window, "scrollY", { configurable: true, value: 3000 - window.innerHeight });
    window.dispatchEvent(new Event("scroll"));
    await wrapper.vm.$nextTick();
    const nodes = wrapper.findAll(".discover-node");
    expect(nodes.length).toBe(7);
    expect(nodes.every((n) => n.classes().includes("reached"))).toBe(true);
    // La maquette des offres montre la note comme l'application : un cercle, plus de pastille.
    expect(wrapper.find(".dmock-score").exists()).toBe(false);
    expect(wrapper.findAll(".dmock .score-ring").length).toBe(3);
    // Sur téléphone, le personnage passe sous la maquette là où il cachait du texte (0.79.2).
    const below = wrapper.findAll(".discover-stage").map((stage) => stage.classes().includes("below"));
    expect(below).toEqual([false, true, false, false, true, true]);
    wrapper.unmount();
  });
});

