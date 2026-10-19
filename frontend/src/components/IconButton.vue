<script setup lang="ts">
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Un bouton sans texte (docs/101) : l'icône seule, son nom annoncé (aria-label) et montré dans
// une infobulle au survol et au focus ; rond, à la hauteur commune des contrôles (docs/94).
withDefaults(defineProps<{ icon: IconName; label: string; danger?: boolean; type?: "button" | "submit" }>(), {
  danger: false,
  type: "button",
});
</script>

<template>
  <button
    :type="type"
    class="icon-button icon-only"
    :class="{ danger }"
    :aria-label="label"
    :data-label="label"
  >
    <AppIcon :name="icon" />
  </button>
</template>
