<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { colorIndex, formatDate, rateText, scoreLevel, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer; selected: boolean }>();
defineEmits<{ select: [] }>();

const name = computed(() => props.offer.company ?? props.offer.title);
const initial = computed(() => name.value.trim().charAt(0).toUpperCase() || "?");
const logo = computed(() => `logo c${colorIndex(name.value)}`);
// Sans résumé de l'IA : début du texte complet, sinon l'extrait de l'alerte.
const excerpt = computed(() => props.offer.description ?? props.offer.snippet ?? null);
const hasSummary = computed(() => Boolean(props.offer.summary_role));
const sites = computed(() => props.offer.links.map((link) => sourceLabel[link.source]).join(", "));
</script>

<template>
  <button
    type="button"
    :class="['job-card', { selected, expired: offer.expired_at && offer.status !== 'applied' }]"
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
          v-if="offer.score !== null && offer.score !== undefined"
          :class="['score', scoreLevel(offer.score), { stale: offer.score_stale }]"
          :title="offer.score_stale ? 'Note faite avec un ancien profil' : 'Note de l\'IA'"
          data-test="score"
        >{{ offer.score }}</span>
        <span
          v-else
          class="score pending"
          :title="offer.summary_role ? 'Pas de note : aucun bloc de profil actif' : 'Pas encore notée'"
        >{{ offer.summary_role ? "–" : "à noter" }}</span>
        <span class="job-date">{{ formatDate(offer.first_seen_at) }}</span>
      </div>
    </div>
    <span
      v-if="offer.filter_reasons?.length"
      class="badge reason"
    >{{ offer.filter_reasons[0] }}</span>
    <dl
      v-if="hasSummary"
      class="summary"
      data-test="summary"
    >
      <div><dt>Poste</dt><dd>{{ offer.summary_role }}</dd></div>
      <div><dt>Demande</dt><dd>{{ offer.summary_asks }}</dd></div>
      <div><dt>Offre</dt><dd>{{ offer.summary_offers }}</dd></div>
    </dl>
    <p
      v-else-if="excerpt"
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
