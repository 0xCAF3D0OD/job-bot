import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useUndo } from "../composables/useUndo";
import NotificationsView from "./NotificationsView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3600_000).toISOString();
const item = (id: number, extra: Record<string, unknown> = {}) => ({
  id,
  kind: "orp_due",
  title: `Notification ${id}`,
  message: "Une phrase.\nUne deuxième ligne.",
  link: "/bilan/orp",
  created_at: new Date().toISOString(),
  read_at: null,
  ...extra,
});

async function mountPage() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
  await router.push("/notifications");
  const wrapper = mount(NotificationsView, { global: { plugins: [router] }, attachTo: document.body });
  await flushPromises();
  return { wrapper, router };
}

beforeEach(() => vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] }));
afterEach(async () => {
  await useUndo().flush();
  vi.useRealTimers();
  vi.resetAllMocks();
});

describe("NotificationsView (maquette Notifications, étape 9a)", () => {
  it("retour, titre, filtre, groupes par jour, lignes lues et non lues, réglages", async () => {
    GET.mockResolvedValue({
      data: {
        unread: 2,
        items: [
          item(1),
          item(2, { created_at: hoursAgo(30) }),
          item(3, { created_at: hoursAgo(24 * 3), read_at: hoursAgo(1) }),
          item(4, { created_at: hoursAgo(24 * 20), read_at: hoursAgo(1), link: null }),
        ],
      },
    });
    const { wrapper } = await mountPage();
    expect(wrapper.find("h1").text()).toBe("Notifications");
    expect(wrapper.find("[data-test=notifications-back]").attributes("aria-label")).toBe("Retour à l’accueil");
    expect(wrapper.find("[data-test=filter-unread]").text()).toBe("Non lues (2)");
    // Les groupes ne dépendent que de l'écart en jours ; près de minuit, « Aujourd'hui » peut manquer.
    // Téléphone (§10.9) : « Aujourd'hui », « Hier », « Plus tôt », plus de « Cette semaine » ; une section nommée par
    // famille, les cartes sans conteneur.
    const titles = wrapper.findAll(".notifications-group h2").map((h) => h.text());
    expect(titles).toContain("Plus tôt");
    expect(titles).not.toContain("Cette semaine");
    expect(titles.at(-1)).toBe("Plus tôt");
    const section = wrapper.get(".notifications-group");
    expect(section.attributes("aria-labelledby")).toBe(section.get("h2").attributes("id"));
    expect(wrapper.find(".notifications-card").exists()).toBe(false);
    const rows = wrapper.findAll("[data-test=notification]");
    expect(rows).toHaveLength(4);
    expect(rows.filter((r) => r.classes().includes("unread"))).toHaveLength(2);
    // Une phrase par ligne : la première du message.
    expect(rows[0]!.text()).toContain("Une phrase.");
    expect(rows[0]!.text()).not.toContain("deuxième");
    // Sans page : un bouton qui marque lue.
    expect(rows[3]!.element.tagName).toBe("BUTTON");
    expect(wrapper.find("[data-test=notifications-settings]").attributes("href")).toBe("/reglages?rubrique=notifications");

    await wrapper.find("[data-test=filter-unread]").trigger("click");
    expect(wrapper.findAll("[data-test=notification]")).toHaveLength(2);
    wrapper.unmount();
  });

  it("toucher une ligne la marque lue tout de suite et ouvre sa page", async () => {
    GET.mockResolvedValue({ data: { unread: 1, items: [item(1)] } });
    POST.mockResolvedValue({ data: { unread: 0, items: [item(1, { read_at: hoursAgo(0) })] } });
    const { wrapper, router } = await mountPage();
    await wrapper.find("[data-test=notification]").trigger("click");
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/inbox/{notification_id}/read", { params: { path: { notification_id: 1 } } });
    expect(router.currentRoute.value.path).toBe("/bilan/orp");
    wrapper.unmount();
  });

  it("« Tout lire » : lu tout de suite, envoyé après 6 s, « Annuler » remet les non lues", async () => {
    GET.mockResolvedValue({ data: { unread: 2, items: [item(1), item(2)] } });
    POST.mockResolvedValue({ data: { unread: 0, items: [item(1, { read_at: hoursAgo(0) }), item(2, { read_at: hoursAgo(0) })] } });
    const { wrapper } = await mountPage();
    const { pending, undo } = useUndo();

    await wrapper.find("[data-test=read-all]").trigger("click");
    expect(wrapper.findAll(".notif-card.unread")).toHaveLength(0);
    expect(wrapper.find("[data-test=read-all]").attributes("disabled")).toBeDefined();
    expect(pending.value?.message).toBe("2 notifications marquées comme lues");
    expect(POST).not.toHaveBeenCalled();
    await undo();
    await flushPromises();
    expect(wrapper.findAll(".notif-card.unread")).toHaveLength(2);

    await wrapper.find("[data-test=read-all]").trigger("click");
    vi.advanceTimersByTime(6000);
    await flushPromises();
    expect(POST).toHaveBeenCalledWith("/api/inbox/read-all", { keepalive: false });
    expect(wrapper.findAll(".notif-card.unread")).toHaveLength(0);
    wrapper.unmount();
  });

  it("tout est lu : le Sourire et son ombre, « Tout est lu » et « Voir toutes les notifications »", async () => {
    GET.mockResolvedValue({ data: { unread: 0, items: [item(1, { read_at: hoursAgo(1) })] } });
    const { wrapper } = await mountPage();
    await wrapper.find("[data-test=filter-unread]").trigger("click");
    const empty = wrapper.find("[data-test=notifications-empty]");
    expect(empty.text()).toContain("Tout est lu");
    // Corrections du 13.11, §7 : le Sourire, 140 px de haut. Un seul des trois : ni cloche ni logo transformé.
    const perso = empty.get("[data-test=notifications-perso] img");
    expect(perso.attributes("src")).toMatch(/sourire-pouce-140\.webp/);
    expect(perso.attributes("height")).toBe("140");
    expect(empty.find(".notifications-perso-shadow").exists()).toBe(true);
    expect(empty.find(".mood, .face-transform, svg").exists()).toBe(false);
    await empty.find("[data-test=show-all]").trigger("click");
    expect(wrapper.findAll("[data-test=notification]")).toHaveLength(1);
    wrapper.unmount();
  });

  it("aucune notification : le visage, sans bouton", async () => {
    GET.mockResolvedValue({ data: { unread: 0, items: [] } });
    const { wrapper } = await mountPage();
    const empty = wrapper.find("[data-test=notifications-empty]");
    expect(empty.text()).toContain("Aucune notification pour l’instant");
    expect(empty.find("[data-test=show-all]").exists()).toBe(false);
    expect(wrapper.find("[data-test=read-all]").attributes("disabled")).toBeDefined();
    wrapper.unmount();
  });
});
