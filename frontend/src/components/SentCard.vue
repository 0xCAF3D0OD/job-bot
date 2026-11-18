<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import type { Application } from "../api/client";
import { sentChips, sentStatus, type SentSectionKey } from "../sentList";
import AppIcon from "./AppIcon.vue";
import ListCard from "./ListCard.vue";

// Une candidature dans Envoyées (maquette Envoyees, 7.11.2026) : la carte de liste d'À traiter, avec la date
// d'envoi (et le canal dans la semaine) ou l'entretien en puce, et le statut à droite (icône dans un rond, un mot).
// Un clic ouvre le panneau de la candidature (?candidature=).
const props = defineProps<{ application: Application; section: SentSectionKey; selected?: boolean }>();
defineEmits<{ select: [] }>();
const route = useRoute();

const to = computed(() => ({ path: route.path, query: { ...route.query, candidature: String(props.application.id) } }));
const chips = computed(() => sentChips(props.application, props.section));

// Comme les offres (planche Candidatures, §26) : une puce qui ne tient pas sur la ligne passe dans « +N », jamais
// coupée au bord de la carte (audit du 17.11, N4). Mesuré après rendu et quand la carte change de largeur.
const card = ref<{ $el: HTMLElement } | null>(null);
const fits = ref(99);
async function fit(): Promise<void> {
  fits.value = 99;
  await nextTick();
  const box = card.value?.$el.querySelector(".list-card-chips");
  const edge = box?.getBoundingClientRect().right ?? 0;
  while (box && chips.value.length > 1 && fits.value > 1 && [...box.children].some((c) => c.getBoundingClientRect().right > edge + 0.5)) {
    fits.value = Math.min(fits.value, chips.value.length) - 1;
    await nextTick();
  }
}
let watcher: ResizeObserver | undefined;
onMounted(() => {
  void fit();
  if (typeof ResizeObserver !== "undefined" && card.value) (watcher = new ResizeObserver(() => void fit())).observe(card.value.$el);
});
onUnmounted(() => watcher?.disconnect());
watch(chips, () => void fit());
const status = computed(() => sentStatus(props.application, props.section));
</script>

<template>
  <ListCard
    ref="card"
    :title="application.job_title"
    :company="application.company"
    :location="application.location"
    :to="to"
    :selected="selected"
    data-test="application"
    @select="$emit('select')"
  >
    <template #chips>
      <span
        v-for="chip in chips.slice(0, fits)"
        :key="chip.text"
        :class="chip.tone"
        data-test="sent-chip"
      >{{ chip.text }}</span>
      <span
        v-if="fits < chips.length"
        class="more"
        :title="chips.slice(fits).map((chip) => chip.text).join(', ')"
        data-test="sent-chip"
      >+{{ chips.length - fits }}</span>
    </template>
    <template #end>
      <span
        :class="['sent-status', status.tone]"
        data-test="sent-status"
      >
        <span class="sent-status-icon"><AppIcon :name="status.icon" /></span>
        {{ status.word }}
      </span>
    </template>
  </ListCard>
</template>

<style>
/* « +N » : les puces qui ne tiennent pas sur la ligne (§26), en gras comme sur la carte d'une offre. */
[data-test="application"] > .list-card-chips > .more { font-weight: var(--weight-bold); }
/* Une puce trop longue pour un écran étroit (360 px), seule ou avant « +N » : elle finit par « … » au lieu d’être coupée net. */
[data-test="application"] > .list-card-chips > :only-child,
[data-test="application"] > .list-card-chips:has(> .more) > :first-child { flex-shrink: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
/* Le rond de 44 px, l'icône de 20 au trait de 2,2, le mot en 12 gras (maquette Envoyees). */
.sent-status { --sent-6: 6px; --sent-15: 15px; display: flex; flex-direction: column; align-items: center; gap: var(--sent-6); line-height: var(--sent-15); font-size: var(--font-caption); font-weight: var(--weight-bold); white-space: nowrap; }
/* Maquette Envoyees (8.11) : l'icône seule, sans fond (D23), 26 px dans une case de 44 × 32. */
.sent-status-icon { display: grid; place-items: center; width: var(--target-min); height: 32px; }
.sent-status-icon .icon { width: 26px; height: 26px; stroke-width: 2; }
.sent-status.peach { color: var(--peach-text); }
.sent-status.green { color: var(--success); }
.sent-status.grey { color: var(--text-tertiary); }
.sent-status.muted { color: var(--text-secondary); }
/* Ordinateur, maquette du 14 novembre (§2) : la puce reste dans la colonne du titre (logo, colonne titre · entreprise ·
   puce, statut) ; le logo et le statut sont centrés sur toute la hauteur de la carte. */
@media (min-width: 1024px) {
  .list-card[data-test="application"] { grid-template-areas: "logo text end" "logo chips end"; }
  .list-card[data-test="application"] > .list-card-end { align-self: center; }
}
</style>
