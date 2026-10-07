<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useProfiles } from "../composables/useProfiles";
import { navigation } from "../router";
import AppIcon from "./AppIcon.vue";

// Menu du compte : Profil, Réglages, profil affiché, déconnexion. Garde la barre du haut
// sur une seule ligne.
const router = useRouter();
const { me, logout } = useAuth();
const { list, current, load, choose } = useProfiles();
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const entries = computed(() => navigation.filter((e) => e.account));

function onChange(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}

async function signOut(): Promise<void> {
  open.value = false;
  await logout();
  await router.push({ name: "news" });
}

function onDocumentClick(event: MouseEvent): void {
  if (open.value && root.value && !root.value.contains(event.target as Node)) open.value = false;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") open.value = false;
}

onMounted(() => {
  void load();
  document.addEventListener("click", onDocumentClick);
  document.addEventListener("keydown", onKeydown);
});
onUnmounted(() => {
  document.removeEventListener("click", onDocumentClick);
  document.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <div
    ref="root"
    class="account-menu"
  >
    <button
      type="button"
      class="icon-button"
      :aria-expanded="open"
      aria-haspopup="menu"
      :aria-label="me?.username ? `Compte : ${me.username}` : 'Compte'"
      data-test="account-menu"
      @click="open = !open"
    >
      <AppIcon name="user" />
    </button>
    <div
      v-if="open"
      class="account-panel"
      role="menu"
      data-test="account-panel"
    >
      <p
        v-if="me?.username"
        class="account-name"
      >
        Connecté : <strong>{{ me.username }}</strong>
      </p>
      <RouterLink
        v-for="entry in entries"
        :key="entry.name"
        :to="entry.path"
        role="menuitem"
        @click="open = false"
      >
        {{ entry.label }}
      </RouterLink>
      <label
        v-if="list && list.items.length > 1"
        class="account-profile"
      >Profil affiché
        <select
          :value="current?.id"
          data-test="profile-switcher"
          @change="onChange"
        >
          <option
            v-for="profile in list.items"
            :key="profile.id"
            :value="profile.id"
          >
            {{ profile.is_main ? "👤 " : "🧪 " }}{{ profile.name }}
          </option>
        </select>
      </label>
      <button
        v-if="me?.auth_enabled"
        type="button"
        class="link"
        role="menuitem"
        data-test="logout"
        @click="signOut"
      >
        Se déconnecter
      </button>
    </div>
  </div>
</template>
