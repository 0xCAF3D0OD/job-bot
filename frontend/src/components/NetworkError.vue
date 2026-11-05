<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import AppIcon from "./AppIcon.vue";
import FaceState from "./FaceState.vue";

// Pas de connexion (planche « Illustrations », 224:2) : l'écran commun quand le chargement d'une page
// échoue pour une raison de réseau. jobA1 réessaie de lui-même dès que le réseau revient (l'événement
// « online » du navigateur) : la phrase le promet parce que c'est vrai ; « Réessayer » le fait tout de
// suite. Rien de ce qui est saisi n'est effacé.
// `title` et `line` (téléphone, maquette ErreurConnexion) : le visage au lieu de l'illustration, une phrase
// propre à la page, et « Réessayer » en bouton principal.
const props = defineProps<{ title?: string; line?: string }>();
const emit = defineEmits<{ retry: [] }>();

function back(): void {
  emit("retry");
}
onMounted(() => globalThis.addEventListener?.("online", back));
onUnmounted(() => globalThis.removeEventListener?.("online", back));
</script>

<template>
  <FaceState
    :title="props.title ?? 'Pas de connexion'"
    :illustration="props.title ? undefined : 'connexion-perdue'"
    mood="attentif"
    :animation="props.title ? 'hochement' : undefined"
    data-test="network-error"
  >
    <p>{{ props.line ?? "jobA1 réessaie dès que le réseau revient. Ce que tu as saisi est gardé." }}</p>
    <div class="face-state-actions">
      <button
        type="button"
        :class="props.title ? 'primary' : 'secondary'"
        data-test="network-retry"
        @click="emit('retry')"
      >
        <span class="with-icon"><AppIcon name="refresh" />Réessayer</span>
      </button>
    </div>
  </FaceState>
</template>
