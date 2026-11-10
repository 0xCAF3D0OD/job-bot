import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import LoginView from "./LoginView.vue";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("../api/client", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
afterEach(async () => {
  vi.resetAllMocks();
  useAuth().me.value = null;
});

const anonymous = { authenticated: false, username: null, setup_needed: false, auth_enabled: true };

async function mountLogin(path = "/connexion?suite=/candidatures") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/connexion", name: "login", component: LoginView },
      { path: "/:any(.*)*", component: { template: "<div />" } },
    ],
  });
  await router.push(path);
  const wrapper = mount(LoginView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("LoginView", () => {
  it("sans compte : explique la commande à lancer", async () => {
    GET.mockResolvedValue({ data: { ...anonymous, setup_needed: true } });
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=setup-needed]").text()).toContain("jobbot set-password");
    expect(wrapper.find("[data-test=login-form]").exists()).toBe(false);
  });

  it("au revoir, après la suppression du compte : les 4 personnages du logo, ce qui est effacé (docs/141, 13)", async () => {
    GET.mockResolvedValue({ data: anonymous });
    const { wrapper } = await mountLogin("/connexion?au-revoir=1");
    expect(wrapper.find("[data-test=goodbye]").text()).toBe("Ton compte est supprimé.");
    expect(wrapper.find("[role=status]").text()).toContain("sont effacés");
    expect(wrapper.find("[data-scene=groupe]").exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Content de");
    expect(wrapper.find("[data-test=login-form]").exists()).toBe(true);
  });

  it("erreur, puis connexion qui ramène à la page demandée", async () => {
    GET.mockResolvedValueOnce({ data: anonymous }).mockResolvedValue({ data: { ...anonymous, authenticated: true, username: "camille" } });
    POST.mockResolvedValueOnce({ response: { ok: false }, error: { detail: "identifiant ou mot de passe incorrect" } }).mockResolvedValue({
      response: { ok: true },
    });
    const { wrapper, router } = await mountLogin();
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("faux");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=login-error]").text()).toBe("Identifiant ou mot de passe incorrect.");
    expect((wrapper.find("[data-test=password]").element as HTMLInputElement).value).toBe("");

    await wrapper.find("[data-test=password]").setValue("le-bon-mot-de-passe");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith("/api/auth/login", { body: { username: "camille", password: "le-bon-mot-de-passe" } });
    expect(router.currentRoute.value.fullPath).toBe("/candidatures");
    expect(useAuth().loggedIn.value).toBe(true);
  });

  it("refuse une adresse de retour externe", async () => {
    GET.mockResolvedValueOnce({ data: anonymous }).mockResolvedValue({ data: { ...anonymous, authenticated: true } });
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountLogin("/connexion?suite=//piege.example");
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("x");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/aujourdhui");
  });
});

describe("LoginView, Apple, Google et Microsoft (docs/65, complément du 2026-11-05)", () => {
  function offer(providers: unknown) {
    GET.mockImplementation((path: string) =>
      Promise.resolve({ data: path === "/api/auth/providers" ? { providers } : path === "/api/auth/signup" ? { open: false } : anonymous }),
    );
  }

  it("aucun fournisseur configuré : ni bouton, ni séparateur, ni « arrive bientôt »", async () => {
    offer([]);
    const { wrapper } = await mountLogin();
    expect(GET).toHaveBeenCalledWith("/api/auth/providers");
    expect(wrapper.find("[data-test=social-signin]").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("arrive bientôt");
    expect(wrapper.find("[data-test=login-form]").exists()).toBe(true);
  });

  it("seulement les fournisseurs configurés, dans l'ordre Apple, Google, Microsoft", async () => {
    offer(["microsoft", "google", "inconnu"]);
    const { wrapper } = await mountLogin();
    const buttons = wrapper.findAll(".social-button");
    expect(buttons.map((b) => b.attributes("data-test"))).toEqual(["social-google", "social-microsoft"]);
    expect(buttons.map((b) => b.text())).toEqual(["Continuer avec Google", "Continuer avec Microsoft"]);
    // Un lien vers le départ du serveur, avec la page où revenir.
    expect(buttons[0]!.attributes("href")).toBe("/api/auth/oauth/google/start?suite=%2Fcandidatures");
    expect(wrapper.find(".social-divider").text()).toBe("ou avec ton identifiant");
  });

  it("les trois configurés : trois boutons ; une adresse de retour externe n'est pas transmise", async () => {
    offer(["apple", "google", "microsoft"]);
    const { wrapper } = await mountLogin("/connexion?suite=//piege.example");
    expect(wrapper.findAll(".social-button").map((b) => b.attributes("href"))).toEqual([
      "/api/auth/oauth/apple/start",
      "/api/auth/oauth/google/start",
      "/api/auth/oauth/microsoft/start",
    ]);
  });

  it("le refus du serveur, dit sur la page (connexion sur invitation)", async () => {
    offer(["google"]);
    const { wrapper } = await mountLogin("/connexion?erreur=aucun-compte&fournisseur=google");
    expect(wrapper.find("[data-test=oauth-error]").text()).toBe("Aucun compte jobA1 n'est lié à ce compte Google.");
    expect(wrapper.find("[data-test=oauth-error]").attributes("role")).toBe("alert");
  });

  it("la demande de compte envoyée", async () => {
    offer(["apple"]);
    const { wrapper } = await mountLogin("/connexion?info=demande&fournisseur=apple");
    expect(wrapper.find("[data-test=oauth-info]").text()).toContain("Ta demande de compte est envoyée");
  });
});

describe("LoginView, maquette Connexion", () => {
  it("le titre, l'illustration décorative et le logo", async () => {
    GET.mockResolvedValue({ data: anonymous });
    const { wrapper } = await mountLogin();
    expect(wrapper.find("h1").text().replace(/\s+/g, " ")).toBe("Content de te revoir.");
    expect(wrapper.find(".login-hand").text()).toBe("te revoir.");
    const art = wrapper.findAll("[data-test=auth-illustration]");
    expect(art.length).toBe(2);
    for (const one of art) {
      // Décorative : cachée aux lecteurs d'écran, image sans texte.
      const img = one.element.tagName === "IMG" ? one : one.find("img");
      expect(img.attributes("aria-hidden") ?? one.attributes("aria-hidden")).toBe("true");
      expect(img.attributes("alt")).toBe("");
      // Les 4 personnages du logo (scène « groupe », §15 du 9 novembre) : taille réservée.
      expect(img.attributes("data-scene")).toBe("groupe");
      expect(img.attributes("src")).toMatch(/\/troupe\/groupe-412\.webp/);
      expect(img.attributes("srcset")).toMatch(/groupe-1200\S* 1200w/);
      expect(Number(img.attributes("height"))).toBeGreaterThan(0);
    }
    // Téléphone : 206 px dans le bandeau ; ordinateur : 720 px au plus (ConnexionOrdinateur).
    expect(art.map((one) => (one.element.tagName === "IMG" ? one : one.find("img")).attributes("width")).sort()).toEqual(["206", "720"]);
    expect(wrapper.find("[data-test=brand-logo]").exists()).toBe(true);
  });

  it("champs vides : l'erreur sous chaque champ, avec aria-invalid", async () => {
    GET.mockResolvedValue({ data: anonymous });
    const { wrapper } = await mountLogin();
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();
    expect(wrapper.find("[data-test=username-error]").text()).toBe("Écris ton identifiant.");
    expect(wrapper.find("[data-test=login-error]").text()).toBe("Écris ton mot de passe.");
    expect(wrapper.find("[data-test=username]").attributes("aria-invalid")).toBe("true");
    expect(wrapper.find("[data-test=username]").attributes("aria-describedby")).toBe("login-username-error");
    expect(wrapper.find("[data-test=password]").attributes("aria-invalid")).toBe("true");
    expect(wrapper.find("[data-test=username-error] .icon").exists()).toBe(true);
  });

  it("« Afficher le mot de passe » : 44 px, aria-pressed", async () => {
    GET.mockResolvedValue({ data: anonymous });
    const { wrapper } = await mountLogin();
    const toggle = wrapper.find("[data-test=password-toggle]");
    expect(toggle.attributes("aria-label")).toBe("Afficher le mot de passe");
    expect(toggle.attributes("aria-pressed")).toBe("false");
    expect(wrapper.find("[data-test=password]").attributes("type")).toBe("password");
    await toggle.trigger("click");
    expect(toggle.attributes("aria-pressed")).toBe("true");
    expect(wrapper.find("[data-test=password]").attributes("type")).toBe("text");
  });
});

describe("LoginView, demander un compte (docs/102)", () => {
  function answer(open: boolean) {
    GET.mockImplementation((path: string) => Promise.resolve({ data: path === "/api/auth/signup" ? { open } : anonymous }));
  }

  it("demandes ouvertes : « Créer un compte » mène à /inscription", async () => {
    answer(true);
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=signup-link]").attributes("href")).toBe("/inscription");
    expect(wrapper.find(".login-foot").text().replace(/\s+/g, " ")).toContain("Pas encore de compte ? Créer un compte");
    expect(wrapper.text()).not.toContain("sur invitation");
  });

  it("demandes fermées : l'invitation, sans lien", async () => {
    answer(false);
    const { wrapper } = await mountLogin();
    expect(wrapper.find("[data-test=signup-link]").exists()).toBe(false);
    expect(wrapper.text()).toContain("L'accès se fait sur invitation.");
  });

  it("un compte qui attend la validation : le message du serveur, tel quel", async () => {
    answer(true);
    POST.mockResolvedValue({ response: { ok: false, status: 403 }, error: { detail: "ton compte attend encore la validation de l'exploitant" } });
    const { wrapper } = await mountLogin();
    await wrapper.find("[data-test=username]").setValue("camille");
    await wrapper.find("[data-test=password]").setValue("un-mot-de-passe-solide");
    await wrapper.find("[data-test=login-form]").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=login-error]").text()).toBe("Ton compte attend encore la validation de l'exploitant.");
  });
});
