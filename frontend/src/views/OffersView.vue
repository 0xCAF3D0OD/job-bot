<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import { api, type Offer, type OfferFacets } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import OfferFiltersPanel from "../components/OfferFiltersPanel.vue";
import { activeCount, useOfferFilters, type View } from "../composables/useOfferFilters";

const PAGE_SIZE = 50;

const { filters, update, reset } = useOfferFilters();
const items = ref<Offer[]>([]);
const total = ref(0);
const counts = ref<Record<View, number>>({
  to_review: 0,
  filtered_out: 0,
  later: 0,
  in_progress: 0,
  all: 0,
});
const applying = ref<ApplicationFormValue | null>(null);
const applyError = ref("");
const notice = ref("");
const facets = ref<OfferFacets>({ sources: [], cantons: [] });
const loading = ref(false);
const failed = ref(false);
const selectedId = ref<number | null>(null);
const chunkTitles = ref<Record<number, string>>({});
const filtersOpen = ref(false);

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);
let requestId = 0;

async function load(append = false): Promise<void> {
  const current = ++requestId;
  loading.value = true;
  failed.value = false;
  const f = filters.value;
  try {
    const { data } = await api.GET("/api/offers", {
      params: {
        query: {
          limit: PAGE_SIZE,
          offset: append ? items.value.length : 0,
          sort: f.sort,
          view: f.view,
          q: f.q || undefined,
          sources: f.sources.length ? f.sources : undefined,
          cantons: f.cantons.length ? f.cantons : undefined,
          min_rate: f.minRate ?? undefined,
          min_score: f.minScore ?? undefined,
          external_only: f.externalOnly || undefined,
        },
      },
    });
    if (current !== requestId) return; // une requête plus récente est partie entre-temps
    if (!data) throw new Error("réponse vide");
    items.value = append ? [...items.value, ...data.items] : data.items;
    total.value = data.total;
    counts.value = data.counts;
    facets.value = data.facets;
  } catch {
    if (current === requestId) failed.value = true;
  } finally {
    if (current === requestId) loading.value = false;
  }
}

async function setStatus(status: "to_review" | "later" | "ignored" | "preparing"): Promise<void> {
  const offer = selected.value;
  if (!offer) return;
  const { error } = await api.PATCH("/api/offers/{offer_id}/status", {
    params: { path: { offer_id: offer.id } },
    body: { status },
  });
  if (error) {
    notice.value = "Changement refusé.";
    return;
  }
  // L'offre quitte la vue actuelle si elle n'y a plus sa place : on recharge.
  if (status !== "preparing") selectedId.value = null;
  await load();
}

async function openApplication(): Promise<void> {
  const offer = selected.value;
  if (!offer) return;
  applyError.value = "";
  const { data } = await api.GET("/api/offers/{offer_id}/application-prefill", {
    params: { path: { offer_id: offer.id } },
  });
  if (data) applying.value = { ...data, status: "en_attente" };
}

async function saveApplication(value: ApplicationFormValue): Promise<void> {
  const { data, error } = await api.POST("/api/applications", {
    body: {
      offer_id: value.offer_id ?? null,
      sent_at: value.sent_at,
      method: value.method,
      assigned_by_orp: value.assigned_by_orp,
      company: value.company,
      company_address: value.company_address || null,
      contact_name: value.contact_name || null,
      contact_phone: value.contact_phone || null,
      job_title: value.job_title,
      location: value.location || null,
      rate_text: value.rate_text || null,
    },
  });
  if (!data) {
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    applyError.value = typeof detail === "string" ? detail : "Vérifie les champs obligatoires.";
    return;
  }
  applying.value = null;
  notice.value = `Candidature chez ${data.company} enregistrée.`;
  await load();
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  if (applying.value) applying.value = null;
  else if (filtersOpen.value) filtersOpen.value = false;
  else selectedId.value = null;
}

watch(filters, () => void load(), { deep: true });
async function loadChunkTitles(): Promise<void> {
  try {
    const { data } = await api.GET("/api/profile-chunks");
    chunkTitles.value = Object.fromEntries((data ?? []).map((c) => [c.id, c.title]));
  } catch {
    chunkTitles.value = {};
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  void load();
  void loadChunkTitles();
});
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <section class="offers-page">
    <div class="offers-heading">
      <div>
        <span class="eyebrow">Offres</span>
        <h1>Les offres pour toi</h1>
      </div>
      <button
        type="button"
        class="secondary filters-toggle"
        :aria-expanded="filtersOpen"
        data-test="filters-toggle"
        @click="filtersOpen = !filtersOpen"
      >
        Filtres{{ activeCount(filters) ? ` (${activeCount(filters)})` : "" }}
      </button>
    </div>

    <div :class="['offers-grid', { 'has-selection': selected }]">
      <aside :class="['filters-column', { open: filtersOpen }]">
        <div class="filters-sheet-head">
          <strong>Filtres</strong>
          <button
            type="button"
            class="close"
            aria-label="Fermer les filtres"
            @click="filtersOpen = false"
          >
            ×
          </button>
        </div>
        <OfferFiltersPanel
          :filters="filters"
          :counts="counts"
          :facets="facets"
          @update="update"
          @reset="reset"
        />
        <button
          type="button"
          class="primary sheet-done"
          @click="filtersOpen = false"
        >
          Voir {{ total }} offre(s)
        </button>
      </aside>

      <div class="offers-list">
        <p
          v-if="notice"
          class="notice"
          role="status"
        >
          {{ notice }}
        </p>
        <p class="count list-count">
          {{ total }} offre(s){{ loading ? "…" : "" }}
        </p>
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
          Aucune offre ne correspond.
          <button
            v-if="activeCount(filters)"
            type="button"
            class="link"
            @click="reset"
          >
            Effacer les filtres
          </button>
        </p>
        <ul class="offer-cards">
          <li
            v-for="offer in items"
            :key="offer.id"
          >
            <OfferCard
              :offer="offer"
              :selected="offer.id === selectedId"
              @select="selectedId = offer.id"
            />
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

      <div
        v-if="selected"
        class="detail-column"
        @click.self="selectedId = null"
      >
        <OfferDetail
          :offer="selected"
          :chunk-titles="chunkTitles"
          @close="selectedId = null"
          @status="setStatus"
          @applied="openApplication"
        />
      </div>
      <div
        v-else
        class="detail-column placeholder"
      >
        <div class="detail-panel empty-detail">
          Choisis une offre pour voir son détail.
        </div>
      </div>
    </div>
  </section>
  <ApplicationForm
    v-if="applying"
    title="Marquer comme envoyée"
    :initial="applying"
    :with-status="false"
    :error="applyError"
    @submit="saveApplication"
    @close="applying = null"
  />
</template>
