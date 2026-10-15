import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { routes } from "../router";
import NotFoundView from "./NotFoundView.vue";

describe("page introuvable (docs/59 §5)", () => {
  it("une adresse inconnue mène à une page qui le dit", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes });
    await router.push("/nulle-part");
    expect(router.currentRoute.value.name).toBe("not-found");
    const wrapper = mount(NotFoundView, { global: { plugins: [router] } });
    expect(wrapper.text()).toContain("Page introuvable");
    expect(wrapper.find("a").attributes("href")).toBe("/aujourdhui");
  });
});
