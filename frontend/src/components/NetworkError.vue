<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import AppIcon from "./AppIcon.vue";
import FaceState from "./FaceState.vue";

// Pas de connexion (planche « Illustrations », 224:2) : l'écran commun quand le chargement d'une page
// échoue pour une raison de réseau. jobA1 réessaie de lui-même dès que le réseau revient (l'événement
// « online » du navigateur) : la phrase le promet parce que c'est vrai ; « Réessayer » le fait tout de
// suite. Rien de ce qui est saisi n'est effacé.
const emit = defineEmits<{ retry: [] }>();

function back(): void {
  emit("retry");
}
onMounted(() => globalThis.addEventListener?.("online", back));
onUnmounted(() => globalThis.removeEventListener?.("online", back));
</script>

<template>
  <FaceState
    title="Pas de connexion"
    illustration="connexion-perdue"
    data-test="network-error"
  >
    <p>jobA1 réessaie dès que le réseau revient. Ce que tu as saisi est gardé.</p>
    <div class="face-state-actions">
      <button
        type="button"
        class="secondary"
        data-test="network-retry"
        @click="emit('retry')"
      >
        <span class="with-icon"><AppIcon name="refresh" />Réessayer</span>
      </button>
    </div>
  </FaceState>
</template>
