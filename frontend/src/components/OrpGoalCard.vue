<script setup lang="ts">
import type { OrpMonth } from "../api/client";
import OrpBar from "./OrpBar.vue";

// L'objectif ORP du mois (docs/139 étape 8, maquettes Explorer et Orp ; B3, B4, Kevin, 2026-11-04) : la barre ORP
// (OrpBar, PR 48 : plus de cercle à vague), ce qui reste à faire et l'échéance. Sans objectif saisi, la carte invite à
// l'indiquer au lieu d'un « 0 sur 0 ». « Recherches » est le mot du formulaire de l'ORP (B5).
defineProps<{ data: OrpMonth }>();

</script>

<template>
  <section
    v-if="data.target"
    class="orp-goal"
    data-test="orp-goal"
  >
    <OrpBar
      :month="data.month"
      :count="data.count"
      :target="data.target"
      :due="data.due_date"
      card
      thick
    />
  </section>
  <section
    v-else
    class="orp-goal"
    data-test="orp-goal-missing"
  >
    <div>
      <h2>Indique ton objectif ORP</h2>
      <p>Le nombre de recherches que l’ORP te demande chaque mois. La barre se remplit à chaque candidature.</p>
      <RouterLink
        :to="{ path: '/reglages', query: { rubrique: 'recherche' } }"
        class="button-link"
      >
        Indiquer mon objectif
      </RouterLink>
    </div>
  </section>
</template>
