<script setup lang="ts">
import { navigation } from "./router";
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
        >jb</span>
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
    </div>
  </header>
  <main class="content">
    <RouterView />
  </main>
</template>
