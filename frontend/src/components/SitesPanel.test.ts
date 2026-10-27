import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../composables/useAuth";
import { useUndo } from "../composables/useUndo";
import SitesPanel from "./SitesPanel.vue";

const GET = vi.fn();
const POST = vi.fn();
const PATCH = vi.fn();
vi.mock("../api/client", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PATCH: (...a: unknown[]) => PATCH(...a),
    DELETE: vi.fn(),
  },
}));
afterEach(() => vi.resetAllMocks());
// L'exploitant : ajouter ou retirer un site change la liste commune (docs/65).
beforeEach(() => {
  useAuth().me.value = { authenticated: true, username: "kevin", setup_needed: false, auth_enabled: true, is_owner: true, welcome: "done", demo: false };
});

const site = (id: number, slug: string, extra: Record<string, unknown> = {}) => ({
  id,
  slug,
  name: slug,
  senders: [`${slug}.ch`],
  url: null,
  reader: "ai",
  active: true,
  builtin: false,
  alerts: 0,
  last_alert_at: null,
  unrecognized: 0,
  ...extra,
});

describe("SitesPanel", () => {
  it("liste, met en pause, ajoute un site et relit les alertes non reconnues", async () => {
    GET.mockResolvedValue({
      data: [site(1, "jobup", { reader: "jobup", builtin: true, alerts: 16 }), site(2, "linkedin", { unrecognized: 3 })],
    });
    PATCH.mockResolvedValue({ data: [site(1, "jobup", { builtin: true }), site(2, "linkedin", { active: false, unrecognized: 3 })] });
    POST.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/api/sites/reread"
          ? { data: { examined: 3, updated: 3, new_offers: 7 } }
          : { data: [site(1, "jobup"), site(2, "linkedin"), site(3, "jobscout24")] },
      ),
    );
    const wrapper = mount(SitesPanel);
    await flushPromises();
    expect(wrapper.findAll("[data-test=site]")).toHaveLength(2);
    expect(wrapper.find("[data-test=remove-jobup]").exists()).toBe(false);
    // Le site décrit sur sa ligne : comment il est lu, ses alertes.
    expect(wrapper.find("[data-test=site] .setting-row-description").text()).toBe("Lu directement · 16 alertes");

    // Ne plus suivre un site : tout de suite à l'écran, « Annuler » pendant 6 s, puis le serveur (1.6.66, §4).
    await wrapper.find("[data-test=active-linkedin]").setValue(false);
    await flushPromises();
    expect(PATCH).not.toHaveBeenCalled();
    expect((wrapper.find("[data-test=active-linkedin]").element as HTMLInputElement).checked).toBe(false);
    const { pending, undo, flush } = useUndo();
    expect(pending.value?.message).toBe("linkedin n'est plus suivi.");
    await undo();
    await flushPromises();
    expect((wrapper.find("[data-test=active-linkedin]").element as HTMLInputElement).checked).toBe(true);
    expect(PATCH).not.toHaveBeenCalled();
    await wrapper.find("[data-test=active-linkedin]").setValue(false);
    await flush();
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/sites/{site_id}", {
      params: { path: { site_id: 2 } },
      body: { active: false },
      keepalive: false,
    });

    await wrapper.find("[data-test=reread]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("3 alertes relues, 7 nouvelles offres");

    await wrapper.find("[data-test=add-site]").trigger("click");
    await wrapper.find("[data-test=site-name]").setValue("JobScout24");
    await wrapper.find("[data-test=site-senders]").setValue("alerts@jobscout24.ch, jobscout24.ch");
    await wrapper.find("[data-test=add-site-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/sites", {
      body: { name: "JobScout24", senders: ["alerts@jobscout24.ch", "jobscout24.ch"], url: null },
    });
  });
});

describe("SitesPanel, compte invité (docs/65)", () => {
  it("met en pause pour soi, sans ajouter ni retirer de site", async () => {
    useAuth().me.value = { authenticated: true, username: "camille", setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
    GET.mockResolvedValue({ data: [] });
    const wrapper = mount(SitesPanel);
    await flushPromises();
    expect(wrapper.find("[data-test=add-site]").exists()).toBe(false);
    expect(wrapper.find("[data-test=site-suggestions]").exists()).toBe(false);
  });
});
