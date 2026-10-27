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
    expect(wrapper.text()).toContain("sans envoyer de candidature.");
  });

  it("se range en lignes de réglage : titre, phrase, et l'action à droite (planche « 5. Réglages »)", async () => {
    GET.mockResolvedValue({ data: [{ id: 3, name: "Firefox sur Mac", created_at: "2026-10-15T10:00:00Z", last_used_at: null }] });
    const wrapper = mount(ExtensionPanel);
    await flushPromises();
    const card = wrapper.find(".setting-card");
    expect(wrapper.find("fieldset").exists()).toBe(false);
    const rows = card.findAll("[data-test=setting-row]");
    expect(rows.map((r) => r.find(".setting-row-title").text())).toEqual([
      "Extension du navigateur",
      "Relier l'extension",
      "Firefox sur Mac",
      "Relier avec un jeton",
    ]);
    expect(rows[0]!.find(".setting-row-control [data-test=extension-install]").text()).toContain("Installer l'extension");
    expect(rows[1]!.find(".setting-row-description").text()).toContain(globalThis.location.origin);
    expect(rows[2]!.find(".setting-row-description").text()).toBe("Navigateur relié · pas encore utilisé.");
    expect(rows[2]!.find(".setting-row-control [data-test=extension-revoke]").exists()).toBe(true);
    expect(rows[3]!.find(".setting-row-control [data-test=extension-create]").text()).toBe("Créer un jeton");
    expect(card.findAll(".setting-row-description a")).toHaveLength(0);
  });
});
