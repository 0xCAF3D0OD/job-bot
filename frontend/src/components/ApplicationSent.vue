<script setup lang="ts">
import { computed } from "vue";

import { dateInSentence } from "../dates";
import BrandMark from "./BrandMark.vue";
import Illustration from "./Illustration.vue";

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
  <section
    class="sent-screen"
    data-test="sent-moment"
  >
    <header class="sent-screen-brand">
      <BrandMark :size="30" />
      <span>jobA1</span>
    </header>
    <div
      class="sent-screen-body"
      role="status"
    >
      <Illustration
        pose="avion"
        :height="280"
        full
      />
      <h1 class="sent-screen-title">
        Candidature envoyée.
      </h1>
      <p class="sent-screen-line">
        {{ title }} chez {{ company }}.<template v-if="searches">
          Elle compte pour l’ORP : <strong data-test="sent-orp">{{ searches }}</strong> ce mois.
        </template>
      </p>
      <p
        v-if="followUpOn"
        class="sent-screen-line sent-screen-small"
        data-test="sent-follow-up"
      >
        Relance prévue {{ dateInSentence(followUpOn) }} si pas de réponse.
      </p>
    </div>
    <div class="sent-screen-actions">
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
    </div>
  </section>
</template>

<style scoped>
/* Valeurs de la maquette CandidatureEnvoyee (390 px), ramenées aux échelles. */
.sent-screen { display: flex; flex-direction: column; min-height: 100dvh; max-width: 30rem; margin-inline: auto; box-sizing: border-box; color: var(--text); }
.sent-screen-brand { flex: none; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-5) var(--space-5) 0; font-size: var(--font-section); font-weight: var(--weight-bold); }
.sent-screen-body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); padding: 0 var(--space-6); text-align: center; }
.sent-screen-title { margin: var(--space-2) 0 0; font-size: var(--font-figure); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.3px; }
.sent-screen-line { margin: 0; max-width: 310px; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.sent-screen-line strong { color: var(--text); }
.sent-screen-small { margin-top: var(--space-1); font-size: var(--font-small); }
.sent-screen-actions { flex: none; display: grid; gap: var(--space-2); padding: var(--space-4) var(--space-5) var(--space-8); }
.sent-screen-primary { justify-content: center; width: 100%; min-height: var(--btn-primary); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
@media (min-width: 821px) { .sent-screen { min-height: 0; padding-block: var(--space-8); } .sent-screen-brand { display: none; } }
.sent-screen-cancel { justify-self: center; min-height: var(--target-min); color: var(--text-secondary); font-weight: var(--weight-regular); }
</style>
