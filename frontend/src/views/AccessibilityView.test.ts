import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import AccessibilityView from "./AccessibilityView.vue";

describe("Accessibilité (docs/117 §1)", () => {
  it("ce qui est vérifié, ce qui ne l'est pas, la dictée, à qui signaler", async () => {
    GET.mockResolvedValue({ data: { contact: "Kevin, contact@joba1.ch", guest_mailbox: true } });
    const wrapper = mount(AccessibilityView);
    await flushPromises();
    const titles = wrapper.findAll("h2").map((h) => h.text());
    expect(titles).toEqual(["Ce qui est vérifié", "Pas encore vérifié", "Dicter", "Signaler un problème"]);
    expect(wrapper.text()).toContain("WCAG 2.1 AA");
    expect(wrapper.find("[data-test=accessibility-contact]").text()).toBe("Kevin, contact@joba1.ch");
  });
});
