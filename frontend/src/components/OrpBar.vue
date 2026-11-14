<script setup lang="ts">
import { computed } from "vue";

import { formatMonth, orpLeftLine, orpPace } from "../format";

// La barre ORP (lot du 11 novembre au soir, PR 48), le seul dessin du mois ORP dans toute l'application : « Mois
// ORP · novembre » et « 7 sur 10 », la barre, puis « Encore 3 d’ici le 5 décembre ». Accueil et Aujourd'hui
// ajoutent le rythme (« · dans les temps », « · en retard », calcul existant) et la ligne « Cette semaine ».
// Objectif atteint ou dépassé : la barre pleine, en vert, et « Objectif atteint ».
// `card` : sur une carte blanche, le fond de la barre est bleu pâle ; sinon (bande bleue) il est blanc.
// `thick` : 12 px au lieu de 10 (Suivi ORP).
const props = defineProps<{
  month: string;
  count: number;
  target: number | null;
  /** L'échéance ORP du mois, pour « d’ici le 5 décembre ». */
  due?: string | null;
  pace?: boolean;
  card?: boolean;
  thick?: boolean;
  week?: { count: number; target: number } | null;
  /** Sans objectif saisi : la phrase à la place de « Encore n… » (le Bilan y invite à l'indiquer). */
  note?: string;
}>();

const name = computed(() => formatMonth(props.month).split(" ")[0]!.toLowerCase());
const reached = computed(() => !!props.target && props.count >= props.target);
const share = computed(() => (props.target ? Math.min(100, Math.round((props.count / props.target) * 100)) : 0));
const line = computed(() => {
  if (!props.target) return props.note ?? "";
  if (reached.value) return "Objectif atteint";
  const left = orpLeftLine(props.count, props.target, props.month, props.due);
  if (!props.pace) return left;
  const state = orpPace(props.count, props.target, props.month, new Date(), props.due)?.state;
  return `${left} · ${state === "behind" ? "en retard" : "dans les temps"}`;
});
</script>

<template>
  <div
    :class="['orp-bar', { 'orp-bar-card': card, 'orp-bar-thick': thick, reached }]"
    data-test="orp-bar"
  >
    <div class="orp-bar-head">
      <b>Mois ORP · {{ name }}</b>
      <b data-test="month-count">{{ target ? `${count} sur ${target}` : count }}</b>
    </div>
    <div
      v-if="target"
      class="orp-bar-track"
      role="progressbar"
      :aria-valuenow="Math.min(count, target)"
      aria-valuemin="0"
      :aria-valuemax="target"
      aria-label="Recherches du mois"
    >
      <span :style="{ width: `${share}%` }" />
    </div>
    <p
      v-if="line"
      class="orp-bar-line"
      data-test="month-left"
    >
      {{ line }}
    </p>
    <p
      v-if="week"
      class="orp-bar-week"
      data-test="orp-bar-week"
    >
      <b>Cette semaine</b><span>{{ week.count }} sur {{ week.target }}</span>
    </p>
  </div>
</template>

<style>
/* Maquettes AccueilV2, AujourdhuiOrdinateurV2, Orp, BilanOrdinateur : 16 px gras, la barre de 10 px 12 px dessous
   (12 px sur le Suivi ORP), la phrase de 14 px 12 px dessous ; « Cette semaine » sous un trait. */
.orp-bar {
  --ob-fill: #2445C2; --ob-track: #FFFFFF; --ob-track-card: #E8ECFB; --ob-rule: #CBD3F3; --ob-done: #17734A; --ob-line: #3D4250;
  --ob-h: 10px; --ob-h-thick: 12px; --ob-16: 1rem; --ob-14: 0.875rem; --ob-15: 0.9375rem;
  display: flex; flex-direction: column; min-width: 0; color: var(--text);
}
:root[data-theme="dark"] .orp-bar { --ob-fill: #7D95FF; --ob-track: #171411; --ob-track-card: #2C3558; --ob-rule: #3A4A86; --ob-done: #7FD3A6; --ob-line: #D9D2C7; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .orp-bar { --ob-fill: #7D95FF; --ob-track: #171411; --ob-track-card: #2C3558; --ob-rule: #3A4A86; --ob-done: #7FD3A6; --ob-line: #D9D2C7; } }
.orp-bar-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); font-size: var(--ob-16); }
.orp-bar-head b { font-weight: var(--weight-bold); }
.orp-bar-track { height: var(--ob-h); margin-top: var(--space-3); border-radius: var(--radius-pill); background: var(--ob-track); overflow: hidden; }
.orp-bar-card .orp-bar-track { background: var(--ob-track-card); }
.orp-bar-thick .orp-bar-track { height: var(--ob-h-thick); }
.orp-bar-track span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--ob-fill); }
.orp-bar.reached .orp-bar-track span { background: var(--ob-done); }
.orp-bar-line { margin: var(--space-3) 0 0; font-size: var(--ob-14); color: var(--ob-line); }
.orp-bar-week { display: flex; justify-content: space-between; gap: var(--space-3); margin: var(--space-4) 0 0; padding-top: var(--space-4); border-top: 1px solid var(--ob-rule); font-size: var(--ob-15); }
</style>
