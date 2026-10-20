<script setup lang="ts">
import { useUndo } from "../composables/useUndo";

// Le bandeau « Annuler » (docs/108 §1) : en bas, au-dessus de la barre d'onglets ; lu par les
// lecteurs d'écran ; Échap le ferme en validant l'action.
const { pending, undo, hold, release, flush } = useUndo();
</script>

<template>
  <div
    v-if="pending"
    :key="pending.id"
    class="toast undo-toast"
    role="status"
    data-test="undo-toast"
    @mouseenter="hold"
    @mouseleave="release"
    @focusin="hold"
    @focusout="release"
    @keydown.esc="flush()"
  >
    <span>{{ pending.message }}</span>
    <button
      type="button"
      class="link"
      data-test="undo"
      @click="undo"
    >
      Annuler
    </button>
  </div>
</template>
