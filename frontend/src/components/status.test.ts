import { describe, expect, it } from "vitest";

import type { StatusResponse } from "../api/client";
import { indicators } from "./status";

const NOW = new Date("2026-10-02T12:00:00Z");

function status(overrides: Partial<StatusResponse> = {}): StatusResponse {
  return {
    version: "0.1.0",
    env: "dev",
    database: { ok: true, revision: "0002", head: "0002", up_to_date: true, error: null },
    worker: { healthy: true, last_heartbeat_at: "2026-10-02T11:58:00Z", stale_after_seconds: 600 },
    collect: { configured: true, last_success_at: "2026-10-02T11:00:00Z", last_failure_at: null, last_error: null },
    ...overrides,
  };
}

describe("indicators", () => {
  it("tout va bien", () => {
    const lights = indicators(status(), NOW);
    expect(lights.map((l) => l.level)).toEqual(["ok", "ok", "ok", "ok"]);
    expect(lights[2]?.detail).toBe("dernier heartbeat il y a 2 minutes");
    expect(lights[3]?.detail).toBe("dernière collecte il y a 1 heure");
  });

  it("base absente", () => {
    const lights = indicators(
      status({
        database: { ok: false, revision: null, head: "0002", up_to_date: false, error: "OperationalError" },
        worker: { healthy: false, last_heartbeat_at: null, stale_after_seconds: 600 },
      }),
      NOW,
    );
    expect(lights.map((l) => l.level).slice(0, 3)).toEqual(["ok", "down", "down"]);
    expect(lights[1]?.detail).toContain("OperationalError");
  });

  it("migration à appliquer", () => {
    const lights = indicators(
      status({ database: { ok: true, revision: "0001", head: "0002", up_to_date: false, error: null } }),
      NOW,
    );
    expect(lights[1]?.level).toBe("warn");
    expect(lights[1]?.detail).toContain("make migrate");
  });

  it("worker silencieux depuis plus de 10 minutes", () => {
    const lights = indicators(
      status({ worker: { healthy: false, last_heartbeat_at: "2026-10-02T11:45:00Z", stale_after_seconds: 600 } }),
      NOW,
    );
    expect(lights[2]?.level).toBe("down");
    expect(lights[2]?.detail).toBe("silencieux, dernier heartbeat il y a 15 minutes");
  });

  it("API injoignable", () => {
    expect(indicators(null, NOW).map((l) => l.level)).toEqual(["down", "down", "down", "down"]);
  });

  it("collecte non configurée", () => {
    const lights = indicators(
      status({ collect: { configured: false, last_success_at: null, last_failure_at: null, last_error: null } }),
      NOW,
    );
    expect(lights[3]?.level).toBe("warn");
    expect(lights[3]?.detail).toContain("JOBBOT_IMAP_USER");
  });

  it("collecte en échec", () => {
    const lights = indicators(
      status({
        collect: {
          configured: true,
          last_success_at: "2026-10-01T11:00:00Z",
          last_failure_at: "2026-10-02T11:00:00Z",
          last_error: "MailboxError: authentification IMAP refusée",
        },
      }),
      NOW,
    );
    expect(lights[3]?.level).toBe("down");
    expect(lights[3]?.detail).toContain("authentification IMAP refusée");
  });
});
