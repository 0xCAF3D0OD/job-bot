import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import NotificationRow from "./NotificationRow.vue";

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
const item = (extra: Record<string, unknown> = {}) => ({
  id: 1,
  kind: "offers",
  title: "5 nouvelles offres pour toi",
  message: "La meilleure : Dev chez Infomaniak, proche.\n72 · Dev — Infomaniak",
  link: "/candidatures/offres?tri=score",
  created_at: new Date().toISOString(),
  read_at: null,
  ...extra,
});
const mountRow = (extra: Record<string, unknown> = {}) => mount(NotificationRow, { props: { item: item(extra) }, global: { plugins: [router] } });

describe("NotificationRow (ordinateur, NotificationsOrdinateur)", () => {
  it("un seul lien : le point « non lue », le titre, la première ligne et le libellé de l'action", () => {
    const wrapper = mountRow();
    const link = wrapper.get("[data-test=notification]");
    expect(link.element.tagName).toBe("A");
    expect(link.attributes("href")).toBe("/candidatures/offres?tri=score");
    expect(wrapper.find("[data-test=unread-dot]").exists()).toBe(true);
    expect(wrapper.get(".notif-row-text").text()).toBe("La meilleure : Dev chez Infomaniak, proche.");
    expect(wrapper.get("[data-test=notification-action]").text()).toBe("Voir les offres");
    // Aucun élément interactif imbriqué (décision du 2026-11-04).
    expect(link.findAll("a, button")).toHaveLength(0);
  });

  it.each([
    ["follow_up", "Relancer"],
    ["orp_due", "Compléter"],
    ["interview", "Préparer"],
    ["training_funding", "Voir la formation"],
    ["budget", "Voir le budget"],
    ["collect_failed", "Voir"],
  ])("%s : « %s »", (kind, action) => {
    expect(mountRow({ kind }).get("[data-test=notification-action]").text()).toBe(action);
  });

  it("un genre sans action, ou sans page : pas de libellé", () => {
    expect(mountRow({ kind: "rhythm_week" }).find("[data-test=notification-action]").exists()).toBe(false);
    const noLink = mountRow({ kind: "budget", link: null });
    expect(noLink.get("[data-test=notification]").element.tagName).toBe("BUTTON");
    expect(noLink.find("[data-test=notification-action]").exists()).toBe(false);
  });
});
