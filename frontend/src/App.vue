<script setup lang="ts">
import AppIcon from "./components/AppIcon.vue";
import { useCollect } from "./composables/useCollect";
import { navigation } from "./router";

const { message, running, collectNow } = useCollect();
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
            </RouterLink>
          </li>
        </ul>
      </nav>
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
  </header>
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
