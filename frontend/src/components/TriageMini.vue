<script setup lang="ts">
import { computed, nextTick, ref, toRef, watch } from "vue";

import type { Offer } from "../api/client";
import { useTriage } from "../composables/useTriage";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import OfferFan from "./OfferFan.vue";
import TriageNone from "./TriageNone.vue";
import "../triage.css";

// L'éventail en petit, dans la colonne de droite d'Aujourd'hui sur ordinateur (maquette du 15 novembre, §20 ;
// planche AujourdhuiOrdinateurV2) : « {n} offres à trier », l'éventail de la page Trier réduit à 66 % (OfferFan),
// « Écarter » et « Garder » dessous. On trie sur place, comme sur la page « Trier les offres » (useTriage) : même
// état « Gardée », même « Annuler » pendant 6 secondes (le bandeau de l'application). Pas de raccourci clavier ici :
// les flèches restent à la page.
const props = defineProps<{ offers: Offer[] }>();
const emit = defineEmits<{ done: []; resumed: [] }>();

const group = ref<HTMLElement | null>(null);
const { queue, index, total, current, finished, decide } = useTriage(toRef(props, "offers"), () => {
  void nextTick(() => group.value?.focus());
});
// La dernière offre triée : le parent le note ; « Annuler » la remet à l'écran et le tri reprend.
watch(finished, (now) => (now ? emit("done") : emit("resumed")));

// Les cartes qui restent, la meilleure devant ; le groupe dit laquelle est la première.
const left = computed(() => queue.value.slice(index.value, index.value + 3));
const label = computed(() => {
  const o = current.value;
  if (!o) return "";
  const head = plural(total.value - index.value, "offre à trier", "offres à trier");
  return `${head}, la première : ${o.title} chez ${o.company || "une entreprise non indiquée"}`;
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
    <div
      ref="group"
      role="group"
      class="tri-mini-fan"
      tabindex="-1"
      :aria-label="label"
      data-test="triage-mini-group"
    >
      <OfferFan
        :offers="left"
        mini
      />
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
/* Les valeurs de la planche AujourdhuiOrdinateurV2 (§20), écrites avec les échelles ; les tailles hors échelle sont
   nommées ici. L'éventail : 20 px sous le titre (--space-5), boutons 24 px dessous (--space-6). */
.tri-mini { --tm-22: 1.375rem; --tm-16: 1rem; --tm-15: 0.9375rem; --tm-20: 1.25rem; --tm-btn: 48px; }
.tri-mini-head { display: flex; justify-content: space-between; align-items: baseline; padding: 0 var(--space-1); }
.tri-mini-head h2 { margin: 0; font-size: var(--tm-22); font-weight: var(--weight-heavy); }
.tri-mini-head span { font-size: var(--tm-15); color: var(--text-lead); }
.tri-mini-fan { margin-top: var(--space-5); border-radius: var(--radius-card); outline-offset: var(--space-1); }
.tri-mini-actions { display: flex; gap: var(--space-3); margin-top: var(--space-6); }
.tri-mini-actions button { flex: 1; box-sizing: border-box; padding-block: 0; display: flex; align-items: center; justify-content: center; gap: var(--space-2); min-height: var(--tm-btn); border-radius: var(--radius-pill); font-size: var(--tm-16); font-weight: var(--weight-bold); }
.tri-mini-actions :deep(svg) { width: var(--tm-20); height: var(--tm-20); }
.tri-mini-dismiss { border: 1.5px solid var(--tri-outline); background: var(--surface); color: var(--text); }
.tri-mini-none { margin-top: var(--space-5); }
.tri-mini-keep { border: 0; background: var(--primary-soft); color: var(--primary-text); }
</style>
