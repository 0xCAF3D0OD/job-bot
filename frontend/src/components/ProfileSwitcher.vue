<script setup lang="ts">
import { onMounted } from "vue";

import { useProfiles } from "../composables/useProfiles";

// Sélecteur de profil (docs/17 §3), seulement s'il existe des profils d'essai.
const { list, current, load, choose } = useProfiles();

function onChange(event: Event): void {
  choose(Number((event.target as HTMLSelectElement).value));
}

onMounted(() => void load());
</script>

<template>
  <label
    v-if="list && list.items.length > 1"
    class="profile-switcher"
  >
    <span class="visually-hidden">Profil</span>
    <select
      :value="current?.id"
      aria-label="Profil"
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
</template>
