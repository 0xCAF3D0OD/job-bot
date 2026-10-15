<script setup lang="ts">
// « Copier » devient « ✓ Copié » (docs/59 §3) : le même retour sur tous les boutons Copier.
defineProps<{ done: boolean; label?: string }>();
</script>

<template>
  <span
    v-if="done"
    class="copy-done"
  >✓ Copié</span>
  <span v-else>{{ label ?? "Copier" }}</span>
</template>
