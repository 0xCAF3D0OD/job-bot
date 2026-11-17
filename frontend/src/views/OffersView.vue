<script setup lang="ts">
import { computed, inject, nextTick, onMounted, onUnmounted, ref, Teleport, watch, type Ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type GoogleJobs, type Offer, type OfferFacets, type OrpMonth } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BusyButton from "../components/BusyButton.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import ApplicationSent from "../components/ApplicationSent.vue";
import GoalReached from "../components/GoalReached.vue";
import { firstGoal } from "../composables/useGoalMoment";
import OfferCard from "../components/OfferCard.vue";
import OfferDetail from "../components/OfferDetail.vue";
import LinkedDetail, { Plain } from "../components/LinkedDetail.vue";
import LinkedPin from "../components/LinkedPin.vue";
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
import EmptyState from "../components/EmptyState.vue";
import FaceState from "../components/FaceState.vue";
import { applicationBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { activeChips, activeCount, scoreLabel, toQuery, useOfferFilters, type View } from "../composables/useOfferFilters";
import { collectWhen, dayKey, dayName, plural } from "../format";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import { useDataChanged } from "../composables/useDataChanged";
import { offerUndo } from "../composables/useUndo";
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
const counts = ref<Record<View | "pending_all", number>>({
  to_review: 0,
  pending: 0,
  pending_all: 0,
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
const sentMoment = ref<{ title: string; company: string; count: number | null; target: number | null; month: string; dueDate: string | null; followUpOn: string | null; applicationId: number; addressMissing: boolean } | null>(null);
const goalMoment = ref<OrpMonth | null>(null);
const applyError = ref("");
const notice = ref("");
const facets = ref<OfferFacets>({ sources: [], cantons: [], scores: [], unscored: 0, sure: 0, provisional: 0 });
const loading = ref(false);
// La fin de la phrase selon le statut regardé : « 4 offres nouvelles. », « 1 offre écartée. » (section 38 du 16.11).
const VIEW_END: Record<string, [string, string]> = {
  pending: ["", ""],
  to_review: [" nouvelle", " nouvelles"],
  in_progress: [" en préparation", " en préparation"],
  later: [" pour plus tard", " pour plus tard"],
  filtered_out: [" écartée", " écartées"],
  expired: [" expirée", " expirées"],
  all: ["", ""],
};
// La phrase décrit la liste affichée, rien d'autre (Kevin, 2026-11-03) : « 35 offres en préparation. »,
// « 12 offres avec ces filtres. » dans « Toutes ». Le nombre de « Toutes » sans filtre est counts.pending_all.
// Avec les écartées ou les expirées en plus, la liste n'est plus seulement « Toutes » : « affichées ».
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
// Aucune offre avec ces filtres, sur téléphone (AucuneOffre, §13 et §17 du 15 novembre) : les filtres actifs passent en
// pastilles sous le titre, sans la rangée du haut ni le bloc « Autres offres ».
const phoneEmptyFiltered = computed(() => phone.value && !loading.value && items.value.length === 0 && activeCount(filters.value) > 0);
// « Note minimale : 75 et +, Taux d’activité : dès 80 %. Élargis un critère pour voir plus d'offres. »
const emptyFiltersLine = computed(() => {
  const q = filters.value.q.trim();
  const parts = [...(q ? [`Recherche « ${q} »`] : []), ...chips.value.map((chip) => chip.label)];
  return `${parts.join(", ")}. Élargis un critère pour voir plus d’offres.`;
});
// Aucune offre avec des filtres : sur ordinateur, l'écran prend toute la largeur (AucuneOffreOrdinateur).
const emptyWithFilters = computed(() => !loading.value && items.value.length === 0 && activeCount(filters.value) > 0);
// Aucune offre du tout (§13 du 15 novembre) : l'état vide commun, centré sur toute la largeur, sans colonne de fiche.
const noneYet = computed(() => !loading.value && !failed.value && items.value.length === 0 && noOffersYet.value);
// Rien encore (décision de Kevin du 15.11, b) : ni recherche, ni filtres, ni « + » tant qu'aucune offre n'est arrivée.
const bare = computed(() => noOffersYet.value && !failed.value && items.value.length === 0);
// Au moins une recherche suivie (§41 du 16.11, CandidaturesVideAlertes) : « Tes premières offres arrivent bientôt », une
// phrase, et la pastille avec la prochaine collecte que le serveur calcule d'après sa planification. Sans heure (planificateur
// arrêté), la pastille dit seulement « En attente des premières offres » : jamais une heure inventée.
const followedSearches = inject<Ref<number | null>>("followedSearches", ref(null));
const alertsReady = computed(() => (followedSearches.value ?? 0) > 0);
const nextCollectAt = inject<Ref<string | null>>("nextCollectAt", ref(null));
const nonePill = computed(() => {
  if (!alertsReady.value) return "Offres collectées chaque jour";
  if (!nextCollectAt.value) return "En attente des premières offres";
  const when = collectWhen(nextCollectAt.value);
  // Téléphone : sans « En attente des premières offres », pour tenir sur une ligne.
  return phone.value ? `Prochaine vérification ${when}` : `En attente des premières offres · prochaine vérification ${when}`;
});
// Candidatures vide, avec ou sans alerte (§22 du 15.11) : le lien Google Emplois sous les boutons, pas de carte.
// « Masquer » sur Aujourd'hui ne le cache pas (Kevin, 15.11) ; le serveur ne l'envoie que sans offre et avec un métier.
const googleLink = ref<GoogleJobs | null>(null);
watch(
  () => noneYet.value,
  async (shown) => {
    if (shown && !googleLink.value) googleLink.value = (await api.GET("/api/google-jobs").catch(() => ({ data: null }))).data ?? null;
  },
  { immediate: true },
);
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
// Le compteur au-dessus de la liste (ordinateur, décision de Kevin du 15.11). Seul « À traiter » a un total sans
// filtre (counts.pending_all) : « 12 sur 38 offres » ; les autres vues disent le nombre seul.
const countLabel = computed(() => {
  const base = counts.value.pending_all;
  if (filters.value.view === "pending" && activeCount(filters.value) && shownTotal.value < base) {
    return `${shownTotal.value} sur ${plural(base, "offre", "offres")}`;
  }
  return shownTotal.value ? plural(shownTotal.value, "offre", "offres") : "Aucune offre";
});
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

// Tri « Par date » (docs/73 §3) : une ligne par jour (« Aujourd'hui », « Hier », « Jeudi
// 15 octobre ») et les offres du jour dessous, sans leur date ; heure suisse.
// Offre ouverte par un lien (?offre=) hors de la vue : posée en tête, sans ligne de jour, et
// comptée dans aucun jour.
const pinnedId = ref<number | null>(null);
// Offre renotée depuis sa fiche (Kevin, 16.11) : si sa nouvelle note la sort des filtres, elle reste en tête,
// ouverte, avec la pastille « Hors de tes filtres », jusqu'au prochain changement de filtre ou au départ de la page. Si
// son statut change ensuite (écartée, gardée…), elle suit la règle commune.
const outside = ref<Offer | null>(null);
const outsideId = computed(() => (pinnedId.value === outside.value?.id ? pinnedId.value : null));
// « Nouvelle note : 38. Elle sort de ton filtre « 50 et + ». », sous la note de la fiche.
const outsideNote = computed(() => {
  const offer = selected.value;
  const f = filters.value;
  if (!offer || offer.id !== outsideId.value || offer.score === null || offer.score === undefined) return null;
  const out = (f.minScore !== null && offer.score < f.minScore) || (f.maxScore !== null && offer.score > f.maxScore);
  return out ? `Nouvelle note : ${offer.score}. Elle sort de ton filtre « ${scoreLabel(f)} ».` : null;
});
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
// Liste reliée au détail (§11 du 15 novembre) : la flèche de la carte choisie entre dans l'encoche de la zone de détail.
const listEl = ref<HTMLElement | null>(null);
const linked = computed(() => wide.value && !phone.value);
const gridTop = ref(0);
function measureGrid(): void {
  if (grid.value) gridTop.value = Math.round(grid.value.getBoundingClientRect().top + window.scrollY);
}
// Sur ordinateur, rien n'est ouvert à l'arrivée ni après « Écarter » (§36 du 16 novembre, décision de Kevin du
// 16.11) : sans ?offre=, la colonne de droite montre « Choisis une offre ».
watch(wide, () => void nextTick(measureGrid));
// La colonne de droite sans offre ouverte (§36) : seulement à côté d'une liste qui a des offres.
const choosing = computed(() => linked.value && !selected.value && !failed.value && firstLoaded.value && !emptyWithFilters.value && !bare.value && items.value.length > 0);

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
  () => !noOffersYet.value && filters.value.view === "pending" && counts.value.pending_all === 0 && !activeCount(filters.value),
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
  filled_values?: Record<string, string>;
}): Promise<void> {
  manualOpen.value = false;
  // Complétée (Kevin, 17.11) : « {n} information(s) ajoutée(s) à l'offre » avec « Annuler », comme Écarter (6 s) ;
  // « Annuler » remet vides les champs remplis.
  const values = result.filled_values ?? {};
  const added = Object.keys(values).length;
  if (added) {
    void offerUndo({
      message: added > 1 ? `${added} informations ajoutées à l’offre` : "1 information ajoutée à l’offre",
      commit: () => true,
      restore: async () => {
        await api.POST("/api/offers/manual/{offer_id}/unfill", { params: { path: { offer_id: result.id } }, body: values });
        await load();
      },
    });
  }
  notice.value = added
    ? ""
    : result.existing
      ? "Elle était déjà dans ta liste"
      : result.status === "filtered_out"
        ? `Offre ajoutée. Tes critères l’écartent (${result.reasons.join(" ; ")}) : elle est dans « Écartées ». Sa note arrive dans un instant.`
        : "Offre ajoutée : sa note arrive dans un instant.";
  await load();
  await router.replace({ query: { ...route.query, offre: String(result.id) } });
  await openFromQuery();
  if (result.existing && !result.filled?.length) void flash(result.id);
  else if (!result.existing) awaitScore(result.id);
}
// Ajoutée, l'offre est notée tout de suite, même écartée (Kevin, 15.11) : « Pas encore notée », puis la carte et la
// fiche prennent la note, relue toutes les 5 s pendant 2 min au plus.
let scoreTimer: ReturnType<typeof setTimeout> | undefined;
function awaitScore(id: number, tries = 24): void {
  clearTimeout(scoreTimer);
  scoreTimer = setTimeout(async () => {
    const { data } = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: id } } });
    if (data) items.value = items.value.map((o) => (o.id === id ? data : o));
    if (tries > 1 && data?.score == null && !data?.score_error) awaitScore(id, tries - 1);
  }, 5000);
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
          hide_agencies: f.hideAgencies || undefined,
          with_filtered_out: (f.view === "pending" && f.showFilteredOut) || undefined,
          with_expired: (f.view === "pending" && f.showExpired) || undefined,
          basis: f.basis ?? undefined,
        },
      },
    });
    if (current !== requestId) return; // une requête plus récente est partie entre-temps
    if (!data) throw new Error("réponse vide");
    const kept = append ? null : await keptOutside(data.items);
    if (current !== requestId) return;
    items.value = append ? [...items.value, ...data.items] : kept ? [kept, ...data.items] : data.items;
    if (!append) pinnedId.value = kept ? kept.id : null;
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
      void nextTick(measureGrid);
    }
  }
}

// L'offre renotée, relue si la liste ne la rend plus ; null si elle y est, a changé de statut, ou n'existe plus.
async function keptOutside(listed: Offer[]): Promise<Offer | null> {
  const keep = outside.value;
  outside.value = null;
  if (!keep || listed.some((o) => o.id === keep.id)) return null;
  const data = (await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: keep.id } } }).catch(() => null))?.data;
  if (data?.status !== keep.status) return null;
  outside.value = data;
  return data;
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
  notice.value = "";
  const previous = offer.status;
  // « Annuler » dans le bandeau commun à trait (§23 du 15.11, Kevin le 15.11 18 h 49) : le statut est déjà parti au
  // serveur, « Annuler » remet celui d'avant (docs/60 §3, 6 secondes, docs/108).
  // « Écarter » depuis « En préparation » a aussi son « Annuler » (§36 du 16.11 : la planche écarte une offre en préparation).
  const undoable = previous === "to_review" || previous === "later" || previous === "ignored" || (status === "ignored" && previous === "preparing");
  if (status in STATUS_TEXT && previous !== status && undoable) {
    const discarded = phone.value ? "Offre écartée. Tu la retrouves dans Suivi." : "Offre écartée";
    void offerUndo({
      message: status === "ignored" ? discarded : status === "later" ? "Offre gardée." : status === "to_review" ? "Remise dans Nouvelles." : `Passée en ${STATUS_TEXT[status]}.`,
      commit: () => true,
      restore: async () => {
        await api.PATCH("/api/offers/{offer_id}/status", { params: { path: { offer_id: offer.id } }, body: { status: previous } });
        await load();
        // Sur ordinateur, l'offre revient à sa place, choisie, son détail ouvert (§36, décision de Kevin du 16.11).
        if (linked.value && items.value.some((o) => o.id === offer.id)) selectOffer(offer.id);
      },
    });
  }
  await load();
}

const STATUS_TEXT: Record<string, string> = { later: "Gardée", ignored: "Ignorées", to_review: "Nouvelles" };

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
  else sentMoment.value = { title: data.job_title, company: data.company, count: orp?.count ?? null, target: orp?.target ?? null, month: data.orp_month, dueDate: orp?.due_date ?? null, followUpOn: data.follow_up_on ?? null, applicationId: data.id, addressMissing: !data.company_address?.trim() };
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
  () => {
    outside.value = null;
    void load();
  },
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
  clearTimeout(scoreTimer);
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
         le nombre est sur la pastille de « Toutes » (maquette Candidatures, Kevin, 2026-11-05). -->
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
      v-if="!bare"
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
            :counts="counts"
            @update="update"
            @reset="reset"
            @close="closeFilters"
          />
        </div>
        <!-- Téléphone (décision de Kevin du 15.11, place définitive) : « + » rond de 48 px à 8 px du champ, nommé
             « Ajouter une offre » ; il suit la recherche (masqué avec elle sur un écran vide). « Postuler spontanément »
             est un lien au bas de la liste. Ordinateur : un seul « + Ajouter » et son menu (1.6.47). -->
        <button
          v-if="phone"
          type="button"
          class="offers-add-compact"
          aria-label="Ajouter une offre"
          data-test="manual-open"
          @click="openManual"
        >
          <AppIcon name="plus" />
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
      v-if="!phoneEmptyFiltered"
      :chips="chips"
      @update="(patch) => update(patch, true)"
      @reset="reset(true)"
    />

    <div
      ref="grid"
      :class="['offers-grid', { 'has-selection': selected, 'offers-grid-empty': (emptyWithFilters || bare) && wide && !phone }]"
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
        ref="listEl"
        :class="['offers-list', { 'linked-list': linked && !bare, 'offers-list-bare': bare }]"
      >
        <div
          v-if="wide && !phone && !bare"
          id="offers-list-tools"
          class="offers-list-tools"
          data-linked-tools
        />
        <LinkedPin
          v-if="linked && selected"
          side="top"
          :title="selected.title"
          :sub="selected.company ?? 'Entreprise non indiquée'"
          :name="selected.company ?? selected.title"
          :logo="selected.has_logo ? `/api/offers/${selected.id}/logo` : null"
        />
        <div class="linked-cards">
          <!-- Le compteur (décision de Kevin du 15.11, au-dessus de la liste, ordinateur) : les offres de la liste montrée,
               filtres compris ; avec un filtre qui en retire, « 12 sur 38 offres », 38 étant « Toutes » sans filtre. -->
          <p
            v-if="wide && !phone && !bare && !failed && shownTotal > 0"
            class="offers-count"
            data-test="offers-count"
          >
            {{ countLabel }}
          </p>
          <p
            v-if="notice"
            class="notice"
            role="status"
          >
            {{ notice }}
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
          <!-- Un compte neuf, sans offre ni filtre (§13 du 15 novembre, CandidaturesVide / CandidaturesOrdinateurVide) :
               l’état vide commun, centré sur toute la largeur ; la phrase devient la pastille. -->
          <EmptyState
            v-else-if="noneYet"
            scene="aucune-offre"
            :title="alertsReady ? 'Tes premières offres arrivent bientôt' : 'Pas encore d’offre'"
            :text="alertsReady ? 'jobA1 récupère les nouvelles offres de tes alertes et les ajoute ici, sans que tu aies rien à faire.' : undefined"
            :pill="nonePill"
            data-test="offers-none-yet"
          >
            <template #actions>
              <template v-if="alertsReady">
                <button
                  type="button"
                  class="primary"
                  data-test="offers-none-add"
                  @click="manualOpen = true"
                >
                  <AppIcon name="plus" />Ajouter une offre
                </button>
                <RouterLink
                  to="/candidatures/alertes"
                  class="button-link secondary"
                  data-test="offers-none-alerts"
                >
                  <AppIcon name="bell" />Voir mes alertes
                </RouterLink>
              </template>
              <template v-else>
                <RouterLink
                  to="/candidatures/alertes"
                  class="button-link primary-link"
                  data-test="offers-none-alerts"
                >
                  <AppIcon name="bell" />Créer mes alertes
                </RouterLink>
                <button
                  type="button"
                  class="secondary"
                  data-test="offers-none-add"
                  @click="manualOpen = true"
                >
                  <AppIcon name="plus" />Ajouter une offre
                </button>
              </template>
            </template>
            <a
              v-if="googleLink"
              :href="googleLink.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link"
              aria-label="Voir les offres sur Google Emplois (nouvel onglet)"
              data-test="offers-none-google"
            >Voir les offres sur Google Emplois<AppIcon name="trend" /></a>
            <!-- Retiré une fois les alertes prêtes (§41 du 16.11) : la candidature spontanée reste dans « Ajouter ». -->
            <button
              v-if="!alertsReady"
              type="button"
              class="link"
              data-test="offers-none-spontaneous"
              @click="spontaneousOpen = true"
            >
              Faire une candidature spontanée<AppIcon name="chevron" />
            </button>
          </EmptyState>
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
            <div
              v-if="phone"
              class="offers-empty-chips"
              role="group"
              aria-label="Filtres actifs"
            >
              <button
                v-for="chip in chips"
                :key="chip.key"
                type="button"
                class="offers-empty-chip"
                :aria-label="`Retirer le filtre ${chip.label}`"
                @click="update(chip.patch)"
              >
                {{ chip.label }}<AppIcon name="close" />
              </button>
            </div>
            <p v-else>
              {{ emptyFiltersLine }}
            </p>
            <div class="face-state-actions">
              <button
                v-if="wide && !phone"
                type="button"
                class="secondary offers-empty-reset"
                data-test="offers-reset"
                @click="reset(true)"
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
            <button
              v-if="phone"
              type="button"
              class="link offers-empty-clear"
              data-test="offers-reset"
              @click="reset(true)"
            >
              Tout effacer
            </button>
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
              @click="reset(true)"
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
                <!-- Ordinateur (CandidaturesOrdinateurB du 13.11) : le nombre seul ; « offres » reste pour le lecteur d’écran. -->
                <span class="offer-day-count">{{ row.day.n }}<span class="offer-day-unit">{{ row.day.count.slice(String(row.day.n).length) }}</span></span>
              </h2>
              <OfferCard
                v-else-if="row.offer"
                :offer="row.offer"
                :selected="row.offer.id === selectedId"
                :show-date="!byDay || row.offer.id === pinnedId"
                :outside="row.offer.id === outsideId"
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
          <template v-if="phone && !loading && !failed && !phoneEmptyFiltered && !bare">
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
        <LinkedPin
          v-if="linked && selected"
          side="bottom"
          :title="selected.title"
          :sub="selected.company ?? 'Entreprise non indiquée'"
          :name="selected.company ?? selected.title"
          :logo="selected.has_logo ? `/api/offers/${selected.id}/logo` : null"
        />
      </div>

      <Transition name="detail">
        <div
          v-if="selected"
          class="detail-column"
          @click.self="selectedId = null"
        >
          <component
            :is="linked ? LinkedDetail : Plain"
            :list="listEl"
          >
            <OfferDetail
              :offer="selected"
              :chunk-titles="chunkTitles"
              :outside-note="outsideNote"
              @close="selectedId = null"
              @status="setStatus"
              @applied="openApplication"
              @expiry="setExpiry"
              @address="setAddress"
              @changed="(rescored) => { if (rescored) outside = selected; load(); }"
            />
          </component>
        </div>
        <div
          v-else-if="choosing"
          class="detail-column"
        >
          <LinkedDetail :list="listEl">
            <EmptyState
              class="choose-detail"
              data-test="choose-detail"
              scene="choisis-offre"
              title="Choisis une offre"
              pill="Son détail s’affiche ici"
              pill-icon="arrow-left"
              :width="340"
              :desktop-width="340"
            />
          </LinkedDetail>
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
      <!-- Offre déjà là : ses boutons remplacent « Ajouter l'offre », sous le champ (retour de Kevin sur la #818). -->
      <BusyButton
        v-if="manualOpen && !manualForm?.duplicate"
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
        v-else-if="!manualOpen && spontaneousForm?.created"
        type="button"
        class="primary"
        data-test="spontaneous-prepare"
        @click="spontaneousForm?.prepare()"
      >
        Préparer la candidature
      </button>
      <BusyButton
        v-else-if="!manualOpen"
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
      v-if="manualForm?.shown && !manualForm?.duplicate"
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

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (max-width: 1200px) {
.detail-enter-active .detail-panel, .detail-leave-active .detail-panel { transition: transform 0.25s ease; }
}
@media (prefers-reduced-motion: reduce) {
.panel-section .full-text { transition: none; }
}
.offer-reading-track { stroke: var(--line); }
.offer-reading-arc { stroke: var(--primary); }
.offer-company { --block-cap: 13px; --block-cap-lh: 18px; --field-pad: 16px; --field-label-lh: 18px; --field-value-lh: 22px; }
.gap-fill { display: grid; gap: var(--space-3); margin: var(--space-3) 0 var(--space-4); line-height: var(--leading-normal); }
@media (max-width: 820px) {
.offer-save[aria-pressed="true"] svg { fill: currentColor; }
}
.offers-chip {
  display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--control-h); box-sizing: border-box;
  padding: 0 var(--space-2) 0 var(--space-4); border: 1px solid var(--accent); border-radius: var(--radius-pill);
  background: var(--accent-soft); color: var(--accent); font-size: var(--font-small); font-weight: var(--weight-semibold);
}
.offers-chip-remove {
  display: inline-grid; place-items: center; width: 1.75rem; height: 1.75rem; padding: 0; border: 0;
  border-radius: 50%; background: none; color: inherit; cursor: pointer;
}
.offers-chip-remove:hover { background: color-mix(in srgb, var(--accent) 12%, transparent); }
</style>

<style scoped>
/* AucuneOffre (téléphone) : pastilles de 36 px bleu clair, 14/600, croix de 14 px, 8 px entre elles, centrées ; puis le
   bouton et le lien « Tout effacer » de 44 px. */
.offers-empty-chips { --chip-36: 36px; --chip-14: 14px; display: flex; flex-wrap: wrap; justify-content: center; gap: var(--space-2); margin-top: var(--space-2); }
.offers-empty-chip { gap: var(--space-1); height: var(--chip-36); min-height: 0; padding: 0 var(--space-2) 0 var(--space-3); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font: inherit; font-size: var(--font-small); font-weight: var(--weight-semibold); }
.offers-empty-chip .icon { width: var(--chip-14); height: var(--chip-14); stroke-width: 2.6; }
.offers-empty-clear { min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); }
.offers-empty-chips + .face-state-actions .primary { --empty-52: 52px; min-height: var(--empty-52); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); }
/* Rien encore (§13) : l'état vide occupe la hauteur sous l'en-tête. Téléphone (CandidaturesVide) : du haut de la liste
   (144 px sans le bandeau Démo) à 130 px du bas de l'écran, la marge basse de la page au-dessus de la barre d'onglets. */
.offers-list-bare { display: flex; flex-direction: column; }
.offers-count { margin: 0 0 var(--space-3); padding-inline: var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--text-secondary); }
@media (max-width: 820px) {
  .offers-list-bare { --bare-chrome: 274px; min-height: calc(100dvh - var(--bare-chrome)); }
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
/* Sur ordinateur, sans offre avec ces filtres : pas de colonne de fiche, l'écran est centré sur toute la largeur ;
   « Tout effacer » en contour gris, texte foncé (planche : trait #C9C5BA, --button-outline). */
@media (min-width: 1024px) {
.offers-grid.offers-grid-empty .offers-list { --empty-tools: 472px; flex: 1; width: auto; }
  .offers-grid-empty .offers-list-tools { max-width: var(--empty-tools); }
  .offers-grid-empty .offers-list :deep(.character-state-wide) { margin-inline: auto; }
  .offers-empty-reset { border-color: var(--button-outline); background: var(--surface); color: var(--text); }
}
.offers-empty-spontaneous { --empty-420: 420px; --empty-15: 15px; display: grid; justify-items: center; gap: var(--space-1); width: min(var(--empty-420), 100%); margin: var(--space-8) auto 0; padding-top: var(--space-8); border-top: 1px solid var(--line); }
.offers-empty-spontaneous p { margin: 0; font-size: var(--empty-15); color: var(--text-secondary); }
.offers-empty-spontaneous .link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); font-size: var(--empty-15); font-weight: var(--weight-bold); color: var(--primary-text); }
.add-sheet :deep(.sheet-actions > .primary) { --add-52: 52px; flex: 1 1 auto; justify-content: center; min-height: var(--add-52); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.offer-flash :deep(.list-card) { outline: 3px solid var(--accent); outline-offset: 2px; }
</style>
