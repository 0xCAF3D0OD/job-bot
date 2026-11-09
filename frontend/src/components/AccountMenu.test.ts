import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountMenu from "./AccountMenu.vue";
import NotificationBell from "./NotificationBell.vue";

const logout = vi.fn();
const me = ref<Record<string, unknown>>({ username: "kevin", auth_enabled: true, demo: false, is_owner: true });
vi.mock("../composables/useAuth", () => ({ useAuth: () => ({ me, logout }) }));
vi.mock("../composables/useProfiles", () => ({ useProfiles: () => ({ load: vi.fn() }) }));
const GET = vi.fn(async (path: string) => {
  if (path === "/api/identity") return { data: { name: "Kevin Di Nocera", email: "kevin@example.ch" } };
  if (path === "/api/profile-image") return { data: { avatar: null } };
  if (path === "/api/documents") return { data: [{ kind: "cv", uploaded_at: "2026-11-02T08:00:00Z" }] };
  if (path === "/api/alert-searches") return { data: { searches: [{ active: true }, { active: true }, { active: false }] } };
  if (path === "/api/inbox") return { data: { unread: 0, items: [] } };
  return { data: undefined };
});
vi.mock("../api/client", () => ({ api: { GET: (path: string) => GET(path), PUT: vi.fn(), POST: vi.fn() } }));

const mounted: { unmount: () => void }[] = [];

async function mountAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/:any(.*)*", component: { template: "<div />" } }],
  });
  await router.push(path);
  const wrapper = mount(AccountMenu, { attachTo: document.body, global: { plugins: [router] } });
  mounted.push(wrapper);
  await flushPromises();
  return { router, wrapper };
}

// Le panneau est téléporté dans <body> : on le lit dans le document.
const q = (selector: string) => document.body.querySelector<HTMLElement>(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll<HTMLElement>(selector));

afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  document.body.innerHTML = "";
  me.value = { username: "kevin", auth_enabled: true, demo: false, is_owner: true };
});

describe("Panneau du compte (maquette du 8 novembre, docs/143, D24)", () => {
  it("l'image nommée « Compte de Kevin » ouvre le panneau : en-tête, Mon compte, Affichage, Aide, Se déconnecter", async () => {
    const { wrapper } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    expect(trigger.attributes("aria-label")).toBe("Compte de Kevin");
    expect(trigger.attributes("data-label")).toBe("Compte de Kevin");
    expect(trigger.find(".profile-image").exists()).toBe(true);
    await trigger.trigger("click");
    await flushPromises();
    const panel = q("[data-test=side-panel]")!;
    expect(panel.getAttribute("role")).toBe("complementary");
    expect(panel.getAttribute("aria-labelledby")).toBe(q("[data-test=account-name]")?.id);
    expect(q("[data-test=account-name]")?.textContent?.trim()).toBe("Kevin Di Nocera");
    expect(panel.textContent).toContain("kevin@example.ch");
    expect(qa(".panel-eyebrow").map((h) => h.textContent?.trim())).toEqual(["Mon compte", "Affichage", "Aide"]);
    expect(q("[data-test=account-profile]")?.textContent).toContain("CV mis à jour le 2 nov.");
    expect(q("[data-test=account-alerts]")?.textContent).toContain("2 recherches suivies");
    expect(q("[data-test=account-settings]")?.getAttribute("href")).toBe("/reglages");
    expect(q("[data-test=side-close]")?.getAttribute("aria-label")).toBe("Fermer le compte");
    // Le titre prend le focus à l'ouverture.
    expect(document.activeElement).toBe(q("[data-test=account-name]"));
    expect(q("[data-test=logout]")?.textContent?.trim()).toBe("Se déconnecter");
  });

  // Incident du 2026-11-09 : le clic menait vers une page qui n'existe pas, la page restait affichée.
  it("« Se déconnecter » ferme le panneau et déconnecte (la page est rechargée par useAuth)", async () => {
    logout.mockClear();
    const { wrapper } = await mountAt("/bilan/orp");
    await wrapper.find("[data-test=account-menu]").trigger("click");
    await flushPromises();
    q("[data-test=logout]")!.click();
    await flushPromises();
    expect(logout).toHaveBeenCalledOnce();
    expect(q("[data-test=side-panel]")).toBeNull();
  });

  it("Échap ferme et rend le focus à l'image ; un autre panneau ferme celui-ci", async () => {
    const { wrapper, router } = await mountAt("/aujourdhui");
    const trigger = wrapper.find("[data-test=account-menu]");
    await trigger.trigger("click");
    await flushPromises();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(q("[data-test=side-panel]")).toBeNull();
    expect(document.activeElement).toBe(trigger.element);

    const bell = mount(NotificationBell, { attachTo: document.body, global: { plugins: [router] } });
    await flushPromises();
    await trigger.trigger("click");
    await flushPromises();
    await bell.find("[data-test=bell]").trigger("click");
    await flushPromises();
    expect(q("[data-test=account-panel]")).toBeNull();
    expect(q("[data-test=bell-panel]")).not.toBeNull();
    bell.unmount();
  });

  it("démo, sans connexion : pas de « Se déconnecter »", async () => {
    me.value = { username: "demo", auth_enabled: false, demo: true };
    const { wrapper } = await mountAt("/aujourdhui");
    await wrapper.find("[data-test=account-menu]").trigger("click");
    await flushPromises();
    expect(q("[data-test=account-panel]")).not.toBeNull();
    expect(q("[data-test=logout]")).toBeNull();
  });
});
