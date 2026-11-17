import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AiWriting from "./AiWriting.vue";

afterEach(() => vi.useRealTimers());

describe("AiWriting (docs/59 §4)", () => {
  it("une barre d’étapes qui avance, la dernière reste en cours", async () => {
    vi.useFakeTimers();
    const wrapper = mount(AiWriting, { props: { kind: "cv" } });
    const current = () => wrapper.find("[aria-current=step]").text();
    expect(current()).toBe("Lire l’offre");
    await vi.advanceTimersByTimeAsync(6000);
    expect(current()).toBe("Choisir ce qui compte");
    expect(wrapper.find("li.done").text()).toBe("Lire l’offre");
    expect(wrapper.find("li.done [data-icon=done]").exists()).toBe(true);
    await vi.advanceTimersByTimeAsync(60000);
    expect(current()).toBe("Relire");
    expect(wrapper.attributes("role")).toBe("status");
  });

  it("la lettre prend le style de ChargementLettre (§53) ; « CV adapté » seulement quand un CV se prépare aussi", async () => {
    vi.useFakeTimers();
    const wrapper = mount(AiWriting, { props: { kind: "letter", withCv: true } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.find(".loading-steps-title").text()).toBe("J’écris ta lettre,puis j’adapte ton CV");
    expect(wrapper.findAll("li").map((li) => li.text().replace(/ : .*/, ""))).toEqual(["Annonce lue", "Lettre", "CV adapté", "Relecture"]);
    expect(wrapper.find("[role=progressbar]").attributes("aria-label")).toBe("Écriture de la lettre");
    expect(wrapper.find("ol").attributes("role")).toBe("status");
    await vi.advanceTimersByTimeAsync(7000);
    expect(wrapper.find("li.is-current").text()).toContain("Lettre");
    // La barre ne finit jamais seule : la fin vient du serveur.
    await vi.advanceTimersByTimeAsync(21000);
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("90");
    expect(wrapper.find("li.is-current").text()).toContain("Relecture");
    // Au-delà de la durée habituelle + 50 % (28 s × 1,5) : une phrase à la place de la barre, jamais une barre figée.
    await vi.advanceTimersByTimeAsync(21000);
    expect(wrapper.find("[role=progressbar]").exists()).toBe(false);
    expect(wrapper.find(".loading-steps-slow").text()).toBe("Ça prend un peu plus de temps que d’habitude");
    expect(wrapper.find(".loading-steps-slow").attributes("role")).toBe("status");
    // La réponse arrive : tout est coché, la barre à 100 %.
    await wrapper.setProps({ done: true });
    expect(wrapper.find("[role=progressbar]").attributes("aria-valuenow")).toBe("100");
    expect(wrapper.findAll("li.is-done")).toHaveLength(4);
    const alone = mount(AiWriting, { props: { kind: "letter" } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(alone.findAll("li")).toHaveLength(3);
    expect(alone.find(".loading-steps-sub").text()).toBe("environ 30 secondes");
  });
});
