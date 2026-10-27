import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import AgendaPanel from "./AgendaPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));
afterEach(() => vi.resetAllMocks());

describe("Abonnement d'agenda (docs/40 §2)", () => {
  it("crée l'adresse avec l'origine du navigateur, la montre une fois, puis la liste", async () => {
    GET.mockResolvedValueOnce({ data: [] });
    POST.mockResolvedValue({ data: { id: 1, name: "Mon agenda", created_at: "2026-10-15T10:00:00Z", last_used_at: null, url: "https://moi.tunnel.ms/api/agenda/feed/jba_x.ics" } });
    GET.mockResolvedValueOnce({ data: [{ id: 1, name: "Mon agenda", created_at: "2026-10-15T10:00:00Z", last_used_at: null }] });
    const wrapper = mount(AgendaPanel);
    await flushPromises();
    await wrapper.find("[data-test=agenda-create]").trigger("click");
    await flushPromises();
    expect(POST.mock.calls[0]![1].body.origin).toBe(globalThis.location.origin);
    expect(POST.mock.calls[0]![1].body.name).toMatch(/^Agenda du /);
    expect(wrapper.find("[data-test=agenda-url] code").text()).toBe("https://moi.tunnel.ms/api/agenda/feed/jba_x.ics");
    expect(wrapper.findAll("[data-test=agenda-revoke]")).toHaveLength(1);
  });

  it("désactive le bouton pendant la création et dit l'échec", async () => {
    GET.mockResolvedValueOnce({ data: [] });
    let answer: (value: unknown) => void = () => {};
    POST.mockReturnValue(new Promise((resolve) => (answer = resolve)));
    const wrapper = mount(AgendaPanel);
    await flushPromises();
    const button = wrapper.find("[data-test=agenda-create]");
    await button.trigger("click");
    expect(button.attributes("disabled")).toBeDefined();
    await button.trigger("click");
    expect(POST).toHaveBeenCalledTimes(1);
    answer({ error: { detail: "refusé" } });
    await flushPromises();
    expect(button.attributes("disabled")).toBeUndefined();
    expect(wrapper.find("[data-test=agenda-error]").text()).toBe("Création impossible : réessaie dans un instant.");
  });

  it("se range en lignes de réglage : titre, phrase, et l'action à droite (planche « 5. Réglages »)", async () => {
    GET.mockResolvedValueOnce({ data: [{ id: 1, name: "Agenda du 15 oct.", created_at: "2026-10-15T10:00:00Z", last_used_at: null }] });
    const wrapper = mount(AgendaPanel);
    await flushPromises();
    const card = wrapper.find(".setting-card");
    expect(card.attributes("data-test")).toBe("agenda-panel");
    expect(wrapper.find("fieldset").exists()).toBe(false);
    const rows = card.findAll("[data-test=setting-row]");
    expect(rows.map((r) => r.find(".setting-row-title").text())).toEqual(["Abonnement d'agenda", "Agenda du 15 oct."]);
    expect(rows[0]!.find(".setting-row-control [data-test=agenda-create]").text()).toBe("Créer l'abonnement");
    expect(rows[1]!.find(".setting-row-description").text()).toBe("Pas encore relue par ton agenda.");
    expect(rows[1]!.find(".setting-row-control [data-test=agenda-revoke]").attributes("aria-label")).toBe("Révoquer Agenda du 15 oct.");
    // Aucune description n'est un lien.
    expect(card.findAll(".setting-row-description a")).toHaveLength(0);
  });
});
