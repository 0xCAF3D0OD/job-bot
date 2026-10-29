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
  it("pastille, liste, clic qui ouvre la page et marque lue", async () => {
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

    await wrapper.find("[data-test=bell]").trigger("click");
    await flushPromises();
    const items = wrapper.findAll("[data-test=bell-item]");
    expect(items).toHaveLength(2);
    expect(items[0]!.classes()).toContain("unread");
    // La règle des dates (§5) : jamais « il y a 2 h », « aujourd'hui » (ou « hier » juste après minuit).
    expect(items[0]!.text()).toMatch(/aujourd'hui|hier/);
    expect(items[0]!.text()).not.toContain("il y a");

    await items[0]!.trigger("click");
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

describe("NotificationBell sous 600 px (planche « Structure téléphone »)", () => {
  it("s'ouvre en feuille plein écran, titre « Notifications » et ✕ « Fermer »", async () => {
    const matchMedia = window.matchMedia;
    window.matchMedia = ((query: string) => ({ matches: query.includes("599px"), media: query, addEventListener: () => undefined, removeEventListener: () => undefined })) as unknown as typeof window.matchMedia;
    GET.mockResolvedValue({ data: { unread: 1, items: [item(1)] } });
    const { wrapper } = await mountBell();
    await wrapper.find("[data-test=bell]").trigger("click");
    await flushPromises();
    const sheet = wrapper.find("dialog.sheet");
    expect(sheet.classes()).toContain("sheet-full");
    expect(sheet.find(".sheet-title").text()).toBe("Notifications");
    expect(sheet.findAll("[data-test=bell-item]")).toHaveLength(1);
    await sheet.find("[data-test=sheet-close]").trigger("click");
    await flushPromises();
    expect(wrapper.find("[data-test=bell]").attributes("aria-expanded")).toBe("false");
    window.matchMedia = matchMedia;
    wrapper.unmount();
  });
});
