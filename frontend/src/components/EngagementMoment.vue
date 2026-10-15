<script setup lang="ts">
import Illustration from "./Illustration.vue";

// La seule fête de la plateforme (docs/60 §2.1) : une candidature passe en Engagement.
// La poignée de main et quelques confettis, une fois ; rien si « réduire les animations ».
defineProps<{ company?: string }>();

// Confettis : direction, distance et couleur fixes (pas de hasard, rendu identique à chaque fois).
const PIECES = Array.from({ length: 18 }, (_, i) => {
  const angle = (i / 18) * Math.PI * 2;
  const distance = 70 + (i % 3) * 28;
  return {
    x: `${Math.round(Math.cos(angle) * distance)}px`,
    y: `${Math.round(Math.sin(angle) * distance * 0.7 - 20)}px`,
    r: `${(i * 47) % 360}deg`,
    color: ["var(--accent)", "var(--mint)", "var(--orange)"][i % 3],
    delay: `${(i % 4) * 40}ms`,
  };
});
</script>

<template>
  <div
    class="engagement-moment"
    role="status"
    data-test="engagement-moment"
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
    <h3>Félicitations !</h3>
    <p>
      {{ company ? `Engagement chez ${company}.` : "Un engagement." }}
      Pense à le signaler à ton conseiller ORP.
    </p>
  </div>
</template>
