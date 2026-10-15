<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type FilterKey, type Offer, type OfferFacets } from "../api/client";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import PushTransition from "../components/PushTransition.vue";
import SidePanel from "../components/SidePanel.vue";
import SpontaneousForm from "../components/SpontaneousForm.vue";
import { usePhone } from "../composables/usePhone";
import OfferFiltersPanel from "../components/OfferFiltersPanel.vue";
import { applicationBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { useJobsMemory } from "../composables/useJobsMemory";
import { activeCount, useOfferFilters, type View } from "../composables/useOfferFilters";
import { plural } from "../format";
import { useDataChanged } from "../composables/useDataChanged";

const PAGE_SIZE = 50;

const { filters, update, reset } = useOfferFilters();
const items = ref<Offer[]>([]);
const total = ref(0);
const counts = ref<Record<View, number>>({
  to_review: 0,
  filtered_out: 0,
  later: 0,
  in_progress: 0,
  expired: 0,
  all: 0,
});
const applying = ref<ApplicationFormValue | null>(null);
const applyError = ref("");
const notice = ref("");
const facets = ref<OfferFacets>({ sources: [], cantons: [], scores: [], unscored: 0 });
const loading = ref(false);
const failed = ref(false);
const selectedId = ref<number | null>(null);
const chunkTitles = ref<Record<number, string>>({});
const filtersOpen = ref(false);
const { phone } = usePhone();
// Candidature spontanée (docs/39) : sans annonce, préparée comme une offre.
const spontaneousOpen = ref(false);

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);

// Tri « Par jour » : les offres groupées comme les Actualités, Aujourd'hui · Cette semaine ·
// Plus ancien (docs/43 n° 12), la date restant sur chaque carte ; heure suisse.
const dayKey = (iso: string): string => new Date(iso).toLocaleDateString("sv-SE", { timeZone: "Europe/Zurich" });
const PERIOD_LABELS = { today: "Aujourd'hui", week: "Cette semaine", older: "Plus ancien" } as const;
function periodOf(iso: string): keyof typeof PERIOD_LABELS {
  if (dayKey(iso) === dayKey(new Date().toISOString())) return "today";
  return Date.now() - new Date(iso).getTime() < 7 * 86_400_000 ? "week" : "older";
}
// Offre ouverte par un lien (?offre=) hors de la vue : posée en tête, sans intertitre, et
// comptée dans aucun groupe (sinon « Plus ancien » apparaissait deux fois).
const pinnedId = ref<number | null>(null);
const periodCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const offer of items.value) {
    if (offer.id === pinnedId.value) continue;
    const key = periodOf(offer.first_seen_at);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});
function dayHeader(index: number): string | null {
  if (filters.value.sort !== "day") return null;
  const offer = items.value[index];
  if (!offer || offer.id === pinnedId.value) return null;
  const key = periodOf(offer.first_seen_at);
  const previous = items.value.slice(0, index).filter((o) => o.id !== pinnedId.value).at(-1);
  if (previous && periodOf(previous.first_seen_at) === key) return null;
  return `${PERIOD_LABELS[key]} · ${plural(periodCounts.value.get(key) ?? 0, "offre", "offres")}`;
}
const route = useRoute();
const router = useRouter();
const assistant = useAssistant();

// L'offre ouverte est l'élément dont parle l'assistant (docs/24 §2.2).
watch(selected, (offer) => {
  assistant.setFocus(offer ? { offerId: offer.id, label: `offre ${offer.title}${offer.company ? ` chez ${offer.company}` : ""}` } : null);
  if (!offer && route.query.offre) void router.replace({ query: { ...route.query, offre: undefined } });
});

// Lien de l'assistant : /candidatures/offres?offre=12 ouvre l'offre, même hors de la liste.
async function openFromQuery(): Promise<void> {
  const id = Number(route.query.offre);
  if (!Number.isInteger(id) || id <= 0) return;
  if (!items.value.some((o) => o.id === id)) {
    const { data } = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: id } } });
    if (!data) return;
    items.value = [data, ...items.value];
    pinnedId.value = id;
  }
  selectedId.value = id;
}
watch(() => route.query.offre, () => void openFromQuery());
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
          max_score: f.maxScore ?? undefined,
          external_only: f.externalOnly || undefined,
          remote: f.remote ?? undefined,
          hide_doubtful: f.hideDoubtful || undefined,
        },
      },
    });
    if (current !== requestId) return; // une requête plus récente est partie entre-temps
    if (!data) throw new Error("réponse vide");
    items.value = append ? [...items.value, ...data.items] : data.items;
    if (!append) pinnedId.value = null;
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

// « Signaler comme expirée » / « Pas expirée » (docs/11 §1) : prioritaire sur la détection.
async function setExpiry(expired: boolean): Promise<void> {
  const offer = selected.value;
  if (!offer) return;
  const { error } = await api.PATCH("/api/offers/{offer_id}/expiry", {
    params: { path: { offer_id: offer.id } },
    body: { expired },
  });
  if (error) {
    notice.value = "Changement refusé.";
    return;
  }
  // En préparation, l'offre reste affichée (avec ou sans bandeau) ; ailleurs elle change d'onglet.
  if (offer.status !== "preparing") selectedId.value = null;
  notice.value = expired ? "Offre signalée comme expirée." : "Offre remise dans sa liste.";
  await load();
}

async function setAddress(address: string): Promise<void> {
  const offer = selected.value;
  if (!offer) return;
  const { error } = await api.PATCH("/api/offers/{offer_id}/address", {
    params: { path: { offer_id: offer.id } },
    body: { address: address.trim() || null },
  });
  notice.value = error ? "Adresse refusée (300 caractères au plus)." : "Adresse enregistrée.";
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
    body: { ...applicationBody(value), offer_id: value.offer_id ?? null },
  });
  if (!data) {
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    applyError.value = typeof detail === "string" ? detail : "Vérifie les champs obligatoires.";
    return;
  }
  applying.value = null;
  if (data.offer_id) useJobsMemory().sent(data.offer_id);
  notice.value = `Candidature chez ${data.company} enregistrée.`;
  await load();
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  // Échap ferme la couche du dessus seulement : bulle d'aide ou panneau latéral d'abord.
  if (event.defaultPrevented || document.documentElement.classList.contains("side-open")) return;
  if (applying.value) applying.value = null;
  else if (filtersOpen.value) filtersOpen.value = false;
  else selectedId.value = null;
}

watch(filters, () => void load(), { deep: true });

// Filtres affichés (docs/10 §3), enregistrés en base ; tous par défaut.
const ALL_FILTERS: FilterKey[] = ["score", "sources", "cantons", "rate", "external"];
const visibleFilters = ref<FilterKey[]>([...ALL_FILTERS]);

async function loadVisibility(): Promise<void> {
  try {
    const { data } = await api.GET("/api/offer-filters");
    if (Array.isArray(data?.visible)) visibleFilters.value = data.visible;
  } catch {
    // Panneau complet si l'API ne répond pas.
  }
}

async function setVisibility(visible: FilterKey[]): Promise<void> {
  visibleFilters.value = visible;
  // Un filtre masqué ne doit pas cacher d'offres sans qu'on le voie : il est remis à zéro.
  const hidden = ALL_FILTERS.filter((key) => !visible.includes(key));
  const patch: Partial<typeof filters.value> = {};
  if (hidden.includes("score") && filters.value.minScore !== null) patch.minScore = null;
  if (hidden.includes("sources") && filters.value.sources.length) patch.sources = [];
  if (hidden.includes("cantons") && filters.value.cantons.length) patch.cantons = [];
  if (hidden.includes("rate") && filters.value.minRate !== null) patch.minRate = null;
  if (hidden.includes("external") && filters.value.externalOnly) patch.externalOnly = false;
  if (Object.keys(patch).length) update(patch);
  await api.PUT("/api/offer-filters", { body: { visible } });
}

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
  void load().then(openFromQuery);
  void loadChunkTitles();
  void loadVisibility();
});
useDataChanged(() => load());
onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
  assistant.setFocus(null);
});
</script>

<template>
  <section class="offers-page">
    <!-- Titre et onglets : en-tête de la rubrique Candidatures (docs/19 §2). -->
    <div class="offers-heading">
      <button
        type="button"
        class="secondary filters-toggle"
        :aria-expanded="filtersOpen"
        data-test="filters-toggle"
        @click="filtersOpen = !filtersOpen"
      >
        Filtrer{{ activeCount(filters) ? ` · ${activeCount(filters)}` : "" }}
      </button>
    </div>

    <div :class="['offers-grid', { 'has-selection': selected }]">
      <!-- Téléphone (docs/36 §3) : une carte pleine largeur qui pousse la liste. -->
      <PushTransition :enabled="phone">
        <aside
          v-show="!phone || filtersOpen"
          :class="['filters-column', { open: filtersOpen }]"
        >
          <div class="filters-sheet-head">
            <span
              class="sheet-grabber"
              aria-hidden="true"
            />
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
            :visible="visibleFilters"
            :total="total"
            @update="update"
            @reset="reset"
            @visibility="setVisibility"
            @done="filtersOpen = false"
          />
        </aside>
      </PushTransition>

      <div class="offers-list">
        <p
          v-if="notice"
          class="notice"
          role="status"
        >
          {{ notice }}
        </p>
        <!-- « Candidature spontanée » sur la ligne du nombre d'offres (docs/43 n° 11). -->
        <div class="list-count-row">
          <p class="count list-count">
            {{ plural(total, "offre", "offres") }}{{ loading ? "…" : "" }}
          </p>
          <button
            type="button"
            class="secondary small spontaneous-open"
            data-test="spontaneous-open"
            @click="spontaneousOpen = true"
          >
            Candidature spontanée
          </button>
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
          <template
            v-for="(offer, index) in items"
            :key="offer.id"
          >
            <li
              v-if="dayHeader(index)"
              class="offer-day"
              data-test="offer-day"
            >
              <h2 class="offer-day-title">
                {{ dayHeader(index) }}
              </h2>
            </li>
            <li>
              <OfferCard
                :offer="offer"
                :selected="offer.id === selectedId"
                @select="selectedId = offer.id"
              />
            </li>
          </template>
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

      <Transition name="detail">
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
            @expiry="setExpiry"
            @address="setAddress"
            @changed="load()"
          />
        </div>
      </Transition>
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
  <SidePanel
    v-if="spontaneousOpen"
    open
    title="Candidature spontanée"
    @close="spontaneousOpen = false"
  >
    <SpontaneousForm @created="load()" />
  </SidePanel>
</template>
