<script setup lang="ts">
// Téléphone (§72q, planche CandidaturesSelection du 19.11) : en mode sélection, cette barre remplace la navigation du bas.
// « Annuler » à contour et « Écarter N offres » plein, qui prend la place restante ; désactivé tant que rien n'est coché.
const props = defineProps<{ count: number }>();
const emit = defineEmits<{ quit: []; discard: [] }>();

function discard(): void {
  if (props.count > 0) emit("discard");
}
</script>

<template>
  <div
    class="multi-bar"
    data-test="multi-bar"
  >
    <button
      type="button"
      class="multi-bar-cancel"
      data-test="multi-cancel"
      @click="emit('quit')"
    >
      Annuler
    </button>
    <button
      type="button"
      class="multi-bar-discard"
      :aria-disabled="count === 0 ? 'true' : undefined"
      data-test="multi-discard"
      @click="discard"
    >
      {{ count > 1 ? `Écarter ${count} offres` : `Écarter ${count} offre` }}
    </button>
  </div>
</template>

<style>
/* 12 px en haut, 16 sur les côtés, 28 en bas (plus la zone sûre), trait de 1 px --line, fond de page ; boutons de 48 px,
   10 px entre eux, texte 16 px gras ; « Annuler » 20 px dedans, trait de 1,5 px --action. */
.multi-bar {
  --sb-gap: 10px; --sb-bottom: calc(28px + env(safe-area-inset-bottom, 0px)); --sb-h: 48px; --sb-x: 20px;
  position: fixed; inset: auto 0 0; z-index: 30; display: flex; gap: var(--sb-gap);
  padding: var(--space-3) var(--space-4) var(--sb-bottom); background: var(--bg); border-top: 1px solid var(--line);
}
.multi-bar > button { height: var(--sb-h); border: 0; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.multi-bar-cancel { flex: none; padding: 0 var(--sb-x); background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--action); color: var(--primary-text); }
.multi-bar-discard { flex: 1; background: var(--action); color: var(--on-action); }
.multi-bar-discard[aria-disabled="true"] { background: var(--line-soft); color: var(--text-secondary); cursor: default; }
</style>
