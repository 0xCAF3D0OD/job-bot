<script setup lang="ts">
import { navigation } from "./router";
</script>

<template>
  <div class="layout">
    <nav
      class="sidebar"
      aria-label="Navigation principale"
    >
      <RouterLink
        to="/"
        class="brand"
      >
        job-bot
      </RouterLink>
      <ul>
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
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>
