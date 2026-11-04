import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import NotificationBell from "./NotificationBell.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(() => vi.resetAllMocks());

const item = (id: number, extra: Record<string, unknown> = {}) => ({
  id,
  kind: "orp_due",
  title: "Preuves de septembre à remettre avant le 5 octobre",
  message: "18 candidatures, 2 lignes à compléter.",
  link: "/orp?mois=2026-09",
  created_at: new Date(Date.now() - 2 * 3600_000).toISOString(),
  read_at: null,
  ...extra,
});

async function mountBell() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/");
  const wrapper = mount(NotificationBell, { global: { plugins: [router], stubs: { teleport: true } }, attachTo: document.body });
  await flushPromises();
  return { wrapper, router };
}

describe("NotificationBell", () => {
  it("pastille, panneau aux lignes de la page, ligne-lien qui marque lue et ouvre la page", async () => {
    GET.mockResolvedValue({ data: { unread: 2, items: [item(1), item(2, { read_at: "2026-10-05T08:00:00Z", title: "Ancienne" })] } });
    POST.mockResolvedValue({ data: { unread: 1, items: [] } });
    const { wrapper, router } = await mountBell();
    expect(wrapper.find("[data-test=bell-badge]").text()).toBe("2");
    // Avec des alertes (1.6.46) : une capsule orange clair, la cloche et le chiffre côte à côte ; la
    // légende reprend le nom accessible.
    const bell = wrapper.find("[data-test=bell]");
    expect(bell.classes()).toContain("has-unread");
    expect(bell.attributes("aria-label")).toBe("Notifications, 2 non lues");
    expect(bell.attributes("data-label")).toBe("Notifications, 2 non lues");

    await bell.trigger("click");
    await flushPromises();
    const rows = wrapper.findAll("[data-test=notification]");
    expect(rows).toHaveLength(2);
    expect(rows[0]!.classes()).toContain("unread");
    expect(rows[0]!.find("[data-test=unread-dot]").attributes("aria-label")).toBe("non lue");
    expect(rows[1]!.find("[data-test=unread-dot]").exists()).toBe(false);
    // N7 : la ligne entière est un seul lien, sans élément interactif à l'intérieur.
    expect(rows[0]!.element.tagName).toBe("A");
    expect(rows[0]!.find("a, button").exists()).toBe(false);
    expect(rows[0]!.text()).not.toContain("il y a");
    expect(wrapper.find("[data-test=bell-all]").attributes("href")).toBe("/notifications");

    await rows[0]!.trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/inbox/{notification_id}/read", { params: { path: { notification_id: 1 } } });
    expect(router.currentRoute.value.fullPath).toBe("/orp?mois=2026-09");
    expect(wrapper.find("[data-test=bell-panel]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("sans alerte : pas de pastille, message vide", async () => {
    GET.mockResolvedValue({ data: { unread: 0, items: [] } });
    const { wrapper } = await mountBell();
    expect(wrapper.find("[data-test=bell-badge]").exists()).toBe(false);
    // Sans alerte : un rond neutre.
    expect(wrapper.find("[data-test=bell]").classes()).not.toContain("has-unread");
    await wrapper.find("[data-test=bell]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=bell-panel]").text()).toContain("Aucune notification");
    wrapper.unmount();
  });
});

describe("NotificationBell sur téléphone (maquette Notifications, N1)", () => {
  it("mène à la page /notifications, sans panneau", async () => {
    const matchMedia = window.matchMedia;
    window.matchMedia = ((query: string) => ({ matches: query.includes("820px"), media: query, addEventListener: () => undefined, removeEventListener: () => undefined })) as unknown as typeof window.matchMedia;
    GET.mockResolvedValue({ data: { unread: 1, items: [item(1)] } });
    const { wrapper, router } = await mountBell();
    const bell = wrapper.find("[data-test=bell]");
    expect(bell.element.tagName).toBe("A");
    expect(bell.attributes("href")).toBe("/notifications");
    await bell.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe("/notifications");
    expect(wrapper.find("[data-test=bell-panel]").exists()).toBe(false);
    window.matchMedia = matchMedia;
    wrapper.unmount();
  });
});
