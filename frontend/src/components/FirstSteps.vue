<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import type { Today } from "../api/client";
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";
import FaceTile from "./FaceTile.vue";
import IconButton from "./IconButton.vue";

// Les premiers pas (docs/128 §1) : en haut d'Aujourd'hui, une seule prochaine action. Le titre
// de l'étape, pourquoi, le bouton ; « 2 sur 5 » et les cinq points. Alertes créées sans offre
// encore : on dit qu'elles arrivent, et on propose d'en ajouter une vue ailleurs.
type Key = Today["first_steps"][number]["key"];
const props = defineProps<{
  steps: Today["first_steps"];
  hasOffers: boolean;
  offerId: number | null;
  // Des offres du jour sont affichées plus bas : l'étape 3 y descend.
  pickReady: boolean;
}>();
const emit = defineEmits<{ dismiss: [] }>();

// Les titres sont des noms (docs/interface.md, Titres 2) ; l'action est sur le bouton.
const STEPS: Record<Key, { title: string; why: string; action: string; icon: IconName }> = {
  profile: { title: "Critères et CV", why: "jobA1 trie les offres avec tes critères.", action: "Compléter mon profil", icon: "user" },
  alerts: { title: "Alertes sur les sites d'emploi", why: "Les offres arrivent ici, notées pour toi.", action: "Créer mes alertes", icon: "bell" },
  keep: { title: "Première offre gardée", why: "Celles qui te vont passent en « À préparer ».", action: "Voir les offres du jour", icon: "briefcase" },
  prepare: { title: "Lettre et CV pour l'offre", why: "Adaptés à l'offre gardée, en quelques minutes.", action: "Préparer", icon: "mail" },
  sent: { title: "Candidature envoyée", why: "Marque-la comme envoyée : elle compte pour ton mois ORP.", action: "Ouvrir la préparation", icon: "send" },
};

const doneCount = computed(() => props.steps.filter((s) => s.done).length);
const next = computed(() => props.steps.find((s) => !s.done) ?? null);
const position = computed(() => (next.value ? props.steps.indexOf(next.value) + 1 : props.steps.length));
// Les alertes sont prêtes, mais aucune offre n'est encore arrivée.
const waiting = computed(() => next.value?.key === "keep" && !props.hasOffers);

const target = computed<RouteLocationRaw>(() => {
  const preparation = props.offerId ? `/candidatures/offres/${props.offerId}/preparer` : "/candidatures/offres";
  switch (next.value?.key) {
    case "profile":
      return "/profil";
    case "alerts":
      return "/candidatures/alertes";
    case "keep":
      // Le tri du jour a son écran (1.6.50) : « Garder » s'y fait.
      return props.pickReady ? { name: "triage" } : "/candidatures/offres";
    case "prepare":
      return preparation;
    default:
      return props.offerId ? { path: preparation, query: { doc: "postuler" } } : "/candidatures/offres";
  }
});
</script>

<template>
  <section
    v-if="next"
    class="dash-card first-steps"
    aria-labelledby="first-steps-title"
    data-test="first-steps"
    :data-step="next.key"
  >
    <FaceTile
      :mood="waiting ? 'neutre' : 'content'"
      :waiting="waiting"
    />
    <div class="first-steps-body">
      <div class="first-steps-head">
        <p class="first-steps-count">
          Premiers pas · {{ position }} sur {{ steps.length }}
        </p>
        <IconButton
          icon="close"
          label="Masquer les premiers pas"
          data-test="first-steps-dismiss"
          @click="emit('dismiss')"
        />
      </div>
      <template v-if="waiting">
        <h2 id="first-steps-title">
          Alertes prêtes
        </h2>
        <p class="first-steps-why">
          Les premières offres arrivent d'ici un ou deux jours.
        </p>
        <RouterLink
          :to="{ path: '/candidatures/offres', query: { ajouter: '1' } }"
          class="button-link primary-link first-steps-action"
          data-test="first-steps-add"
        >
          <span class="with-icon"><AppIcon name="plus" />Ajouter une offre que j'ai vue</span>
        </RouterLink>
      </template>
      <template v-else>
        <h2 id="first-steps-title">
          {{ STEPS[next.key].title }}
        </h2>
        <p class="first-steps-why">
          {{ STEPS[next.key].why }}
        </p>
        <RouterLink
          :to="target"
          class="button-link primary-link first-steps-action"
          data-test="first-steps-action"
        >
          <span class="with-icon"><AppIcon :name="STEPS[next.key].icon" />{{ STEPS[next.key].action }}</span>
        </RouterLink>
      </template>
      <!-- Les cinq points, lus en une phrase. -->
      <div
        class="first-steps-dots"
        role="img"
        :aria-label="`${doneCount} étapes faites sur ${steps.length}`"
      >
        <span
          v-for="step in steps"
          :key="step.key"
          :class="{ done: step.done, current: step === next }"
          :data-test="`first-step-${step.key}`"
        />
      </div>
    </div>
  </section>
</template>
