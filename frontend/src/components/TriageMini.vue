<script setup lang="ts">
import { computed, nextTick, ref, toRef, watch } from "vue";

import type { Offer } from "../api/client";
import { useTriage } from "../composables/useTriage";
import { companyPlace, plural, scoreWord } from "../format";
import { buildExcerpt, matchedPassages, offerText } from "../offerPassages";
import AppIcon from "./AppIcon.vue";
import BookmarkMark from "./BookmarkMark.vue";
import CompanyLogo from "./CompanyLogo.vue";
import ScoreRing from "./ScoreRing.vue";
import TriageNone from "./TriageNone.vue";
import "../triage.css";

// Le livre en petit, dans la colonne de droite d'Aujourd'hui sur ordinateur (lot du 11 novembre au soir, PR 49 ;
// maquette AujourdhuiOrdinateurV2) : « {n} offres à trier », la meilleure offre ouverte (pages de 200 × 260 px),
// « Écarter » et « Garder » dessous. On trie sur place, comme sur la page « Trier les offres » (useTriage) : même
// état « Gardée », même « Annuler » pendant 6 secondes (le bandeau de l'application). Pas de raccourci clavier ici :
// les flèches restent à la page.
const props = defineProps<{ offers: Offer[] }>();
const emit = defineEmits<{ done: []; resumed: [] }>();

const title = ref<HTMLElement | null>(null);
const { index, total, current, finished, decide } = useTriage(toRef(props, "offers"), () => {
  void nextTick(() => title.value?.focus());
});
// La dernière offre triée : le parent le note ; « Annuler » la remet à l'écran et le tri reprend.
watch(finished, (now) => (now ? emit("done") : emit("resumed")));

const word = computed(() => (current.value?.score == null ? null : scoreWord(current.value.score)));
// L'extrait tient dans la page de droite : court, construit autour des passages retrouvés.
const EXCERPT = 110;
const excerpt = computed(() => {
  const o = current.value;
  const text = o ? offerText(o) : "";
  return text ? buildExcerpt(text, matchedPassages(o!), EXCERPT) : null;
});
</script>

<template>
  <section
    v-if="current"
    class="tri-mini"
    aria-labelledby="tri-mini-title"
    data-test="triage-mini"
  >
    <div class="tri-mini-head">
      <h2 id="tri-mini-title">
        {{ plural(total, "offre à trier", "offres à trier") }}
      </h2>
      <span data-test="triage-mini-count">{{ index + 1 }} sur {{ total }}</span>
    </div>
    <div class="tri-mini-stage">
      <div class="tri-mini-book">
        <div
          :key="current.id"
          class="tri-mini-pages"
        >
          <div class="tri-mini-left">
            <CompanyLogo
              :offer="current"
              pair
              class="tri-mini-logo"
            />
            <h3
              ref="title"
              tabindex="-1"
              data-test="triage-mini-title"
            >
              {{ current.title }}
            </h3>
            <p class="tri-mini-sub">
              {{ companyPlace(current.company || "Entreprise non indiquée", current.location) }}
            </p>
            <div class="tri-mini-score">
              <ScoreRing
                :score="current.score ?? null"
                :stale="current.score_stale"
                bare
              />
              <b
                v-if="word"
                :class="`tone-${word.tone}`"
                aria-hidden="true"
              >{{ word.word }}</b>
            </div>
          </div>
          <div class="tri-mini-right">
            <template v-if="excerpt">
              <p
                class="tri-mini-quote"
                data-test="triage-mini-excerpt"
              >
                «&nbsp;<template
                  v-for="(part, i) in excerpt.segments"
                  :key="i"
                >
                  <mark v-if="part.mark">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
                </template>&nbsp;»
              </p>
              <p
                v-if="excerpt.count"
                class="tri-mini-legend"
                data-test="triage-mini-legend"
              >
                <span aria-hidden="true" />{{ plural(excerpt.count, "point retrouvé", "points retrouvés") }}
              </p>
            </template>
          </div>
        </div>
        <BookmarkMark
          class="tri-mini-bookmark"
          :width="40"
        />
      </div>
    </div>
    <div class="tri-mini-actions">
      <button
        type="button"
        class="tri-mini-dismiss"
        data-test="triage-mini-dismiss"
        @click="decide('dismiss')"
      >
        <AppIcon name="close" />Écarter
      </button>
      <button
        type="button"
        class="tri-mini-keep"
        data-test="triage-mini-keep"
        @click="decide('keep')"
      >
        <AppIcon name="bookmark" />Garder
      </button>
    </div>
  </section>
  <section
    v-else-if="finished"
    class="tri-mini"
    aria-labelledby="tri-mini-title"
    data-test="triage-mini-done"
  >
    <div class="tri-mini-head">
      <h2 id="tri-mini-title">
        Offres à trier
      </h2>
    </div>
    <TriageNone
      class="tri-mini-none"
      title="Tri terminé · À demain"
    />
  </section>
</template>

<style scoped>
/* Les valeurs de la maquette AujourdhuiOrdinateurV2, écrites avec les échelles ; les tailles hors échelle sont
   nommées ici. Hors grille de 4, ramenés à la grille : marge intérieure du livre 6 8 14 (8 8 16), haut de la page de
   droite 68 px (le marque-page), écart de la note 10 px (12). */
.tri-mini {
  --tm-22: 1.375rem; --tm-16: 1rem; --tm-15: 0.9375rem; --tm-13: 0.8125rem; --tm-20: 1.25rem; --tm-23: 1.4375rem; --tm-book-r: 18px; --tm-page-w: 200px; --tm-page-h: 260px;
  --tm-book: 416px; --tm-logo: 40px; --tm-ring: 44px; --tm-top: 68px; --tm-btn: 48px; --tm-3: 3px; --tm-mark-r: 4px; --tm-legend-w: 22px; --tm-legend-h: 11px; --tm-up: -14px; --tm-half: 20px;
}
.tri-mini-head { display: flex; justify-content: space-between; align-items: baseline; padding: 0 var(--space-1); }
.tri-mini-head h2 { margin: 0; font-size: var(--tm-22); font-weight: var(--weight-heavy); }
.tri-mini-head span { font-size: var(--tm-15); color: var(--text-lead); }
.tri-mini-stage { width: var(--tm-book); max-width: 100%; margin: var(--space-6) auto 0; }
.tri-mini-book { position: relative; box-sizing: border-box; width: var(--tm-book); max-width: 100%; padding: var(--space-2) var(--space-2) var(--space-4); border-radius: var(--tm-book-r); background: var(--tri-edge); box-shadow: var(--tri-book-shadow); }
.tri-mini-pages { display: flex; border-radius: var(--space-3); box-shadow: 0 0 0 var(--tm-3) var(--tri-rim); }
.tri-mini-left, .tri-mini-right { box-sizing: border-box; width: var(--tm-page-w); height: var(--tm-page-h); padding: var(--space-4); overflow: hidden; background: var(--surface); }
.tri-mini-left { border-radius: var(--space-3) 0 0 var(--space-3); box-shadow: inset -18px 0 16px -12px var(--tri-fold); }
.tri-mini-right { padding-top: var(--tm-top); border-radius: 0 var(--space-3) var(--space-3) 0; box-shadow: inset 18px 0 16px -12px var(--tri-fold); }
.tri-mini-logo { width: var(--tm-logo); height: var(--tm-logo); }
.tri-mini h3 { margin: var(--space-3) 0 0; font-size: var(--tm-16); line-height: var(--tm-22); font-weight: var(--weight-bold); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; outline-offset: 2px; }
.tri-mini-sub { margin: var(--space-1) 0 0; font-size: var(--tm-13); line-height: var(--tm-20); color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tri-mini-score { display: flex; align-items: center; gap: var(--space-3); margin-top: var(--space-4); }
.tri-mini-score :deep(.score-ring-wrap) { padding: 0; }
.tri-mini-score :deep(.score-ring) { width: var(--tm-ring); height: var(--tm-ring); font-size: var(--tm-15); }
.tri-mini-score b { font-size: var(--tm-13); font-weight: var(--weight-bold); color: var(--success); }
.tri-mini-score b.tone-dig { color: var(--score-dig); }
.tri-mini-score b.tone-far { color: var(--text-secondary); }
.tri-mini-quote { margin: 0; font-size: var(--tm-13); line-height: var(--tm-23); color: var(--tri-tag-text); display: -webkit-box; -webkit-line-clamp: 6; -webkit-box-orient: vertical; overflow: hidden; }
.tri-mini-quote mark { padding: 0 var(--space-1); border-radius: var(--tm-mark-r); background: var(--tri-mark); color: inherit; }
.tri-mini-legend { display: flex; align-items: center; gap: var(--space-2); margin: var(--space-3) 0 0; font-size: var(--tm-13); color: var(--tri-tag-text); }
.tri-mini-legend span { flex: none; width: var(--tm-legend-w); height: var(--tm-legend-h); border-radius: var(--tm-mark-r); background: var(--tri-mark); }
.tri-mini-bookmark { position: absolute; left: calc(50% - var(--tm-half)); top: var(--tm-up); }
.tri-mini-actions { display: flex; gap: var(--space-3); margin-top: var(--space-6); }
.tri-mini-actions button { flex: 1; box-sizing: border-box; padding-block: 0; display: flex; align-items: center; justify-content: center; gap: var(--space-2); min-height: var(--tm-btn); border-radius: var(--radius-pill); font-size: var(--tm-16); font-weight: var(--weight-bold); }
.tri-mini-actions :deep(svg) { width: var(--tm-20); height: var(--tm-20); }
.tri-mini-dismiss { border: 1.5px solid var(--tri-outline); background: var(--surface); color: var(--text); }
.tri-mini-none { margin-top: var(--space-5); }
.tri-mini-keep { border: 0; background: var(--primary-soft); color: var(--primary-text); }
</style>
