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
    expect(wrapper.find("[data-test=agenda-url] code").text()).toBe("https://moi.tunnel.ms/api/agenda/feed/jba_x.ics");
    expect(wrapper.findAll("[data-test=agenda-revoke]")).toHaveLength(1);
  });
});
