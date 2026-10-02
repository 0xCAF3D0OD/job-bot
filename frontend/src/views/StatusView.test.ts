import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import StatusView from "./StatusView.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

afterEach(() => GET.mockReset());

const healthy = {
  version: "0.1.0",
  env: "dev",
  database: { ok: true, revision: "0002", head: "0002", up_to_date: true, error: null },
  worker: { healthy: true, last_heartbeat_at: new Date().toISOString(), stale_after_seconds: 600 },
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
    expect(lights.map((l) => l.classes())).toEqual([
      expect.arrayContaining(["ok"]),
      expect.arrayContaining(["ok"]),
      expect.arrayContaining(["ok"]),
    ]);
    expect(wrapper.findAll("[data-test=run]")).toHaveLength(1);
    expect(wrapper.text()).toContain("réussie");
    wrapper.unmount();
  });

  it("API injoignable : voyants rouges, pas d'appel aux tâches", async () => {
    GET.mockRejectedValue(new TypeError("Failed to fetch"));
    const wrapper = mount(StatusView);
    await flushPromises();
    expect(wrapper.findAll("[data-test=indicator]").every((l) => l.classes().includes("down"))).toBe(true);
    expect(GET).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("Aucune exécution enregistrée.");
    wrapper.unmount();
  });
});
