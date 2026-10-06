<script setup lang="ts">
import { onMounted } from "vue";

import AppIcon from "./components/AppIcon.vue";
import NotificationBell from "./components/NotificationBell.vue";
import ProfileSwitcher from "./components/ProfileSwitcher.vue";
import { useNewsCount } from "./composables/useNewsCount";
import { useCollect } from "./composables/useCollect";
import { useProfiles } from "./composables/useProfiles";
import { navigation } from "./router";

const { message, running, collectNow } = useCollect();
const { count: newsCount, start: startNewsCount } = useNewsCount();
const { current: profile, main: mainProfile, choose } = useProfiles();
onMounted(() => startNewsCount());
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
            v-for="entry in navigation"
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
      <div class="topbar-actions">
        <ProfileSwitcher />
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
      </div>
    </div>
  </header>
  <div
    v-if="profile && !profile.is_main"
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
