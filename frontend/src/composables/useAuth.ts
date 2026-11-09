import { computed, ref } from "vue";

import { api, PROFILE_KEY, type Me } from "../api/client";

// Connexion (docs/18 §1) : état partagé par le routeur, la barre du haut et les pages.
const me = ref<Me | null>(null);

// Après la déconnexion, la page est rechargée sur la connexion (incident du 2026-11-09) : tout ce
// que l'application gardait en mémoire (candidatures, Suivi ORP, profil) disparaît avec elle. Un
// simple changement de route laissait la page affichée, et les données restaient en mémoire.
export const LOGIN_PATH = "/connexion";
export const leave = { to: (path: string): void => window.location.replace(path) };
let loading: Promise<void> | null = null;

export function useAuth() {
  const loggedIn = computed(() => Boolean(me.value?.authenticated));

  // Une seule lecture au démarrage ; `force` après connexion ou déconnexion.
  async function load(force = false): Promise<void> {
    if (me.value && !force) return;
    loading ??= (async () => {
      try {
        const { data } = await api.GET("/api/auth/me");
        me.value = data ?? { authenticated: false, username: null, setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
      } finally {
        loading = null;
      }
    })();
    await loading;
  }

  async function login(username: string, password: string): Promise<string | null> {
    const { error, response } = await api.POST("/api/auth/login", { body: { username, password } });
    if (response.ok) {
      await load(true);
      return null;
    }
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    return typeof detail === "string" ? detail : "connexion impossible";
  }

  // Même si l'appel échoue (réseau coupé), la page quitte les données du compte.
  async function logout(everywhere = false): Promise<void> {
    try {
      if (everywhere) await api.POST("/api/auth/logout-all");
      else await api.POST("/api/auth/logout");
    } finally {
      me.value = { authenticated: false, username: null, setup_needed: false, auth_enabled: true, is_owner: false, welcome: "done", demo: false };
      // Le profil d'essai choisi appartient à ce compte : le suivant repart du sien.
      try {
        globalThis.localStorage?.removeItem(PROFILE_KEY);
      } catch {
        // Stockage refusé : rien n'y était gardé.
      }
      leave.to(LOGIN_PATH);
    }
  }

  function expired(): void {
    if (me.value) me.value = { ...me.value, authenticated: false, username: null };
  }

  return { me, loggedIn, load, login, logout, expired };
}
