<script setup lang="ts">
import { computed } from "vue";
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
const status = computed(() => sentStatus(props.application, props.section));
</script>

<template>
  <ListCard
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
        v-for="chip in chips"
        :key="chip.text"
        :class="chip.tone"
        data-test="sent-chip"
      >{{ chip.text }}</span>
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
/* Le rond de 44 px, l'icône de 20 au trait de 2,2, le mot en 12 gras (maquette Envoyees). */
.sent-status { --sent-6: 6px; --sent-15: 15px; display: flex; flex-direction: column; align-items: center; gap: var(--sent-6); line-height: var(--sent-15); font-size: var(--font-caption); font-weight: var(--weight-bold); white-space: nowrap; }
/* Maquette Envoyees (8.11) : l'icône seule, sans fond (D23), 26 px dans une case de 44 × 32. */
.sent-status-icon { display: grid; place-items: center; width: var(--target-min); height: 32px; }
.sent-status-icon .icon { width: 26px; height: 26px; stroke-width: 2; }
.sent-status.peach { color: var(--peach-text); }
.sent-status.green { color: var(--success); }
.sent-status.grey { color: var(--text-tertiary); }
.sent-status.muted { color: var(--text-secondary); }
</style>
