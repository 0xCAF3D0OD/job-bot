<script setup lang="ts">
import BookmarkMark from "./BookmarkMark.vue";
import "../triage.css";

// « Rien à trier pour l’instant » (lot du 11 novembre au soir, PR 49 ; état « vide » d'AccueilV2 et
// d'AujourdhuiOrdinateurV2) : un bloc à bordure pointillée, le contour du marque-page à droite, puis « Élargir ma
// recherche » vers les critères. `title` : un jour de repos, en pause ou le tri fini, la page le dit à la place ;
// `widen` : le lien, seulement quand il n'y a vraiment aucune offre.
defineProps<{ title?: string; widen?: boolean }>();
</script>

<template>
  <div
    class="tri-none"
    data-test="triage-none"
  >
    <div class="tri-none-box">
      <p>
        <b>{{ title ?? "Rien à trier pour l’instant" }}</b>
        <span>jobA1 cherche chaque matin. Les prochaines offres arrivent demain.</span>
      </p>
      <BookmarkMark
        outline
        :width="38"
      />
    </div>
    <RouterLink
      v-if="widen"
      :to="{ path: '/reglages', query: { rubrique: 'recherche' } }"
      class="tri-none-widen"
      data-test="triage-widen"
    >
      Élargir ma recherche
    </RouterLink>
  </div>
</template>

<style scoped>
.tri-none { --tn-dash: #E3BFA8; --tn-r: 18px; --tn-17: 1.0625rem; --tn-15: 0.9375rem; --tn-22: 1.375rem; --tn-line: 2px; --tn-offset: 3px; }
.tri-none-box { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); border: var(--tn-line) dashed var(--tn-dash); border-radius: var(--tn-r); }
.tri-none-box p { flex: 1; margin: 0; }
.tri-none-box b { display: block; font-size: var(--tn-17); line-height: var(--space-6); font-weight: var(--weight-bold); }
.tri-none-box span { display: block; margin-top: var(--space-1); font-size: var(--tn-15); line-height: var(--tn-22); color: var(--text-lead); }
.tri-none-box :deep(svg) { flex: none; }
.tri-none-widen { display: inline-flex; align-items: center; min-height: var(--target-min); margin: var(--space-2) var(--space-1) 0; font-size: var(--tn-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: underline; text-underline-offset: var(--tn-offset); }
@media (min-width: 821px) { .tri-none-box { padding: var(--space-6); } }
</style>
