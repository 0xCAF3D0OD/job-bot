<script setup lang="ts">
import { useId } from "vue";
import type { RouteLocationRaw } from "vue-router";

// La bande d'action (docs/regles-ui-ergonomie.md §3, 1.6.48) : une bande accent pleine largeur sous la
// conclusion, avec une carte posée dessus qui rend explicite l'action la plus importante de la page et
// porte sa seule action principale. Une seule par page ; la page ne la montre que s'il y a quelque chose
// à faire. L'action est un lien (`to`) ou un bouton (`@action`).
defineProps<{ title: string; summary?: string; action: string; to?: RouteLocationRaw }>();
defineEmits<{ action: [] }>();
const titleId = useId();
</script>

<template>
  <section
    class="action-band"
    :aria-labelledby="titleId"
    data-test="action-band"
  >
    <div class="action-band-card">
      <div class="action-band-body">
        <h2
          :id="titleId"
          class="action-band-title"
        >
          {{ title }}
        </h2>
        <p
          v-if="summary"
          class="action-band-summary"
        >
          {{ summary }}
        </p>
        <!-- Un aperçu, si la page en a un (la meilleure offre, le prochain rendez-vous…). -->
        <slot />
      </div>
      <RouterLink
        v-if="to"
        :to="to"
        class="button-link primary-link action-band-action"
        data-test="action-band-action"
      >
        {{ action }}
      </RouterLink>
      <button
        v-else
        type="button"
        class="primary action-band-action"
        data-test="action-band-action"
        @click="$emit('action')"
      >
        {{ action }}
      </button>
    </div>
  </section>
</template>
