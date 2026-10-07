<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useProfiles } from "../composables/useProfiles";
import AppIcon from "./AppIcon.vue";

// Menu du compte (docs/19 §1) : profil affiché (profils d'essai) et déconnexion.
const router = useRouter();
const { me, logout } = useAuth();
const { list, current, load, choose } = useProfiles();
const open = ref(false);
const root = ref<HTMLElement | null>(null);
// Rien à proposer (un seul profil, connexion désactivée) : pas d'icône.
const visible = computed(() => Boolean(me.value?.auth_enabled || (list.value && list.value.items.length > 1)));

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
    v-if="visible"
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
