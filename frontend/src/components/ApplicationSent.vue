<script setup lang="ts">
import { computed } from "vue";

import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";
import MomentScreen from "./MomentScreen.vue";

// « Candidature envoyée. » (maquette CandidatureEnvoyee, §15 du 9 novembre) : après « J'ai postulé » dans Ma
// candidature ou « Marquer comme envoyée », quand l'objectif ORP du mois n'est pas atteint (sinon « C'est
// fait ! »). Les 4 personnages du logo (scène « envoyee »), ce qui compte pour l'ORP, la relance prévue s'il y en
// a une, puis « Voir mes candidatures » et « Préparer la prochaine ». « Je n'ai pas postulé » reste, en lien
// discret, quand la vue sait l'annuler.
const props = withDefaults(
  defineProps<{
    title: string;
    company: string;
    count?: number | null;
    target?: number | null;
    followUpOn?: string | null;
    cancellable?: boolean;
    // La candidature enregistrée, et si l'adresse de l'entreprise y manque (corrections du 13.11 au soir, §8).
    applicationId?: number | null;
    addressMissing?: boolean;
  }>(),
  { count: null, target: null, followUpOn: null, cancellable: false, applicationId: null, addressMissing: false },
);
// `leave` : un des deux liens est suivi (la vue qui reste sur la même adresse referme l'écran).
const emit = defineEmits<{ cancel: []; leave: [] }>();

const searches = computed(() => {
  if (props.count === null) return "";
  const n = `${props.count} ${props.count <= 1 ? "recherche" : "recherches"}`;
  return props.target ? `${n} sur ${props.target}` : n;
});
</script>

<template>
  <MomentScreen
    scene="envoyee"
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
    <!-- §8 (MaCandidatureV2 « finadresse », CandidatureEnvoyeeOrdinateur « adr ») : seulement si l’adresse manque,
         jamais bloquant. « Ajouter » ouvre « Modifier la candidature », le curseur dans l’adresse : c’est celle de la
         candidature que lit le suivi ORP (décision de Kevin du 14.11). -->
    <div
      v-if="addressMissing && applicationId"
      class="sent-address"
      data-test="sent-address"
    >
      <AppIcon
        name="pin"
        class="sent-address-icon"
      />
      <span class="sent-address-text">
        <strong>Il manque l’adresse de l’entreprise</strong>
        <span>Il la faut pour ton suivi ORP</span>
      </span>
      <RouterLink
        :to="{ path: '/candidatures/suivi', query: { candidature: String(applicationId), modifier: 'adresse' } }"
        class="sent-address-add"
        data-test="sent-address-add"
        @click="emit('leave')"
      >
        Ajouter<span class="visually-hidden"> l’adresse de l’entreprise</span>
      </RouterLink>
    </div>
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
        Je n’ai pas postulé
      </button>
    </template>
  </MomentScreen>
</template>

<style scoped>
/* La ligne « Il manque l'adresse de l'entreprise » (valeurs du HTML des planches) : un filet au-dessus, l'épingle
   brune de 24 px, le texte à gauche, « Ajouter » à droite sur une zone de 44 px. */
.sent-address { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; width: min(100%, 440px); min-height: 64px; margin-top: var(--space-2); border-top: 1px solid var(--line); text-align: left; }
.sent-address-icon { flex: none; width: 24px; height: 24px; color: var(--peach-text); }
.sent-address-text { flex: 1; min-width: 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.sent-address-text strong { display: block; font-size: var(--font-label); color: var(--text); }
.sent-address-add { flex: none; display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
</style>
