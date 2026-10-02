<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { api, type ParseStatus, type Search, type SearchDetail, type Source } from "../api/client";
import { formatDateTime, parseStatusLabel, rateText, sourceLabel } from "../format";

const PAGE_SIZE = 50;

const source = ref<Source | "">("");
const parseStatus = ref<ParseStatus | "">("");
const items = ref<Search[]>([]);
const total = ref(0);
const loading = ref(false);
const failed = ref(false);
const selected = ref<SearchDetail | null>(null);
const collectMessage = ref("");
const collecting = ref(false);

async function load(append = false): Promise<void> {
  loading.value = true;
  failed.value = false;
  try {
    const { data } = await api.GET("/api/searches", {
      params: {
        query: {
          source: source.value || undefined,
          parse_status: parseStatus.value || undefined,
          limit: PAGE_SIZE,
          offset: append ? items.value.length : 0,
        },
      },
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

async function select(search: Search): Promise<void> {
  if (selected.value?.id === search.id) {
    selected.value = null;
    return;
  }
  const { data } = await api.GET("/api/searches/{search_id}", {
    params: { path: { search_id: search.id } },
  });
  selected.value = data ?? null;
}

async function collectNow(): Promise<void> {
  collecting.value = true;
  try {
    const { data, response } = await api.POST("/api/collect");
    if (response.status === 409) {
      collectMessage.value = "Collecte non configurée : renseigne JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD dans .env.";
    } else if (data?.result === "already_queued") {
      collectMessage.value = "Une collecte attend déjà son tour.";
    } else if (data?.result === "queued") {
      collectMessage.value = "Collecte lancée. Le journal se met à jour d'ici une minute.";
    } else {
      collectMessage.value = "La collecte n'a pas pu être lancée.";
    }
  } catch {
    collectMessage.value = "API injoignable.";
  } finally {
    collecting.value = false;
  }
}

watch([source, parseStatus], () => {
  selected.value = null;
  void load();
});
onMounted(() => void load());
</script>

<template>
  <section>
    <div class="page-head">
      <div>
        <h1>Journal</h1>
        <p class="muted">
          Alertes reçues : chaque e-mail est une recherche exécutée par un site.
        </p>
      </div>
      <button
        type="button"
        class="primary"
        :disabled="collecting"
        data-test="collect"
        @click="collectNow"
      >
        Collecter maintenant
      </button>
    </div>
    <p
      v-if="collectMessage"
      class="notice"
      role="status"
    >
      {{ collectMessage }}
    </p>

    <div class="filters">
      <label>
        Site
        <select
          v-model="source"
          data-test="filter-source"
        >
          <option value="">Tous</option>
          <option
            v-for="(label, key) in sourceLabel"
            :key="key"
            :value="key"
          >{{ label }}</option>
        </select>
      </label>
      <label>
        Analyse
        <select
          v-model="parseStatus"
          data-test="filter-status"
        >
          <option value="">Toutes</option>
          <option
            v-for="(label, key) in parseStatusLabel"
            :key="key"
            :value="key"
          >{{ label }}</option>
        </select>
      </label>
      <span class="muted">{{ total }} alerte(s)</span>
    </div>

    <p
      v-if="failed"
      class="notice error"
    >
      Impossible de charger le journal.
    </p>
    <p
      v-else-if="!loading && items.length === 0"
      class="muted"
    >
      Aucune alerte reçue pour l'instant.
    </p>

    <table
      v-if="items.length"
      class="runs clickable"
    >
      <thead>
        <tr>
          <th>Reçue</th>
          <th>Site</th>
          <th>Alerte</th>
          <th>Offres</th>
          <th>Nouvelles</th>
          <th>Analyse</th>
        </tr>
      </thead>
      <tbody>
        <template
          v-for="search in items"
          :key="search.id"
        >
          <tr
            :class="{ selected: selected?.id === search.id }"
            data-test="search"
            tabindex="0"
            @click="select(search)"
            @keydown.enter="select(search)"
          >
            <td>{{ formatDateTime(search.received_at) }}</td>
            <td>{{ sourceLabel[search.source] }}</td>
            <td>{{ search.alert_label ?? search.subject ?? "–" }}</td>
            <td>{{ search.results_count }}</td>
            <td>{{ search.new_offers_count }}</td>
            <td :class="['parse', search.parse_status]">
              {{ parseStatusLabel[search.parse_status] }}
            </td>
          </tr>
          <tr
            v-if="selected?.id === search.id"
            class="detail-row"
          >
            <td colspan="6">
              <p
                v-if="selected.error"
                class="notice error"
              >
                {{ selected.error }}
              </p>
              <p
                v-if="selected.offers.length === 0"
                class="muted"
              >
                Aucune offre extraite de cet e-mail.
              </p>
              <ul
                v-else
                class="offer-list"
              >
                <li
                  v-for="offer in selected.offers"
                  :key="offer.id"
                  data-test="detail-offer"
                >
                  <span
                    v-if="offer.is_first"
                    class="badge new"
                  >nouvelle</span>
                  <strong>{{ offer.title }}</strong>
                  <span class="detail">
                    {{ [offer.company, offer.location, rateText(offer.rate_min, offer.rate_max)].filter(Boolean).join(" · ") }}
                  </span>
                  <a
                    v-for="link in offer.links"
                    :key="link.source"
                    :href="link.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="link"
                  >voir sur {{ sourceLabel[link.source] }}</a>
                </li>
              </ul>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

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
