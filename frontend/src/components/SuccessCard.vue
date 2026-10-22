<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import IconButton from "./IconButton.vue";
import FaceMark from "./FaceMark.vue";
import Illustration, { type IllustrationName } from "./Illustration.vue";

// Une réussite (docs/61 §1) : une carte qui vient devant, de manière souple, la page grisée
// derrière ; l'illustration est posée au-dessus de la carte, à cheval sur son bord, pas dedans.
// Elle se ferme seule après 4 secondes, ou avec « Fermer », Échap, un clic à côté.
// `face` : une victoire (docs/123 §2, R : un entretien proposé, l'objectif du mois atteint) ; le
// visage ravi à la place de l'illustration, de petites bulles autour, une fois ; `wink` pour
// l'objectif atteint. `keepFocus` : ouverte sans geste de la personne (au chargement d'une page),
// la carte ne prend pas le focus ; elle reste annoncée (`role="status"`).
const props = withDefaults(defineProps<{ name?: IllustrationName; face?: boolean; wink?: boolean; title: string; closeAfterMs?: number; testId?: string; keepFocus?: boolean }>(), {
  name: undefined,
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
const closeButton = ref<InstanceType<typeof IconButton> | null>(null);
onMounted(() => {
  if (!props.keepFocus) (closeButton.value?.$el as HTMLButtonElement | undefined)?.focus({ preventScroll: true });
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
        <span
          v-if="face"
          class="success-art success-face"
          aria-hidden="true"
        >
          <span
            v-for="bubble in 6"
            :key="bubble"
            :class="['victory-bubble', `b${bubble}`]"
          />
          <FaceMark
            mood="ravi"
            :size="120"
            :wink="wink"
          />
        </span>
        <Illustration
          v-else-if="name"
          :name="name"
          class="success-art"
        />
        <h3>{{ title }}</h3>
        <slot />
        <IconButton
          ref="closeButton"
          icon="close"
          label="Fermer"
          class="success-close"
          data-test="success-close"
          @click="close"
        />
      </div>
    </div>
  </Teleport>
</template>
