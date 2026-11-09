<script setup lang="ts">
import { computed } from "vue";

import AppIcon from "./AppIcon.vue";

// « Copier » devient « Copié » (docs/59 §3) : le même retour sur tous les boutons Copier.
// Icône seule (docs/101) : deux feuilles, puis la coche pendant que « Copié » s'affiche ; le nom
// reste lu par un lecteur d'écran (texte masqué) et montré en infobulle au survol du bouton.
const props = defineProps<{ done: boolean; label?: string }>();
const name = computed(() => (props.done ? "Copié" : (props.label ?? "Copier")));
// Prompt du 9 novembre : l'infobulle dit seulement « Copier » (ou « Copié ») ; le libellé complet est lu.
const tip = computed(() => (props.done ? "Copié" : "Copier"));
</script>

<template>
  <span
    :class="['copy-label', { 'copy-done': done }]"
    :data-label="tip"
  >
    <AppIcon :name="done ? 'done' : 'copy'" />
    <span class="visually-hidden">{{ name }}</span>
  </span>
</template>
