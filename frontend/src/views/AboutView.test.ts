// À propos et le pied de page (docs/126 §4).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import AppFooter from "../components/AppFooter.vue";
import { PUBLIC_ROUTES, pageTitle } from "../router";
import AboutView from "./AboutView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

const router = () => createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });

describe("À propos et le pied de page", () => {
  it("pourquoi, ce que jobA1 promet, qui est derrière, le code ; publique", async () => {
    GET.mockResolvedValue({ data: { contact: "contact@joba1.ch", guest_mailbox: true, billing: false } });
    const wrapper = mount(AboutView, { global: { plugins: [router()] } });
    await flushPromises();
    const text = wrapper.find("[data-test=about]").text();
    expect(text).toContain("jobA1 s'occupe des preuves et t'aide pour les offres.");
    expect(text).not.toContain("Less searching");
    expect(text).toContain("Tes coordonnées ne partent jamais à l'IA.");
    expect(text).toContain("Kevin Di Nocera");
    expect(wrapper.find("[data-test=about-contact]").text()).toBe("contact@joba1.ch");
    expect(wrapper.find("a[href='https://github.com/0xCAF3D0OD/job-bot']").exists()).toBe(true);
    expect(PUBLIC_ROUTES.has("about")).toBe(true);
    expect(pageTitle("about")).toBe("À propos · jobA1");
  });

  it("le pied de page mène aux quatre pages", () => {
    const footer = mount(AppFooter, { global: { plugins: [router()] } });
    expect(footer.findAll("a").map((a) => a.attributes("href"))).toEqual(["/tes-donnees", "/conditions", "/accessibilite", "/a-propos"]);
  });
});
