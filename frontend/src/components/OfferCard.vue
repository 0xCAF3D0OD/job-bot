<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { colorIndex, formatDate, rateText, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer; selected: boolean }>();
defineEmits<{ select: [] }>();

const name = computed(() => props.offer.company ?? props.offer.title);
const initial = computed(() => name.value.trim().charAt(0).toUpperCase() || "?");
const logo = computed(() => `logo c${colorIndex(name.value)}`);
// En attendant le résumé de l'IA (0.4.0-b) : début du texte complet, sinon l'extrait.
const excerpt = computed(() => props.offer.description ?? props.offer.snippet ?? null);
const sites = computed(() => props.offer.links.map((link) => sourceLabel[link.source]).join(", "));
</script>

<template>
  <button
    type="button"
    :class="['job-card', { selected }]"
    :aria-pressed="selected"
    data-test="offer"
    @click="$emit('select')"
  >
    <div class="job-head">
      <span
        :class="logo"
        aria-hidden="true"
      >{{ initial }}</span>
      <div>
        <span class="job-title">{{ offer.title }}</span>
        <span class="job-company">{{ offer.company ?? "Entreprise non indiquée" }}</span>
      </div>
      <div class="job-side">
        <span
          class="score pending"
          title="La note de l'IA arrive avec la version 0.4"
        >à noter</span>
        <span class="job-date">{{ formatDate(offer.first_seen_at) }}</span>
      </div>
    </div>
    <span
      v-if="offer.filter_reasons?.length"
      class="badge reason"
    >{{ offer.filter_reasons[0] }}</span>
    <p
      v-if="excerpt"
      class="job-snippet"
    >
      {{ excerpt }}
    </p>
    <div class="job-meta">
      <span v-if="offer.location"><AppIcon name="pin" />{{ offer.location }}</span>
      <span v-if="rateText(offer.rate_min, offer.rate_max)">
        <AppIcon name="rate" />{{ rateText(offer.rate_min, offer.rate_max) }}
      </span>
      <span><AppIcon name="globe" />{{ sites }}</span>
      <span
        v-if="offer.apply_kind === 'external'"
        class="meta-accent"
      >chez l'employeur</span>
    </div>
  </button>
</template>
