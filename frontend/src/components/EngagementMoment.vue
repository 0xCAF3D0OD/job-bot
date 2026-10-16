<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import Illustration from "./Illustration.vue";

// La seule fête de la plateforme (docs/60 §2.1) : une candidature passe en Engagement. En grand,
// par-dessus la page et sans carte (complément du 2026-10-16) : la poignée de main et quelques
// confettis, une fois ; « Fermer », Échap ou un clic à côté referment.
defineProps<{ company?: string }>();
const emit = defineEmits<{ close: [] }>();

// Confettis : direction, distance et couleur fixes (pas de hasard, rendu identique à chaque fois).
const PIECES = Array.from({ length: 24 }, (_, i) => {
  const angle = (i / 24) * Math.PI * 2;
  const distance = 120 + (i % 3) * 45;
  return {
    x: `${Math.round(Math.cos(angle) * distance)}px`,
    y: `${Math.round(Math.sin(angle) * distance * 0.7 - 30)}px`,
    r: `${(i * 47) % 360}deg`,
    color: ["var(--accent)", "var(--mint)", "var(--orange)"][i % 3],
    delay: `${(i % 4) * 40}ms`,
  };
});

const closeButton = ref<HTMLButtonElement | null>(null);
function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    event.stopPropagation();
    emit("close");
  }
}
onMounted(() => {
  closeButton.value?.focus();
  document.addEventListener("keydown", onKey, true);
});
onUnmounted(() => document.removeEventListener("keydown", onKey, true));
</script>

<template>
  <Teleport to="body">
    <div
      class="engagement-overlay"
      data-test="engagement-moment"
      @click.self="emit('close')"
    >
      <div
        class="engagement-moment"
        role="dialog"
        aria-modal="true"
        aria-labelledby="engagement-title"
      >
        <div class="engagement-art">
          <Illustration name="handshake-deal" />
          <span
            class="confetti"
            aria-hidden="true"
          >
            <span
              v-for="(piece, index) in PIECES"
              :key="index"
              :style="{ '--x': piece.x, '--y': piece.y, '--r': piece.r, '--c': piece.color, animationDelay: piece.delay }"
            />
          </span>
        </div>
        <h3 id="engagement-title">
          Félicitations !
        </h3>
        <p>
          {{ company ? `Engagement chez ${company}.` : "Un engagement." }}
          Pense à le signaler à ton conseiller ORP.
        </p>
        <button
          ref="closeButton"
          type="button"
          class="secondary"
          data-test="engagement-close"
          @click="emit('close')"
        >
          Fermer
        </button>
      </div>
    </div>
  </Teleport>
</template>
