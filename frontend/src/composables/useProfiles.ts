import { computed, ref } from "vue";

import { api, PROFILE_KEY, type ProfileList } from "../api/client";

// Profils d'essai (docs/17) : liste partagée par le sélecteur, la bande et les Réglages.
const list = ref<ProfileList | null>(null);

export function useProfiles() {
  const current = computed(() => list.value?.items.find((p) => p.id === list.value?.current_id) ?? null);
  const main = computed(() => list.value?.items.find((p) => p.is_main) ?? null);

  async function load(): Promise<void> {
    const { data } = await api.GET("/api/profiles");
    if (data && Array.isArray(data.items)) list.value = data;
  }

  function set(data: ProfileList): void {
    list.value = data;
  }

  // Changer de profil recharge la page : toutes les données affichées suivent le profil.
  function choose(id: number): void {
    try {
      if (main.value?.id === id) localStorage.removeItem(PROFILE_KEY);
      else localStorage.setItem(PROFILE_KEY, String(id));
    } catch {
      // Stockage indisponible (navigation privée) : le profil principal reste utilisé.
    }
    window.location.reload();
  }

  return { list, current, main, load, set, choose };
}
