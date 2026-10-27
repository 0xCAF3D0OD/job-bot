import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import StatusView from "./StatusPanel.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

afterEach(() => GET.mockReset());

const healthy = {
  version: "0.1.0",
  env: "dev",
  database: { ok: true, revision: "0002", head: "0002", up_to_date: true, error: null },
  worker: { healthy: true, last_heartbeat_at: new Date().toISOString(), stale_after_seconds: 600 },
  collect: { configured: true, last_success_at: new Date().toISOString(), last_failure_at: null, last_error: null },
};

describe("StatusView", () => {
  it("affiche les voyants et les dernières tâches", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/status"
            ? healthy
            : [
                {
                  id: 1,
                  job: "heartbeat",
                  run_id: "00000000-0000-0000-0000-000000000001",
                  started_at: new Date().toISOString(),
                  finished_at: new Date().toISOString(),
                  status: "success",
                  items_in: 0,
                  items_out: 0,
                  error: null,
                },
              ],
      }),
    );
    const wrapper = mount(StatusView);
    await flushPromises();
    const lights = wrapper.findAll("[data-test=indicator]");
    expect(lights).toHaveLength(4);
    expect(lights.every((l) => l.classes().includes("ok"))).toBe(true);
    expect(wrapper.findAll("[data-test=run]")).toHaveLength(1);
    expect(wrapper.text()).toContain("Réussie");
    wrapper.unmount();
  });

  it("API injoignable : voyants rouges, pas d'appel aux tâches", async () => {
    GET.mockRejectedValue(new TypeError("Failed to fetch"));
    const wrapper = mount(StatusView);
    await flushPromises();
    expect(wrapper.findAll("[data-test=indicator]").every((l) => l.classes().includes("down"))).toBe(true);
    expect(GET.mock.calls.some((c) => c[0] === "/api/job-runs")).toBe(false);
    expect(wrapper.text()).toContain("Aucune exécution enregistrée.");
    wrapper.unmount();
  });

  it("une colonne de lignes : le voyant, son détail, l'état en mots à droite (1.6.67, WCAG 1.4.1)", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === "/api/status"
            ? { ...healthy, collect: { ...healthy.collect, last_error: "IMAP refusé" } }
            : [
                {
                  id: 2,
                  job: "collect",
                  run_id: "00000000-0000-0000-0000-000000000002",
                  started_at: new Date().toISOString(),
                  finished_at: new Date().toISOString(),
                  status: "failure",
                  items_in: 3,
                  items_out: null,
                  error: "IMAP refusé",
                },
              ],
      }),
    );
    const wrapper = mount(StatusView);
    await flushPromises();
    expect(wrapper.find("table").exists()).toBe(false);
    const collect = wrapper.findAll("[data-test=indicator]").find((row) => row.find(".setting-row-title").text() === "Collecte");
    expect(collect?.find(".setting-row-description").text()).toContain("IMAP refusé");
    expect(collect?.find(".setting-row-control").text()).toBe("En panne");
    const header = wrapper.find("[data-test=runs] [data-test=setting-row]");
    expect(header.find(".setting-row-title").text()).toBe("Dernières tâches");
    const run = wrapper.find("[data-test=run]");
    expect(run.find(".setting-row-title").text()).toBe("collect");
    expect(run.find(".setting-row-description").text()).toContain("entrées 3, sorties –");
    expect(run.find(".setting-row-control").text()).toBe("Échec");
    wrapper.unmount();
  });
});
