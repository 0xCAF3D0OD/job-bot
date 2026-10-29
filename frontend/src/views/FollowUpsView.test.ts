// Les relances une à une (planche « Tri et panneau de commande », B2).
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import FollowUpsView from "./FollowUpsView.vue";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a), POST: vi.fn() },
}));
afterEach(() => vi.resetAllMocks());

const app = (id: number, company: string, sent_at: string, status = "en_attente") => ({
  id,
  company,
  job_title: "DevOps Engineer",
  location: "Vevey",
  sent_at,
  method: "electronique",
  status,
  offer_id: null,
  interviews: [],
  contacts: [],
});

async function mountView(list: unknown[]) {
  GET.mockResolvedValue({ data: list });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/candidatures/relances");
  const wrapper = mount(FollowUpsView, { global: { plugins: [router], stubs: { FollowUpPanel: true } } });
  await flushPromises();
  return wrapper;
}

describe("Les relances une à une", () => {
  it("une candidature à la fois, les plus anciennes d'abord ; « Passer » n'enregistre rien", async () => {
    const wrapper = await mountView([
      app(1, "Récente SA", "2026-10-25"),
      app(2, "Maquette Médias Sàrl", "2026-09-08"),
      app(3, "Beta SA", "2026-09-20"),
    ]);
    expect(wrapper.find("[data-test=step-progress]").text()).toBe("1 sur 2");
    const card = wrapper.find("[data-test=follow-up-card]");
    expect(card.text()).toContain("Maquette Médias Sàrl · Vevey");
    expect(card.text()).toContain("Envoyée le 8 septembre, par courriel.");
    expect(card.text()).toContain("Dernier échange : aucune réponse.");
    expect(card.find("[data-test=state-pill]").text()).toMatch(/^Sans réponse depuis \d+ jours$/);
    await wrapper.find("[data-test=follow-up-later]").trigger("click");
    expect(wrapper.find("[data-test=follow-up-later]").text()).toBe("Passer");
    expect(wrapper.find("[data-test=follow-up-card]").text()).toContain("Beta SA");
    expect(PUT).not.toHaveBeenCalled();
  });

  it("« Classer sans réponse » part après 6 s, « Annuler » la remet ; puis l'écran de fin", async () => {
    PUT.mockResolvedValue({ response: { ok: true } });
    const wrapper = await mountView([app(2, "Maquette Médias Sàrl", "2026-09-08")]);
    await wrapper.find("[data-test=follow-up-archive]").trigger("click");
    expect(wrapper.find("[data-test=follow-ups-done]").exists()).toBe(true);
    await useUndo().undo();
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-card]").exists()).toBe(true);
    await wrapper.find("[data-test=follow-up-archive]").trigger("click");
    await useUndo().flush();
    await flushPromises();
    expect(PUT).toHaveBeenCalledWith(
      "/api/applications/{application_id}",
      expect.objectContaining({ params: { path: { application_id: 2 } }, body: expect.objectContaining({ status: "sans_reponse" }) }),
    );
    const done = wrapper.find("[data-test=follow-ups-done]");
    expect(done.text()).toContain("Relances du jour terminées");
    expect(done.text()).toContain("1 classée sans réponse.");
  });

  it("« Relancer » ouvre la feuille ; une fois relancée, la suivante", async () => {
    const wrapper = await mountView([app(2, "Maquette Médias Sàrl", "2026-09-08"), app(3, "Beta SA", "2026-09-20")]);
    await wrapper.find("[data-test=follow-up-open]").trigger("click");
    const panel = wrapper.findComponent({ name: "FollowUpPanel" });
    expect(panel.exists()).toBe(true);
    // Les deux actions dans la rangée de la feuille : « Rédiger » en contour, « Marquer comme relancée » en principal.
    expect(wrapper.find("[data-test=follow-up-write]").text()).toContain("Rédiger");
    expect(wrapper.find("[data-test=follow-up-done]").classes()).toContain("primary");
    panel.vm.$emit("done");
    await flushPromises();
    expect(wrapper.find("[data-test=follow-up-card]").text()).toContain("Beta SA");
  });

  it("rien à relancer : un écran vide", async () => {
    const wrapper = await mountView([app(1, "Récente SA", "2026-10-25")]);
    expect(wrapper.find("[data-test=follow-ups-empty]").text()).toContain("Rien à relancer");
  });
});
