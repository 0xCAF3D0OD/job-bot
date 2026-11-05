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

describe("NotificationRow (maquette Notifications, N8)", () => {
  it("un seul lien : l'icône du genre, le titre, la première ligne et le libellé de l'action", () => {
    const wrapper = mountRow();
    const link = wrapper.get("[data-test=notification]");
    expect(link.element.tagName).toBe("A");
    expect(link.attributes("href")).toBe("/candidatures/offres?tri=score");
    expect(wrapper.get("svg.notif-icon").attributes("data-shape")).toBe("offers");
    expect(wrapper.get(".notif-row-text").text()).toBe("La meilleure : Dev chez Infomaniak, proche.");
    expect(wrapper.get("[data-test=notification-action]").text()).toBe("Voir les offres");
    // Aucun élément interactif imbriqué (décision du 2026-11-04).
    expect(link.findAll("a, button")).toHaveLength(0);
  });

  it.each([
    ["follow_up", "orp", "Relancer"],
    ["orp_due", "orp", "Compléter"],
    ["interview", "orp", "Préparer"],
    ["training_funding", "orp", "Voir la formation"],
    ["budget", "warning", "Voir le budget"],
    ["collect_failed", "warning", "Voir"],
  ])("%s : forme %s, « %s »", (kind, shape, action) => {
    const wrapper = mountRow({ kind });
    expect(wrapper.get("svg.notif-icon").attributes("data-shape")).toBe(shape);
    expect(wrapper.get("[data-test=notification-action]").text()).toBe(action);
  });

  it("un genre sans action, ou sans page : le visage content, pas de libellé", () => {
    const calm = mountRow({ kind: "rhythm_week" });
    expect(calm.get("svg.notif-icon").attributes("data-shape")).toBe("calm");
    expect(calm.find("[data-test=notification-action]").exists()).toBe(false);
    const noLink = mountRow({ kind: "budget", link: null });
    expect(noLink.get("[data-test=notification]").element.tagName).toBe("BUTTON");
    expect(noLink.find("[data-test=notification-action]").exists()).toBe(false);
  });
});
