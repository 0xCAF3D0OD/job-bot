<script setup lang="ts">
import { computed } from "vue";

import type { Offer } from "../api/client";
import { formatDate, rateText, scoreLevel, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";

const props = defineProps<{ offer: Offer; selected: boolean }>();
defineEmits<{ select: [] }>();

// Sans résumé de l'IA : début du texte complet, sinon l'extrait de l'alerte.
const excerpt = computed(() => props.offer.description ?? props.offer.snippet ?? null);
const hasSummary = computed(() => Boolean(props.offer.summary_role));
// Étiquettes courtes (docs/11 §3) ; les phrases restent pour les notes plus anciennes.
const hasKeywords = computed(() =>
  Boolean(
    props.offer.keywords_role?.length || props.offer.keywords_asks?.length || props.offer.keywords_offers?.length,
  ),
);
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
      <CompanyLogo :offer="offer" />
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
    <div
      v-if="hasKeywords"
      class="kw-rows"
      data-test="keywords"
    >
      <div
        v-if="offer.keywords_role?.length"
        class="kw-row"
      >
        <span class="kw-label">Poste</span>
        <span
          v-for="word in offer.keywords_role"
          :key="word"
          class="kw"
        >{{ word }}</span>
      </div>
      <div
        v-if="offer.keywords_asks?.length"
        class="kw-row"
      >
        <span class="kw-label">Demande</span>
        <span
          v-for="ask in offer.keywords_asks"
          :key="ask.text"
          :class="['kw', { gap: ask.covered === false }]"
          :title="ask.covered === false ? 'Pas couvert par ton profil' : undefined"
        >{{ ask.text }}</span>
      </div>
      <div
        v-if="offer.keywords_offers?.length"
        class="kw-row"
      >
        <span class="kw-label">Offre</span>
        <span
          v-for="word in offer.keywords_offers"
          :key="word"
          class="kw offer"
        >{{ word }}</span>
      </div>
    </div>
    <dl
      v-else-if="hasSummary"
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
