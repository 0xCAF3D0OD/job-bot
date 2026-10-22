import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import ProfileGauge from "./ProfileGauge.vue";

const GET = vi.fn();
vi.mock("../api/client", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
afterEach(() => vi.resetAllMocks());

function answer(chunks: { kind: string; active: boolean }[], saved: boolean, identity: Record<string, string | null>) {
  GET.mockImplementation((path: string) =>
    Promise.resolve({
      data:
        path === "/api/profile-chunks"
          ? chunks
          : path === "/api/criteria"
            ? { criteria: {}, keywords: {}, saved_at: saved ? "2026-10-01T00:00:00Z" : null }
            : identity,
    }),
  );
}

async function mountGauge() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/profil");
  const wrapper = mount(ProfileGauge, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("la jauge du profil (docs/121 §C.4)", () => {
  it("le compte, les segments et ce qui manque en premier", async () => {
    answer(
      [
        { kind: "experience", active: true },
        { kind: "competence", active: true },
        { kind: "competence", active: false },
      ],
      true,
      { name: "Léa", city: "Sion" },
    );
    const wrapper = await mountGauge();
    expect(wrapper.find("[data-test=profile-gauge]").text()).toContain("Profil · 3 sur 5");
    expect(wrapper.findAll(".segment.done")).toHaveLength(3);
    // Une seule compétence active : il en faut deux.
    const next = wrapper.find("[data-test=profile-gauge-next]");
    expect(next.text()).toBe("Ajouter des compétences");
    expect(next.attributes("href")).toBe("/profil?onglet=parcours");
  });

  it("tout est là : la jauge part", async () => {
    answer(
      [
        { kind: "experience", active: true },
        { kind: "competence", active: true },
        { kind: "competence", active: true },
        { kind: "formation", active: true },
      ],
      true,
      { name: "Léa", city: "Sion" },
    );
    const wrapper = await mountGauge();
    expect(wrapper.find("[data-test=profile-gauge]").exists()).toBe(false);
  });
});
