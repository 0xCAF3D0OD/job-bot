<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { api, type ParseStatus, type Search, type SearchDetail, type Source } from "../api/client";
import { useCollect } from "../composables/useCollect";
import AppIcon from "./AppIcon.vue";
import StatusPill from "./StatusPill.vue";
import { dateWithTime } from "../dates";
import { SITE_NAMES, parseStatusLabel, plural, rateText, sourceLabel } from "../format";

// L'analyse d'une alerte en pastille (§4) : réussie en vert, le rouge seulement pour un vrai échec.
const PARSE_TONE: Record<ParseStatus, "neutral" | "ok" | "error"> = { parsed: "ok", empty: "neutral", unrecognized: "neutral", failed: "error" };

const PAGE_SIZE = 10;

const source = ref<Source | "">("");
const parseStatus = ref<ParseStatus | "">("");
const items = ref<Search[]>([]);
const total = ref(0);
const loading = ref(false);
const failed = ref(false);
const selected = ref<SearchDetail | null>(null);
const { running: collecting, collectNow } = useCollect();

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

watch([source, parseStatus], () => {
  selected.value = null;
  void load();
});
onMounted(() => void load());
</script>

<template>
  <div class="panel-actions">
    <button
      type="button"
      class="primary small"
      :disabled="collecting"
      data-test="collect"
      @click="collectNow"
    >
      Collecter maintenant
    </button>
  </div>
  <div class="panel">
    <div class="toolbar">
      <div class="filters">
        <label>
          Site
          <select
            v-model="source"
            data-test="filter-source"
          >
            <option value="">Tous</option>
            <option
              v-for="(label, key) in SITE_NAMES"
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
      </div>
      <span class="count">{{ plural(total, "alerte", "alertes") }}</span>
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
            <td>{{ dateWithTime(search.received_at) }}</td>
            <td>{{ sourceLabel[search.source] }}</td>
            <td>{{ search.alert_label ?? search.subject ?? "–" }}</td>
            <td>
              {{ search.results_count }}<span
                v-if="search.off_topic_count"
                class="hint"
                data-test="off-topic"
              > (+ {{ search.off_topic_count }} hors métier, écartées)</span>
            </td>
            <td>{{ search.new_offers_count }}</td>
            <td>
              <StatusPill :tone="PARSE_TONE[search.parse_status]">
                {{ parseStatusLabel[search.parse_status] }}
              </StatusPill>
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
                  <strong>{{ offer.title }}</strong>
                  <StatusPill
                    v-if="offer.is_first"
                    :dot="false"
                    data-test="detail-offer-new"
                  >
                    Nouvelle
                  </StatusPill>
                  <span
                    class="detail meta-line"
                    data-test="detail-offer-meta"
                  >
                    <span v-if="offer.company"><AppIcon name="building" /><span class="visually-hidden">Entreprise : </span>{{ offer.company }}</span>
                    <span v-if="offer.location"><AppIcon name="pin" /><span class="visually-hidden">Lieu : </span>{{ offer.location }}</span>
                    <span v-if="rateText(offer.rate_min, offer.rate_max)"><AppIcon name="rate" /><span class="visually-hidden">Taux : </span>{{ rateText(offer.rate_min, offer.rate_max) }}</span>
                  </span>
                  <a
                    v-for="link in offer.links"
                    :key="link.source"
                    :href="link.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="link"
                  ><span class="with-icon"><AppIcon name="external" />voir sur {{ sourceLabel[link.source] }}<span class="visually-hidden"> (nouvel onglet)</span></span></a>
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
      <span class="with-icon"><AppIcon name="chevron-down" />Afficher plus</span>
    </button>
  </div>
</template>
