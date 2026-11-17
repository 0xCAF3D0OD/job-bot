import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { defineComponent, h } from "vue";

import { useJobA1Extension } from "../composables/useJobA1Extension";
import WelcomeAlertExtension from "./WelcomeAlertExtension.vue";

const PROPS = { searchLabel: "DevOps · Lausanne", url: "https://www.jobup.ch/fr/emplois/?term=DevOps" };
const current = (w: ReturnType<typeof mount>) => w.findAll("li.wa-step").findIndex((li) => li.attributes("aria-current") === "step") + 1;

describe("Crée ton alerte avec l’extension (section 42 du paquet du 16.11)", () => {
  it("extension absente : 3 étapes, la première mène à la boutique", () => {
    const wrapper = mount(WelcomeAlertExtension, { props: { ...PROPS, installed: false, progress: null } });
    expect(wrapper.findAll("li.wa-step")).toHaveLength(3);
    expect(current(wrapper)).toBe(1);
    const install = wrapper.get("[data-test=welcome-ext-install]");
    expect(install.text()).toContain("Installer l’extension");
    expect(install.attributes("target")).toBe("_blank");
    expect(wrapper.find("[data-test=welcome-ext-open]").exists()).toBe(false);
  });

  it("extension installée : 2 étapes ; ouvrir jobup lance le suivi en direct", async () => {
    const wrapper = mount(WelcomeAlertExtension, { props: { ...PROPS, installed: true, progress: null } });
    expect(wrapper.findAll("li.wa-step")).toHaveLength(2);
    expect(wrapper.find("[data-test=welcome-ext-track]").exists()).toBe(false);
    await wrapper.get("[data-test=welcome-ext-open]").trigger("click");
    expect(current(wrapper)).toBe(2);
    expect(wrapper.find("[data-test=welcome-ext-reopen]").exists()).toBe(true);
    const track = wrapper.get("[data-test=welcome-ext-track]");
    expect(track.attributes("role")).toBe("status");
    expect(track.findAll("li").map((li) => li.classes().find((c) => ["done", "now", "next"].includes(c)))).toEqual(["now", "next", "next", "next"]);
    await wrapper.setProps({ progress: "code-pasted" });
    const items = wrapper.get("[data-test=welcome-ext-track]").findAll("li");
    expect(items.map((li) => li.classes().find((c) => ["done", "now", "next"].includes(c)))).toEqual(["done", "done", "done", "now"]);
    expect(items[3]!.text()).toContain("En attente de ta confirmation sur jobup");
    await wrapper.setProps({ progress: "fallback" });
    expect(wrapper.get("[data-test=welcome-ext-track]").text()).toContain("Le code est dans la fenêtre de l’extension");
  });
});

describe("useJobA1Extension : la détection sans requête au serveur", () => {
  afterEach(() => delete document.documentElement.dataset.joba1Extension);
  const Probe = defineComponent({
    setup() {
      const { version, step } = useJobA1Extension();
      return () => h("p", `${version.value ?? "-"} ${step.value ?? "-"}`);
    },
  });
  const send = (data: unknown, source: MessageEventSource | null = window) =>
    window.dispatchEvent(new MessageEvent("message", { data, source, origin: window.location.origin }));

  it("l’attribut sur <html>, puis le message ready et les étapes ; les autres messages sont ignorés", async () => {
    const wrapper = mount(Probe);
    expect(wrapper.text()).toBe("- -");
    send({ source: "joba1-extension", type: "ready", version: "0.64.0" });
    await flushPromises();
    expect(wrapper.text()).toBe("0.64.0 -");
    send({ source: "autre", type: "alert-progress", site: "jobup", step: "sent" });
    send({ source: "joba1-extension", type: "alert-progress", site: "indeed", step: "sent" });
    send({ source: "joba1-extension", type: "alert-progress", site: "jobup", step: "code: 482913" });
    await flushPromises();
    expect(wrapper.text()).toBe("0.64.0 -");
    send({ source: "joba1-extension", type: "alert-progress", site: "jobup", step: "sent" });
    await flushPromises();
    expect(wrapper.text()).toBe("0.64.0 sent");
  });

  it("l’attribut posé avant le chargement de la page suffit", () => {
    document.documentElement.dataset.joba1Extension = "0.64.0";
    expect(mount(Probe).text()).toBe("0.64.0 -");
  });
});
