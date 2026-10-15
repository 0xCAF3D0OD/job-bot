<script setup lang="ts">
import DisclosureRow from "./DisclosureRow.vue";

// Étapes à suivre trop longues pour une bulle « ? » (docs/32 §1) : une ligne dépliable.
withDefaults(defineProps<{ label?: string; value?: string }>(), { label: "En savoir plus", value: "" });
</script>

<template>
  <DisclosureRow
    class="more-info"
    :title="label"
    :value="value"
  >
    <slot />
  </DisclosureRow>
</template>
