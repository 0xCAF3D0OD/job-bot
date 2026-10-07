<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { UNAUTHORIZED_EVENT } from "./api/client";

import AppIcon from "./components/AppIcon.vue";
import NotificationBell from "./components/NotificationBell.vue";
import AccountMenu from "./components/AccountMenu.vue";
import { useAuth } from "./composables/useAuth";
import { useNewsCount } from "./composables/useNewsCount";
import { useCollect } from "./composables/useCollect";
import { useProfiles } from "./composables/useProfiles";
import { navigation, PUBLIC_ROUTES } from "./router";

const { message, running, collectNow } = useCollect();
const { count: newsCount, start: startNewsCount } = useNewsCount();
const { current: profile, main: mainProfile, choose } = useProfiles();
const route = useRoute();
const router = useRouter();
const { me, loggedIn, load, expired } = useAuth();
// Sans connexion : seulement les Actualités dans le menu (docs/18 §1).
// Six entrées (docs/19 §1) ; sans connexion, seulement les Actualités (docs/18 §1).
const menu = computed(() => (loggedIn.value ? navigation : navigation.filter((e) => PUBLIC_ROUTES.has(e.name))));

function onUnauthorized(): void {
  expired();
  if (!PUBLIC_ROUTES.has(String(route.name))) {
    void router.push({ name: "login", query: { suite: route.fullPath } });
  }
}


onMounted(async () => {
  window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  await load();
  startNewsCount();
});
onUnmounted(() => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized));
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <RouterLink
        to="/"
        class="brand"
        aria-label="job-bot, accueil"
      >
        <span
          class="brand-mark"
          aria-hidden="true"
        />
        job-bot
      </RouterLink>
      <nav aria-label="Navigation principale">
        <ul class="nav">
          <li
            v-for="entry in menu"
            :key="entry.name"
          >
            <RouterLink :to="entry.path">
              {{ entry.label }}
              <span
                v-if="entry.name === 'news' && newsCount"
                class="nav-count"
                data-test="news-count"
              >{{ newsCount }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>
      <div
        v-if="loggedIn"
        class="topbar-actions"
      >
        <NotificationBell />
        <button
          type="button"
          class="primary small"
          :disabled="running"
          data-test="collect-top"
          @click="collectNow"
        >
          Collecter <AppIcon name="chevron" />
        </button>
        <AccountMenu />
      </div>
      <div
        v-else-if="me"
        class="topbar-actions"
      >
        <RouterLink
          :to="{ name: 'login', query: route.name === 'login' ? route.query : { suite: route.fullPath } }"
          class="button-link primary-link"
          data-test="login-link"
        >
          Se connecter
        </RouterLink>
      </div>
    </div>
  </header>
  <div
    v-if="loggedIn && profile && !profile.is_main"
    class="profile-banner"
    role="status"
    data-test="profile-banner"
  >
    <strong>Profil d'essai : {{ profile.name }}</strong>
    <span>Seules les Actualités et les Formations suivent ce profil ; les autres pages restent les tiennes.</span>
    <button
      v-if="mainProfile"
      type="button"
      class="link"
      data-test="profile-back"
      @click="choose(mainProfile.id)"
    >
      Revenir à {{ mainProfile.name }}
    </button>
  </div>
  <p
    v-if="message"
    class="toast"
    role="status"
  >
    {{ message }}
  </p>
  <main>
    <RouterView />
  </main>
</template>
