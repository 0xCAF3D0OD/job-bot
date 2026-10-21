import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ExtensionPanel from "./ExtensionPanel.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a), POST: vi.fn(), DELETE: vi.fn() } }));
afterEach(() => vi.resetAllMocks());

describe("Extension (docs/71)", () => {
  it("s'installe depuis la boutique de Mozilla, et dit ce qu'elle fait", async () => {
    GET.mockResolvedValue({ data: [] });
    const wrapper = mount(ExtensionPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=extension-install]").attributes("href")).toBe(
      "https://addons.mozilla.org/addon/joba1-remplir-mes-candidatures/",
    );
    expect(wrapper.text()).toContain("Aucune candidature n'est envoyée à ta place.");
  });
});
