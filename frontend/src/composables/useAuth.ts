import { computed, ref } from "vue";

import { api, type Me } from "../api/client";

// Connexion (docs/18 §1) : état partagé par le routeur, la barre du haut et les pages.
const me = ref<Me | null>(null);
let loading: Promise<void> | null = null;

export function useAuth() {
  const loggedIn = computed(() => Boolean(me.value?.authenticated));

  // Une seule lecture au démarrage ; `force` après connexion ou déconnexion.
  async function load(force = false): Promise<void> {
    if (me.value && !force) return;
    loading ??= (async () => {
      try {
        const { data } = await api.GET("/api/auth/me");
        me.value = data ?? { authenticated: false, username: null, setup_needed: false, auth_enabled: true };
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

  async function logout(everywhere = false): Promise<void> {
    if (everywhere) await api.POST("/api/auth/logout-all");
    else await api.POST("/api/auth/logout");
    me.value = { authenticated: false, username: null, setup_needed: false, auth_enabled: true };
  }

  function expired(): void {
    if (me.value) me.value = { ...me.value, authenticated: false, username: null };
  }

  return { me, loggedIn, load, login, logout, expired };
}
