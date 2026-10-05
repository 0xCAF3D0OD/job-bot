<script setup lang="ts">
import type { Offer } from "../api/client";
import { colorIndex, formatDate, rateText, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

defineProps<{ offer: Offer }>();
defineEmits<{ close: [] }>();

function initial(offer: Offer): string {
  return (offer.company ?? offer.title).trim().charAt(0).toUpperCase() || "?";
}
</script>

<template>
  <article
    class="detail-panel"
    data-test="offer-detail"
  >
    <div class="detail-top">
      <span
        :class="['logo', 'large', `c${colorIndex(offer.company ?? offer.title)}`]"
        aria-hidden="true"
      >{{ initial(offer) }}</span>
      <button
        type="button"
        class="close"
        aria-label="Fermer le détail"
        data-test="close-detail"
        @click="$emit('close')"
      >
        ×
      </button>
    </div>
    <div>
      <h2>{{ offer.title }}</h2>
      <span class="detail">{{ offer.company ?? "Entreprise non indiquée" }}</span>
    </div>
    <div class="actions">
      <a
        v-if="offer.apply_url"
        :href="offer.apply_url"
        target="_blank"
        rel="noopener noreferrer"
        data-test="apply"
      >{{ offer.apply_kind === "external" ? "Postuler chez l'employeur" : "Postuler sur jobup" }}
        <AppIcon name="chevron" /></a>
      <a
        v-for="link in offer.links"
        :key="link.source"
        :class="{ secondary: offer.apply_url }"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
      >Voir sur {{ sourceLabel[link.source] }} <AppIcon name="chevron" /></a>
    </div>
    <ul
      v-if="offer.filter_reasons?.length"
      class="reasons"
      data-test="reasons"
    >
      <li
        v-for="reason in offer.filter_reasons"
        :key="reason"
      >
        {{ reason }}
      </li>
    </ul>
    <p
      v-if="offer.enrich_status === 'expired'"
      class="badge reason"
    >
      L'annonce n'est plus en ligne sur jobup.
    </p>
    <ul class="checks">
      <li>
        <AppIcon name="check" /><strong>Lieu.</strong>
        <span>{{ offer.location ?? "non indiqué" }}</span>
      </li>
      <li>
        <AppIcon name="check" /><strong>Taux.</strong>
        <span>{{ rateText(offer.rate_min, offer.rate_max) || "non indiqué" }}</span>
      </li>
      <li v-if="offer.employment_type">
        <AppIcon name="check" /><strong>Type.</strong>
        <span>{{ offer.employment_type }}</span>
      </li>
      <li>
        <AppIcon name="check" /><strong>Vue.</strong>
        <span>{{ offer.seen_count }} fois, depuis le {{ formatDate(offer.first_seen_at) }}</span>
      </li>
    </ul>
    <div
      v-if="offer.description"
      class="full-text"
      data-test="description"
    >
      {{ offer.description }}
    </div>
    <p
      v-else-if="offer.snippet"
      class="detail-snippet"
    >
      {{ offer.snippet }}
    </p>
    <p
      v-else
      class="detail-snippet"
    >
      Pas d'extrait dans l'alerte : le texte complet de l'annonce est sur le site.
    </p>
  </article>
</template>
