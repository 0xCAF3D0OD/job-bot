import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import NotificationCard from "./NotificationCard.vue";

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }] });
const item = (extra: Record<string, unknown> = {}) => ({
  id: 1,
  kind: "offers",
  title: "5 nouvelles offres pour toi",
  message: "La meilleure : Infomaniak, très proche.\n72 · Dev — Infomaniak",
  link: "/candidatures/offres?tri=score",
  created_at: new Date().toISOString(),
  read_at: null,
  ...extra,
});
const mountCard = (extra: Record<string, unknown> = {}) => mount(NotificationCard, { props: { item: item(extra) }, global: { plugins: [router] } });

describe("NotificationCard (MODIFICATIONS du 8 novembre au soir, §10.9)", () => {
  it("une carte cliquable : icône, titre, première ligne, « Non lue » · heure, cercle à flèche", () => {
    const wrapper = mountCard();
    const card = wrapper.get("[data-test=notification]");
    expect(card.element.tagName).toBe("A");
    expect(card.classes()).toContain("block-row");
    expect(card.classes()).toContain("unread");
    expect(card.findAll("a, button")).toHaveLength(0);
    expect(wrapper.get(".notif-card-icon").attributes("data-icon")).toBe("briefcase");
    expect(wrapper.get(".notif-card-text").text()).toBe(", La meilleure : Infomaniak, très proche.");
    // La couleur n'est jamais le seul repère : le mot « Non lue » suit le point, décoratif.
    expect(wrapper.get("[data-test=unread-dot]").attributes("aria-hidden")).toBe("true");
    expect(wrapper.get(".notif-card-info").text()).toMatch(/^, Non lue·, \d\d:\d\d$/);
    expect(wrapper.find(".arrow-circle").attributes("aria-hidden")).toBe("true");
  });

  it("lue : ni point ni « Non lue » ; sans description, la carte n'a que le titre et l'heure", () => {
    const wrapper = mountCard({ read_at: new Date().toISOString(), message: null });
    expect(wrapper.get("[data-test=notification]").classes()).not.toContain("unread");
    expect(wrapper.find("[data-test=unread-dot]").exists()).toBe(false);
    expect(wrapper.find(".notif-card-unread").exists()).toBe(false);
    expect(wrapper.find(".notif-card-text").exists()).toBe(false);
  });

  it.each([
    ["follow_up", "send", false],
    ["orp_due", "alert-circle", true],
    ["budget", "alert-circle", true],
    ["rhythm_week", "trend", false],
    ["orp_meeting", "calendar", false],
    ["site_code", "file", false],
  ])("%s : icône %s", (kind, icon, late) => {
    const icon_ = mountCard({ kind }).get(".notif-card-icon");
    expect(icon_.attributes("data-icon")).toBe(icon);
    expect(icon_.classes().includes("late")).toBe(late);
  });

  it("sans page : un bouton qui la marque lue", async () => {
    const wrapper = mountCard({ link: null });
    const card = wrapper.get("[data-test=notification]");
    expect(card.element.tagName).toBe("BUTTON");
    await card.trigger("click");
    expect(wrapper.emitted("open")).toHaveLength(1);
  });
});
