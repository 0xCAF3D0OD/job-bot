<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

import LoadingDrawing from "./LoadingDrawing.vue";

// La page d'attente (docs/79) : par-dessus tout, sans recharger ; le reste de l'écran est
// inerte tant qu'elle est là, et retrouvé tel quel ensuite.
const props = defineProps<{ waiting: boolean; message: string | null }>();
const panel = ref<HTMLElement | null>(null);

function setInert(on: boolean): void {
  const app = document.getElementById("app");
  if (!app) return;
  if (on) app.setAttribute("inert", "");
  else app.removeAttribute("inert");
}

// L'élément où l'on était (la lettre en cours…) retrouve le curseur au retour (docs/81 §2).
let before: HTMLElement | null = null;

watch(
  () => props.waiting,
  async (on) => {
    if (on) before = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setInert(on);
    if (on) {
      await nextTick();
      panel.value?.focus();
    } else if (before?.isConnected) {
      before.focus();
      before = null;
    }
  },
  { immediate: true },
);
</script>

<template>
  <Teleport to="body">
    <div
      v-if="waiting"
      ref="panel"
      class="maintenance"
      role="dialog"
      aria-modal="true"
      aria-labelledby="maintenance-title"
      tabindex="-1"
      data-test="maintenance"
    >
      <div class="container">
        <!-- Le dessin unDraw de la maintenance : il bouge tant que l'attente dure (docs/80 §2). -->
        <div class="illustrated phone-small">
          <LoadingDrawing name="maintenance" />
          <div class="illustrated-body">
            <h1 id="maintenance-title">
              jobA1 revient dans un instant
            </h1>
            <p
              class="maintenance-message"
              aria-live="polite"
            >
              {{ message || "La plateforme se met à jour, ou la connexion est coupée." }}
            </p>
            <p class="muted">
              On réessaie toutes les 10 secondes. Ta page t'attend telle quelle : ce que tu étais en train d'écrire n'est pas perdu.
            </p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
