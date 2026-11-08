<script setup lang="ts">
import { computed } from "vue";

import { dateInSentence } from "../dates";
import MomentScreen from "./MomentScreen.vue";

// « Candidature envoyée. » (maquette CandidatureEnvoyee du 6.11, docs/141, 8) : après « J'ai postulé » dans Ma
// candidature ou « Marquer comme envoyée », quand l'objectif ORP du mois n'est pas atteint (sinon « C'est
// fait ! »). Le personnage à l'avion, ce qui compte pour l'ORP, la relance prévue s'il y en a une, puis « Voir
// mes candidatures » et « Préparer la prochaine ». « Je n'ai pas postulé » reste, en lien discret, quand la vue
// sait l'annuler.
const props = withDefaults(
  defineProps<{
    title: string;
    company: string;
    count?: number | null;
    target?: number | null;
    followUpOn?: string | null;
    cancellable?: boolean;
  }>(),
  { count: null, target: null, followUpOn: null, cancellable: false },
);
// `leave` : un des deux liens est suivi (la vue qui reste sur la même adresse referme l'écran).
const emit = defineEmits<{ cancel: []; leave: [] }>();

const searches = computed(() => {
  if (props.count === null) return "";
  const n = `${props.count} ${props.count === 1 ? "recherche" : "recherches"}`;
  return props.target ? `${n} sur ${props.target}` : n;
});
</script>

<template>
  <MomentScreen
    pose="avion"
    title="Candidature"
    hand="envoyée."
    data-test="sent-moment"
  >
    <p>
      {{ title }} chez {{ company }}.<template v-if="searches">
        Elle compte pour l’ORP : <strong data-test="sent-orp">{{ searches }}</strong> ce mois.
      </template>
    </p>
    <p
      v-if="followUpOn"
      class="sent-screen-small"
      data-test="sent-follow-up"
    >
      Relance prévue {{ dateInSentence(followUpOn) }} si pas de réponse.
    </p>
    <template #actions>
      <RouterLink
        to="/candidatures/suivi"
        class="button-link primary-link sent-screen-primary"
        data-test="sent-applications"
        @click="emit('leave')"
      >
        Voir mes candidatures
      </RouterLink>
      <RouterLink
        to="/candidatures/offres"
        class="goal-reached-home"
        data-test="next-offer"
        @click="emit('leave')"
      >
        Préparer la prochaine
      </RouterLink>
      <button
        v-if="cancellable"
        type="button"
        class="link sent-screen-cancel"
        data-test="cancel-applied"
        @click="emit('cancel')"
      >
        Je n'ai pas postulé
      </button>
    </template>
  </MomentScreen>
</template>
