<script setup lang="ts">
import type { Offer } from "../api/client";
import { colorIndex, expiredText, formatDate, rateText, scoreLevel, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer; chunkTitles?: Record<number, string> }>();

function sources(ids: number[]): string {
  return ids
    .map((id) => props.chunkTitles?.[id])
    .filter(Boolean)
    .join(", ");
}
const emit = defineEmits<{
  close: [];
  status: [status: "to_review" | "later" | "ignored" | "preparing"];
  applied: [];
}>();

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
    <p
      v-if="offer.expired_at && offer.status !== 'applied'"
      class="notice expired-notice"
      data-test="expired"
    >
      {{ expiredText(offer) }}
    </p>
    <div
      class="triage"
      data-test="triage"
    >
      <template v-if="offer.status === 'applied'">
        <span class="badge new">Candidature envoyée</span>
        <RouterLink
          to="/candidatures"
          class="link"
        >
          Voir le suivi
        </RouterLink>
      </template>
      <template v-else>
        <span
          v-if="offer.status === 'preparing'"
          class="badge"
        >En préparation</span>
        <RouterLink
          :to="`/offres/${offer.id}/preparer`"
          class="button-link"
          data-test="prepare"
        >
          {{ offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
        </RouterLink>
        <button
          type="button"
          class="primary small"
          data-test="mark-applied"
          @click="emit('applied')"
        >
          Marquer comme envoyée
        </button>
        <button
          v-if="offer.status === 'later' || offer.status === 'ignored' || offer.status === 'preparing'"
          type="button"
          class="link"
          data-test="back-to-review"
          @click="emit('status', 'to_review')"
        >
          Remettre à examiner
        </button>
        <template v-else>
          <button
            type="button"
            class="link"
            data-test="later"
            @click="emit('status', 'later')"
          >
            Plus tard
          </button>
          <button
            type="button"
            class="link danger"
            data-test="ignore"
            @click="emit('status', 'ignored')"
          >
            Ignorer
          </button>
        </template>
      </template>
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
    <section
      v-if="offer.summary_role"
      class="ai-block"
      data-test="ai"
    >
      <div class="ai-head">
        <span
          v-if="offer.score !== null && offer.score !== undefined"
          :class="['score', 'big', scoreLevel(offer.score)]"
        >{{ offer.score }}<small>/100</small></span>
        <span class="detail">
          Résumé et note par l'IA{{ offer.summary_partial ? ", sur l'extrait de l'alerte seulement" : "" }}.
          <template v-if="offer.score_stale">Ton profil a changé depuis : note à refaire.</template>
          <template v-if="offer.score === null">Pas de note : aucun bloc de profil actif.</template>
        </span>
      </div>
      <dl class="summary">
        <div><dt>Poste</dt><dd>{{ offer.summary_role }}</dd></div>
        <div><dt>Demande</dt><dd>{{ offer.summary_asks }}</dd></div>
        <div><dt>Offre</dt><dd>{{ offer.summary_offers }}</dd></div>
      </dl>
      <div
        v-if="offer.strengths?.length || offer.gaps?.length"
        class="points"
      >
        <div v-if="offer.strengths?.length">
          <h3>Points forts</h3>
          <ul data-test="strengths">
            <li
              v-for="point in offer.strengths"
              :key="point.text"
            >
              {{ point.text }}
              <span
                v-if="sources(point.chunk_ids)"
                class="detail"
              >Bloc : {{ sources(point.chunk_ids) }}</span>
            </li>
          </ul>
        </div>
        <div v-if="offer.gaps?.length">
          <h3>Manques</h3>
          <ul
            class="gaps"
            data-test="gaps"
          >
            <li
              v-for="point in offer.gaps"
              :key="point.text"
            >
              {{ point.text }}
            </li>
          </ul>
        </div>
      </div>
    </section>
    <p
      v-else-if="offer.score_error"
      class="badge reason"
    >
      Note impossible : {{ offer.score_error }}
    </p>
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
