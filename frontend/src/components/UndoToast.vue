<script setup lang="ts">
import { UNDO_MS, useUndo } from "../composables/useUndo";

// Le bandeau « Annuler » (docs/108 §1) : en bas, au-dessus de la barre d'onglets et du panneau de
// commande ; lu par les lecteurs d'écran ; Échap le ferme en validant l'action.
// `inline` : posé dans la page, entre le contenu et ses actions (le tri, planche « Tri et panneau de
// commande »), à partir de 600 px ; tant qu'il est là, celui d'App se cache. Sous 600 px, c'est
// l'inverse : le bandeau d'App, au-dessus du panneau. Un seul des deux est affiché, donc annoncé.
// Tous les bandeaux ont le trait qui se vide pendant UNDO_MS, la seule durée (§23 du 15.11 ; Kevin, 19.11) ; arrêté, plein, tant
// que la souris ou le focus est dessus, il repart de plein ensuite.
// `bar` : le bandeau de la page Trier (paquet du 13 novembre) : la page le place et le dessine (classe tri-toast) ;
// tant qu'il est là, celui d'App se cache.
const props = withDefaults(defineProps<{ inline?: boolean; bar?: boolean }>(), { inline: false, bar: false });
const { pending, undo, see, hold, release, flush } = useUndo();
</script>

<template>
  <div
    v-if="pending"
    :key="pending.id"
    :class="props.bar ? 'tri-toast' : ['toast', 'undo-toast', { inline }]"
    role="status"
    :data-test="bar ? 'triage-toast' : inline ? 'undo-inline' : 'undo-toast'"
    @mouseenter="hold"
    @mouseleave="release"
    @focusin="hold"
    @focusout="release"
    @keydown.esc="flush()"
  >
    <span>{{ pending.message }}</span>
    <button
      v-if="pending.see"
      type="button"
      :class="{ link: !bar }"
      data-test="undo-see"
      @click="see"
    >
      Voir
    </button>
    <button
      type="button"
      :class="{ link: !bar }"
      data-test="undo"
      @click="undo"
    >
      Annuler
    </button>
    <i
      class="toast-bar"
      :style="{ animationDuration: `${UNDO_MS}ms` }"
      aria-hidden="true"
    />
  </div>
</template>

<style>
/* « Voir » puis « Annuler », serrés à droite : seul le premier bouton pousse vers la droite (K5, 17.11). */
.undo-toast > button.link + button.link { margin-left: 0; }
</style>
