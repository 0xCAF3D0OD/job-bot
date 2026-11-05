<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, Teleport, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type FilterKey, type Offer, type OfferFacets } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import IconButton from "../components/IconButton.vue";
import OfferActionSheet from "../components/OfferActionSheet.vue";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import ShowMore from "../components/ShowMore.vue";
import SidePanel from "../components/SidePanel.vue";
import SpontaneousForm from "../components/SpontaneousForm.vue";
import ManualOfferForm from "../components/ManualOfferForm.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import FirstOffers from "../components/FirstOffers.vue";
import { usePhone } from "../composables/usePhone";
import OfferFilterSheet from "../components/OfferFilterSheet.vue";
import OfferFiltersPanel from "../components/OfferFiltersPanel.vue";
import OfferFilterChips from "../components/OfferFilterChips.vue";
import OfferSearch from "../components/OfferSearch.vue";
import FaceState from "../components/FaceState.vue";
import { applicationBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { useJobsMemory } from "../composables/useJobsMemory";
import { activeChips, activeCount, toQuery, useOfferFilters, type View } from "../composables/useOfferFilters";
import { dayKey, dayName, plural } from "../format";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import { useDataChanged } from "../composables/useDataChanged";
import { usePageReady } from "../composables/usePageTransition";
import PlanLimit from "../components/PlanLimit.vue";
import CountBadge from "../components/CountBadge.vue";

const PAGE_SIZE = 50;

const { filters, update, reset } = useOfferFilters();
const items = ref<Offer[]>([]);
const total = ref(0);
const counts = ref<Record<View, number>>({
  to_review: 0,
  pending: 0,
  filtered_out: 0,
  later: 0,
  in_progress: 0,
  expired: 0,
  all: 0,
});
// Aucune offre du tout, ni filtre : un compte neuf (docs/128 §3).
const noOffersYet = computed(() => counts.value.all === 0 && counts.value.expired === 0 && !activeCount(filters.value));
const applying = ref<ApplicationFormValue | null>(null);
const applyError = ref("");
const notice = ref("");
const facets = ref<OfferFacets>({ sources: [], cantons: [], scores: [], unscored: 0 });
const loading = ref(false);
// La fin de la phrase selon le statut regardé : « 4 offres à examiner. », « 1 offre écartée. ».
const VIEW_END: Record<string, [string, string]> = {
  pending: [" à traiter", " à traiter"],
  to_review: [" à examiner", " à examiner"],
  in_progress: [" en cours", " en cours"],
  later: [" pour plus tard", " pour plus tard"],
  filtered_out: [" écartée", " écartées"],
  expired: [" expirée", " expirées"],
  all: ["", ""],
};
// La phrase décrit la liste affichée, rien d'autre (Kevin, 2026-11-03) : « 35 offres en cours. »,
// « 12 offres à traiter avec ces filtres. ». Le nombre de tout « À traiter » est sur la pastille du segment.
// Avec les écartées ou les expirées en plus, la liste n'est plus seulement « à traiter » : « affichées ».
const sentenceEnd = computed(() => {
  const f = filters.value;
  const mixed = f.view === "pending" && (f.showFilteredOut || f.showExpired);
  const [one, many] = mixed ? [" affichée", " affichées"] : (VIEW_END[f.view] ?? ["", ""]);
  return `${total.value > 1 ? many : one}${activeCount(f) ? " avec ces filtres" : ""}`;
});
const failed = ref(false);
// Une panne de réseau (planche « Illustrations ») : l'écran « Pas de connexion », qui réessaie seul.
const offline = ref(false);
const firstLoaded = ref(false);
usePageReady("offers", () => firstLoaded.value);
const selectedId = ref<number | null>(null);
const chunkTitles = ref<Record<number, string>>({});
const filtersOpen = ref(false);
const { phone } = usePhone();
// Barre d'outils (1.6.55) : « Filtrer » ouvre un panneau sous le bouton (ordinateur) ou une feuille en
// bas de l'écran (téléphone) ; les filtres actifs restent visibles en pastilles sous la barre.
const chips = computed(() => activeChips(filters.value));
// « Note minimale : Proche et plus, Taux : 80 % et plus. Élargis un critère pour voir plus d'offres. »
const emptyFiltersLine = computed(() => {
  const q = filters.value.q.trim();
  const parts = [...(q ? [`Recherche « ${q} »`] : []), ...chips.value.map((chip) => chip.label)];
  return `${parts.join(", ")}. Élargis un critère pour voir plus d'offres.`;
});
const filterLabel = computed(() => {
  const active = chips.value.length ? `, ${plural(chips.value.length, "filtre actif", "filtres actifs")}` : "";
  if (phone.value) return `Filtres${active}`;
  return active ? `Filtrer${active}` : undefined;
});
const filterAnchor = ref<HTMLElement | null>(null);
const filterToggle = ref<HTMLButtonElement | null>(null);
// Le panneau tient sous le bouton, dans la fenêtre ; au-delà, il défile et garde son pied en bas.
const filtersRoom = ref("");
function openFilters(): void {
  const bottom = filterToggle.value?.getBoundingClientRect().bottom ?? 0;
  filtersRoom.value = `${Math.max(240, window.innerHeight - bottom - 24)}px`;
  filtersOpen.value = true;
}
function closeFilters(): void {
  filtersOpen.value = false;
  void nextTick(() => filterToggle.value?.focus({ preventScroll: true }));
}
// Un clic hors du panneau le referme (ordinateur) ; sur téléphone, c'est le voile.
function onPointerDown(event: PointerEvent): void {
  if (!filtersOpen.value || phone.value) return;
  if (event.target instanceof Node && filterAnchor.value?.contains(event.target)) return;
  filtersOpen.value = false;
}
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
// À traiter (C2, C8) : les offres en préparation viennent d'abord (le serveur les met en tête) ; triées
// par jour, elles ont leur propre titre, « En préparation », avant les jours.
function groupKey(offer: Offer): string {
  return filters.value.view === "pending" && offer.status === "preparing" ? "preparing" : dayKey(offer.first_seen_at);
}
const dayCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const offer of items.value) {
    if (offer.id === pinnedId.value) continue;
    const key = groupKey(offer);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});
type Day = { name: string; count: string; n: number };
function dayHeader(index: number): Day | null {
  const offer = items.value[index];
  if (!offer || offer.id === pinnedId.value) return null;
  const key = groupKey(offer);
  // Sur téléphone, « En préparation » a toujours son titre de section (Kevin, 2026-11-05) : les cartes
  // n'ont plus d'étiquette.
  if (!byDay.value && !(phone.value && key === "preparing")) return null;
  const previous = items.value.slice(0, index).filter((o) => o.id !== pinnedId.value).at(-1);
  if (previous && groupKey(previous) === key) return null;
  const n = dayCounts.value.get(key) ?? 0;
  return { name: key === "preparing" ? "En préparation" : dayName(offer.first_seen_at), count: plural(n, "offre", "offres"), n };
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
  if (!offer) void opening.then(() => leaveOffer());
});

// L'offre ouverte dans l'adresse : sur téléphone, la sous-page /candidatures/offres/12 (O1) ; sur ordinateur,
// ?offre=12 à côté de la liste. Les filtres de la liste restent dans l'adresse.
const routeOfferId = (): number => Number(route.params.id || route.query.offre);
// Fermer la sous-page revient à la liste par l'historique : même défilement, mêmes filtres, et le geste de
// retour d'iOS fait la même chose. Arrivé directement sur la sous-page, on remplace l'adresse.
function leaveOffer(): void {
  if (route.params.id) {
    const back = (window.history.state as { back?: string } | null)?.back;
    if (back?.startsWith("/candidatures/offres") && !/\/offres\/\d/.test(back)) router.back();
    else void router.replace({ name: "offers", params: {}, query: route.query });
  } else if (route.query.offre) void router.replace({ query: { ...route.query, offre: undefined } });
}

// Lien de l'assistant : /candidatures/offres?offre=12 ouvre l'offre, même hors de la liste.
async function openFromQuery(): Promise<void> {
  const id = routeOfferId();
  if (!Number.isInteger(id) || id <= 0) return;
  // Sur téléphone, un lien ?offre= devient la sous-page.
  if (phone.value && route.query.offre) {
    void router.replace({ name: "offers", params: { id: String(id) }, query: { ...route.query, offre: undefined } });
    return;
  }
  if (!items.value.some((o) => o.id === id)) {
    const { data } = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: id } } });
    if (!data) return;
    // Deux ouvertures en même temps (l'ajout et l'adresse) : l'offre n'est posée qu'une fois.
    if (!items.value.some((o) => o.id === id)) items.value = [data, ...items.value];
    pinnedId.value = id;
  }
  selectedId.value = id;
}
// L'adresse suit l'offre ouverte : « Retour » du navigateur la referme (Nielsen 3, audit du
// 22.10.2026).
watch(
  () => [route.params.id, route.query.offre],
  () => {
    if (routeOfferId()) void openFromQuery();
    else selectedId.value = null;
  },
);

// Ouvrir une offre de la liste : l'adresse change, et le focus passe à son titre (le lecteur
// d'écran et le clavier suivent, audit du 22.10.2026).
let opening: Promise<unknown> = Promise.resolve();
function selectOffer(id: number): void {
  selectedId.value = id;
  if (phone.value) {
    if (route.params.id !== String(id)) opening = router.push({ name: "offers", params: { id: String(id) }, query: route.query });
  } else if (route.query.offre !== String(id)) opening = router.push({ query: { ...route.query, offre: String(id) } });
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

// Tout est examiné (1.6.50) : la vue « À examiner » est vide alors que le compte a des offres.
const allReviewed = computed(
  () => !noOffersYet.value && filters.value.view === "pending" && counts.value.pending === 0 && !activeCount(filters.value),
);

// Le menu de « + Ajouter » (1.6.47) : « Ajouter une offre » attend une liste ; un compte neuf la trouve
// dans l'écran vide.
const addItems = computed<MoreMenuItem[]>(() => [
  ...(noOffersYet.value ? [] : [{ label: "Ajouter une offre", test: "manual-open", icon: "briefcase" as const, run: openManual }]),
  { label: "Postuler spontanément", test: "spontaneous-open", icon: "send" as const, run: () => (spontaneousOpen.value = true) },
]);

// L'offre ajoutée (ou déjà là) s'ouvre ; écartée par les critères, elle est gardée avec la raison.
async function manualAdded(result: {
  id: number;
  existing: boolean;
  status: string;
  reasons: string[];
  filled?: string[];
}): Promise<void> {
  manualOpen.value = false;
  undo.value = null;
  // Complétée : sa note est refaite quand le texte de l'annonce arrive.
  notice.value = result.filled?.length
    ? result.filled.includes("description")
      ? "Offre complétée : sa note est refaite avec le texte de l'annonce."
      : "Offre complétée."
    : result.existing
      ? "Cette offre était déjà là : la voici."
      : result.status === "filtered_out"
        ? `Offre ajoutée. Tes critères l'écartent (${result.reasons.join(" ; ")}) : elle est dans « Écartées ».`
        : "Offre ajoutée : sa note arrive dans un instant.";
  await load();
  await router.replace({ query: { ...route.query, offre: String(result.id) } });
  await openFromQuery();
}
// « L'ouvrir » dans l'avis d'une offre déjà là (candidature spontanée) : le panneau se ferme, l'offre s'ouvre.
async function openExisting(id: number): Promise<void> {
  spontaneousOpen.value = false;
  await router.replace({ query: { ...route.query, offre: String(id) } });
  await openFromQuery();
}
let requestId = 0;

function loadMore(): void {
  if (!loading.value) void load(true);
}

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
          with_filtered_out: (f.view === "pending" && f.showFilteredOut) || undefined,
          with_expired: (f.view === "pending" && f.showExpired) || undefined,
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
  } catch (cause) {
    if (current === requestId) {
      failed.value = true;
      offline.value = isNetworkError(cause);
    }
  } finally {
    if (current === requestId) {
      loading.value = false;
      firstLoaded.value = true;
    }
  }
}

async function setStatus(status: "to_review" | "later" | "ignored" | "preparing", target: Offer | null = selected.value): Promise<void> {
  const offer = target;
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
  // Le signet de la sous-page (« Plus tard » et retour) laisse la fiche ouverte : l'offre reste dans « À traiter ».
  const stays = status === "preparing" || (phone.value && (status === "later" || status === "to_review"));
  if (!stays && selectedId.value === offer.id) selectedId.value = null;
  const previous = offer.status;
  undo.value =
    status in STATUS_TEXT && previous !== status && (previous === "to_review" || previous === "later" || previous === "ignored")
      ? { id: offer.id, status: previous }
      : null;
  notice.value = undo.value ? (status === "ignored" ? "Offre écartée." : `Passée en ${STATUS_TEXT[status]}.`) : "";
  // « Annuler » reste 6 s (docs/108), puis le message s'efface.
  clearTimeout(undoTimer);
  if (undo.value) {
    const shown = undo.value;
    undoTimer = setTimeout(() => {
      if (undo.value !== shown) return;
      undo.value = null;
      notice.value = "";
    }, 6000);
  }
  await load();
}
let undoTimer: ReturnType<typeof setTimeout> | undefined;

// La feuille d'actions d'une carte (téléphone, C6) : l'offre dont on a touché le « ⋯ ».
const actionsOffer = ref<Offer | null>(null);
function discardFromSheet(offer: Offer): void {
  actionsOffer.value = null;
  void setStatus("ignored", offer);
}
function sentFromSheet(offer: Offer): void {
  actionsOffer.value = null;
  void openApplication(offer);
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

async function openApplication(target: Offer | null = selected.value): Promise<void> {
  const offer = target;
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
    applyError.value = typeof detail === "string" ? detail : "Enregistrement impossible pour l'instant : réessaie.";
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
  // Une feuille du bas ouverte (<dialog>) se ferme seule : la fiche dessous reste ouverte.
  if (document.querySelector("dialog[open]")) return;
  if (applying.value) applying.value = null;
  else if (filtersOpen.value) closeFilters();
  else selectedId.value = null;
}

// La liste se recharge quand un filtre change, pas pour ?offre= : l'offre ouverte hors de la liste
// (ajoutée à la main, ou par un lien) en serait effacée et sa fiche refermée aussitôt.
watch(
  () => JSON.stringify(toQuery(filters.value)),
  () => void load(),
);

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
  document.addEventListener("pointerdown", onPointerDown);
  void load().then(openFromQuery);
  openShared();
  void loadChunkTitles();
  void loadVisibility();
});
useDataChanged(() => {
  void load();
});
onUnmounted(() => {
  clearTimeout(undoTimer);
  window.removeEventListener("keydown", onKeydown);
  document.removeEventListener("pointerdown", onPointerDown);
  assistant.setFocus(null);
});
</script>

<template>
  <section class="offers-page">
    <!-- La conclusion en une phrase (règles §3.2), le compte en accent comme sur Aujourd'hui. Pas sur téléphone :
         le nombre est sur la pastille de « À traiter » (maquette Candidatures, Kevin, 2026-11-05). -->
    <p
      v-if="!phone && !failed && (!loading || items.length)"
      class="offers-sentence"
      data-test="offers-sentence"
    >
      <strong v-if="total">{{ plural(total, "offre", "offres") }}</strong><span v-else>{{ "Aucune offre" }}</span>{{ sentenceEnd }}{{ "." }}
    </p>
    <!-- La barre d'outils (1.6.55, planche « Barre d'outils Offres ») : la recherche qui prend la ligne
         (ordinateur), « Filtrer » et « + Ajouter » ; les filtres actifs en pastilles dessous. La liste a
         toute la largeur, sans colonne de filtres. -->
    <!-- Téléphone (docs/139 étape 5a, maquette Candidatures) : la recherche et « Ajouter » montent au-dessus
         des vues (#jobs-tools), le bouton des filtres dans l'en-tête, à côté d'« Alertes ». -->
    <component
      :is="phone ? Teleport : 'div'"
      v-bind="phone ? { to: '#jobs-tools', defer: true } : { class: 'in-place' }"
    >
      <div
        class="offers-toolbar"
        data-test="offers-toolbar"
      >
        <OfferSearch
          class="offers-toolbar-search"
          :value="filters.q"
          :placeholder="phone ? 'Poste, entreprise, lieu' : undefined"
          @search="(q) => update({ q })"
        />
        <div
          ref="filterAnchor"
          class="offers-filter"
        >
          <component
            :is="phone ? Teleport : 'div'"
            v-bind="phone ? { to: '#topbar-page-tools', defer: true } : { class: 'in-place' }"
          >
            <!-- L'entonnoir et le mot (1.6.26), le nombre de filtres actifs en pastille ; sur téléphone,
                 l'icône seule, ronde, 44 px. -->
            <button
              ref="filterToggle"
              type="button"
              :class="phone ? 'icon-button offers-filter-icon' : 'secondary offers-toolbar-button'"
              :aria-label="filterLabel"
              :aria-expanded="filtersOpen"
              aria-controls="offers-filters"
              data-test="filters-toggle"
              @click="filtersOpen ? closeFilters() : openFilters()"
            >
              <span class="with-icon"><AppIcon :name="phone ? 'settings' : 'filter'" /><template v-if="!phone">Filtrer</template></span>
              <CountBadge
                v-if="chips.length"
                aria-hidden="true"
                data-test="filters-count"
                :count="chips.length"
              />
            </button>
          </component>
          <!-- Téléphone (sous 820 px, seuil unique D8) : la feuille « Filtres » de la maquette ; ordinateur : le
               panneau sous le bouton, sans Teleport, pour ne pas être recréé à chaque filtre. -->
          <OfferFilterSheet
            v-if="phone"
            :open="filtersOpen"
            :filters="filters"
            :facets="facets"
            :total="total"
            @update="update"
            @reset="reset"
            @close="closeFilters"
          />
          <div
            v-else
            class="offers-filters-anchor"
          >
            <section
              v-if="filtersOpen"
              id="offers-filters"
              class="offers-filters"
              :style="{ '--filters-room': filtersRoom }"
              role="dialog"
              aria-labelledby="offers-filters-title"
              data-test="filters-dialog"
            >
              <div class="offers-filters-head">
                <h2 id="offers-filters-title">
                  Filtres
                </h2>
                <IconButton
                  icon="close"
                  label="Fermer les filtres"
                  class="close"
                  data-test="close-filters"
                  @click="closeFilters"
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
                @done="closeFilters"
              />
            </section>
          </div>
        </div>
        <!-- Téléphone (C10) : « Ajouter » compact, à côté de la recherche ; « Postuler spontanément » est un
             lien au bas de la liste. Ordinateur : un seul « + Ajouter » et son menu (1.6.47). -->
        <button
          v-if="phone"
          type="button"
          class="secondary offers-add-compact"
          data-test="manual-open"
          @click="openManual"
        >
          <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
        </button>
        <MoreMenu
          v-else
          class="offers-add"
          :items="addItems"
          trigger="Ajouter"
          trigger-icon="plus"
          test-id="add-menu"
          :inline="false"
        />
      </div>
    </component>
    <OfferFilterChips
      :chips="chips"
      @update="update"
      @reset="reset"
    />

    <div :class="['offers-grid', { 'has-selection': selected }]">
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
        <PlanLimit usage="score" />
        <!-- Téléphone (maquette ErreurConnexion, C9) : le visage, la phrase des offres, « Réessayer ». -->
        <NetworkError
          v-if="failed && offline"
          :title="phone ? 'Connexion perdue' : undefined"
          :line="phone ? 'Impossible de charger les offres. Vérifie ta connexion, puis réessaie.' : undefined"
          @retry="load()"
        />
        <p
          v-else-if="failed"
          class="notice error"
        >
          Impossible de charger les offres.
        </p>
        <!-- La liste charge : des blocs gardent sa place (comme Aujourd'hui). -->
        <LoadingBlocks
          v-else-if="loading && !items.length"
          :heights="['4.5rem', '4.5rem', '4.5rem']"
        />
        <!-- Un compte neuf, sans filtre (docs/128 §3) : pourquoi c'est vide, et quoi faire. -->
        <FaceState
          v-else-if="!loading && items.length === 0 && noOffersYet"
          title="Pas encore d'offre"
          data-test="offers-none-yet"
        >
          <p>Elles arrivent par tes alertes.</p>
          <div class="face-state-actions">
            <RouterLink
              to="/candidatures/alertes"
              class="button-link primary-link"
            >
              <span class="with-icon"><AppIcon name="bell" />Créer mes alertes</span>
            </RouterLink>
            <button
              type="button"
              class="button-link"
              data-test="offers-none-add"
              @click="manualOpen = true"
            >
              <span class="with-icon"><AppIcon name="plus" />Ajouter une offre</span>
            </button>
          </div>
        </FaceState>
        <!-- Tout est examiné (1.6.50) : pas de bande, pas de bouton ; les nouvelles viennent seules. -->
        <FaceState
          v-else-if="!loading && items.length === 0 && allReviewed"
          title="Tout est examiné"
          illustration="reussite"
          data-test="offers-all-reviewed"
        >
          <p>Les nouvelles arrivent chaque matin.</p>
        </FaceState>
        <!-- Rien en préparation (planche « Illustrations ») : garder une offre dans le tri. -->
        <FaceState
          v-else-if="!loading && items.length === 0 && filters.view === 'in_progress' && !activeCount(filters)"
          title="Rien à préparer pour l'instant"
          illustration="preparer-vide"
          data-test="offers-nothing-to-prepare"
        >
          <p>Garde une offre dans le tri : sa lettre et son CV se préparent ici.</p>
          <div class="face-state-actions">
            <RouterLink
              :to="{ name: 'triage' }"
              class="button-link primary-link"
            >
              Commencer le tri
            </RouterLink>
          </div>
        </FaceState>
        <!-- Téléphone (maquette AucuneOffre, C9) : ce qui filtre, en mots, et « Modifier les filtres ». -->
        <FaceState
          v-else-if="!loading && items.length === 0 && activeCount(filters) && phone"
          title="Aucune offre avec ces filtres"
          mood="neutre"
          animation="loupe"
          data-test="offers-empty"
        >
          <p>{{ emptyFiltersLine }}</p>
          <div class="face-state-actions">
            <button
              type="button"
              class="primary"
              data-test="offers-edit-filters"
              @click="openFilters()"
            >
              Modifier les filtres
            </button>
          </div>
        </FaceState>
        <!-- Aucun résultat avec des filtres (règles §4) : une ligne grise et « Effacer les filtres ». -->
        <p
          v-else-if="!loading && items.length === 0 && activeCount(filters)"
          class="muted empty"
          data-test="offers-empty"
        >
          Aucune offre avec ces filtres.
          <button
            type="button"
            class="link"
            data-test="offers-reset"
            @click="reset"
          >
            Effacer les filtres
          </button>
        </p>
        <FaceState
          v-else-if="!loading && items.length === 0"
          title="Aucune offre"
          data-test="offers-empty"
        >
          <p>Rien ne correspond pour l'instant.</p>
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
            <!-- Le titre du jour, son nombre en gris (maquette Candidatures, C8) ; « En préparation » d'abord. -->
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
              @more="actionsOffer = row.offer"
            />
          </li>
        </TransitionGroup>
        <!-- La suite de la liste, sur place (règles §4, « Afficher plus (N) ») : chargée par pages. -->
        <ShowMore
          v-if="items.length < total"
          :model-value="false"
          :hidden="total - items.length"
          test-id="offers-more"
          @update:model-value="loadMore"
        />
        <p
          v-if="phone && !loading && !failed"
          class="offers-spontaneous"
        >
          <button
            type="button"
            class="link"
            data-test="spontaneous-open"
            @click="spontaneousOpen = true"
          >
            Postuler spontanément
          </button>
        </p>
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
  <OfferActionSheet
    v-if="phone"
    :offer="actionsOffer"
    @close="actionsOffer = null"
    @discard="discardFromSheet"
    @sent="sentFromSheet"
  />
  <SidePanel
    v-if="spontaneousOpen"
    open
    title="Candidature spontanée"
    @close="spontaneousOpen = false"
  >
    <SpontaneousForm
      @created="load()"
      @open="openExisting"
    />
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
