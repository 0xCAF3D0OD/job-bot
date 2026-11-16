import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import DocSearch from "./DocSearch.vue";

// jsdom ne mesure rien : chaque texte est « visible » et chaque résultat a une place.
beforeEach(() => {
  vi.spyOn(Element.prototype, "getClientRects").mockReturnValue([{}] as unknown as DOMRectList);
  Range.prototype.getBoundingClientRect = () => ({ top: 10, left: 10, width: 40, height: 15 }) as DOMRect;
  window.scrollBy = vi.fn();
  window.matchMedia = vi.fn().mockReturnValue({ matches: true }) as never;
});
afterEach(() => vi.restoreAllMocks());

function page(): HTMLElement {
  const el = document.createElement("article");
  el.innerHTML = "<p>Clusters <b>Kubernetes</b> en production.</p><p>Exploitation kubernetes et Héroku, expérience.</p>";
  document.body.append(el);
  return el;
}

describe("DocSearch", () => {
  it("compte les résultats sans tenir compte des majuscules ni des accents ; Entrée, Maj+Entrée, Échap", async () => {
    const wrapper = mount(DocSearch, { props: { target: page(), label: "Chercher dans le CV" }, attachTo: document.body });
    const input = wrapper.get("[data-test=doc-search-input]");
    expect(input.attributes("aria-label")).toBe("Chercher dans le CV");
    expect(document.activeElement).toBe(input.element);
    const count = wrapper.get("[data-test=doc-search-count]");
    expect(count.attributes("aria-live")).toBe("polite");
    await input.setValue("KUBERNETES");
    expect(count.text()).toBe("1 sur 2");
    await input.trigger("keydown", { key: "Enter" });
    expect(count.text()).toBe("2 sur 2");
    await input.trigger("keydown", { key: "Enter" });
    expect(count.text()).toBe("1 sur 2");
    await input.trigger("keydown", { key: "Enter", shiftKey: true });
    expect(count.text()).toBe("2 sur 2");
    await wrapper.get("[data-test=doc-search-prev]").trigger("click");
    expect(count.text()).toBe("1 sur 2");
    // Le contour du résultat courant est placé, et la page défile jusqu'à lui.
    expect(wrapper.get(".doc-hit-box").attributes("hidden")).toBeUndefined();
    await nextTick();
    expect(window.scrollBy).toHaveBeenCalledWith({ top: -120, behavior: "auto" });
    await input.setValue("experience");
    expect(count.text()).toBe("1 sur 1");
    await input.setValue("heroku");
    expect(count.text()).toBe("1 sur 1");
    await input.setValue("introuvable");
    expect(count.text()).toBe("0 sur 0");
    expect(wrapper.get("[data-test=doc-search-next]").attributes("disabled")).toBeDefined();
    await wrapper.get("[data-test=doc-search]").trigger("keydown", { key: "Escape" });
    await wrapper.get("[data-test=doc-search-close]").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(2);
    wrapper.unmount();
  });
});
