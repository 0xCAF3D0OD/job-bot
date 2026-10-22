<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type FilterKey, type Offer, type OfferFacets } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import IconButton from "../components/IconButton.vue";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import PushTransition from "../components/PushTransition.vue";
import SidePanel from "../components/SidePanel.vue";
import SpontaneousForm from "../components/SpontaneousForm.vue";
import ManualOfferForm from "../components/ManualOfferForm.vue";
import FirstOffers from "../components/FirstOffers.vue";
import { usePhone } from "../composables/usePhone";
import OfferFiltersPanel from "../components/OfferFiltersPanel.vue";
import FaceState from "../components/FaceState.vue";
import { applicationBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { useJobsMemory } from "../composables/useJobsMemory";
import { activeCount, useOfferFilters, type View } from "../composables/useOfferFilters";
import { dayKey, dayName, plural } from "../format";
import { useDataChanged } from "../composables/useDataChanged";
import { usePageReady } from "../composables/usePageTransition";
import PlanLimit from "../components/PlanLimit.vue";

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
const firstLoaded = ref(false);
usePageReady("offers", () => firstLoaded.value);
const selectedId = ref<number | null>(null);
const chunkTitles = ref<Record<number, string>>({});
const filtersOpen = ref(false);
const { phone } = usePhone();
// Candidature spontanée (docs/39) : sans annonce, préparée comme une offre.
const spontaneousOpen = ref(false);
// Ajouter une offre trouvée ailleurs (docs/111), aussi par « Partager vers jobA1 » sur Android :
// /candidatures/offres?ajouter=1&url=…&text=… ouvre le formulaire, lien ou texte déjà là.
const manualOpen = ref(false);
const shared = ref<{ url: string | null; text: string | null }>({ url: null, text: null });

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);

// Tri « Par jour » (docs/73 §3) : une ligne par jour (« Aujourd'hui », « Hier », « Jeudi
// 15 octobre ») et les offres du jour dessous, sans leur date ; heure suisse.
// Offre ouverte par un lien (?offre=) hors de la vue : posée en tête, sans ligne de jour, et
// comptée dans aucun jour.
const pinnedId = ref<number | null>(null);
const byDay = computed(() => filters.value.sort === "day");
const dayCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const offer of items.value) {
    if (offer.id === pinnedId.value) continue;
    const key = dayKey(offer.first_seen_at);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});
type Day = { name: string; count: string };
function dayHeader(index: number): Day | null {
  if (!byDay.value) return null;
  const offer = items.value[index];
  if (!offer || offer.id === pinnedId.value) return null;
  const key = dayKey(offer.first_seen_at);
  const previous = items.value.slice(0, index).filter((o) => o.id !== pinnedId.value).at(-1);
  if (previous && dayKey(previous.first_seen_at) === key) return null;
  return { name: dayName(offer.first_seen_at), count: plural(dayCounts.value.get(key) ?? 0, "offre", "offres") };
}
// Une liste à plat (lignes de jour et offres) pour que chaque offre s'anime seule (docs/60 §3).
const rows = computed(() =>
  items.value.flatMap((offer, index) => {
    const day = dayHeader(index);
    const card = { key: `offer-${offer.id}`, day: null as Day | null, offer };
    return day ? [{ key: `day-${offer.id}`, day, offer: null }, card] : [card];
  }),
);
const route = useRoute();
const router = useRouter();
const assistant = useAssistant();

// L'offre ouverte est l'élément dont parle l'assistant (docs/24 §2.2).
watch(selected, (offer) => {
  assistant.setFocus(offer ? { offerId: offer.id, label: `offre ${offer.title}${offer.company ? ` chez ${offer.company}` : ""}` } : null);
  // Après la navigation d'ouverture encore en cours, sinon l'offre se rouvrirait.
  if (!offer)
    void opening.then(() => {
      if (route.query.offre) void router.replace({ query: { ...route.query, offre: undefined } });
    });
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
// L'adresse suit l'offre ouverte : « Retour » du navigateur la referme (Nielsen 3, audit du
// 22.10.2026).
watch(
  () => route.query.offre,
  (offre) => {
    if (offre) void openFromQuery();
    else selectedId.value = null;
  },
);

// Ouvrir une offre de la liste : l'adresse change, et le focus passe à son titre (le lecteur
// d'écran et le clavier suivent, audit du 22.10.2026).
let opening: Promise<unknown> = Promise.resolve();
function selectOffer(id: number): void {
  selectedId.value = id;
  if (route.query.offre !== String(id)) opening = router.push({ query: { ...route.query, offre: String(id) } });
  void nextTick(() => document.querySelector<HTMLElement>("[data-test=offer-detail-title]")?.focus({ preventScroll: true }));
}

// Android partage souvent le lien dans le texte (« Titre https://… ») : on l'en sort.
function openShared(): void {
  if (!route.query.ajouter) return;
  const pick = (key: string) => (typeof route.query[key] === "string" ? String(route.query[key]).trim() : "");
  const sharedText = [pick("title"), pick("text")].filter(Boolean).join("\n");
  const found = pick("url") || sharedText.match(/https:\/\/\S+/)?.[0] || "";
  const rest = sharedText.replace(found, "").trim();
  shared.value = { url: found || null, text: found ? null : rest || null };
  manualOpen.value = true;
  void router.replace({ query: { ...route.query, ajouter: undefined, url: undefined, text: undefined, title: undefined } });
}
watch(() => route.query.ajouter, () => openShared());

function openManual(): void {
  shared.value = { url: null, text: null };
  manualOpen.value = true;
}

// L'offre ajoutée (ou déjà là) s'ouvre ; écartée par les critères, elle est gardée avec la raison.
async function manualAdded(result: { id: number; existing: boolean; status: string; reasons: string[] }): Promise<void> {
  manualOpen.value = false;
  undo.value = null;
  notice.value = result.existing
    ? "Cette offre était déjà là : la voici."
    : result.status === "filtered_out"
      ? `Offre ajoutée. Tes critères l'écartent (${result.reasons.join(" ; ")}) : elle est dans « Écartées ».`
      : "Offre ajoutée : sa note arrive dans un instant.";
  await load();
  await router.replace({ query: { ...route.query, offre: String(result.id) } });
  await openFromQuery();
}
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
    if (current === requestId) {
      loading.value = false;
      firstLoaded.value = true;
    }
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
  // L'offre quitte la vue actuelle si elle n'y a plus sa place : on recharge ; sa carte
  // s'efface et les suivantes remontent (docs/60 §3), avec « Annuler » dans le message.
  if (status !== "preparing") selectedId.value = null;
  const previous = offer.status;
  undo.value =
    status in STATUS_TEXT && previous !== status && (previous === "to_review" || previous === "later" || previous === "ignored")
      ? { id: offer.id, status: previous }
      : null;
  notice.value = undo.value ? `Passée en ${STATUS_TEXT[status]}.` : "";
  await load();
}

const STATUS_TEXT: Record<string, string> = { later: "Plus tard", ignored: "Ignorées", to_review: "À examiner" };
const undo = ref<{ id: number; status: "to_review" | "later" | "ignored" } | null>(null);
async function undoStatus(): Promise<void> {
  const last = undo.value;
  if (!last) return;
  undo.value = null;
  notice.value = "";
  await api.PATCH("/api/offers/{offer_id}/status", { params: { path: { offer_id: last.id } }, body: { status: last.status } });
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
  openShared();
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
      <!-- Filtrer (docs/101) : l'entonnoir seul, le nombre de filtres actifs en pastille. -->
      <button
        type="button"
        class="icon-button icon-only filters-toggle"
        :aria-label="activeCount(filters) ? `Filtrer, ${plural(activeCount(filters), 'filtre actif', 'filtres actifs')}` : 'Filtrer'"
        data-label="Filtrer"
        :aria-expanded="filtersOpen"
        data-test="filters-toggle"
        @click="filtersOpen = !filtersOpen"
      >
        <AppIcon name="filter" />
        <span
          v-if="activeCount(filters)"
          class="icon-badge"
          aria-hidden="true"
          data-test="filters-count"
        >{{ activeCount(filters) }}</span>
      </button>
    </div>

    <div :class="['offers-grid', { 'has-selection': selected }]">
      <!-- Téléphone (docs/36 §3) : une carte pleine largeur qui pousse la liste. -->
      <PushTransition :enabled="phone">
        <section
          v-show="!phone || filtersOpen"
          :class="['filters-column', { open: filtersOpen }]"
        >
          <div class="filters-sheet-head">
            <span
              class="sheet-grabber"
              aria-hidden="true"
            />
            <strong>Filtres</strong>
            <IconButton
              icon="close"
              label="Fermer les filtres"
              class="close"
              data-test="close-filters"
              @click="filtersOpen = false"
            />
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
        </section>
      </PushTransition>

      <div class="offers-list">
        <p
          v-if="notice"
          class="notice"
          role="status"
        >
          {{ notice }}
          <button
            v-if="undo"
            type="button"
            class="link"
            data-test="undo-status"
            @click="undoStatus"
          >
            Annuler
          </button>
        </p>
        <!-- Les premières offres (docs/104, 0.80.0) : la recherche publique de jobup. -->
        <FirstOffers
          where="offers"
          @arrived="load()"
        />
        <!-- « Ajouter une offre » et « Candidature spontanée » sur la ligne du nombre d'offres
             (docs/43 n° 11, docs/111). -->
        <div class="list-count-row">
          <p class="count list-count">
            {{ plural(total, "offre", "offres") }}{{ loading ? "…" : "" }}
          </p>
          <span class="list-count-actions">
            <button
              type="button"
              class="secondary small"
              data-test="manual-open"
              @click="openManual"
            >
              Ajouter une offre
            </button>
            <button
              type="button"
              class="secondary small"
              data-test="spontaneous-open"
              @click="spontaneousOpen = true"
            >
              Candidature spontanée
            </button>
          </span>
        </div>
        <PlanLimit usage="score" />
        <p
          v-if="failed"
          class="notice error"
        >
          Impossible de charger les offres.
        </p>
        <FaceState
          v-else-if="!loading && items.length === 0"
          title="Aucune offre"
          data-test="offers-empty"
        >
          <p>
            Rien ne correspond pour l'instant.
            <button
              v-if="activeCount(filters)"
              type="button"
              class="link"
              @click="reset"
            >
              <span class="with-icon"><AppIcon name="close" />Effacer les filtres</span>
            </button>
          </p>
        </FaceState>
        <TransitionGroup
          tag="ul"
          name="card"
          class="offer-cards"
        >
          <li
            v-for="row in rows"
            :key="row.key"
            :class="{ 'offer-day': row.day }"
            :data-test="row.day ? 'offer-day' : undefined"
          >
            <h2
              v-if="row.day"
              class="offer-day-title"
            >
              <span class="offer-day-name">{{ row.day.name }}</span>
              <span class="offer-day-count">{{ row.day.count }}</span>
            </h2>
            <OfferCard
              v-else-if="row.offer"
              :offer="row.offer"
              :selected="row.offer.id === selectedId"
              :show-date="!byDay || row.offer.id === pinnedId"
              @select="selectOffer(row.offer.id)"
            />
          </li>
        </TransitionGroup>
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
  <SidePanel
    v-if="manualOpen"
    open
    title="Ajouter une offre"
    @close="manualOpen = false"
  >
    <ManualOfferForm
      :initial-url="shared.url"
      :initial-text="shared.text"
      @added="manualAdded"
    />
  </SidePanel>
</template>
