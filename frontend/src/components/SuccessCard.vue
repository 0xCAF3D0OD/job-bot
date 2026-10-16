<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import Illustration, { type IllustrationName } from "./Illustration.vue";

// Une réussite (docs/61 §1) : une carte qui vient devant, de manière souple, la page grisée
// derrière ; l'illustration est posée au-dessus de la carte, à cheval sur son bord, pas dedans.
// Elle se ferme seule après 4 secondes, ou avec « Fermer », Échap, un clic à côté.
const props = withDefaults(defineProps<{ name: IllustrationName; title: string; closeAfterMs?: number; testId?: string }>(), {
  closeAfterMs: 4000,
  testId: "success-card",
});
const emit = defineEmits<{ close: [] }>();

const leaving = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;
function close(): void {
  if (leaving.value) return;
  leaving.value = true;
  clearTimeout(timer);
  // Le temps qu'elle redescende en s'effaçant (250 ms).
  setTimeout(() => emit("close"), 250);
}
function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    event.stopPropagation();
    close();
  }
}
const closeButton = ref<HTMLButtonElement | null>(null);
onMounted(() => {
  closeButton.value?.focus({ preventScroll: true });
  document.addEventListener("keydown", onKey, true);
  if (props.closeAfterMs > 0) timer = setTimeout(close, props.closeAfterMs);
});
onUnmounted(() => {
  clearTimeout(timer);
  document.removeEventListener("keydown", onKey, true);
});
</script>

<template>
  <Teleport to="body">
    <div
      :class="['success-overlay', { leaving }]"
      @click.self="close"
    >
      <div
        class="success-card"
        role="status"
        :data-test="testId"
      >
        <Illustration
          :name="name"
          class="success-art"
        />
        <h3>{{ title }}</h3>
        <slot />
        <button
          ref="closeButton"
          type="button"
          class="secondary small"
          data-test="success-close"
          @click="close"
        >
          Fermer
        </button>
      </div>
    </div>
  </Teleport>
</template>
