<script setup lang="ts">
// « En savoir plus » (docs/21 §2) : une phrase d'aide visible, le détail replié.
withDefaults(defineProps<{ label?: string }>(), { label: "En savoir plus" });
</script>

<template>
  <details class="more-info">
    <summary>{{ label }}</summary>
    <div class="more-info-body">
      <slot />
    </div>
  </details>
</template>
