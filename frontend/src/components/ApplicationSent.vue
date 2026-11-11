<script setup lang="ts">
import { computed } from "vue";

import { usePhone } from "../composables/usePhone";
import { dateInSentence, dateWithTime } from "../dates";
import AppIcon from "./AppIcon.vue";
import MomentScreen from "./MomentScreen.vue";
import OrpBar from "./OrpBar.vue";

// « Candidature envoyée. » : après « J'ai postulé » dans Ma candidature ou « Marquer comme envoyée », quand
// l'objectif ORP du mois n'est pas atteint (sinon « C'est fait ! »).
// Lot du 11 novembre au soir, PR 51 (maquettes CandidatureEnvoyeeOrdinateur ; MaCandidatureV2, états `fin` et
// `finpreuve`) : sous le titre et le poste, la barre ORP mise à jour (PR 48), la preuve pour l'ORP, la relance
// prévue. Sur ordinateur, une carte de 480 px sous « Candidature envoyée. » ; sur téléphone, l'écran de fin de Ma
// candidature (bande bleue, illustration, « Envoyée ! » manuscrit), les lignes, le pied collé en bas.
// La preuve : jobA1 n'envoie pas l'e-mail et ne garde pas de pièce par candidature. La ligne dit donc ce qui existe :
// la recherche est enregistrée dans les justificatifs du mois (« gardée ») ou il lui manque un champ (« Il manque… »,
// avec le lien qui ouvre la candidature pour le compléter).
// « Je n'ai pas postulé » reste, en lien discret, quand la vue sait l'annuler.
const props = withDefaults(
  defineProps<{
    title: string;
    company: string;
    month?: string | null;
    count?: number | null;
    target?: number | null;
    due?: string | null;
    followUpOn?: string | null;
    /** Ce qui manque à la ligne des justificatifs ; `null` : inconnu, pas de ligne « preuve ». */
    missing?: string[] | null;
    savedAt?: string | null;
    applicationId?: number | null;
    cancellable?: boolean;
  }>(),
  { month: null, count: null, target: null, due: null, followUpOn: null, missing: null, savedAt: null, applicationId: null, cancellable: false },
);
// `leave` : un des deux liens est suivi (la vue qui reste sur la même adresse referme l'écran).
const emit = defineEmits<{ cancel: []; leave: [] }>();
const { phone } = usePhone();

const bar = computed(() => (props.month && props.count !== null && props.target ? { month: props.month, count: props.count, target: props.target } : null));
const lacking = computed(() => (props.missing ?? []).map((m) => m.replace(/'/g, "’")).join(", "));
const complete = computed(() => ({ path: "/candidatures/suivi", query: props.applicationId ? { candidature: String(props.applicationId) } : {} }));
</script>

<template>
  <!-- Téléphone (MaCandidatureV2, état `fin`). -->
  <section
    v-if="phone"
    class="sent-screen sent-fin"
    data-test="sent-moment"
  >
    <div
      class="sent-fin-band"
      role="status"
    >
      <div class="sent-fin-top">
        <RouterLink
          to="/candidatures/suivi"
          class="sent-fin-back"
          aria-label="Voir mes candidatures"
          @click="emit('leave')"
        >
          <AppIcon name="arrow-left" />
        </RouterLink>
      </div>
      <img
        class="sent-fin-image"
        src="/tri/envoyee.webp"
        alt=""
        width="240"
        height="122"
      >
      <h1 class="sent-fin-title">
        <span class="sent-fin-hand">Envoyée&#8239;!</span>
      </h1>
      <p class="sent-fin-offer">
        {{ title }} · {{ company }}
      </p>
    </div>
    <div
      v-if="bar"
      class="sent-fin-orp"
    >
      <OrpBar
        v-bind="bar"
        :due="due"
        card
      />
    </div>
    <ul class="sent-rows">
      <li
        v-if="missing && !missing.length"
        data-test="sent-proof"
      >
        <span
          class="sent-row-ok"
          aria-hidden="true"
        ><AppIcon name="tick" /></span>
        <span class="sent-row-text"><b>Preuve pour l’ORP gardée</b><span v-if="savedAt">Enregistrée {{ dateWithTime(savedAt) }}</span></span>
      </li>
      <li
        v-else-if="missing"
        data-test="sent-proof-missing"
      >
        <AppIcon
          name="alert-circle"
          class="sent-row-warn"
        />
        <span class="sent-row-text"><b>Il manque la preuve pour l’ORP</b><span>À compléter&#8239;: {{ lacking }}</span></span>
        <RouterLink
          :to="complete"
          class="sent-row-action"
          data-test="sent-proof-add"
          @click="emit('leave')"
        >
          Compléter
        </RouterLink>
      </li>
      <li
        v-if="followUpOn"
        data-test="sent-follow-up"
      >
        <AppIcon
          name="clock"
          class="sent-row-icon"
        />
        <span class="sent-row-text"><b>Relance prévue {{ dateInSentence(followUpOn) }}</b><span>jobA1 te la prépare</span></span>
      </li>
    </ul>
    <footer class="sent-fin-foot">
      <RouterLink
        to="/candidatures/offres"
        class="sent-fin-primary"
        data-test="next-offer"
        @click="emit('leave')"
      >
        Préparer la suivante
      </RouterLink>
      <RouterLink
        to="/candidatures/suivi"
        class="sent-fin-link"
        data-test="sent-applications"
        @click="emit('leave')"
      >
        Voir mes candidatures
      </RouterLink>
      <button
        v-if="cancellable"
        type="button"
        class="link sent-fin-cancel"
        data-test="cancel-applied"
        @click="emit('cancel')"
      >
        Je n’ai pas postulé
      </button>
    </footer>
  </section>
  <!-- Ordinateur (CandidatureEnvoyeeOrdinateur). -->
  <MomentScreen
    v-else
    scene="envoyee"
    title="Candidature"
    hand="envoyée."
    data-test="sent-moment"
  >
    <p>
      {{ title }} chez {{ company }}.
    </p>
    <div
      v-if="bar || missing || followUpOn"
      class="sent-card"
      data-test="sent-card"
    >
      <OrpBar
        v-if="bar"
        v-bind="bar"
        :due="due"
        card
      />
      <ul class="sent-rows">
        <li
          v-if="missing && !missing.length"
          data-test="sent-proof"
        >
          <span
            class="sent-row-ok"
            aria-hidden="true"
          ><AppIcon name="tick" /></span>
          <span class="sent-row-text"><b>Preuve pour l’ORP gardée</b><span v-if="savedAt">Enregistrée {{ dateWithTime(savedAt) }}</span></span>
        </li>
        <li
          v-else-if="missing"
          data-test="sent-proof-missing"
        >
          <AppIcon
            name="alert-circle"
            class="sent-row-warn"
          />
          <span class="sent-row-text"><b>Il manque la preuve pour l’ORP</b><span>À compléter&#8239;: {{ lacking }}</span></span>
          <RouterLink
            :to="complete"
            class="sent-row-action"
            data-test="sent-proof-add"
            @click="emit('leave')"
          >
            Compléter
          </RouterLink>
        </li>
        <li
          v-if="followUpOn"
          data-test="sent-follow-up"
        >
          <AppIcon
            name="clock"
            class="sent-row-icon"
          />
          <span class="sent-row-text"><b>Relance prévue {{ dateInSentence(followUpOn) }}</b><span>jobA1 te la prépare</span></span>
        </li>
      </ul>
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

<style>
/* Les lignes (les deux écrans) : pastille verte à coche ou icône de 24 px, titre 15 gras, détail 14 gris, 12 px
   d'écart ; 64 px au moins sur téléphone (trait #E5E2D9), 60 px dans la carte de l'ordinateur (trait #ECE9E1). */
.sent-rows { --sent-ok: #1F7A4D; --sent-warn: #8A4A12; --sent-rule: #E5E2D9; --sent-64: 64px; --sent-60: 60px; --sent-15: 0.9375rem; list-style: none; margin: 0; padding: 0; text-align: left; }
:root[data-theme="dark"] .sent-rows { --sent-ok: #7FD3A6; --sent-warn: #F3B08A; --sent-rule: #38322B; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .sent-rows { --sent-ok: #7FD3A6; --sent-warn: #F3B08A; --sent-rule: #38322B; } }
.sent-rows > li { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-64); border-top: 1px solid var(--sent-rule); }
.sent-row-ok { flex: none; display: flex; align-items: center; justify-content: center; width: var(--space-6); height: var(--space-6); border-radius: 50%; background: var(--sent-ok); color: var(--bg); }
.sent-row-ok .icon { width: var(--space-4); height: var(--space-4); stroke-width: 3; }
.sent-rows .sent-row-icon, .sent-rows .sent-row-warn { flex: none; width: var(--space-6); height: var(--space-6); color: var(--text-lead); }
.sent-rows .sent-row-warn { color: var(--sent-warn); }
.sent-row-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.sent-row-text b { font-size: var(--sent-15); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--text); }
.sent-row-text span { font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.sent-row-action { flex: none; display: inline-flex; align-items: center; min-height: var(--target-min); font-size: var(--sent-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
/* Ordinateur : la carte de 480 px, bordure 1 px #E5E2D9, rayon 18, 16 px 20 px 4 px ; 16 px entre la barre et les lignes. */
.sent-card { --sent-card-w: 480px; --sent-card-line: #E5E2D9; --sent-card-rule: #ECE9E1; --sent-18: 18px; box-sizing: border-box; width: min(100%, var(--sent-card-w)); margin-top: var(--space-6); padding: var(--space-4) var(--space-5) var(--space-1); border: 1px solid var(--sent-card-line); border-radius: var(--sent-18); background: var(--surface); text-align: left; }
:root[data-theme="dark"] .sent-card { --sent-card-line: #38322B; --sent-card-rule: #2C2722; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .sent-card { --sent-card-line: #38322B; --sent-card-rule: #2C2722; } }
.sent-card .sent-rows { margin-top: var(--space-4); }
.sent-card .sent-rows > li { min-height: var(--sent-60); border-top-color: var(--sent-card-rule); }
.sent-card .sent-rows:first-child { margin-top: 0; }
.sent-card .sent-rows:first-child > li:first-child { border-top: 0; }
/* Téléphone : la bande bleue (#E8ECFB, rayon 32 en bas, 20 px dessous), l'en-tête de 56 px, l'illustration de 240 px,
   « Envoyée ! » en Caveat Brush 48 penché de -4°, le poste 16 px 8 px dessous ; la barre ORP à 24 px des bords ; le
   pied collé en bas (trait #ECE9E1, 12 px 20 px 28 px), bouton plein de 52 px puis lien de 48 px. */
.sent-fin { --fin-band: #E8ECFB; --fin-ink: #1A3496; --fin-rule: #ECE9E1; --fin-56: 56px; --fin-48: 3rem; --fin-52: 52px; --fin-26: 26px; --fin-32: 32px; --fin-28: 28px; --fin-240: 240px; --fin-15: 0.9375rem; display: flex; flex-direction: column; color: var(--text); }
:root[data-theme="dark"] .sent-fin { --fin-band: #232B45; --fin-ink: #AEBDFF; --fin-rule: #2C2722; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .sent-fin { --fin-band: #232B45; --fin-ink: #AEBDFF; --fin-rule: #2C2722; } }
.sent-fin-band { flex: none; padding-bottom: var(--space-5); border-radius: 0 0 var(--fin-32) var(--fin-32); background: var(--fin-band); text-align: center; }
.sent-fin-top { display: flex; align-items: center; height: var(--fin-56); padding: 0 var(--space-1); }
.sent-fin-back { display: flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); color: var(--text); }
.sent-fin-back .icon { width: var(--space-6); height: var(--space-6); }
.sent-fin-image { display: block; width: var(--fin-240); height: auto; margin: 0 auto; }
.sent-fin-title { margin: var(--space-1) 0 0; font-size: var(--fin-48); line-height: var(--fin-48); font-weight: var(--weight-regular); }
.sent-fin-hand { display: inline-block; font-family: var(--font-hand); color: var(--fin-ink); transform: rotate(-4deg); }
.sent-fin-offer { margin: var(--space-2) var(--space-6) 0; font-size: var(--font-body); line-height: var(--space-6); color: var(--text-lead); }
.sent-fin-orp { padding: var(--space-6) var(--space-6) var(--space-4); }
.sent-fin > .sent-rows { margin: 0 var(--space-6); }
.sent-fin-foot { position: sticky; bottom: 0; display: flex; flex-direction: column; margin-top: auto; padding: var(--space-3) var(--space-5) calc(var(--fin-28) + env(safe-area-inset-bottom)); border-top: 1px solid var(--fin-rule); background: var(--bg); }
.sent-fin-primary { display: flex; align-items: center; justify-content: center; height: var(--fin-52); border-radius: var(--fin-26); background: var(--action); color: var(--on-action); font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none; }
.sent-fin-link { display: flex; align-items: center; justify-content: center; height: var(--fin-48); margin-top: var(--space-1); font-size: var(--fin-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.sent-fin .sent-fin-foot button.sent-fin-cancel { align-self: center; min-height: var(--target-min); color: var(--text-secondary); font-weight: var(--weight-regular); }
/* Les personnages gardent leur trait sombre sur la bande bleu nuit. */
:root[data-theme="dark"] .sent-fin-image { filter: drop-shadow(0 0 1px rgb(243 238 230 / 55%)); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .sent-fin-image { filter: drop-shadow(0 0 1px rgb(243 238 230 / 55%)); } }
</style>
