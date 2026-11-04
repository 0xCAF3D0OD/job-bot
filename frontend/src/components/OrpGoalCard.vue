<script setup lang="ts">
import { computed } from "vue";

import type { OrpMonth } from "../api/client";
import { plural } from "../format";
import LiquidCircle from "./LiquidCircle.vue";

// L'objectif ORP du mois (docs/139 étape 8, maquettes Explorer et Orp ; B3, B4, Kevin, 2026-11-04) : le cercle
// liquide, ce qui reste à faire et l'échéance (la fin du mois suivi). Sans objectif saisi, la carte invite à
// l'indiquer au lieu d'un « 0 sur 0 ». « Recherches » est le mot du formulaire de l'ORP (B5).
const props = defineProps<{ data: OrpMonth }>();

const LONG_DAY = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
const deadline = computed(() => {
  const [year, month] = props.data.month.split("-").map(Number);
  return LONG_DAY.format(new Date(year!, month!, 0));
});
const left = computed(() => (props.data.target ?? 0) - props.data.count);
const title = computed(() => (left.value > 0 ? `${plural(left.value, "recherche", "recherches")} à faire` : "Objectif du mois atteint"));
</script>

<template>
  <section
    v-if="data.target"
    class="orp-goal"
    data-test="orp-goal"
  >
    <LiquidCircle
      :count="data.count"
      :target="data.target"
      :size="112"
    />
    <div>
      <h2>{{ title }}</h2>
      <p>Objectif fixé avec l'ORP. Échéance le {{ deadline }}.</p>
    </div>
  </section>
  <section
    v-else
    class="orp-goal"
    data-test="orp-goal-missing"
  >
    <div>
      <h2>Indique ton objectif ORP</h2>
      <p>Le nombre de recherches que l'ORP te demande chaque mois. Le cercle se remplit à chaque candidature.</p>
      <RouterLink
        :to="{ path: '/reglages', query: { rubrique: 'recherche' } }"
        class="button-link"
      >
        Indiquer mon objectif
      </RouterLink>
    </div>
  </section>
</template>
