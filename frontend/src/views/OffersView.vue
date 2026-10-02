<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type Offer } from "../api/client";
import { formatDateTime, rateText, sourceLabel } from "../format";

const PAGE_SIZE = 50;

const items = ref<Offer[]>([]);
const total = ref(0);
const loading = ref(false);
const failed = ref(false);

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
      Offres collectées, sans doublon. Le tri par prérequis arrive en 0.3, la note et les actions en 0.4.
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

    <ul class="offer-cards">
      <li
        v-for="offer in items"
        :key="offer.id"
        class="offer-card"
        data-test="offer"
      >
        <div class="offer-head">
          <strong>{{ offer.title }}</strong>
          <span
            v-if="offer.seen_count > 1"
            class="badge muted-badge"
          >vue {{ offer.seen_count }} fois</span>
        </div>
        <span class="detail">
          {{ [offer.company, offer.location, rateText(offer.rate_min, offer.rate_max)].filter(Boolean).join(" · ") }}
        </span>
        <p
          v-if="offer.snippet"
          class="snippet"
        >
          {{ offer.snippet }}
        </p>
        <div class="offer-foot">
          <span class="detail">depuis le {{ formatDateTime(offer.first_seen_at) }}</span>
          <a
            v-for="link in offer.links"
            :key="link.source"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
            class="link"
          >{{ sourceLabel[link.source] }}</a>
        </div>
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
  </section>
</template>
