<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Offer } from "../api/client";
import { formatDateTime, rateText, sourceLabel } from "../format";

const PAGE_SIZE = 50;

const items = ref<Offer[]>([]);
const total = ref(0);
const loading = ref(false);
const failed = ref(false);
const selectedId = ref<number | null>(null);

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);

function initial(offer: Offer): string {
  return (offer.company ?? offer.title).trim().charAt(0).toUpperCase() || "?";
}

async function load(append = false): Promise<void> {
  loading.value = true;
  failed.value = false;
  try {
    const { data } = await api.GET("/api/offers", {
      params: { query: { limit: PAGE_SIZE, offset: append ? items.value.length : 0 } },
    });
    if (!data) throw new Error("réponse vide");
    items.value = append ? [...items.value, ...data.items] : data.items;
    total.value = data.total;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <section>
    <h1>Offres</h1>
    <p class="muted">
      {{ total }} offre(s) collectée(s), sans doublon. Le tri par prérequis arrive en 0.3, la note et les actions en 0.4.
    </p>

    <p
      v-if="failed"
      class="notice error"
    >
      Impossible de charger les offres.
    </p>
    <p
      v-else-if="!loading && items.length === 0"
      class="muted"
    >
      Aucune offre collectée pour l'instant.
    </p>

    <div
      v-else
      :class="['offers-layout', { 'has-selection': selected }]"
    >
      <div>
        <ul class="offer-cards">
          <li
            v-for="offer in items"
            :key="offer.id"
          >
            <button
              type="button"
              :class="['offer-card', { selected: offer.id === selectedId }]"
              :aria-pressed="offer.id === selectedId"
              data-test="offer"
              @click="selectedId = offer.id"
            >
              <div class="offer-head">
                <span class="offer-title">{{ offer.title }}</span>
                <span
                  v-if="offer.seen_count > 1"
                  class="badge seen"
                >vue {{ offer.seen_count }} fois</span>
              </div>
              <span class="detail">{{ [offer.company, offer.location].filter(Boolean).join(" · ") }}</span>
              <div class="offer-meta">
                <span
                  v-if="rateText(offer.rate_min, offer.rate_max)"
                  class="badge rate"
                >{{ rateText(offer.rate_min, offer.rate_max) }}</span>
                <span
                  v-for="link in offer.links"
                  :key="link.source"
                  class="badge site"
                >{{ sourceLabel[link.source] }}</span>
                <span class="detail">{{ formatDateTime(offer.first_seen_at) }}</span>
              </div>
            </button>
          </li>
        </ul>
        <button
          v-if="items.length < total"
          type="button"
          class="secondary more"
          :disabled="loading"
          @click="load(true)"
        >
          Afficher plus
        </button>
      </div>

      <article
        v-if="selected"
        class="detail-panel"
        data-test="offer-detail"
      >
        <button
          type="button"
          class="secondary back"
          @click="selectedId = null"
        >
          ← Retour à la liste
        </button>
        <div class="detail-head">
          <span
            class="company-mark"
            aria-hidden="true"
          >{{ initial(selected) }}</span>
          <div>
            <h2>{{ selected.title }}</h2>
            <span class="detail">{{ selected.company ?? "Entreprise non indiquée" }}</span>
          </div>
        </div>
        <dl class="facts">
          <div>
            <dt>Lieu</dt>
            <dd>{{ selected.location ?? "–" }}</dd>
          </div>
          <div>
            <dt>Taux</dt>
            <dd>{{ rateText(selected.rate_min, selected.rate_max) || "non indiqué" }}</dd>
          </div>
          <div>
            <dt>Vue</dt>
            <dd>{{ selected.seen_count }} fois</dd>
          </div>
          <div>
            <dt>Première fois</dt>
            <dd>{{ formatDateTime(selected.first_seen_at) }}</dd>
          </div>
        </dl>
        <p
          v-if="selected.snippet"
          class="snippet"
        >
          {{ selected.snippet }}
        </p>
        <p
          v-else
          class="muted"
        >
          Pas d'extrait dans l'alerte. Le texte complet de l'annonce est sur le site.
        </p>
        <div class="actions">
          <a
            v-for="link in selected.links"
            :key="link.source"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
          >Voir sur {{ sourceLabel[link.source] }}</a>
        </div>
      </article>
      <div
        v-else
        class="detail-panel empty-detail"
      >
        Choisis une offre pour voir son détail.
      </div>
    </div>
  </section>
</template>
