import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AiWritingLetter from "./AiWritingLetter.vue";

afterEach(() => vi.useRealTimers());

const steps = (w: ReturnType<typeof mount>) => w.findAll("li").map((li) => li.attributes("class"));

describe("AiWritingLetter (§53, planche ChargementLettre)", () => {
  it("logo, titre, barre et étapes ; les étapes suivent ce qui se passe vraiment, « CV adapté » coché seulement CV prêt", async () => {
    vi.useFakeTimers();
    const wrapper = mount(AiWritingLetter, { props: { cv: "busy", phase: "write" } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.find("[data-test=brand-logo]").attributes("width")).toBe("64");
    expect(wrapper.find(".loading-steps-title").text()).toBe("J’écris ta lettre,puis j’adapte ton CV");
    expect(wrapper.findAll("li").map((li) => li.text().replace(/D’après.*| : .*/, ""))).toEqual(["Annonce lue", "Lettre", "CV adapté", "Relecture"]);
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Écriture de la lettre");
    expect(wrapper.find("ol").attributes("role")).toBe("status");
    expect(steps(wrapper)).toEqual(["is-done", "is-current", "is-todo", "is-todo"]);
    expect(wrapper.find("li.is-current .loading-steps-detail").text()).toBe("D’après ton CV et l’annonce");
    // Le temps ne fait pas avancer les étapes : la lettre s'écrit encore.
    await vi.advanceTimersByTimeAsync(28000);
    expect(steps(wrapper)).toEqual(["is-done", "is-current", "is-todo", "is-todo"]);
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("90");
    // Relecture, CV pas encore prêt : le CV s'adapte encore.
    await wrapper.setProps({ phase: "review" });
    expect(steps(wrapper)).toEqual(["is-done", "is-done", "is-current", "is-current"]);
    // Le CV finit : la liste garde sa longueur (le choix est fixé au début).
    await wrapper.setProps({ cv: "", cvReady: true });
    expect(steps(wrapper)).toEqual(["is-done", "is-done", "is-done", "is-current"]);
    await wrapper.setProps({ done: true });
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("100");
    expect(wrapper.findAll("li.is-done")).toHaveLength(4);
  });

  it("CV pas prêt à la fin : « CV adapté » n'est jamais coché ; sans CV dans le passage, trois étapes", async () => {
    const wrapper = mount(AiWritingLetter, { props: { cv: "busy", phase: "write" } });
    await vi.dynamicImportSettled();
    await flushPromises();
    await wrapper.setProps({ cv: "failed", done: true });
    expect(steps(wrapper)).toEqual(["is-done", "is-done", "is-todo", "is-done"]);
    const alone = mount(AiWritingLetter, { props: { phase: "write" } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(alone.findAll("li")).toHaveLength(3);
    expect(alone.find(".loading-steps-sub").text()).toBe("environ 30 secondes");
  });
});
