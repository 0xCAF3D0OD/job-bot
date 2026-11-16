<script setup lang="ts">
import { computed } from "vue";

import { dateInSentence } from "../dates";
import { formatMonth } from "../format";
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import MomentScreen from "./MomentScreen.vue";

// « Candidature envoyée. » : après « J'ai postulé » dans Ma candidature ou « Marquer comme envoyée », quand
// l'objectif ORP du mois n'est pas atteint (sinon « C'est fait ! »).
// Sur ordinateur, l'écran est refait d'après la planche CandidatureEnvoyeeOrdinateur du 13 novembre (règle de Kevin
// du 14.11 : refaire le visuel à partir de la planche) : la scène, le titre, la phrase, la carte « Mois ORP » (barre,
// échéance, relance prévue, adresse manquante), puis « Voir mes candidatures » et « Préparer la prochaine ».
// La ligne « Preuve pour l'ORP gardée » de la planche n'est pas affichée : jobA1 n'a pas cette donnée.
// Sur téléphone, l'écran reste celui de MomentScreen (maquette CandidatureEnvoyee), refait plus tard avec le téléphone.
// « Je n'ai pas postulé » (absent de la planche) reste en lien discret, quand la vue sait l'annuler.
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
    // Le mois ORP de la candidature (« 2026-11 ») et le jour où remettre ses justificatifs.
    month?: string | null;
    dueDate?: string | null;
  }>(),
  { count: null, target: null, followUpOn: null, cancellable: false, applicationId: null, addressMissing: false, month: null, dueDate: null },
);
// `leave` : un des deux liens est suivi (la vue qui reste sur la même adresse referme l'écran).
const emit = defineEmits<{ cancel: []; leave: [] }>();

const { phone: desk } = usePhone("(min-width: 1024px)");

const searches = computed(() => {
  if (props.count === null) return "";
  const n = `${props.count} ${props.count <= 1 ? "recherche" : "recherches"}`;
  return props.target ? `${n} sur ${props.target}` : n;
});

// La carte « Mois ORP » : « 8 sur 10 », la barre, « Encore 2 d'ici le 5 décembre ».
const monthName = computed(() => (props.month ? formatMonth(props.month).split(" ")[0]!.toLowerCase() : ""));
const ratio = computed(() => (props.count !== null && props.target ? Math.min(1, props.count / props.target) : null));
const remaining = computed(() => {
  if (props.count === null || !props.target) return "";
  const left = props.target - props.count;
  if (left <= 0) return "";
  return props.dueDate ? `Encore ${left} d’ici ${dateInSentence(`${props.dueDate}T12:00:00`)}` : `Encore ${left} ce mois`;
});
const addressRow = computed(() => props.addressMissing && props.applicationId !== null);
const showCard = computed(() => props.count !== null || !!props.followUpOn || addressRow.value);
</script>

<template>
  <MomentScreen
    scene="envoyee"
    title="Candidature"
    hand="envoyée."
    :class="{ 'sent-desk': desk }"
    data-test="sent-moment"
  >
    <template v-if="desk">
      <p class="sent-desk-line">
        {{ title }} chez {{ company }}.
      </p>
      <div
        v-if="showCard"
        class="sent-desk-card"
      >
        <template v-if="count !== null">
          <p class="sent-desk-month">
            <span>Mois ORP<template v-if="monthName"> · {{ monthName }}</template></span>
            <span data-test="sent-orp">{{ target ? `${count} sur ${target}` : searches }}</span>
          </p>
          <div
            v-if="ratio !== null"
            class="sent-desk-bar"
            aria-hidden="true"
          >
            <span :style="{ width: `${Math.round(ratio * 100)}%` }" />
          </div>
          <p
            v-if="remaining"
            class="sent-desk-left"
            data-test="sent-orp-left"
          >
            {{ remaining }}
          </p>
        </template>
        <div
          v-if="followUpOn"
          class="sent-desk-row"
          data-test="sent-follow-up"
        >
          <AppIcon
            name="clock"
            class="sent-desk-icon"
          />
          <span class="sent-desk-text">
            <strong>Relance prévue {{ dateInSentence(`${followUpOn}T12:00:00`) }}</strong>
            <span>jobA1 te la prépare</span>
          </span>
        </div>
        <div
          v-if="addressRow"
          class="sent-desk-row"
          data-test="sent-address"
        >
          <AppIcon
            name="pin"
            class="sent-desk-icon sent-desk-icon-pin"
          />
          <span class="sent-desk-text">
            <strong>Il manque l’adresse de l’entreprise</strong>
            <span>Il la faut pour ton suivi ORP</span>
          </span>
          <RouterLink
            :to="{ path: '/candidatures/suivi', query: { candidature: String(applicationId), modifier: 'adresse' } }"
            class="sent-desk-add"
            data-test="sent-address-add"
            @click="emit('leave')"
          >
            Ajouter<span class="visually-hidden"> l’adresse de l’entreprise</span>
          </RouterLink>
        </div>
      </div>
    </template>
    <template v-else>
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
      <!-- §8 (MaCandidatureV2 « finadresse ») : seulement si l’adresse manque, jamais bloquant. « Ajouter » ouvre
           « Modifier la candidature », le curseur dans l’adresse (décision de Kevin du 14.11). -->
      <div
        v-if="addressRow"
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
    </template>
    <!-- Sur ordinateur, MomentScreen range les deux liens côte à côte : « Voir mes candidatures » au contour, puis
         « Préparer la prochaine » plein (planche) ; « Je n’ai pas postulé » dessous. -->
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
/* Téléphone : la ligne « Il manque l'adresse de l'entreprise » (valeurs du HTML des planches). */
.sent-address { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; width: min(100%, 440px); min-height: 64px; margin-top: var(--space-2); border-top: 1px solid var(--line); text-align: left; }
.sent-address-icon { flex: none; width: 24px; height: 24px; color: var(--peach-text); }
.sent-address-text { flex: 1; min-width: 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.sent-address-text strong { display: block; font-size: var(--font-label); color: var(--text); }
.sent-address-add { flex: none; display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }

/* Ordinateur : valeurs du HTML de CandidatureEnvoyeeOrdinateur (13.11). MomentScreen donne la colonne de 880 px, la
   scène de 471 px, le titre 34/42 et sa fin manuscrite ; ici la phrase 18/28 en gris de tête, la carte de 480 px
   (padding 16/20/4, bordure 1 px, rayon 18), la barre de 12 px, les lignes de 60 px séparées d'un filet, et 20 px
   au-dessus des boutons. */
/* La règle globale « .sent-screen » (écran poussé du détail sur téléphone, style.css) fixait l'écran par-dessus
   l'en-tête : sur ordinateur il reste dans la page, sous l'en-tête et le bandeau (comme TriageDone). */
.sent-desk { --sd-480: 480px; --sd-12: 12px; --sd-60: 60px; --sd-20: 20px; --sd-24: 24px; position: static; overflow: visible; background: none; }
.sent-desk :deep(.sent-screen-actions) { padding-top: var(--sd-20); }
.sent-desk .sent-screen-cancel { justify-content: center; text-align: center; }
.sent-desk .sent-desk-line { color: var(--text-lead); }
.sent-desk-card { box-sizing: border-box; width: min(100%, var(--sd-480)); margin-top: var(--sd-24); padding: var(--space-4) var(--sd-20) var(--space-1); border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface); text-align: left; }
.sent-desk-card p.sent-desk-month { display: flex; justify-content: space-between; gap: var(--space-3); max-width: none; margin: 0; font-size: var(--font-body); line-height: var(--space-6); font-weight: var(--weight-bold); color: var(--text); }
.sent-desk-bar { height: var(--sd-12); margin: var(--sd-12) 0; border-radius: var(--radius-pill); background: var(--primary-soft); overflow: hidden; }
.sent-desk-bar > span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--primary-graphic); }
.sent-desk-card p.sent-desk-left { max-width: none; margin: 0 0 var(--sd-12); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); }
.sent-desk-row { display: flex; align-items: center; gap: var(--sd-12); min-height: var(--sd-60); border-top: 1px solid var(--surface-muted); }
.sent-desk-card > .sent-desk-row:first-child { border-top: 0; }
.sent-desk-icon { flex: none; width: var(--sd-24); height: var(--sd-24); color: var(--text); }
.sent-desk-icon-pin { color: var(--peach-text); }
.sent-desk-text { flex: 1; min-width: 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.sent-desk-text > * { display: block; }
.sent-desk-text strong { font-size: var(--font-label); color: var(--text); }
.sent-desk-add { flex: none; display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
</style>
