<script setup lang="ts">
import { computed } from "vue";

import { dateInSentence } from "../dates";
import { formatMonth } from "../format";
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import MomentScreen from "./MomentScreen.vue";
import TroupeScene from "./TroupeScene.vue";

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
  <section
    v-if="desk"
    class="sent-desk"
    data-test="sent-moment"
  >
    <div
      class="sent-desk-body"
      role="status"
    >
      <TroupeScene
        scene="envoyee"
        full
      />
      <h1 class="sent-desk-title">
        Candidature <span class="sent-desk-hand">envoyée.</span>
      </h1>
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
      <div class="sent-desk-actions">
        <RouterLink
          to="/candidatures/suivi"
          class="sent-desk-button"
          data-test="sent-applications"
          @click="emit('leave')"
        >
          Voir mes candidatures
        </RouterLink>
        <RouterLink
          to="/candidatures/offres"
          class="sent-desk-button sent-desk-button-primary"
          data-test="next-offer"
          @click="emit('leave')"
        >
          Préparer la prochaine
        </RouterLink>
      </div>
      <button
        v-if="cancellable"
        type="button"
        class="link sent-desk-cancel"
        data-test="cancel-applied"
        @click="emit('cancel')"
      >
        Je n’ai pas postulé
      </button>
    </div>
  </section>
  <MomentScreen
    v-else
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

/* Ordinateur : valeurs du HTML de CandidatureEnvoyeeOrdinateur (13.11). Colonne de 880 px, contenu centré ; scène de
   471 px ; titre 34/42 en 800, fin manuscrite à 1,45 em ; phrase 18/28 ; carte de 480 px (padding 16/20/4, bordure 1 px,
   rayon 18) ; barre de 12 px ; lignes de 60 px séparées d'un filet ; boutons de 44 px, 10 px d'écart. */
.sent-desk { --sd-880: 880px; --sd-471: 471px; --sd-480: 480px; --sd-560: 560px; --sd-34: 34px; --sd-42: 42px; --sd-18: 18px; --sd-28: 28px; --sd-12: 12px; --sd-60: 60px; --sd-10: 10px; --sd-20: 20px; --sd-24: 24px; --sd-48: 48px;
  box-sizing: border-box; width: min(100%, var(--sd-880)); margin: 0 auto; padding: var(--sd-24) 0 var(--sd-48); color: var(--text); }
.sent-desk-body { display: flex; flex-direction: column; align-items: center; text-align: center; padding-bottom: var(--space-2); }
.sent-desk-title { margin: var(--sd-24) 0 0; font-size: var(--sd-34); line-height: var(--sd-42); font-weight: var(--weight-heavy); letter-spacing: normal; }
.sent-desk-hand { font-family: var(--font-hand); font-weight: var(--weight-regular); font-size: 1.45em; line-height: 0; color: var(--primary-graphic); }
.sent-desk-line { max-width: var(--sd-560); margin: var(--sd-12) 0 0; font-size: var(--sd-18); line-height: var(--sd-28); color: var(--text-lead); }
.sent-desk-card { box-sizing: border-box; width: min(100%, var(--sd-480)); margin-top: var(--sd-24); padding: var(--space-4) var(--sd-20) var(--space-1); border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface); text-align: left; }
.sent-desk-month { display: flex; justify-content: space-between; gap: var(--space-3); margin: 0; font-size: var(--font-body); font-weight: var(--weight-bold); }
.sent-desk-bar { height: var(--sd-12); margin-top: var(--sd-12); border-radius: var(--radius-pill); background: var(--primary-soft); overflow: hidden; }
.sent-desk-bar > span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--primary-graphic); }
.sent-desk-left { margin: var(--sd-12) 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-lead); }
.sent-desk-month + .sent-desk-bar:last-child, .sent-desk-month:last-child { margin-bottom: var(--sd-12); }
.sent-desk-row { display: flex; align-items: center; gap: var(--sd-12); min-height: var(--sd-60); border-top: 1px solid var(--surface-muted); }
.sent-desk-card > .sent-desk-row:first-child { border-top: 0; }
.sent-desk-icon { flex: none; width: var(--sd-24); height: var(--sd-24); color: var(--text); }
.sent-desk-icon-pin { color: var(--peach-text); }
.sent-desk-text { flex: 1; min-width: 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.sent-desk-text > * { display: block; }
.sent-desk-text strong { font-size: var(--font-label); color: var(--text); }
.sent-desk-add { flex: none; display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.sent-desk-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: var(--sd-10); margin-top: var(--sd-20); }
.sent-desk-button { box-sizing: border-box; display: inline-flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-4); border: 1.5px solid var(--card-line); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-semibold); text-decoration: none; white-space: nowrap; }
.sent-desk-button-primary { padding: 0 var(--sd-20); border-color: transparent; background: var(--action); color: var(--on-action); font-weight: var(--weight-bold); }
.sent-desk-cancel { min-height: var(--target-min); margin-top: var(--space-2); color: var(--text-secondary); font-weight: var(--weight-regular); }
</style>
