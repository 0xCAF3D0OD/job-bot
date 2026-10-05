import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

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

    await wrapper.find("[data-test=active-linkedin]").setValue(false);
    await flushPromises();
    expect(PATCH).toHaveBeenCalledWith("/api/sites/{site_id}", { params: { path: { site_id: 2 } }, body: { active: false } });

    await wrapper.find("[data-test=reread]").trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("3 alerte(s) relue(s), 7 nouvelle(s) offre(s)");

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
