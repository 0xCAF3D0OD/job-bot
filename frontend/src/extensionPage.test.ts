// Le script de la page jobA1 (extension/page-joba1.js, section 42) : l'attribut sur <html>, même
// quand <html> n'existe pas encore à document_start, et le message « ready ».
import { beforeEach, describe, expect, it, vi } from "vitest";

const posted: unknown[] = [];

beforeEach(() => {
  posted.length = 0;
  Object.assign(globalThis, {
    chrome: {
      runtime: { getManifest: () => ({ version: "0.64.0" }), onMessage: { addListener: vi.fn() }, sendMessage: vi.fn() },
    },
  });
  vi.spyOn(window, "postMessage").mockImplementation((data: unknown) => void posted.push(data));
  vi.resetModules();
});

describe("le script de la page jobA1", () => {
  it("pose data-joba1-extension et envoie « ready »", async () => {
    // @ts-expect-error script de l'extension, sans types
    await import("../../extension/page-joba1.js");
    expect(document.documentElement.dataset.joba1Extension).toBe("0.64.0");
    expect(posted).toContainEqual({ source: "joba1-extension", type: "ready", version: "0.64.0" });
  });

  it("attend <html> s’il n’existe pas encore", async () => {
    const html = document.documentElement;
    delete html.dataset.joba1Extension;
    html.remove();
    expect(document.documentElement).toBeNull();
    // @ts-expect-error script de l'extension, sans types
    await import("../../extension/page-joba1.js");
    expect(posted).toEqual([]);
    document.appendChild(html);
    await new Promise((r) => setTimeout(r, 0));
    expect(document.documentElement.dataset.joba1Extension).toBe("0.64.0");
    expect(posted).toContainEqual({ source: "joba1-extension", type: "ready", version: "0.64.0" });
  });
});
