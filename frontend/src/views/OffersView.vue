<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, Teleport, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Offer, type OfferFacets, type OrpMonth } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BusyButton from "../components/BusyButton.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import ApplicationSent from "../components/ApplicationSent.vue";
import GoalReached from "../components/GoalReached.vue";
import { firstGoal } from "../composables/useGoalMoment";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import ShowMore from "../components/ShowMore.vue";
import SidePanel from "../components/SidePanel.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import SpontaneousForm from "../components/SpontaneousForm.vue";
import ManualOfferForm from "../components/ManualOfferForm.vue";
import FirstOffers from "../components/FirstOffers.vue";
import { usePhone } from "../composables/usePhone";
import OfferFilterSheet from "../components/OfferFilterSheet.vue";
import OfferFilterPanel from "../components/OfferFilterPanel.vue";
import BottomSheet from "../components/BottomSheet.vue";
import OfferFilterChips from "../components/OfferFilterChips.vue";
import OfferSearch from "../components/OfferSearch.vue";
import CharacterState from "../components/CharacterState.vue";
import FaceState from "../components/FaceState.vue";
import { applicationBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { activeChips, activeCount, toQuery, useOfferFilters, type View } from "../composables/useOfferFilters";
import { dayKey, dayName, plural } from "../format";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import { useDataChanged } from "../composables/useDataChanged";
import { usePageReady } from "../composables/usePageTransition";
import { useProfileEmpty } from "../composables/useProfileEmpty";
import PlanLimit from "../components/PlanLimit.vue";
import CountBadge from "../components/CountBadge.vue";

const PAGE_SIZE = 50;
// Sur téléphone, « Afficher n offres de plus » charge 20 offres par appui (prompt du 10 novembre, fin de soirée, PR 35 ;
// Kevin : 50 au premier chargement, puis + 20).
const MORE_SIZE = 20;

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
// L'écran qui suit « Marquer comme envoyée » (docs/141, 8 et 9), à la place de la page.
const sentMoment = ref<{ title: string; company: string; count: number | null; target: number | null; followUpOn: string | null } | null>(null);
const goalMoment = ref<OrpMonth | null>(null);
const applyError = ref("");
const notice = ref("");
const facets = ref<OfferFacets>({ sources: [], cantons: [], scores: [], unscored: 0, sure: 0, provisional: 0 });
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
  return `${shownTotal.value > 1 ? many : one}${activeCount(f) ? " avec ces filtres" : ""}`;
});
const failed = ref(false);
// Une panne de réseau (planche « Illustrations ») : l'écran « Pas de connexion », qui réessaie seul.
const offline = ref(false);
// « Réessayer » après une connexion perdue : le feston d'attente jusqu'à la réponse (maquette ErreurConnexion).
const retrying = ref(false);
const firstLoaded = ref(false);
usePageReady("offers", () => firstLoaded.value);
const selectedId = ref<number | null>(null);
const chunkTitles = ref<Record<number, string>>({});
const filtersOpen = ref(false);
const { phone } = usePhone();
// Ordinateur à partir de 1 024 px (maquette CandidaturesOrdinateur, 7.11.2026) : la barre d'outils monte dans
// l'en-tête, à côté des vues ; la liste (560 px) et la fiche défilent chacune dans sa colonne.
const { phone: wide } = usePhone("(min-width: 1024px)");
// Barre d'outils (1.6.55) : « Filtrer » ouvre un panneau sous le bouton (ordinateur) ou une feuille en
// bas de l'écran (téléphone) ; les filtres actifs restent visibles en pastilles sous la barre.
const chips = computed(() => activeChips(filters.value));
// « Note minimale : Proche et plus, Taux : 80 % et plus. Élargis un critère pour voir plus d'offres. »
const emptyFiltersLine = computed(() => {
  const q = filters.value.q.trim();
  const parts = [...(q ? [`Recherche « ${q} »`] : []), ...chips.value.map((chip) => chip.label)];
  return `${parts.join(", ")}. Élargis un critère pour voir plus d’offres.`;
});
const filterLabel = computed(() => {
  const active = chips.value.length ? `, ${plural(chips.value.length, "filtre actif", "filtres actifs")}` : "";
  if (phone.value) return `Filtres${active}`;
  return active ? `Filtrer${active}` : undefined;
});
const filterAnchor = ref<HTMLElement | null>(null);
const filterToggle = ref<HTMLButtonElement | null>(null);
const filterPanel = ref<HTMLElement | null>(null);
// Ordinateur (maquette du 8 novembre, D24) : le panneau des filtres remplace la colonne liste ; le titre prend le focus.
function openFilters(): void {
  filtersOpen.value = true;
  void nextTick(() => document.getElementById("offers-filters-title")?.focus({ preventScroll: true }));
}
function closeFilters(): void {
  filtersOpen.value = false;
  void nextTick(() => filterToggle.value?.focus({ preventScroll: true }));
}
// Un clic hors du panneau le referme (ordinateur) ; sur téléphone, c'est le voile.
function onPointerDown(event: PointerEvent): void {
  if (!filtersOpen.value || phone.value) return;
  if (event.target instanceof Node && (filterAnchor.value?.contains(event.target) || filterPanel.value?.contains(event.target))) return;
  filtersOpen.value = false;
}
// Candidature spontanée (docs/39) : sans annonce, préparée comme une offre.
const spontaneousOpen = ref(false);
// Ajouter une offre trouvée ailleurs (docs/111), aussi par « Partager vers jobA1 » sur Android :
// /candidatures/offres?ajouter=1&url=…&text=… ouvre le formulaire, lien ou texte déjà là.
const manualOpen = ref(false);
const shared = ref<{ url: string | null; text: string | null }>({ url: null, text: null });

const selected = computed(() => items.value.find((o) => o.id === selectedId.value) ?? null);

// Les offres « Loin » (note sous 50) cachées sur téléphone (maquette Candidatures, Kevin 2026-11-06) : un lien en
// bas de liste les montre, avec leur nombre (les tranches de note du serveur, toute la liste). Pas quand un
// filtre de note est posé : il dit déjà quoi montrer. Une offre sans note reste visible.
const FAR_BELOW = 50;
const showFar = ref(false);
const hidesFar = computed(() => phone.value && filters.value.minScore === null && filters.value.maxScore === null);
const farCount = computed(() => facets.value.scores.slice(0, FAR_BELOW / 5).reduce((sum, n) => sum + n, 0));
// Le nombre que disent la phrase et « Afficher n offres » : la liste montrée, sans les offres « Loin » cachées.
const shownTotal = computed(() => (hidesFar.value && !showFar.value ? Math.max(0, total.value - farCount.value) : total.value));
const shown = computed(() =>
  hidesFar.value && !showFar.value
    ? items.value.filter((o) => o.score === null || o.score === undefined || o.score >= FAR_BELOW || o.id === pinnedId.value)
    : items.value,
);
// Bas de liste sur téléphone (PR 35) : les offres qui restent à charger dans la liste montrée, et combien le prochain
// appui en ajoute (« Afficher 12 offres de plus · 12 restantes »).
const remaining = computed(() => (items.value.length < total.value ? Math.max(0, shownTotal.value - shown.value.length) : 0));
const nextCount = computed(() => Math.min(MORE_SIZE, remaining.value));
const moreLabel = computed(() => `Afficher ${plural(nextCount.value, "offre", "offres")} de plus`);
const remainingLabel = computed(() => ` · ${remaining.value} ${remaining.value > 1 ? "restantes" : "restante"}`);

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
  for (const offer of shown.value) {
    if (offer.id === pinnedId.value) continue;
    const key = groupKey(offer);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});
type Day = { name: string; count: string; n: number };
function dayHeader(index: number): Day | null {
  const offer = shown.value[index];
  if (!offer || offer.id === pinnedId.value) return null;
  const key = groupKey(offer);
  // « En préparation » a toujours son titre de section (Kevin, 2026-11-05, et maquette CandidaturesOrdinateur) :
  // les cartes n'ont pas d'étiquette.
  if (!byDay.value && key !== "preparing") return null;
  const previous = shown.value.slice(0, index).filter((o) => o.id !== pinnedId.value).at(-1);
  if (previous && groupKey(previous) === key) return null;
  const n = dayCounts.value.get(key) ?? 0;
  return { name: key === "preparing" ? "En préparation" : dayName(offer.first_seen_at), count: plural(n, "offre", "offres"), n };
}
// Une liste à plat (lignes de jour et offres) pour que chaque offre s'anime seule (docs/60 §3).
const rows = computed(() =>
  shown.value.flatMap((offer, index) => {
    const day = dayHeader(index);
    const card = { key: `offer-${offer.id}`, day: null as Day | null, offer };
    return day ? [{ key: `day-${offer.id}`, day, offer: null }, card] : [card];
  }),
);
const route = useRoute();
const router = useRouter();
const assistant = useAssistant();

// Ordinateur (≥ 1 024 px) : les deux colonnes tiennent dans la fenêtre, sous l'en-tête ; la hauteur part du haut
// de la grille, relu au chargement et au redimensionnement (bandeau de démo, pastilles de filtres).
const grid = ref<HTMLElement | null>(null);
const gridTop = ref(0);
function measureGrid(): void {
  if (grid.value) gridTop.value = Math.round(grid.value.getBoundingClientRect().top + window.scrollY);
}
// Sur ordinateur, une offre est toujours ouverte à droite (maquette) : sans ?offre=, la première de la liste.
// L'adresse est remplacée, pas empilée : le retour arrière ne repasse pas par elle.
watch(wide, () => void nextTick(() => {
  measureGrid();
  selectFirst();
}));
function selectFirst(): void {
  if (!wide.value || routeOfferId() || failed.value) return;
  const first = shown.value[0];
  if (first) void router.replace({ query: { ...route.query, offre: String(first.id) } });
}

// L'offre ouverte est l'élément dont parle l'assistant (docs/24 §2.2).
watch(selected, (offer) => {
  assistant.setFocus(offer ? { offerId: offer.id, label: `offre ${offer.title}${offer.company ? ` chez ${offer.company}` : ""}` } : null);
  // Après la navigation d'ouverture encore en cours, sinon l'offre se rouvrirait.
  if (!offer) void opening.then(() => leaveOffer());
});

// L'offre ouverte dans l'adresse : sur téléphone, la sous-page /candidatures/offres/12 (O1) ; sur ordinateur,
// ?offre=12 à côté de la liste. Les filtres de la liste restent dans l'adresse.
// Sur ordinateur, ?offre= passe avant le chemin : sinon /offres/384?offre=675 rouvrait toujours la 384 (Kevin, 6.11).
const routeOfferId = (): number => Number(phone.value ? route.params.id || route.query.offre : route.query.offre || route.params.id);
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
  // Sur ordinateur, la sous-page (« Retour à l'offre » de la préparation, ou l'écran élargi) devient ?offre=.
  if (!phone.value && route.params.id) {
    void router.replace({ name: "offers", params: {}, query: { ...route.query, offre: String(id) } });
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
  () => [route.params.id, route.query.offre, phone.value],
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
// L'adresse est nettoyée avant d'ouvrir : le panneau ajoute une entrée d'historique pour le bouton retour, et la
// retire en se fermant. Ouvert avant le nettoyage, ce retour ramenait sur « ?ajouter=1 » et le panneau se rouvrait
// (Échap, la croix et le clic à l'extérieur ne le fermaient plus).
async function openShared(): Promise<void> {
  if (!route.query.ajouter) return;
  const pick = (key: string) => (typeof route.query[key] === "string" ? String(route.query[key]).trim() : "");
  const sharedText = [pick("title"), pick("text")].filter(Boolean).join("\n");
  const found = pick("url") || sharedText.match(/https:\/\/\S+/)?.[0] || "";
  const rest = sharedText.replace(found, "").trim();
  shared.value = { url: found || null, text: found ? null : rest || null };
  await router.replace({ query: { ...route.query, ajouter: undefined, url: undefined, text: undefined, title: undefined } });
  manualOpen.value = true;
}
watch(() => route.query.ajouter, () => void openShared());

function openManual(): void {
  shared.value = { url: null, text: null };
  manualOpen.value = true;
}

// Tout est examiné (1.6.50) : la vue « À examiner » est vide alors que le compte a des offres.
const allReviewed = computed(
  () => !noOffersYet.value && filters.value.view === "pending" && counts.value.pending === 0 && !activeCount(filters.value),
);

// « + Ajouter » sur ordinateur (MODIFICATIONS du 9 novembre, §2.6 ; maquettes CandidaturesOrdinateurAjouter et
// CandidaturesOrdinateurSpontanee) : un seul panneau, deux onglets, « Une offre » et « Candidature spontanée ».
const ADD_TABS = [
  { value: "offer", label: "Une offre", test: "add-tab-offer" },
  { value: "spontaneous", label: "Candidature spontanée", test: "add-tab-spontaneous" },
];
const addTab = computed<string>({
  get: () => (spontaneousOpen.value ? "spontaneous" : "offer"),
  set: (value) => {
    spontaneousOpen.value = value === "spontaneous";
    manualOpen.value = value !== "spontaneous";
  },
});
// Le bouton du pied du panneau parle pour le formulaire affiché (libellé, attente).
const manualForm = ref<InstanceType<typeof ManualOfferForm> | null>(null);
const spontaneousForm = ref<InstanceType<typeof SpontaneousForm> | null>(null);
function closeAdd(): void {
  manualOpen.value = false;
  spontaneousOpen.value = false;
}

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
      ? "Offre complétée : sa note est refaite avec le texte de l’annonce."
      : "Offre complétée."
    : result.existing
      ? "Elle était déjà dans ta liste"
      : result.status === "filtered_out"
        ? `Offre ajoutée. Tes critères l’écartent (${result.reasons.join(" ; ")}) : elle est dans « Écartées ».`
        : "Offre ajoutée : sa note arrive dans un instant.";
  await load();
  await router.replace({ query: { ...route.query, offre: String(result.id) } });
  await openFromQuery();
  if (result.existing && !result.filled?.length) void flash(result.id);
}
// L'offre déjà là (PR 38) : la liste défile jusqu'à sa carte, mise en avant 2 secondes.
const flashId = ref<number | null>(null);
let flashTimer: ReturnType<typeof setTimeout> | undefined;
async function flash(id: number): Promise<void> {
  await nextTick();
  const row = document.querySelector<HTMLElement>(`[data-offer-row="${id}"]`);
  const calm = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  row?.scrollIntoView?.({ block: "center", behavior: calm ? "auto" : "smooth" });
  flashId.value = id;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => (flashId.value = null), 2000);
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

// Téléphone : charge la suite, puis met le focus sur la première nouvelle carte (PR 35).
async function showMoreOffers(): Promise<void> {
  if (loading.value) return;
  const before = new Set(shown.value.map((offer) => offer.id));
  await load(true);
  const first = shown.value.find((offer) => !before.has(offer.id));
  if (!first) return;
  await nextTick();
  document.querySelector<HTMLElement>(`[data-offer-row="${first.id}"] .list-card`)?.focus();
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
          limit: append && phone.value ? MORE_SIZE : PAGE_SIZE,
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
          basis: f.basis ?? undefined,
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
      retrying.value = false;
      firstLoaded.value = true;
      void nextTick(() => {
        measureGrid();
        selectFirst();
      });
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
  const discarded = phone.value ? "Offre écartée. Tu la retrouves dans Suivi." : "Offre écartée.";
  notice.value = undo.value ? (status === "ignored" ? discarded : `Passée en ${STATUS_TEXT[status]}.`) : "";
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
    applyError.value = typeof detail === "string" ? detail : "Enregistrement impossible pour l’instant : réessaie.";
    return;
  }
  applying.value = null;
  // « Candidature envoyée. » ou, si elle atteint l'objectif ORP du mois, « C'est fait ! » (docs/141, 8 et 9).
  const orp = (await api.GET("/api/orp", { params: { query: { month: data.orp_month } } }).catch(() => null))?.data;
  if (orp && firstGoal(data.orp_month, orp.count, orp.target)) goalMoment.value = { ...orp, month: data.orp_month };
  else sentMoment.value = { title: data.job_title, company: data.company, count: orp?.count ?? null, target: orp?.target ?? null, followUpOn: data.follow_up_on ?? null };
  window.scrollTo?.({ top: 0 });
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

async function loadChunkTitles(): Promise<void> {
  try {
    const { data } = await api.GET("/api/profile-chunks");
    chunkTitles.value = Object.fromEntries((data ?? []).map((c) => [c.id, c.title]));
  } catch {
    chunkTitles.value = {};
  }
}

// Sans profil, les cartes le disent par une puce (useProfileEmpty).
const { refresh: refreshProfile } = useProfileEmpty();
onMounted(() => {
  void refreshProfile();
  window.addEventListener("keydown", onKeydown);
  window.addEventListener("resize", measureGrid);
  document.addEventListener("pointerdown", onPointerDown);
  void load().then(openFromQuery);
  void openShared();
  void loadChunkTitles();
});
useDataChanged(() => {
  void load();
});
onUnmounted(() => {
  clearTimeout(undoTimer);
  window.removeEventListener("keydown", onKeydown);
  window.removeEventListener("resize", measureGrid);
  document.removeEventListener("pointerdown", onPointerDown);
  assistant.setFocus(null);
});
</script>

<template>
  <GoalReached
    v-if="goalMoment"
    :data="goalMoment"
    :cancellable="false"
  />
  <ApplicationSent
    v-else-if="sentMoment"
    v-bind="sentMoment"
    @leave="sentMoment = null"
  />
  <section
    v-else
    class="offers-page"
  >
    <!-- La conclusion en une phrase (règles §3.2), le compte en accent comme sur Aujourd'hui. Pas sur téléphone :
         le nombre est sur la pastille de « À traiter » (maquette Candidatures, Kevin, 2026-11-05). -->
    <p
      v-if="!phone && !wide && !failed && (!loading || items.length)"
      class="offers-sentence"
      data-test="offers-sentence"
    >
      <strong v-if="shownTotal">{{ plural(shownTotal, "offre", "offres") }}</strong><span v-else>{{ "Aucune offre" }}</span>{{ sentenceEnd }}{{ "." }}
    </p>
    <!-- La barre d'outils (1.6.55, planche « Barre d'outils Offres ») : la recherche qui prend la ligne
         (ordinateur), « Filtrer » et « + Ajouter » ; les filtres actifs en pastilles dessous. La liste a
         toute la largeur, sans colonne de filtres. -->
    <!-- Téléphone (docs/139 étape 5a, maquette Candidatures) : la recherche et « Ajouter » montent au-dessus
         des vues (#jobs-tools), le bouton des filtres dans l’en-tête, à côté d'« Alertes ». -->
    <component
      :is="phone || wide ? Teleport : 'div'"
      v-bind="phone || wide ? { to: phone ? '#jobs-tools' : '#offers-list-tools', defer: true } : { class: 'in-place' }"
    >
      <div
        class="offers-toolbar"
        data-test="offers-toolbar"
      >
        <OfferSearch
          class="offers-toolbar-search"
          :value="filters.q"
          :placeholder="phone ? 'Poste, entreprise, lieu' : wide ? 'Filtrer par titre ou entreprise' : undefined"
          :icon="wide && !phone ? 'filter' : undefined"
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
                 l’icône seule, ronde, 44 px. -->
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
              <span class="with-icon"><AppIcon :name="phone || wide ? 'settings' : 'filter'" /><template v-if="wide && !phone">Plus de filtres</template><template v-else-if="!phone">Filtrer</template></span>
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
            :total="shownTotal"
            @update="update"
            @reset="reset"
            @close="closeFilters"
          />
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
        <button
          v-else-if="!wide"
          type="button"
          class="secondary offers-add"
          data-test="add-open"
          @click="openManual"
        >
          <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
        </button>
      </div>
    </component>
    <OfferFilterChips
      :chips="chips"
      @update="update"
      @reset="reset"
    />

    <div
      ref="grid"
      :class="['offers-grid', { 'has-selection': selected }]"
      :style="wide ? { '--offers-top': `${gridTop}px` } : undefined"
    >
      <!-- Ordinateur : « Plus de filtres » remplace la colonne liste ; la liste reste montée, ses choix gardés. -->
      <div
        v-if="!phone && filtersOpen"
        ref="filterPanel"
        class="offers-filter-column"
      >
        <OfferFilterPanel
          :filters="filters"
          :counts="counts"
          :facets="facets"
          :total="shownTotal"
          @update="update"
          @reset="reset"
          @close="closeFilters"
        />
      </div>
      <div
        v-show="!(!phone && filtersOpen)"
        class="offers-list"
      >
        <div
          v-if="wide && !phone"
          id="offers-list-tools"
          class="offers-list-tools"
        />
        <!-- Téléphone (§10.1) : « Écarter » agit tout de suite, puis un message en bas, fond inversé, avec « Annuler »
             pendant 6 secondes (Material 3, snackbar). -->
        <p
          v-if="notice"
          :class="['notice', { 'undo-snackbar': phone && undo }]"
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
        <FaceState
          v-if="retrying && loading"
          title="Chargement…"
          animation="attente"
          role="status"
          class="network-waiting"
          data-test="network-waiting"
        >
          <p>On récupère tes offres.</p>
        </FaceState>
        <NetworkError
          v-else-if="failed && offline"
          :class="{ 'network-waiting': phone }"
          :title="phone ? 'Connexion perdue' : undefined"
          :line="phone ? 'Impossible de charger les offres. Vérifie ta connexion, puis réessaie.' : undefined"
          @retry="retrying = true; load()"
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
        <!-- En attente de la première collecte : les 4 personnages du logo (scène « aucune-offre », §15). -->
        <CharacterState
          v-else-if="!loading && items.length === 0 && noOffersYet"
          scene="aucune-offre"
          title="Pas encore d’offre"
          data-test="offers-none-yet"
        >
          <p>Tes premières offres arrivent après la prochaine collecte.</p>
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
        </CharacterState>
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
          title="Rien à préparer pour l’instant"
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
        <!-- Téléphone (maquette AucuneOffre, §15 du 9 novembre) : la scène « aucune-offre » (330 px), ce qui filtre,
             en mots, et « Modifier les filtres ». -->
        <!-- Ordinateur (maquette AucuneOffreOrdinateur) : le même écran, la scène à 482 px,
             « Tout effacer » puis « Modifier les filtres ». -->
        <CharacterState
          v-else-if="!loading && items.length === 0 && activeCount(filters) && (phone || wide)"
          scene="aucune-offre"
          title="Aucune offre avec ces filtres"
          :full="wide && !phone"
          :class="{ 'character-state-wide': wide && !phone }"
          data-test="offers-empty"
        >
          <p>{{ emptyFiltersLine }}</p>
          <div class="face-state-actions">
            <button
              v-if="wide && !phone"
              type="button"
              class="secondary"
              data-test="offers-reset"
              @click="reset"
            >
              Tout effacer
            </button>
            <button
              type="button"
              class="primary"
              data-test="offers-edit-filters"
              @click="openFilters()"
            >
              Modifier les filtres
            </button>
          </div>
          <!-- Sous un trait de 420 px (§2.7, AucuneOffreOrdinateur) : la candidature spontanée, qui ouvre « Ajouter ». -->
          <div
            v-if="wide && !phone"
            class="offers-empty-spontaneous"
          >
            <p>Tu vises une entreprise précise, même sans offre ?</p>
            <button
              type="button"
              class="link"
              data-test="empty-spontaneous"
              @click="spontaneousOpen = true"
            >
              Faire une candidature spontanée<AppIcon name="chevron" />
            </button>
          </div>
        </CharacterState>
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
          v-else-if="!loading && shown.length === 0 && !(hidesFar && farCount)"
          title="Aucune offre"
          data-test="offers-empty"
        >
          <p>Rien ne correspond pour l’instant.</p>
        </FaceState>
        <!-- Connexion perdue ou nouvel essai : l'écran d'erreur seul, sans l'ancienne liste dessous. -->
        <TransitionGroup
          v-if="!(failed && offline) && !(retrying && loading)"
          tag="ul"
          name="card"
          class="offer-cards"
        >
          <li
            v-for="row in rows"
            :key="row.key"
            :class="{ 'offer-day': row.day, 'offer-flash': !!row.offer && row.offer.id === flashId }"
            :data-test="row.day ? 'offer-day' : undefined"
            :data-offer-row="row.offer?.id"
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
            />
          </li>
        </TransitionGroup>
        <!-- Ordinateur : la suite de la liste, sur place (règles §4, « Afficher plus (N) ») : chargée par pages. -->
        <ShowMore
          v-if="!phone && items.length < total"
          :model-value="false"
          :hidden="total - items.length"
          test-id="offers-more"
          @update:model-value="loadMore"
        />
        <!-- Téléphone, bas de la liste (prompt du 10 novembre, fin de soirée, PR 35 ; maquettes Candidatures et
             CandidaturesSombre, état bas-de-liste) : un bouton contour pleine largeur, puis le groupe « Autres offres ». -->
        <template v-if="phone && !loading && !failed">
          <button
            v-if="remaining > 0"
            type="button"
            class="offers-more-phone"
            data-test="offers-more"
            @click="showMoreOffers"
          >
            <strong>{{ moreLabel }}</strong><span>{{ remainingLabel }}</span>
          </button>
          <h2
            id="offers-other-title"
            class="offers-other-cap"
          >
            Autres offres
          </h2>
          <div
            class="offers-other"
            role="group"
            aria-labelledby="offers-other-title"
          >
            <!-- « Loin de ton profil » et « Expirées » : ouvertes, même titre, « n offres affichées », chevron vers le
                 haut (Kevin, 10.11). Masquées si leur nombre vaut 0. -->
            <button
              v-if="hidesFar && farCount"
              type="button"
              class="offers-other-row"
              :aria-expanded="showFar"
              data-test="offers-far"
              @click="showFar = !showFar"
            >
              <span class="offers-other-text">
                <strong>Loin de ton profil</strong>
                <span><span class="visually-hidden">, </span>{{ plural(farCount, "offre", "offres") }}{{ showFar ? (farCount > 1 ? " affichées" : " affichée") : ", notées plus bas" }}</span>
              </span>
              <span
                class="arrow-circle"
                aria-hidden="true"
              ><AppIcon :name="showFar ? 'chevron-up' : 'arrow-right'" /></span>
            </button>
            <button
              v-if="filters.view === 'pending' && counts.expired > 0"
              type="button"
              class="offers-other-row"
              :aria-expanded="filters.showExpired"
              data-test="offers-expired"
              @click="update({ showExpired: !filters.showExpired })"
            >
              <span class="offers-other-text">
                <strong>Expirées</strong>
                <span><span class="visually-hidden">, </span>{{ plural(counts.expired, "offre", "offres") }}{{ filters.showExpired ? (counts.expired > 1 ? " affichées" : " affichée") : ", pour mémoire" }}</span>
              </span>
              <span
                class="arrow-circle"
                aria-hidden="true"
              ><AppIcon :name="filters.showExpired ? 'chevron-up' : 'arrow-right'" /></span>
            </button>
            <button
              type="button"
              class="offers-other-row"
              aria-haspopup="dialog"
              data-test="spontaneous-open"
              @click="spontaneousOpen = true"
            >
              <span class="offers-other-text">
                <strong>Postuler spontanément</strong>
                <span><span class="visually-hidden">, </span>À une entreprise sans offre publiée</span>
              </span>
              <span
                class="arrow-circle"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </button>
          </div>
        </template>
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
  <BottomSheet
    v-if="!phone && (manualOpen || spontaneousOpen)"
    open
    title="Ajouter"
    subtitle="Une offre ou une candidature spontanée"
    icon="plus"
    class="add-sheet"
    data-test="add-sheet"
    @close="closeAdd"
  >
    <SegmentedControl
      v-model="addTab"
      :options="ADD_TABS"
      label="Ce que tu ajoutes"
      class="add-tabs"
      full
    />
    <ManualOfferForm
      v-if="manualOpen"
      ref="manualForm"
      form-id="add-offer-form"
      :initial-url="shared.url"
      :initial-text="shared.text"
      @added="manualAdded"
    />
    <SpontaneousForm
      v-else
      ref="spontaneousForm"
      form-id="add-spontaneous-form"
      @created="load()"
      @open="openExisting"
    />
    <!-- Le seul bouton d'action du panneau, dans le pied (D30, PR 38). -->
    <template #actions>
      <BusyButton
        v-if="manualOpen"
        type="submit"
        form="add-offer-form"
        class="primary"
        :busy="manualForm?.busy ?? false"
        :busy-label="manualForm?.busyLabel ?? 'Ajout…'"
        :disabled="manualForm?.full"
        data-test="manual-add"
      >
        {{ manualForm?.label ?? "Ajouter l’offre" }}
      </BusyButton>
      <button
        v-else-if="spontaneousForm?.created"
        type="button"
        class="primary"
        data-test="spontaneous-prepare"
        @click="spontaneousForm?.prepare()"
      >
        Préparer la candidature
      </button>
      <BusyButton
        v-else
        type="submit"
        form="add-spontaneous-form"
        class="primary"
        :busy="spontaneousForm?.busy ?? false"
        busy-label="Création…"
        data-test="spontaneous-create"
      >
        {{ spontaneousForm?.label ?? "Créer la candidature" }}
      </BusyButton>
    </template>
  </BottomSheet>
  <SidePanel
    v-if="phone && spontaneousOpen"
    open
    title="Candidature spontanée"
    @close="spontaneousOpen = false"
  >
    <SpontaneousForm
      @created="load()"
      @open="openExisting"
    />
  </SidePanel>
  <BottomSheet
    v-if="phone && manualOpen"
    open
    title="Ajouter une offre"
    subtitle="Colle le lien ou le texte de l’annonce, ou importe son PDF. jobA1 la lit et la note."
    class="manual-sheet"
    @close="manualOpen = false"
  >
    <ManualOfferForm
      ref="manualForm"
      form-id="add-offer-form"
      :initial-url="shared.url"
      :initial-text="shared.text"
      @added="manualAdded"
    />
    <template
      v-if="manualForm?.shown"
      #actions
    >
      <BusyButton
        type="submit"
        form="add-offer-form"
        class="primary"
        :busy="manualForm?.busy ?? false"
        :busy-label="manualForm?.busyLabel ?? 'Ajout…'"
        data-test="manual-add"
      >
        {{ manualForm?.label ?? "Ajouter l’offre" }}
      </BusyButton>
    </template>
  </BottomSheet>
</template>

<style scoped>
/* Le message « Offre écartée » du téléphone (§10.1, captures Offre--ecartee et OffreSombre--ecartee) : au-dessus de la
   barre du bas, à 20 px des bords, fond --text, texte --bg, « Annuler » en --inverse-link (jamais en orange, D30). */
@media (max-width: 820px) {
  .notice.undo-snackbar {
    --snack-margin: 20px; --snack-bottom: 12px;
    position: fixed; left: var(--snack-margin); right: var(--snack-margin); bottom: calc(var(--tabbar-h, 0px) + var(--snack-bottom) + env(safe-area-inset-bottom)); z-index: 45;
    display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin: 0; padding: var(--space-1) var(--space-2) var(--space-1) var(--space-4);
    border: 0; border-radius: var(--radius-sm); background: var(--text); color: var(--bg); font-size: var(--font-label); font-weight: var(--weight-semibold); line-height: var(--space-5);
  }
  .notice.undo-snackbar .link { flex: none; min-height: var(--target-min); padding: 0 var(--space-2); color: var(--inverse-link); font-weight: var(--weight-bold); text-decoration: none; }
}
/* Maquette ErreurConnexion (téléphone) : « Connexion perdue » puis l'attente après « Réessayer », centrés,
   titre 22 px gras, phrase 16 px, « Réessayer » en pilule de 52 px. Valeurs de l’échelle les plus proches
   (gap 14, 800, marge 10 de la maquette n’y sont pas). Ici plutôt que dans NetworkError, pour ne pas
   peser sur le CSS du premier écran. */
.network-waiting { gap: var(--space-3); min-height: 60vh; align-content: center; padding: 0 var(--space-4) var(--space-8); }
.network-waiting :deep(.face-state-title) { font-size: var(--font-section); line-height: var(--leading-tight); font-weight: var(--weight-bold); }
.network-waiting :deep(.face-state-line) { font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.network-waiting :deep(.face-state-actions) { margin-top: var(--space-2); }
.network-waiting :deep(button.primary) { min-height: 3.25rem; padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
/* Aucune offre (§2.7, AucuneOffreOrdinateur) : trait de 420 px à 32 px sous les boutons, phrase 15 grise à 32 dessous,
   lien 15/700 de 44 px. Le panneau « Ajouter » (§2.6) : les onglets, puis la phrase 15 à 24 dessous. */
.offers-empty-spontaneous { --empty-420: 420px; --empty-15: 15px; display: grid; justify-items: center; gap: var(--space-1); width: min(var(--empty-420), 100%); margin: var(--space-8) auto 0; padding-top: var(--space-8); border-top: 1px solid var(--line); }
.offers-empty-spontaneous p { margin: 0; font-size: var(--empty-15); color: var(--text-secondary); }
.offers-empty-spontaneous .link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); font-size: var(--empty-15); font-weight: var(--weight-bold); color: var(--primary-text); }
.add-sheet :deep(.sheet-actions > .primary) { --add-52: 52px; flex: 1 1 auto; justify-content: center; min-height: var(--add-52); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.offer-flash :deep(.list-card) { outline: 3px solid var(--accent); outline-offset: 2px; }
</style>
