<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import { colorIndex, formatDate, rateText, sourceLabel } from "../format";

const PAGE_SIZE = 50;

type View = "to_review" | "filtered_out" | "all";

const VIEWS: { value: View; label: string }[] = [
  { value: "to_review", label: "À examiner" },
  { value: "filtered_out", label: "Écartées" },
  { value: "all", label: "Toutes" },
];

const view = ref<View>("to_review");
const sort = ref<"recent" | "popular">("recent");
const counts = ref<Record<View, number>>({ to_review: 0, filtered_out: 0, all: 0 });
const items = ref<Offer[]>([]);
const total = ref(0);
const loading = ref(false);
const failed = ref(false);
const selectedId = ref<number | null>(null);

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);

function initial(offer: Offer): string {
  return (offer.company ?? offer.title).trim().charAt(0).toUpperCase() || "?";
}

function logoClass(offer: Offer): string {
  return `logo c${colorIndex(offer.company ?? offer.title)}`;
}

function sites(offer: Offer): string {
  return offer.links.map((link) => sourceLabel[link.source]).join(", ");
}

async function load(append = false): Promise<void> {
  loading.value = true;
  failed.value = false;
  try {
    const { data } = await api.GET("/api/offers", {
      params: {
        query: {
          limit: PAGE_SIZE,
          offset: append ? items.value.length : 0,
          sort: sort.value,
          view: view.value,
        },
      },
    });
    if (!data) throw new Error("réponse vide");
    items.value = append ? [...items.value, ...data.items] : data.items;
    total.value = data.total;
    counts.value = data.counts;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

watch([sort, view], () => {
  selectedId.value = null;
  void load();
});
onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Offres"
    title="Les offres pour toi"
    subtitle="Les offres reçues par tes alertes, sans doublon, triées selon tes prérequis. La note de l'IA arrive en 0.4."
  />

  <section class="plain">
    <div class="container">
      <div class="view-tabs">
        <div
          class="tabs"
          role="tablist"
          aria-label="Offres à afficher"
        >
          <button
            v-for="entry in VIEWS"
            :key="entry.value"
            type="button"
            role="tab"
            :aria-selected="view === entry.value"
            :data-test="`view-${entry.value}`"
            @click="view = entry.value"
          >
            {{ entry.label }} <span class="tab-count">{{ counts[entry.value] }}</span>
          </button>
        </div>
      </div>

      <p
        v-if="failed"
        class="notice error"
      >
        Impossible de charger les offres.
      </p>
      <p
        v-else-if="!loading && items.length === 0"
        class="muted empty"
      >
        {{ view === "filtered_out" ? "Aucune offre écartée." : "Aucune offre ici pour l'instant." }}
      </p>

      <div
        v-else
        :class="['offers-layout', { 'has-selection': selected }]"
      >
        <div>
          <div class="offers-toolbar">
            <div
              class="tabs"
              role="tablist"
              aria-label="Tri des offres"
            >
              <button
                type="button"
                role="tab"
                :aria-selected="sort === 'recent'"
                data-test="sort-recent"
                @click="sort = 'recent'"
              >
                Récentes
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="sort === 'popular'"
                data-test="sort-popular"
                @click="sort = 'popular'"
              >
                Populaires
              </button>
            </div>
            <span class="count">{{ total }} offre(s)</span>
          </div>

          <ul class="offer-cards">
            <li
              v-for="offer in items"
              :key="offer.id"
            >
              <button
                type="button"
                :class="['job-card', { selected: offer.id === selectedId }]"
                :aria-pressed="offer.id === selectedId"
                data-test="offer"
                @click="selectedId = offer.id"
              >
                <div class="job-head">
                  <span
                    :class="logoClass(offer)"
                    aria-hidden="true"
                  >{{ initial(offer) }}</span>
                  <div>
                    <span class="job-title">{{ offer.title }}</span>
                    <span class="job-company">{{ offer.company ?? "Entreprise non indiquée" }}</span>
                  </div>
                  <span class="job-date">{{ formatDate(offer.first_seen_at) }}</span>
                </div>
                <span
                  v-if="offer.filter_reasons?.length"
                  class="badge reason"
                >{{ offer.filter_reasons[0] }}</span>
                <p
                  v-if="offer.snippet"
                  class="job-snippet"
                >
                  {{ offer.snippet }}
                </p>
                <div class="job-meta">
                  <span v-if="offer.location"><AppIcon name="pin" />{{ offer.location }}</span>
                  <span v-if="rateText(offer.rate_min, offer.rate_max)">
                    <AppIcon name="rate" />{{ rateText(offer.rate_min, offer.rate_max) }}
                  </span>
                  <span><AppIcon name="globe" />{{ sites(offer) }}</span>
                  <span v-if="offer.seen_count > 1"><AppIcon name="eye" />vue {{ offer.seen_count }} fois</span>
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
            Afficher plus <AppIcon name="chevron" />
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
          <span
            :class="[logoClass(selected), 'large']"
            aria-hidden="true"
          >{{ initial(selected) }}</span>
          <div>
            <h2>{{ selected.title }}</h2>
            <span class="detail">{{ selected.company ?? "Entreprise non indiquée" }}</span>
          </div>
          <p
            v-if="selected.snippet"
            class="detail-snippet"
          >
            {{ selected.snippet }}
          </p>
          <p
            v-else
            class="detail-snippet"
          >
            Pas d'extrait dans l'alerte : le texte complet de l'annonce est sur le site.
          </p>
          <ul
            v-if="selected.filter_reasons?.length"
            class="reasons"
            data-test="reasons"
          >
            <li
              v-for="reason in selected.filter_reasons"
              :key="reason"
            >
              {{ reason }}
            </li>
          </ul>
          <ul class="checks">
            <li>
              <AppIcon name="check" /><strong>Lieu.</strong>
              <span>{{ selected.location ?? "non indiqué" }}</span>
            </li>
            <li>
              <AppIcon name="check" /><strong>Taux.</strong>
              <span>{{ rateText(selected.rate_min, selected.rate_max) || "non indiqué" }}</span>
            </li>
            <li>
              <AppIcon name="check" /><strong>Vue.</strong>
              <span>{{ selected.seen_count }} fois, sur {{ sites(selected) }}</span>
            </li>
            <li>
              <AppIcon name="check" /><strong>Depuis.</strong>
              <span>{{ formatDate(selected.first_seen_at) }}</span>
            </li>
          </ul>
          <div class="actions">
            <a
              v-for="link in selected.links"
              :key="link.source"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
            >Voir sur {{ sourceLabel[link.source] }} <AppIcon name="chevron" /></a>
          </div>
        </article>
        <div
          v-else
          class="detail-panel empty-detail"
        >
          Choisis une offre pour voir son détail.
        </div>
      </div>
    </div>
  </section>
</template>
