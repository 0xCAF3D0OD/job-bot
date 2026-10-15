<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import { useCollect } from "../composables/useCollect";
import { useJobsMemory } from "../composables/useJobsMemory";
import { useProfiles } from "../composables/useProfiles";
import type { NavEntry } from "../router";
import SidePanel from "./SidePanel.vue";

// Menu « burger » (docs/33 §2) : sur un écran étroit, la barre du haut ne garde que le logo,
// la cloche et ☰ ; les pages, la collecte et le compte passent dans ce panneau.
const props = defineProps<{ menu: NavEntry[]; newsCount: number }>();

const open = ref(false);
const route = useRoute();
const router = useRouter();
const { me, logout } = useAuth();
const { list, current, choose } = useProfiles();
const { running, collectNow } = useCollect();
const { last: lastJobsPage } = useJobsMemory();

const entries = computed(() =>
  props.menu.map((entry) => ({
    ...entry,
    to: entry.name === "jobs" ? lastJobsPage.value : entry.path,
    active: entry.name === "jobs" ? route.path.startsWith("/candidatures") : route.path.startsWith(entry.path),
  })),
);

// Une page choisie ferme le menu.
watch(
  () => route.fullPath,
  () => (open.value = false),
);

async function collect(): Promise<void> {
  open.value = false;
  await collectNow();
}

function onProfile(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}

async function signOut(): Promise<void> {
  open.value = false;
  await logout();
  await router.push({ name: "news" });
}
</script>

<template>
  <button
    type="button"
    class="icon-button burger"
    :aria-expanded="open"
    aria-label="Menu"
    data-test="burger"
    @click="open = true"
  >
    <span
      class="burger-lines"
      aria-hidden="true"
    />
  </button>
  <SidePanel
    :open="open"
    title="Menu"
    @close="open = false"
  >
    <nav aria-label="Navigation principale (menu)">
      <ul class="mobile-nav">
        <li
          v-for="entry in entries"
          :key="entry.name"
        >
          <RouterLink
            :to="entry.to"
            :class="{ active: entry.active }"
            :aria-current="entry.active ? 'page' : undefined"
            :data-test="`burger-${entry.name}`"
            @click="open = false"
          >
            {{ entry.label }}
            <span
              v-if="entry.name === 'news' && newsCount"
              class="nav-count"
            >{{ newsCount }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
    <div class="mobile-menu-section">
      <button
        type="button"
        class="link"
        :disabled="running"
        data-test="burger-collect"
        @click="collect"
      >
        Collecter maintenant
      </button>
    </div>
    <div
      v-if="me?.username || (list && list.items.length > 1) || me?.auth_enabled"
      class="mobile-menu-section"
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
          data-test="burger-profile"
          @change="onProfile"
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
        data-test="burger-logout"
        @click="signOut"
      >
        Se déconnecter
      </button>
    </div>
  </SidePanel>
</template>
