
<script setup lang="ts">
import { computed, onMounted, ref, watch, type FunctionalComponent } from "vue";
import { useRoute } from "vue-router";

import { api, type Offer, type RegistryCandidate } from "../api/client";
import { MATCH_TITLE, pointParts } from "../compat";
import { dateInList, dateInSentence } from "../dates";
import { cityOnly, expiredText, frenchName, gapSkill, rateText, remoteText, scoreWord, sourceLabel } from "../format";
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CompanyLogo from "./CompanyLogo.vue";
import DisclosureRow from "./DisclosureRow.vue";
import ContactsPanel from "./ContactsPanel.vue";
import DetailTwoColumns from "./DetailTwoColumns.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import OfferActionSheet from "./OfferActionSheet.vue";
import OfferCompatSheet, { type CompatPoint } from "./OfferCompatSheet.vue";
import OfferTextNotice from "./OfferTextNotice.vue";
import ScoreRing from "./ScoreRing.vue";
import GapFill from "./GapFill.vue";
import ScoreCorrection from "./ScoreCorrection.vue";
import StatusPill from "./StatusPill.vue";
import { useAssistant } from "../composables/useAssistant";
import { usePhone } from "../composables/usePhone";
import { useProfileEmpty } from "../composables/useProfileEmpty";
import ProfileCompletionPanel from "./ProfileCompletionPanel.vue";
import { languageLabel } from "./ProfileCompletionForm.vue";

import HoverNote from "./HoverNote.vue";
import IconButton from "./IconButton.vue";
const props = defineProps<{ offer: Offer; chunkTitles?: Record<number, string> }>();

// Les contacts dans le panneau latéral (docs/32 §2.2) ; l'entreprise a sa section (docs/45).
const contactsCount = ref(0);
// « Trouver un contact chez … » de Postuler (C7) : la fiche s'ouvre sur ses Contacts, dépliés.
const toContacts = useRoute()?.hash === "#contacts";
onMounted(() => {
  if (toContacts) document.getElementById("contacts")?.scrollIntoView?.({ block: "start" });
});
// L'annonce repliée à 6 lignes (docs/45) : « Lire toute l'annonce » la déplie.
const LONG_TEXT = 420;
const textOpen = ref(false);
const textEl = ref<HTMLElement | null>(null);
const textHeight = ref<string | undefined>(undefined);
function openText(): void {
  textHeight.value = textEl.value ? `${textEl.value.scrollHeight}px` : undefined;
  textOpen.value = true;
}
watch(
  () => props.offer.id,
  () => {
    contactsCount.value = 0;
    textOpen.value = false;
    textHeight.value = undefined;
  },
);
const emit = defineEmits<{
  close: [];
  status: [status: "to_review" | "later" | "ignored" | "preparing"];
  applied: [];
  expiry: [expired: boolean];
  address: [address: string];
  changed: [];
}>();

// Annonce chez l'employeur (docs/20 §2) : lien vérifié, ou recherche à la demande.
const PROXY_HOSTS = ["jobup.ch", "jobs.ch", "indeed.", "linkedin.com", "glassdoor.", "jobscout24.", "job-room.ch"];
const EMPLOYER_SOURCES: Record<string, string> = {
  site: "sur son site",
  ats: "via son outil de recrutement",
  web: "sur Internet",
};
const employerBusy = ref(false);
const employerMessage = ref("");
// Lien vers l'employeur déjà donné par l'annonce jobup : rien à chercher.
const employerKnown = computed(() => {
  const url = props.offer.apply_url;
  return props.offer.apply_kind === "external" && !!url && !PROXY_HOSTS.some((h) => url.includes(h));
});

async function findEmployer(): Promise<void> {
  employerBusy.value = true;
  employerMessage.value = "";
  try {
    const { data, error } = await api.POST("/api/offers/{offer_id}/employer", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      employerMessage.value = typeof detail === "string" ? `Recherche impossible : ${detail}.` : "Recherche impossible.";
      return;
    }
    // L'état (« Pas trouvée… », lien trouvé) s'affiche avec l'offre rechargée : pas de second message.
    emit("changed");
  } finally {
    employerBusy.value = false;
  }
}

// Bouton « Postuler » (docs/21 §5) : chez l'employeur si l'annonce y est, sinon sur le site.
const postLink = computed(() => {
  const o = props.offer;
  if (o.employer_url) return { url: o.employer_url, label: "Postuler chez l’employeur" };
  if (o.apply_url) {
    return { url: o.apply_url, label: o.apply_kind === "external" ? "Postuler chez l’employeur" : "Postuler sur jobup" };
  }
  const link = o.links[0];
  if (link?.source === "manual") return { url: link.url, label: "Ouvrir l’annonce" };
  return link ? { url: link.url, label: `Postuler sur ${sourceLabel[link.source]}` } : null;
});

// Registre IDE (docs/12 §2.2) : propositions quand le nom ne suffit pas à trancher.
const searching = ref(false);
const proposals = ref<RegistryCandidate[]>([]);
const registryMessage = ref("");

async function searchRegistry(): Promise<void> {
  searching.value = true;
  registryMessage.value = "";
  proposals.value = [];
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/address-candidates", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      registryMessage.value = "Registre IDE injoignable, réessaie plus tard.";
    } else if (data.chosen_uid && props.offer.company_address_source !== "registry") {
      registryMessage.value = "Adresse trouvée dans le registre IDE.";
      emit("changed");
    } else if (data.web_address) {
      registryMessage.value = "Adresse trouvée sur Internet : vérifie la source.";
      proposals.value = data.candidates;
      emit("changed");
    } else {
      proposals.value = data.candidates;
      const web = data.web_unavailable
        ? ` Recherche sur Internet impossible : ${data.web_unavailable}.`
        : " Rien de fiable sur Internet non plus.";
      registryMessage.value = data.candidates.length
        ? `Pas de correspondance sûre : choisis parmi le registre, ou saisis l’adresse.${web}`
        : `Aucune entreprise à ce nom dans le registre.${web} Saisis l’adresse à la main.`;
    }
  } catch {
    registryMessage.value = "API injoignable.";
  } finally {
    searching.value = false;
  }
}

async function chooseRegistry(uid: string): Promise<void> {
  const { data } = await api.POST("/api/offers/{offer_id}/address-candidates/choose", {
    params: { path: { offer_id: props.offer.id } },
    body: { uid },
  });
  proposals.value = [];
  registryMessage.value = data ? "" : "Choix refusé.";
  if (data) emit("changed");
}

const STATUS_LABEL: Partial<Record<Offer["status"], string>> = {
  preparing: "En préparation",
  later: "Plus tard",
  ignored: "Ignorée",
  filtered_out: "Écartée par le filtre",
  applied: "Candidature envoyée",
};
const statusLabel = computed(() =>
  props.offer.expired_at && props.offer.status !== "applied" ? "Expirée" : (STATUS_LABEL[props.offer.status] ?? ""),
);
// Le ton de la pastille (règle §4) : vert seulement pour la candidature envoyée, le reste neutre.
const pillTone = computed(() =>
  props.offer.status === "applied" ? ("ok" as const) : ("neutral" as const),
);
// « À savoir » (planche « Fiche d'une offre ») : une ligne « libellé : valeur » pour ce qui est
// connu seulement ; l'adresse a toujours sa ligne (« Adresse inconnue · Ajouter »). Puis les faits à
// vérifier : alerte à vérifier, croix pour la raison d'un écart.
type Fact = { mark: "check" | "no"; text: string; excerpt?: string; scam?: boolean };
const MARKS: Record<Fact["mark"], IconName> = { check: "alert", no: "x-circle" };
// Les étiquettes de la tête (O5) : taux, contrat, télétravail, date de réception. Un contrat inconnu se dit
// (issue 468) ; la date suit la règle des dates, jamais « il y a ».
const tags = computed(() => {
  const o = props.offer;
  const rate = rateText(o.rate_min, o.rate_max);
  const remote = remoteText(o);
  const received = o.first_seen_at ? dateInList(o.first_seen_at) : "";
  return [
    ...(rate ? [{ test: "rate", text: rate }] : []),
    { test: "contract", text: o.employment_type || "Contrat non précisé" },
    ...(remote ? [{ test: "remote", text: remote }] : []),
    ...(received ? [{ test: "received", text: /^\d/.test(received) ? `Reçue ${dateInSentence(o.first_seen_at)}` : `Reçue ${received}` }] : []),
  ];
});
const facts = computed<Fact[]>(() => {
  const o = props.offer;
  const list: Fact[] = [];
  if (o.remote_from_switzerland === false) list.push({ mark: "check", text: "Télétravail pas ouvert depuis la Suisse" });
  for (const doubt of o.doubts ?? []) {
    list.push({ mark: "check", text: doubt.text, excerpt: doubt.excerpt ?? undefined, scam: doubt.kind === "scam" });
  }
  for (const reason of o.filter_reasons ?? []) list.push({ mark: "no", text: reason });
  // « Non renseigné » n'écarte rien (PR 17, point 3) : la langue exigée par l'annonce est seulement à vérifier.
  for (const language of o.languages_to_check ?? []) list.push({ mark: "check", text: `Langue à vérifier : ${languageLabel(language).toLowerCase()}` });
  if (o.enrich_status === "expired") list.push({ mark: "no", text: "L’annonce n’est plus en ligne sur jobup." });
  return list;
});
// Points forts et manques (planche) : trois au plus, le mot clé en gras en tête (« Kubernetes : … »).
const POINTS_MAX = 3;
// Sur téléphone (sous 820 px), la fiche est une sous-page (maquette Offre, docs/139 étape 6a) : en-tête
// « retour » avec Sauvegarder, « ⋯ » et Partager ; en bas, « Écarter » et « Préparer ma candidature ».
// « Cette note ne me correspond pas » passe dans la feuille « ⋯ » et s'ouvre dans une feuille du bas.
const { phone: sub } = usePhone();
const withBar = computed(() => sub.value && props.offer.status !== "applied");
const scored = computed(() => props.offer.score !== null && props.offer.score !== undefined);
const correcting = ref(false);
// La carte de correspondance (O3, O4) : le mot en titre, le chiffre dans l'anneau (D12), les lignes ✓ et (!).
const matchWord = computed(() => (scored.value ? scoreWord(props.offer.score!) : null));
const matchTone = computed(() => matchWord.value?.tone ?? "none");
const matchTitle = computed(() => {
  if (matchWord.value) return MATCH_TITLE[matchWord.value.tone]!;
  return props.offer.score_error ? "Note impossible" : "Pas encore notée";
});
// Sans profil, la note n'arrive jamais : la fiche le dit et envoie vers Profil › Expériences (test du 10 novembre).
const { empty: profileEmpty, refresh: refreshProfile } = useProfileEmpty();
onMounted(() => void refreshProfile());
const needsProfile = computed(() => !scored.value && profileEmpty.value);
// « Compléter mon profil » (PR 17, point 4) : le formulaire des premiers pas en panneau ; à l'enregistrement, la fiche
// reste ouverte et l'offre est notée (le serveur lance la notation au premier élément du profil).
const completing = ref(false);
async function profileSaved(): Promise<void> {
  completing.value = false;
  await refreshProfile();
}
const matchSub = computed(() => {
  const o = props.offer;
  if (needsProfile.value) return "Il manque ton profil pour noter cette offre.";
  if (!scored.value) return o.score_error ?? "La note arrive dès que l’annonce est lue.";
  // Le chiffre est dans l'anneau (D12) : la phrase dit seulement sur quoi il repose (maquette Offre).
  // Note provisoire (maquette OffreProvisoire du 10 novembre) : pendant la lecture automatique de l'annonce, elle
  // attend le texte complet ; si le site bloque la lecture, les exigences n'ont pas pu être vérifiées.
  if (provisional.value) {
    return o.text_reading === "refused"
      ? "Calculée sur l’extrait de l’alerte : les exigences n’ont pas pu être vérifiées."
      : "Calculée sur l’extrait de l’alerte, en attendant l’annonce complète.";
  }
  const base = "Selon ton profil et tes préférences";
  return o.summary_partial ? `${base}, sur l’extrait de l’alerte seulement` : base;
});
const pointTitle = (text: string): string => pointParts(text).key || pointParts(text).rest;
const matchLines = computed(() => [
  ...strengths.value.map((p) => ({ mark: "ok" as const, text: pointTitle(p.text) })),
  ...gaps.value.map((p) => ({ mark: "gap" as const, text: pointTitle(p.text) })),
  ...(props.offer.level && props.offer.level_detail ? [{ mark: "gap" as const, text: props.offer.level_detail }] : []),
]);
const noteDetail = computed(() => {
  const o = props.offer;
  return !!(o.why || o.level || strengths.value.length || gaps.value.length || scoreNote.value || scored.value);
});
// La feuille « Compatibilité » du téléphone (§10.1, 3 bis) : tous les points forts et tous les manques, le critère
// séparé de sa valeur (« Compétences : Kubernetes… ») ; le niveau compte comme un point à vérifier.
const compatOpen = ref(false);
const compatPoint = (text: string): CompatPoint => {
  const parts = pointParts(text);
  return { key: parts.key, value: parts.rest };
};
const compatStrengths = computed(() => (props.offer.strengths ?? []).map((p) => compatPoint(p.text)));
const compatGaps = computed(() => [
  ...(partial.value ? [] : (props.offer.gaps ?? [])).map((p) => compatPoint(p.text)),
  ...(props.offer.level && props.offer.level_detail ? [{ key: "Niveau", value: props.offer.level_detail }] : []),
]);
const compatHow = computed(() =>
  [props.offer.why, scoreNote.value].filter((t): t is string => !!t?.trim()),
);
// Le poste (O6) : les trois résumés de l'IA, dans l'ordre du poste, de ce qu'il demande, de ce qu'il offre.
const summaryParts = computed(() =>
  [props.offer.summary_role, props.offer.summary_asks, props.offer.summary_offers].filter((t): t is string => !!t?.trim()),
);
const strengths = computed(() => (props.offer.strengths ?? []).slice(0, POINTS_MAX));
// Note provisoire : l'offre n'a que l'extrait de l'alerte (pas de texte complet). Ses manques sont alors
// génériques (« Exigences », « Données », « Conseil ») : la lecture de l'annonce complète les remplace.
const partial = computed(() => !props.offer.description && !props.offer.spontaneous);
const gaps = computed(() => (partial.value ? [] : (props.offer.gaps ?? []).slice(0, POINTS_MAX)));
// Notée sur l'extrait seulement : pastille « Provisoire », anneau pâli, sous-titre qui le dit.
const provisional = computed(() => partial.value && scored.value);
// L'annonce lue (automatiquement) ou collée : la note est refaite, la carte le confirme (prompt du 10 novembre, état
// `done`).
const redone = computed(() => props.offer.text_reading === "done");
// Les annonces d'origine qui ne sont pas déjà le bouton « Postuler » (docs/45 : pas de doublon).
const otherLinks = computed(() =>
  props.offer.links.filter((link) => props.offer.status === "applied" || link.url !== postLink.value?.url),
);
// « Préparer ma candidature » lance l'écriture de la lettre dès l'arrivée, le CV adapté en même temps (MODIFICATIONS
// du 9 novembre, §7 n° 1) ; « Reprendre la lettre » ouvre seulement la préparation.
const prepareLink = computed(() =>
  props.offer.status === "preparing"
    ? `/candidatures/offres/${props.offer.id}/preparer`
    : `/candidatures/offres/${props.offer.id}/preparer?ecrire=1`,
);
const ADDRESS_SOURCE: Record<string, string> = {
  page: "annonce",
  registry: "registre IDE",
  web: "trouvée sur Internet",
  letter: "relevée dans l’annonce",
  manual: "saisie par toi",
};

// Menu « ⋯ » : les actions rares, hors de la vue principale (docs/12 §1, docs/45, docs/50 §1).
const assistant = useAssistant();
function askAssistant(): void {
  const o = props.offer;
  assistant.askAbout({ offerId: o.id, label: `offre ${o.title}${o.company ? ` chez ${o.company}` : ""}` });
}

// Sous la note, en petit : elle ne porte que sur l'extrait de l'alerte. Les autres réserves suivent
// la phrase « pourquoi ».
const scoreNote = computed(() => {
  const o = props.offer;
  return [o.score_stale && "Ton profil a changé depuis : note à refaire.", o.score === null && "Pas de note : aucun bloc de profil actif."]
    .filter(Boolean)
    .join(" ");
});
// Ordinateur dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB état « actions ») : d'abord les entrées
// dessinées, dans leur ordre (ouvrir l'annonce, garder pour plus tard, détail de la note, copier le lien, puis
// « Signaler une erreur dans l'offre » après un trait) ; les autres actions de la fiche suivent (docs/143, écarts).
const { phone: wide } = usePhone("(min-width: 1024px)");
// À traiter sur ordinateur (MODIFICATIONS du 8 novembre au soir, lot 13.1) : la note et le poste à gauche, « L'offre en
// bref » à droite (gabarit DetailTwoColumns). Sous 1 024 px, la fiche garde une colonne, dans le même ordre.
const columns = computed(() => wide.value && !sub.value);
const Flat: FunctionalComponent = (_props, { slots }) => [slots.main?.(), slots.aside?.()];
const layout = computed(() => (columns.value ? DetailTwoColumns : Flat));
const layoutProps = computed(() => (columns.value ? { asideLabel: "L’offre en bref" } : {}));
function upperFirst(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
// « Hier, par une alerte e-mail » ; une offre ajoutée à la main le dit.
const receivedText = computed(() => {
  const o = props.offer;
  if (!o.first_seen_at) return "Non précisé";
  const day = dateInList(o.first_seen_at);
  const when = upperFirst(/^\d/.test(day) ? dateInSentence(o.first_seen_at) : day);
  return `${when}, ${o.added_by_you ? "ajoutée par toi" : "par une alerte e-mail"}`;
});
const brief = computed(() => {
  const o = props.offer;
  return [
    { label: "Lieu", value: o.location || "Non précisé", test: "brief-place" },
    { label: "Contrat", value: o.employment_type || "Non précisé", test: "brief-contract" },
    { label: "Taux d’activité", value: rateText(o.rate_min, o.rate_max) || "Non précisé", test: "brief-rate" },
    { label: "Reçue", value: receivedText.value, test: "brief-received" },
  ];
});
function showNoteDetail(): void {
  const row = document.querySelector<HTMLElement>("[data-test=note-detail]");
  const toggle = row?.querySelector<HTMLButtonElement>("button[aria-expanded]");
  if (toggle?.getAttribute("aria-expanded") === "false") toggle.click();
  row?.scrollIntoView?.({ block: "nearest" });
  toggle?.focus({ preventScroll: true });
}
async function copyLink(): Promise<void> {
  const url = shareUrl.value;
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    saidAloud.value = "Lien copié.";
  } catch {
    saidAloud.value = "Copie impossible.";
  }
}
const desktopItems = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (shareUrl.value) items.push({ label: "Ouvrir l’annonce sur le site", test: "open-ad", icon: "external", href: shareUrl.value });
  if (o.status === "later") items.push({ label: "Remettre à examiner", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
  else if (o.status !== "applied") items.push({ label: "Garder pour plus tard", test: "later", icon: "clock", run: () => emit("status", "later") });
  if (noteDetail.value) items.push({ label: "Voir le détail de la note", test: "show-note-detail", icon: "eye", run: showNoteDetail });
  if (shareUrl.value) items.push({ label: "Copier le lien", test: "copy-link", icon: "link", run: () => void copyLink() });
  if (withBar.value && scored.value) {
    items.push({ label: "Signaler une erreur dans l’offre", test: "score-correction-menu", icon: "flag", separator: true, run: () => (correcting.value = true) });
  }
  if (o.status !== "applied") {
    items.push({ label: "J’ai postulé", test: "mark-applied", icon: "check-circle", separator: true, run: () => emit("applied") });
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "alert", run: () => emit("expiry", true) },
    );
  }
  if (assistant.available.value) items.push({ label: "Demander à l’assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  return items;
});
const menuItems = computed<MoreMenuItem[]>(() => {
  if (wide.value) return desktopItems.value;
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (o.status !== "applied") {
    items.push({ label: "J’ai déjà postulé", test: "mark-applied", icon: "check-circle", run: () => emit("applied") });
    if (o.status === "later" || o.status === "ignored" || o.status === "preparing") {
      items.push({ label: "Remettre à examiner", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
    } else {
      items.push({ label: "Plus tard", test: "later", icon: "clock", run: () => emit("status", "later") });
      // Un seul mot pour une action (étape 6, O8) : « Écarter », comme dans la feuille de la liste.
      items.push({ label: "Écarter", test: "ignore", icon: "x-circle", run: () => emit("status", "ignored") });
    }
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "alert", run: () => emit("expiry", true) },
    );
  }
  if (withBar.value && scored.value) {
    items.push({ label: "Cette note ne me correspond pas", test: "score-correction-menu", icon: "star", run: () => (correcting.value = true) });
  }
  if (assistant.available.value) {
    items.push({ label: "Demander à l’assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  }
  return items;
});

// La feuille « ⋯ » de la sous-page (O9) : « Écarter l'offre » et « Marquer comme envoyée », puis les actions
// propres à la fiche. « Plus tard » devient le signet de l'en-tête (O2).
const sheetOpen = ref(false);
const sheetExtra = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (o.status === "later" || o.status === "ignored" || o.status === "preparing") {
    items.push({ label: "Remettre à examiner", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
  }
  if (o.status !== "applied") {
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "alert", run: () => emit("expiry", true) },
    );
  }
  if (scored.value) items.push({ label: "Cette note ne me correspond pas", test: "score-correction-menu", icon: "star", run: () => (correcting.value = true) });
  // Lot 18 (maquette Offre) : l'en-tête n'a plus que retour, garder et « … » ; Partager passe dans la feuille.
  if (shareUrl.value) items.push({ label: "Partager l’annonce", test: "share", icon: "upload", run: () => void share() });
  if (assistant.available.value) items.push({ label: "Demander à l’assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  return items;
});
// Sauvegarder (O2) : l'état « Plus tard », qui existe déjà ; le signet est plein quand l'offre y est.
const saved = computed(() => props.offer.status === "later");
const canSave = computed(() => ["to_review", "later"].includes(props.offer.status));
function toggleSaved(): void {
  emit("status", saved.value ? "to_review" : "later");
  saidAloud.value = saved.value ? "Offre remise à examiner." : "Offre gardée pour plus tard.";
}
// Partager (O2) : le lien public de l'annonce (employeur, puis site source), jamais l'adresse jobA1, qui est
// privée. La feuille de partage du téléphone, sinon le lien copié.
const shareUrl = computed(() => props.offer.employer_url || props.offer.links.find((l) => l.url)?.url || null);
const saidAloud = ref("");
async function share(): Promise<void> {
  const url = shareUrl.value;
  if (!url) return;
  const title = [props.offer.title, props.offer.company].filter(Boolean).join(" · ");
  if (typeof navigator.share === "function") {
    await navigator.share({ title, url }).catch(() => undefined);
    return;
  }
  try {
    await navigator.clipboard.writeText(url);
    saidAloud.value = "Lien copié.";
  } catch {
    saidAloud.value = "Copie impossible.";
  }
}
// Offre expirée (O7) : le bouton principal mène aux offres proches, par le titre du poste.
const nearbyLink = computed(() => ({ path: "/candidatures/offres", query: { q: props.offer.title } }));

// Partie « Entreprise » (docs/74) : l'adresse visible, les actions dans son « ⋯ ».
const canSearchEmployer = computed(
  () =>
    !employerKnown.value &&
    props.offer.employer_status !== "agency" &&
    !(props.offer.employer_url && props.offer.employer_checked_at),
);
const companyItems = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  if (o.company_address) items.push({ label: "Modifier l’adresse", test: "edit-address", icon: "pencil", run: startAddress });
  if (o.company && o.company_address_source !== "manual" && o.company_address_source !== "page") {
    items.push({
      label: "Chercher l’adresse",
      test: "search-registry",
      icon: "ai",
      disabled: searching.value,
      run: () => void searchRegistry(),
    });
  }
  if (canSearchEmployer.value) {
    items.push({
      label: o.employer_checked_at ? "Chercher à nouveau chez l’employeur" : "Chercher l’offre chez l’employeur",
      test: "find-employer",
      icon: "ai",
      disabled: employerBusy.value,
      run: () => void findEmployer(),
    });
  }
  if (o.company_address_source === "web" && o.company_address_url) {
    items.push({ label: "Vérifier la source de l’adresse", test: "address-source", href: o.company_address_url });
  }
  return items;
});
// Les annonces d'origine, dans le « ⋯ » de la partie « Annonce ».
const announceItems = computed<MoreMenuItem[]>(() =>
  otherLinks.value.map((link) => ({ label: `Voir sur ${sourceLabel[link.source]}`, test: `source-${link.source}`, href: link.url })),
);

const editingAddress = ref(false);
const addressDraft = ref("");
function startAddress(): void {
  addressDraft.value = props.offer.company_address ?? "";
  editingAddress.value = true;
}
function saveAddress(): void {
  editingAddress.value = false;
  emit("address", addressDraft.value);
}
watch(
  () => props.offer.id,
  () => {
    editingAddress.value = false;
    proposals.value = [];
    registryMessage.value = "";
  },
);
</script>


<template>
  <article
    :class="['detail-panel', { 'offer-cols': columns, 'offer-blocks': sub }]"
    data-test="offer-detail"
  >
    <!-- La sous-page du téléphone (maquette Offre) : retour à gauche ; Sauvegarder, « ⋯ », Partager à droite. -->
    <header
      v-if="sub"
      class="offer-subhead grille-top"
      data-test="offer-subhead"
    >
      <IconButton
        icon="chevron-left"
        label="Retour aux candidatures"
        data-test="back-detail"
        @click="$emit('close')"
      />
      <div class="offer-subhead-actions">
        <button
          v-if="canSave"
          type="button"
          class="icon-button icon-only offer-save"
          :aria-pressed="saved"
          aria-label="Garder pour plus tard"
          data-label="Garder pour plus tard"
          data-test="offer-save"
          @click="toggleSaved"
        >
          <AppIcon name="bookmark" />
        </button>
        <IconButton
          icon="more"
          label="Plus d’actions sur l’offre"
          data-test="detail-more"
          @click="sheetOpen = true"
        />
      </div>
      <p
        class="visually-hidden"
        aria-live="polite"
        data-test="offer-said"
      >
        {{ saidAloud }}
      </p>
    </header>
    <!-- Sur un écran moyen, le retour en haut à gauche, au-dessus de la fiche (règles §2). -->
    <button
      v-else
      type="button"
      class="link detail-back"
      data-test="back-detail"
      @click="$emit('close')"
    >
      <span class="with-icon"><AppIcon name="arrow-left" /><span><span class="visually-hidden">Retour aux </span>Offres</span></span>
    </button>

    <!-- La tête (maquette Offre, étape 6b) : logo, poste, « Entreprise · Lieu », l'état, les étiquettes. Sur
         ordinateur, les deux actions dessous (O10) ; sur téléphone, elles sont dans la barre du bas. -->
    <section
      :class="['detail-offer', { 'grille-info': sub }]"
      data-test="section-offer"
    >
      <div class="detail-head">
        <CompanyLogo
          :offer="offer"
          large
        />
        <div class="detail-top-actions">
          <!-- Fermer (croix) sur écran moyen ; sur téléphone, le retour de l'en-tête. -->
          <IconButton
            v-if="!sub"
            icon="close"
            label="Fermer le détail"
            class="detail-close"
            data-test="close-detail"
            @click="$emit('close')"
          />
          <MoreMenu
            v-if="menuItems.length && !sub"
            :items="menuItems"
            label="Plus d’actions sur l’offre"
          />
        </div>
      </div>
      <div class="detail-title">
        <h2
          tabindex="-1"
          data-test="offer-detail-title"
        >
          {{ offer.title }}
        </h2>
        <p
          class="detail-sub"
          data-test="detail-meta"
        >
          <span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée"
          }} · <span class="visually-hidden">Lieu : </span>{{ (sub ? cityOnly(offer.location) : frenchName(offer.location)) || "Lieu non précisé" }}
        </p>
      </div>
      <!-- Sur téléphone, l'état n'a pas de ligne (maquette Offre) : le bouton du bas le dit déjà
           (« Reprendre la lettre ») ; une candidature envoyée garde la sienne, avec son lien. -->
      <div
        v-if="statusLabel && (!sub || offer.status === 'applied')"
        class="status-line"
      >
        <StatusPill
          :tone="pillTone"
          data-test="status-pill"
        >
          {{ statusLabel }}
        </StatusPill>
        <RouterLink
          v-if="offer.status === 'applied'"
          to="/candidatures/suivi"
          class="link"
        >
          Voir le suivi
        </RouterLink>
      </div>
      <p
        v-if="offer.expired_at && offer.status !== 'applied'"
        class="notice expired-notice"
        data-test="expired"
      >
        {{ expiredText(offer) }}
      </p>
      <ul
        class="offer-tags"
        data-test="offer-tags"
      >
        <li
          v-for="tag in tags"
          :key="tag.test"
          :data-test="`tag-${tag.test}`"
        >
          {{ tag.text }}
        </li>
      </ul>
      <div
        v-if="offer.status !== 'applied' && !sub"
        class="detail-actions"
        data-test="triage"
      >
        <RouterLink
          v-if="offer.expired_at && offer.status !== 'preparing'"
          :to="nearbyLink"
          class="button-link primary-link"
          data-test="nearby"
        >
          Voir des offres proches
        </RouterLink>
        <RouterLink
          v-else
          :to="prepareLink"
          class="button-link primary-link"
          data-test="prepare"
        >
          {{ offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
        </RouterLink>
        <button
          v-if="offer.status !== 'ignored'"
          type="button"
          class="secondary"
          data-test="offer-discard"
          @click="emit('status', 'ignored')"
        >
          Écarter
        </button>
        <!-- Lot 15.2 : le parcours « Marquer comme envoyée », en niveau 2 à droite de « Écarter ». -->
        <button
          type="button"
          class="secondary"
          data-test="offer-already-applied"
          @click="emit('applied')"
        >
          J’ai déjà postulé
        </button>
      </div>
    </section>

    <BottomSheet
      v-if="withBar && scored"
      :open="correcting"
      title="Corriger la note"
      data-test="score-correction-sheet"
      @close="correcting = false"
    >
      <ScoreCorrection
        :offer-id="offer.id"
        start-open
        @changed="correcting = false; emit('changed')"
        @cancel="correcting = false"
      />
    </BottomSheet>
    <OfferActionSheet
      v-if="sub"
      :offer="sheetOpen ? offer : null"
      :extra="sheetExtra"
      sent-title="J’ai déjà postulé"
      @close="sheetOpen = false"
      @discard="sheetOpen = false; emit('status', 'ignored')"
      @sent="sheetOpen = false; emit('applied')"
    />
    <OfferCompatSheet
      v-if="(sub || columns) && scored"
      :open="compatOpen"
      :score="offer.score ?? null"
      :provisional="provisional"
      :stale="offer.score_stale"
      :verdict="matchTitle"
      :tone="matchTone"
      :subtitle="`${offer.title} · ${offer.company ?? 'Entreprise non indiquée'}`"
      :strengths="compatStrengths"
      :gaps="compatGaps"
      :how="compatHow"
      @close="compatOpen = false"
    />
    <!-- La barre du bas de la sous-page (O8) : « Écarter » (avec « Annuler » 6 s) et l'action principale ;
         une offre expirée mène aux offres proches (O7). -->
    <div
      v-if="withBar"
      class="offer-bar grille-bar"
      data-test="offer-bar"
    >
      <button
        v-if="offer.status !== 'ignored'"
        type="button"
        class="secondary action-2 offer-bar-discard"
        data-test="offer-discard"
        @click="emit('status', 'ignored')"
      >
        Écarter
      </button>
      <RouterLink
        v-if="offer.expired_at && offer.status !== 'preparing'"
        :to="nearbyLink"
        class="button-link primary-link offer-bar-main"
        data-test="nearby"
      >
        Voir des offres proches
      </RouterLink>
      <RouterLink
        v-else
        :to="prepareLink"
        class="button-link primary-link offer-bar-main"
        data-test="prepare"
      >
        {{ offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
      </RouterLink>
    </div>

    <!-- La correspondance (O3, O4) : l'anneau sans chiffre (D3), le mot en titre, « 92 sur 100 » dessous
         (docs/121) ; une ligne par point fort (coche) et par manque (gris chaud, D5 : un manque n’est pas une
         action) ; le détail de la note replié. -->
    <component
      :is="layout"
      v-bind="layoutProps"
    >
      <template #main>
        <section
          :class="['detail-card', 'match-card', { 'detail-section': columns, 'grille-info': sub }]"
          aria-labelledby="match-title"
          data-test="section-for-you"
        >
          <div :class="['match-head', { 'match-head-alone': columns && !scored }]">
            <ScoreRing
              v-if="scored"
              :score="offer.score ?? null"
              :stale="offer.score_stale"
              :provisional="provisional"
              large
              bare
            />
            <div>
              <div class="match-title-row">
                <h3
                  id="match-title"
                  :class="['match-title', `is-${matchTone}`]"
                  data-test="match-title"
                >
                  {{ matchTitle }}
                </h3>
                <span
                  v-if="provisional"
                  class="provisional-pill"
                  data-test="provisional"
                >Provisoire</span>
              </div>
              <p
                class="match-sub"
                data-test="match-sub"
              >
                {{ matchSub }}
              </p>
              <button
                v-if="needsProfile"
                type="button"
                class="match-profile-link"
                aria-haspopup="dialog"
                data-test="match-profile-link"
                @click="completing = true"
              >
                Compléter mon profil<AppIcon name="chevron" />
              </button>
            </div>
          </div>
          <ul
            v-if="matchLines.length && !sub && !columns"
            class="match-lines"
            data-test="match-lines"
          >
            <li
              v-for="line in matchLines"
              :key="line.mark + line.text"
              :class="line.mark"
            >
              <AppIcon :name="line.mark === 'ok' ? 'tick' : 'alert-circle'" /><span><span class="visually-hidden">{{ line.mark === "ok" ? "Point fort : " : "Manque : " }}</span>{{ line.text }}</span>
            </li>
          </ul>
          <OfferTextNotice
            v-if="partial"
            :offer="offer"
            @changed="emit('changed')"
            @refresh="emit('changed')"
          />
          <p
            v-else-if="redone"
            class="redone"
            role="status"
            data-test="redone"
          >
            <AppIcon name="done" />Note refaite sur l’annonce complète.
          </p>
          <!-- Téléphone (§10.1) et ordinateur (MODIFICATIONS du 9 novembre, §2.1) : une seule ligne cliquable, « Voir la
               compatibilité », sur la ligne de texte du verdict ; le détail est dans le panneau. -->
          <button
            v-if="(sub || columns) && scored"
            type="button"
            class="compat-open"
            aria-haspopup="dialog"
            data-test="compat-open"
            @click="compatOpen = true"
          >
            <!-- Téléphone (prompt du 10 novembre, PR 15) : « Le détail de la note », aligné sur le contenu de la carte,
                 chevron à droite, que la note soit provisoire ou non. Ordinateur : « Voir la compatibilité ». -->
            {{ sub ? "Le détail de la note" : "Voir la compatibilité" }}
            <AppIcon name="chevron" />
          </button>
          <DisclosureRow
            v-if="noteDetail && !sub && !columns"
            title="Le détail de la note"
            class="match-detail"
            data-test="note-detail"
          >
            <p
              v-if="offer.why"
              data-test="score-why"
            >
              {{ offer.why }}
            </p>
            <p
              v-if="offer.level"
              class="level-line"
              data-test="score-level"
            >
              <HoverNote :text="offer.level_detail ?? ''">
                {{ offer.level === "above" ? "Niveau au-dessus" : "Niveau en dessous" }}
              </HoverNote>
            </p>
            <template v-if="strengths.length">
              <h4>Points forts</h4>
              <ul data-test="strengths">
                <li
                  v-for="point in strengths"
                  :key="point.text"
                >
                  <strong v-if="pointParts(point.text).key">{{ pointParts(point.text).key }} :</strong>
                  {{ pointParts(point.text).rest }}
                </li>
              </ul>
            </template>
            <template v-if="gaps.length">
              <h4>Manques</h4>
              <ul
                class="gaps"
                data-test="gaps"
              >
                <li
                  v-for="point in gaps"
                  :key="point.text"
                >
                  <strong v-if="pointParts(point.text).key">{{ pointParts(point.text).key }} :</strong>
                  {{ pointParts(point.text).rest }}
                  <!-- Une exigence absente du profil (aucun bloc cité) : « Je l'ai » (docs/121 §C.3). -->
                  <GapFill
                    v-if="!point.chunk_ids.length && gapSkill(point.text)"
                    :offer-id="offer.id"
                    :gap="point.text"
                    @added="emit('changed')"
                  />
                </li>
              </ul>
            </template>
            <p
              v-if="scoreNote"
              class="hint score-note"
              data-test="score-note"
            >
              {{ scoreNote }}
            </p>
            <!-- « Cette note ne me correspond pas » (docs/114) ; sur téléphone, dans la feuille « ⋯ ». -->
            <ScoreCorrection
              v-if="scored && !sub"
              :offer-id="offer.id"
              @changed="emit('changed')"
            />
          </DisclosureRow>
        </section>

        <!-- Le poste (O6) : le résumé rédigé par jobA1, dit comme tel ; l'annonce complète se déplie sur place ;
         « Postuler chez l’employeur » à côté (O7) ; les réserves sur l’annonce dessous. -->
        <section
          :class="['detail-post', { 'detail-section': columns }]"
          aria-labelledby="post-title"
          data-test="section-ad"
        >
          <div class="detail-post-head">
            <h3 id="post-title">
              Le poste
            </h3>
            <MoreMenu
              v-if="announceItems.length"
              class="section-more"
              :items="announceItems"
              label="Plus d’actions sur l’annonce"
              test-id="ad-more"
            />
          </div>
          <!-- Note provisoire : l'extrait de l'alerte, dit comme tel (maquette OffreProvisoire). -->
          <p
            v-if="partial"
            class="post-by"
            data-test="snippet-by"
          >
            Extrait de l’alerte
          </p>
          <template v-if="summaryParts.length && !partial">
            <p
              class="post-by"
              data-test="summary-by"
            >
              Résumé par jobA1
            </p>
            <p
              v-for="part in summaryParts"
              :key="part"
              class="post-summary"
              data-test="summary"
            >
              {{ part }}
            </p>
          </template>
          <p
            v-else-if="!offer.description"
            class="detail-snippet"
          >
            {{ offer.snippet || "Pas d’extrait dans l’alerte : le texte complet de l’annonce est sur le site." }}
          </p>
          <div
            v-if="offer.description && (textOpen || !summaryParts.length)"
            ref="textEl"
            :class="['full-text', { folded: !textOpen && offer.description.length > LONG_TEXT }]"
            :style="textOpen && textHeight ? { maxHeight: textHeight } : undefined"
            data-test="description"
          >
            {{ offer.description }}
          </div>
          <div class="post-links">
            <button
              v-if="offer.description && !textOpen && (summaryParts.length || offer.description.length > LONG_TEXT)"
              type="button"
              class="link read-more"
              data-test="read-more"
              @click="openText"
            >
              Voir l’annonce complète
            </button>
            <a
              v-if="postLink && offer.status !== 'applied'"
              :href="postLink.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link"
              :data-test="offer.employer_url ? 'employer' : 'apply'"
            ><span class="with-icon">{{ postLink.label }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
          </div>
          <ul
            v-if="facts.length"
            class="offer-facts"
            data-test="facts"
          >
            <li
              v-for="fact in facts"
              :key="fact.mark + fact.text"
              :class="[fact.mark, { scam: fact.scam }]"
            >
              <span
                class="fact-mark"
                :data-mark="fact.mark"
              ><AppIcon :name="MARKS[fact.mark]" /></span>
              <span>
                {{ fact.text }}
                <q v-if="fact.excerpt">{{ fact.excerpt }}</q>
              </span>
            </li>
          </ul>
        </section>

        <!-- Entreprise et Contacts (O7, O9) : deux lignes repliables, hors de la maquette, gardées. -->
        <div :class="['detail-more-rows', 'disclosure-list', { 'detail-section': columns }]">
          <DisclosureRow
            title="Entreprise"
            :value="offer.company ?? ''"
            class="detail-disclosure"
            data-test="company-section"
          >
            <template
              v-if="companyItems.length"
              #actions
            >
              <MoreMenu
                class="section-more"
                :items="companyItems"
                label="Plus d’actions sur l’entreprise"
                test-id="company-more"
              />
            </template>
            <dl class="detail-rows">
              <div data-test="address">
                <dt>Adresse</dt>
                <dd v-if="editingAddress">
                  <form
                    class="address-form"
                    @submit.prevent="saveAddress"
                  >
                    <textarea
                      v-model="addressDraft"
                      rows="2"
                      placeholder="Rue et numéro&#10;NPA localité"
                      aria-label="Adresse de l’entreprise"
                      data-test="address-input"
                    />
                    <div>
                      <button
                        type="submit"
                        class="secondary small"
                        data-test="save-address"
                      >
                        Enregistrer
                      </button>
                      <button
                        type="button"
                        class="link"
                        @click="editingAddress = false"
                      >
                        Annuler
                      </button>
                    </div>
                  </form>
                </dd>
                <dd v-else-if="offer.company_address">
                  {{ offer.company_address.split("\n").join(", ") }}
                  <span class="hint">· {{ ADDRESS_SOURCE[offer.company_address_source ?? "manual"] }}</span>
                </dd>
                <dd v-else>
                  Adresse inconnue · <button
                    type="button"
                    class="link"
                    data-test="add-address"
                    @click="startAddress"
                  >
                    Ajouter
                  </button>
                </dd>
              </div>
            </dl>
            <p
              v-if="searching"
              class="hint"
              role="status"
            >
              Recherche dans le registre IDE…
            </p>
            <div
              v-if="registryMessage || proposals.length"
              class="registry-proposals"
              data-test="registry"
            >
              <p
                v-if="registryMessage"
                class="hint"
              >
                {{ registryMessage }}
              </p>
              <ul v-if="proposals.length">
                <li
                  v-for="proposal in proposals"
                  :key="proposal.uid"
                >
                  <span>
                    <strong>{{ proposal.name }}</strong><br>
                    <span class="muted">{{ proposal.address.split("\n").join(", ") }}</span>
                  </span>
                  <button
                    type="button"
                    class="secondary small"
                    data-test="choose-registry"
                    @click="chooseRegistry(proposal.uid)"
                  >
                    Choisir
                  </button>
                </li>
              </ul>
            </div>
            <p
              v-if="!employerKnown && (offer.employer_checked_at || offer.employer_status === 'agency' || employerBusy || employerMessage)"
              class="hint employer-line"
              data-test="employer-line"
            >
              <span
                v-if="employerBusy"
                role="status"
              >Recherche chez l’employeur en cours (jusqu’à 30 s)…</span>
              <span
                v-else-if="offer.employer_url && offer.employer_checked_at"
              >Trouvée chez l’employeur {{ EMPLOYER_SOURCES[offer.employer_url_source ?? "web"] }}, vérifiée
                {{ dateInSentence(offer.employer_checked_at) }}.</span>
              <span v-else-if="offer.employer_status === 'agency'">Annonce d’agence : employeur non indiqué.</span>
              <span v-else-if="offer.employer_status === 'not_found'">Pas trouvée chez l’employeur.</span>
              <span v-else-if="offer.employer_status === 'gone'">L’annonce a disparu du site de l’employeur.</span>
              <span
                v-if="employerMessage"
                role="status"
              >{{ employerMessage }}</span>
            </p>
          </DisclosureRow>
          <DisclosureRow
            v-if="offer.company"
            id="contacts"
            title="Contacts"
            :value="contactsCount ? String(contactsCount) : ''"
            :start-open="toContacts"
            class="detail-disclosure"
            data-test="contacts-section"
          >
            <ContactsPanel
              :key="offer.id"
              :offer-id="offer.id"
              @count="contactsCount = $event"
            />
          </DisclosureRow>
        </div>
      </template>
      <template #aside>
        <section
          v-if="columns"
          class="detail-section"
          data-test="offer-brief"
        >
          <h3>L’offre en bref</h3>
          <dl class="detail-list">
            <div
              v-for="row in brief"
              :key="row.test"
              :data-test="row.test"
            >
              <dt>{{ row.label }}</dt>
              <dd>{{ row.value }}</dd>
            </div>
          </dl>
          <a
            v-if="shareUrl"
            :href="shareUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="detail-link strong offer-brief-link"
            data-test="brief-link"
          >Voir l’annonce sur le site<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </section>
      </template>
    </component>
    <ProfileCompletionPanel
      :open="completing"
      title="Compléter mon profil"
      @close="completing = false"
      @saved="profileSaved"
    />
  </article>
</template>

<style>
/* À traiter sur ordinateur, deux colonnes (MODIFICATIONS du 8 novembre au soir, lot 13.1 ; HTML de
   CandidaturesOrdinateurB, onglet À traiter) : la note sans carte, l’anneau de 64 et le verdict, les critères en ligne
   (12 × 24), le bandeau pêche en bloc (18/20, boutons de 44 à 10 d’écart), « Le détail de la note » à 16 dessous ;
   « Le poste » en 15/23 ; « L’offre en bref » en <dl>, puis le lien vers l’annonce, 12 dessous. */
.offer-cols { --cols-match-gap: 16px; --cols-lines-gap: 12px 24px; --cols-band-pad: 18px 20px; --cols-band-gap: 14px; --cols-band-btn: 10px; --cols-text: 23px; --cols-48: 48px; --cols-2: 2px; }
.offer-cols .match-card.detail-section { display: block; padding: var(--cols-pad-top) 0 var(--cols-pad-bottom); background: none; border: 0; border-radius: 0; }
.offer-cols .match-card .match-head { gap: var(--space-4); padding-bottom: var(--space-4); }
.offer-cols .match-card .match-lines { display: flex; flex-wrap: wrap; gap: var(--cols-lines-gap); padding-bottom: var(--space-6); font-size: var(--font-label); }
.offer-cols .match-card .match-lines li { gap: var(--space-2); }
/* Lecture refusée (prompt du 10 novembre, PR 13 ; CandidaturesOrdinateurB) : un bloc pêche 16 px sous la carte, rayon 18,
   18,5 dedans ; titre 15 gras, phrase 14 ; « Coller le texte » tonal de 44 px et « Ouvrir l'annonce » en lien, 16 d'écart. */
.offer-cols .offer-text-refused { --cols-refused-pad: 18.5px; gap: var(--space-4); padding: var(--cols-refused-pad); background: var(--peach-soft); border: 1px solid var(--peach); border-radius: var(--radius-card); }
.offer-cols .offer-text-refused h4 { font-size: var(--font-label); }
.offer-cols .offer-text-refused p { font-size: var(--font-small); color: var(--text-tertiary); }
.offer-cols .offer-text-actions button { min-height: var(--target-min); font-size: var(--font-small); }
.offer-cols .offer-text-open { font-size: var(--font-small); }
/* Niveaux d'action D30 (§2.2) : « Préparer ma candidature » plein, « Écarter » à contour bleu. */
.offer-cols .detail-actions button.secondary { border: var(--action-line) solid var(--primary-graphic); background: var(--surface); color: var(--primary-text); }
.offer-cols .detail-actions .button-link.primary-link { background: var(--action); border-color: var(--action); color: var(--on-action); }
/* La note en carte d'information (MODIFICATIONS du 9 novembre, §2.1 ; HTML de CandidaturesOrdinateurB) : fond --bg sur le
   blanc du détail, trait de 1,5 px --card-line, rayon 18, 18,5 dedans ; anneau de 64, verdict 18 ; puis, 16 px dessous et
   après un trait --line, « Voir la compatibilité » 15/700 sur 56 px, calé sur le texte du verdict (18,5 + 64 + 16), chevron
   de 24. Le bandeau pêche vient 16 px sous la carte. La tête et la ligne forment la carte, sans enveloppe en plus. */
.offer-cols .match-card.detail-section { --cols-info-pad: 18.5px; --cols-info-text: 98.5px; --cols-56: 56px; --cols-24: 24px; display: flex; flex-direction: column; gap: 0; }
.offer-cols .match-card .match-head { order: 1; padding: var(--cols-info-pad) var(--cols-info-pad) var(--space-4); background: var(--bg); border: 1.5px solid var(--card-line); border-bottom: 0; border-radius: var(--radius-card) var(--radius-card) 0 0; }
.offer-cols .match-card .match-head:only-child, .offer-cols .match-card .match-head.match-head-alone { padding-bottom: var(--cols-info-pad); border-bottom: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.offer-cols .match-card .match-title { font-size: var(--font-title); }
/* « Compléter mon profil » sous la phrase, quand le profil manque : le style du lien « Ce qui part à l’IA ». */
.match-profile-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); padding: 0; border: 0; background: none; font: inherit; cursor: pointer; color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-bold); text-decoration: none; }
.match-profile-link:hover { text-decoration: underline; }
.match-profile-link .icon { width: 14px; height: 14px; }
.offer-cols .match-card .match-sub { font-size: var(--font-small); color: var(--text-secondary); }
.offer-cols .match-card .compat-open {
  order: 2; display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); width: 100%; max-width: none; min-height: var(--cols-56); margin: 0; padding: 0 var(--cols-info-pad) 0 var(--cols-info-text);
  background: var(--bg); border: 1.5px solid var(--card-line); border-top: 1px solid var(--line); border-radius: 0 0 var(--radius-card) var(--radius-card);
  color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer;
}
.offer-cols .match-card .compat-open:hover { text-decoration: underline; }
.offer-cols .match-card .compat-open > .icon { flex: none; width: var(--cols-24); height: var(--cols-24); }
.offer-cols .match-card > :not(.match-head, .compat-open) { order: 3; margin-top: var(--space-4); }
.offer-cols .match-card .match-detail { margin-top: var(--space-4); border-top: 0; }
.offer-cols .match-card .match-detail > .disclosure-row { min-height: var(--cols-48); padding: 0; }
.offer-cols .detail-post.detail-section { display: grid; gap: var(--space-3); padding-bottom: var(--space-2); }
.offer-cols .detail-post :is(.post-summary, .detail-snippet, .full-text) { font-size: var(--font-label); line-height: var(--cols-text); color: var(--text-tertiary); }
.offer-cols .detail-more-rows.detail-section { padding-bottom: var(--space-2); }
.offer-brief-link { margin-top: var(--space-3); }
/* La colonne principale est plus étroite : « Écrire à » et « Canal » des contacts passent l’un sous l’autre. */
.offer-cols .contact-writer-form { grid-template-columns: minmax(0, 1fr); }
/* Le détail d'une offre sur téléphone, version du 9 novembre (MODIFICATIONS §10.1, D35 ; HTML des maquettes Offre,
   OffreSombre, OffreCompatibilite) : fond --bg partout ; en-tête à 20 px ; deux cartes d’information (D35) blanches à
   trait de 1,5 px --card-line, rayon 18, 20 px dedans trait compris, 12 px au-dessus, à 20 px des bords : le poste
   (logo 56, 16 px, intitulé 22/28 800, étiquettes grises 16 px dessous) et la note (anneau 56, verdict 18/24, puis
   « Voir la compatibilité » sur la ligne du verdict, 56 px, trait au-dessus, chevron de 24 à 20 px du bord) ; puis
   « Le poste » en section sur le fond (20 px au-dessus, sans trait) ; barre du bas sur --bg avec un trait :
   « Écarter » à contour (48) et « Préparer ma candidature » plein (52). */
@media (max-width: 820px) {
  .offers-grid > .detail-column:not(.placeholder):has(.offer-blocks) { z-index: 39; background: var(--bg); }
  .offer-blocks {
    --ob-pad: 18.5px; --ob-margin: 20px; --ob-gap: 16px; --ob-56: 56px; --ob-48: 48px; --ob-52: 52px; --ob-28: 28px;
    --ob-24: 24px; --ob-23: 23px; --ob-21: 21px; --ob-12: 12px; --ob-13: 13px;
  }
  .offers-grid > .detail-column:not(.placeholder) .detail-panel.offer-blocks { gap: 0; padding-left: 0; padding-right: 0; background: var(--bg); }
  .offer-blocks .offer-subhead { margin: 0; padding: var(--ob-12) var(--ob-margin); background: var(--bg); }
  .offer-blocks .offer-subhead .icon-button { width: var(--target-min); height: var(--target-min); color: var(--primary-text); }
  .offer-blocks > .detail-offer, .offer-blocks .match-card {
    margin: var(--ob-12) var(--ob-margin) 0; padding: var(--ob-pad); background: var(--surface); border: 1.5px solid var(--card-line);
    border-radius: var(--radius-card); box-shadow: none;
  }
  .offer-blocks .detail-post, .offer-blocks .detail-more-rows {
    margin: 0 var(--ob-margin); padding: var(--space-6) 0; background: transparent; border: 0; border-top: 1px solid var(--line); border-radius: 0; box-shadow: none;
  }
  .offer-blocks .match-card + .detail-post { border-top: 0; padding-top: var(--space-5); }
  .offer-blocks > .detail-offer { display: grid; grid-template-columns: var(--ob-56) minmax(0, 1fr); column-gap: var(--ob-gap); row-gap: 0; align-items: center; }
  .offer-blocks > .detail-offer > :not(.detail-head, .detail-title) { grid-column: 1 / -1; }
  .offer-blocks .detail-head { display: contents; }
  .offer-blocks .detail-top-actions { display: none; }
  .offer-blocks .detail-head > .logo.large { width: var(--ob-56); height: var(--ob-56); border-radius: var(--radius-sm); }
  .offer-blocks .detail-title { gap: 0; }
  .offer-blocks .detail-title h2 { font-size: var(--font-section); line-height: var(--ob-28); font-weight: var(--weight-heavy); letter-spacing: 0; }
  .offer-blocks .detail-title .detail-sub { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--ob-21); color: var(--text-secondary); }
  .offer-blocks .offer-tags { gap: var(--space-2); margin-top: var(--ob-gap); }
  .offer-blocks .offer-tags li { padding: var(--space-1) var(--space-2); background: var(--surface-muted); border: 0; border-radius: var(--radius-sm); font-size: var(--ob-13); font-weight: var(--weight-semibold); color: var(--text-tertiary); }
  .offer-blocks .detail-offer .status-line, .offer-blocks .detail-offer .expired-notice { margin-top: var(--ob-gap); }
  .offer-blocks .match-card { display: block; }
  .offer-blocks .match-head { gap: var(--ob-gap); padding: 0; }
  .offer-blocks .match-head .score-ring.large { width: var(--ob-56); height: var(--ob-56); }
  .offer-blocks .match-title { font-size: var(--font-title); line-height: var(--ob-24); font-weight: var(--weight-bold); }
  .offer-blocks .match-sub { margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--ob-21); color: var(--text-secondary); }
  /* « Le détail de la note » (prompt du 10 novembre, PR 15) : toute la ligne est le bouton, le texte au même retrait que
     le contenu de la carte (18,5 px, pas le retrait du verdict ni les 98,5 px de l'ordinateur), le chevron à droite. */
  .offer-blocks .compat-open {
    display: flex; align-items: center; justify-content: space-between; gap: var(--ob-gap); width: calc(100% + 2 * var(--ob-pad)); max-width: none; min-height: var(--ob-56);
    margin: var(--ob-gap) calc(-1 * var(--ob-pad)) calc(-1 * var(--ob-pad)); padding: 0 var(--ob-pad); border: 0; border-top: 1px solid var(--line-soft);
    border-radius: 0 0 var(--radius-card) var(--radius-card); background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer;
  }
  .offer-blocks .compat-open > .icon { flex: none; width: var(--ob-24); height: var(--ob-24); }
  /* Lecture de l'annonce complète (prompt du 10 novembre, PR 13 ; OffreProvisoire) : tout reste DANS la carte, au
     retrait du contenu, jamais en pleine largeur. La ligne « jobA1 lit l'annonce complète… » 16 px sous le verdict ; le
     refus séparé par un filet, 16 px dessus (14 dans la maquette, sur la grille de 4), 12 px entre ses lignes ; puis
     « Le détail de la note » sans vide. */
  .offer-blocks .match-card .offer-reading, .offer-blocks .match-card .redone { margin-top: var(--ob-gap); }
  .offer-blocks .match-card .offer-text-refused { margin-top: var(--ob-gap); padding-top: var(--ob-gap); border-top: 1px solid var(--line-soft); }
  .offer-blocks .detail-post { display: block; }
  .offer-blocks .detail-post-head h3 { font-size: var(--font-title); line-height: var(--ob-24); }
  .offer-blocks .post-summary, .offer-blocks .detail-snippet { margin: var(--space-1) 0 0; font-size: var(--font-label); line-height: var(--ob-23); color: var(--text-tertiary); }
  .offer-blocks .post-links { margin-top: var(--space-2); }
  .offer-blocks .post-links .link { color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); }
  .offer-blocks .offer-bar { z-index: 40; gap: var(--space-2); padding: var(--ob-12) var(--ob-margin) calc(var(--space-4) + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line); }
  .offer-blocks .offer-bar-discard { flex: none; min-height: var(--ob-48); padding: 0 var(--ob-margin); font-size: var(--font-label); font-weight: var(--weight-bold); }
  .offer-blocks .offer-bar-main { flex: 1; min-height: var(--ob-52); background: var(--action); border-color: var(--action); color: var(--on-action); }
  /* §2.9 : chaque lien de la sous-page est une cible de 44 px de haut, et rien n'est poussé par une marge « auto »
     (hors de la grille de 4) : l’en-tête de section et le repliable répartissent la place eux-mêmes. */
  .offer-blocks :is(.link, .more-direct) { display: inline-flex; align-items: center; min-height: var(--target-min); }
  .offer-blocks .section-more, .offer-blocks .disclosure-chevron { margin-left: 0; }
  .offer-blocks .disclosure-row { justify-content: space-between; }
}
</style>
