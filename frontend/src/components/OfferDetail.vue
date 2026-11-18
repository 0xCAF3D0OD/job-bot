
<script setup lang="ts">
import { computed, onMounted, ref, watch, type FunctionalComponent } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Offer, type RegistryCandidate } from "../api/client";
import { MATCH_TITLE, pointParts } from "../compat";
import { dateInList, dateInSentence } from "../dates";
import { cityOnly, expiredText, frenchName, gapSkill, onDay, rateText, remoteText, scoreWord, sourceLabel } from "../format";
import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";
import AgencyNote from "./AgencyNote.vue";
import BottomSheet from "./BottomSheet.vue";
import CompanyLogo from "./CompanyLogo.vue";
import DisclosureRow from "./DisclosureRow.vue";
import ContactsPanel from "./ContactsPanel.vue";
import DetailTwoColumns from "./DetailTwoColumns.vue";
import CopyButton from "./CopyButton.vue";
import CopyField from "./CopyField.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import OfferActionSheet from "./OfferActionSheet.vue";
import OfferCompatSheet, { type CompatPoint, type TipAction } from "./OfferCompatSheet.vue";
import OfferTextNotice from "./OfferTextNotice.vue";
import ScoreRing from "./ScoreRing.vue";
import GapFill from "./GapFill.vue";
import ScoreCorrection from "./ScoreCorrection.vue";
import StatusPill from "./StatusPill.vue";
import { useAssistant } from "../composables/useAssistant";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { useProfileEmpty } from "../composables/useProfileEmpty";
import { offerUndo } from "../composables/useUndo";
import { displayTitle } from "../offerTitle";
import type { CompletionSection } from "./ProfileCompletionForm.vue";
import ProfileCompletionPanel from "./ProfileCompletionPanel.vue";
import { languageLabel } from "./ProfileCompletionForm.vue";

import BusyButton from "./BusyButton.vue";
import HoverNote from "./HoverNote.vue";
import IconButton from "./IconButton.vue";
// `outsideNote` (Kevin, 16.11) : « Nouvelle note : 38. Elle sort de ton filtre « … ». », sous la note, quand l'offre
// renotée reste dans la liste hors de ses filtres.
const props = defineProps<{ offer: Offer; chunkTitles?: Record<number, string>; outsideNote?: string | null }>();

// Les contacts dans le panneau latéral (docs/32 §2.2) ; l'entreprise a sa section (docs/45).
const contactsCount = ref(0);
// « Trouver un contact chez … » de Postuler (C7) : la fiche s'ouvre sur ses Contacts, dépliés.
const toContacts = useRoute()?.hash === "#contacts";
const router = useRouter();
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
  changed: [rescored?: true];
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

// « Ce n'est pas une agence » (section 35 du 16.11) et « C'est une agence de placement » (menu de la fiche, Kevin
// 16.11 23 h 33) : gardés pour cette entreprise, dans ce compte, la dernière correction l'emporte ; la liste relue, la
// pastille et la ligne suivent. « Correction enregistrée · Annuler » avec le trait, comme « Offre écartée » : la
// correction est déjà partie, « Annuler » la retire.
const agencyBusy = ref(false);
async function correctAgency(agency: boolean): Promise<void> {
  agencyBusy.value = true;
  try {
    const url = agency ? "/api/offers/{offer_id}/agency" : "/api/offers/{offer_id}/not-agency";
    const path = { offer_id: props.offer.id };
    const { data } = await api.POST(url, { params: { path } });
    if (!data) return;
    emit("changed");
    void offerUndo({
      message: "Correction enregistrée.",
      commit: () => true,
      restore: async () => {
        await api.DELETE(url, { params: { path } });
        emit("changed");
      },
    });
  } finally {
    agencyBusy.value = false;
  }
}
// Le choix du menu, seulement quand la ligne Agence n'est pas là et que l'offre nomme une entreprise.
const markAgency = computed<MoreMenuItem[]>(() => {
  const o = props.offer;
  return o.agency || o.spontaneous || !o.company?.trim()
    ? []
    : [{ label: "C’est une agence de placement", test: "mark-agency", icon: "flag", run: () => void correctAgency(true) }];
});

// Le seul lien vers l'annonce de toute la fiche, hors menu « … » (prompt récapitulatif du 11 novembre, PR 25) :
// « Voir l'annonce sur [source] », dans « Le poste » sur téléphone et dans « L'offre en bref » sur ordinateur.
// Chez l'employeur si l'annonce y est, sinon sur le site d'où elle vient : la même adresse que « Ouvrir l'annonce sur
// le site » du menu « … ». L'adresse pour postuler (`apply_url`) n'est pas l'annonce : elle reste dans Préparer.
const postLink = computed(() => {
  const o = props.offer;
  const view = (url: string, where: string) => ({ url, label: `Voir l’annonce sur ${where}` });
  if (o.employer_url) return view(o.employer_url, "le site de l’employeur");
  // Le lien d'un texte collé à l'ajout n'est pas une page (manual_offers.NO_LINK).
  const link = o.links.find((l) => l.url && !l.url.startsWith("https://annonce-collee.invalid/"));
  if (!link) return null;
  return view(link.url, link.source === "manual" ? "le site" : (sourceLabel[link.source] ?? link.source));
});

// Registre IDE (docs/12 §2.2) : propositions quand le nom ne suffit pas à trancher.
const searching = ref(false);
const proposals = ref<RegistryCandidate[]>([]);
const registryMessage = ref("");
// Planche OffreAdresseNonTrouvee (18.11) : « Pas trouvée au registre » après une recherche faite ici sans résultat (le
// serveur ne garde pas les recherches vaines) ; la pastille « Trouvée au registre du commerce » vient de la source.
const notFound = ref(false);

// « Adresse trouvée » seulement si l'adresse affichée change (audit du 17.11, K6) : le serveur peut connaître
// l'entreprise sans que l'adresse de l'offre bouge. La recherche reste « en cours » jusqu'à la fiche relue, puis
// la phrase dit ce que la fiche montre. Sans relecture au bout de 10 s, on n'affirme rien.
const RELOAD_WAIT_MS = 10_000;
let awaited: { before: string | null; found: string; timer: ReturnType<typeof setTimeout> } | null = null;
function awaitReload(found: string): void {
  if (awaited) clearTimeout(awaited.timer);
  awaited = {
    before: props.offer.company_address ?? null,
    found,
    timer: setTimeout(() => {
      awaited = null;
      searching.value = false;
    }, RELOAD_WAIT_MS),
  };
  emit("changed");
}
watch(
  () => props.offer,
  (offer) => {
    if (!awaited) return;
    clearTimeout(awaited.timer);
    const changed = (offer.company_address ?? null) !== awaited.before;
    // Trouvée au registre : la pastille le dit (planche OffreAdresseTrouvee) ; trouvée sur Internet : la phrase.
    registryMessage.value = changed ? awaited.found : offer.company_address ? "Aucune nouvelle adresse trouvée." : "";
    notFound.value = !changed && !offer.company_address;
    awaited = null;
    searching.value = false;
  },
);

async function searchRegistry(): Promise<void> {
  searching.value = true;
  registryMessage.value = "";
  notFound.value = false;
  proposals.value = [];
  let waiting = false;
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/address-candidates", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      registryMessage.value = "Registre IDE injoignable, réessaie plus tard.";
    } else if (data.chosen_uid && props.offer.company_address_source !== "registry") {
      waiting = true;
      awaitReload("");
    } else if (data.web_address) {
      proposals.value = data.candidates;
      waiting = true;
      awaitReload("Adresse trouvée sur Internet : vérifie la source.");
    } else {
      proposals.value = data.candidates;
      const web = data.web_unavailable
        ? ` Recherche sur Internet impossible : ${data.web_unavailable}.`
        : " Rien de fiable sur Internet non plus.";
      if (data.candidates.length) registryMessage.value = `Pas de correspondance sûre : choisis parmi le registre, ou saisis l’adresse.${web}`;
      else {
        notFound.value = true;
        registryMessage.value = data.web_unavailable ? `Recherche sur Internet impossible : ${data.web_unavailable}.` : "";
      }
    }
  } catch {
    registryMessage.value = "API injoignable.";
  } finally {
    if (!waiting) searching.value = false;
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
  later: "Gardée",
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
    // Offre provisoire sur téléphone (§17 du 15 novembre) : pas de pastille « Contrat non précisé ».
    ...(o.employment_type || !(sub.value && provisional.value) ? [{ test: "contract", text: o.employment_type || "Contrat non précisé" }] : []),
    ...(remote ? [{ test: "remote", text: remote }] : []),
    ...(received ? [{ test: "received", text: /^\d/.test(received) ? `Reçue ${dateInSentence(o.first_seen_at)}` : `Reçue ${received}` }] : []),
  ];
});
// La date de réception sur la ligne de l'entreprise (téléphone) : « reçue hier », « reçue le 12 nov. ».
const receivedLine = computed(() => {
  const at = props.offer.first_seen_at;
  if (!at) return "";
  const day = dateInList(at);
  return /^\d/.test(day) ? `reçue le ${day}` : `reçue ${day}`;
});
// La grille de la planche Offre : trois cases toujours là ; une valeur inconnue le dit.
const gridCells = computed(() => {
  const o = props.offer;
  const remote =
    o.remote === "hybrid" ? (o.remote_days ? `${o.remote_days} j/sem.` : "Partiel") : o.remote === "full" ? "100 %" : "Non précisé";
  return [
    { test: "rate", label: "Taux", value: rateText(o.rate_min ?? null, o.rate_max ?? null) || "Non précisé" },
    { test: "contract", label: "Contrat", value: o.employment_type || "Non précisé" },
    { test: "remote", label: "Télétravail", value: remote },
  ];
});
const facts = computed<Fact[]>(() => {
  const o = props.offer;
  const list: Fact[] = [];
  if (o.remote_from_switzerland === false) list.push({ mark: "check", text: "Télétravail pas ouvert depuis la Suisse" });
  for (const doubt of o.doubts ?? []) {
    // Pour une agence, la ligne « Agence de placement » le dit déjà (Kevin, 16.11).
    if (o.agency && doubt.kind === "hidden_employer") continue;
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
const matchTone = computed(() => matchWord.value?.tone ?? (aside.value ? "aside" : "none"));
// A2 (Kevin, 16.11) : une note impossible (après trois échecs, ou sans texte) le dit, avec sa cause ; une offre
// écartée sans note n'affiche jamais « Pas encore notée ». Un échec pas encore final est une attente : la tâche des
// 10 minutes refait la note.
const finalCause = computed(() => (scored.value ? null : (props.offer.score_final ?? null)));
const retryable = computed(() => finalCause.value === "reponse_vide" || finalCause.value === "erreur");
const setAside = computed(
  () => !scored.value && !props.offer.added_by_you && (props.offer.status === "filtered_out" || props.offer.status === "ignored"),
);
// §30 du 16.11 : écartée sans note, « Écartée le 12 nov. » (date de la mise à l'écart, décision de Kevin du 16.11) ; une
// offre écartée avant la date enregistrée garde « Écartée » seul. « Remettre dans le tri » la remet dans les offres à
// traiter (sa note part alors, dans le plafond du jour) ; « Écarter » disparaît.
const aside = computed(() => setAside.value && !finalCause.value);
const discarded = computed(() => props.offer.status === "ignored" || props.offer.status === "filtered_out");
const matchTitle = computed(() => {
  if (matchWord.value) return MATCH_TITLE[matchWord.value.tone]!;
  if (finalCause.value) return "Note impossible";
  if (!setAside.value) return "Pas encore notée";
  const at = props.offer.set_aside_at;
  if (!at) return "Écartée";
  // « 12 nov. », l'année seulement si ce n'est pas l'année en cours (décision du 16.11) ; ici plutôt que dans dates.ts,
  // pour ne pas alourdir le socle commun à toutes les pages.
  const year = new Date(at).getFullYear() === new Date().getFullYear() ? undefined : "numeric";
  return `Écartée le ${new Date(at).toLocaleDateString("fr-CH", { day: "numeric", month: "short", year, timeZone: "Europe/Zurich" })}`;
});
// Sans profil, la note n'arrive jamais : la fiche le dit et envoie vers Profil › Expériences (test du 10 novembre).
const { empty: profileEmpty, refresh: refreshProfile } = useProfileEmpty();
onMounted(() => void refreshProfile());
const needsProfile = computed(() => !scored.value && profileEmpty.value);
// « Compléter mon profil » (PR 17, point 4) : le formulaire des premiers pas en panneau ; à l'enregistrement, la fiche
// reste ouverte et l'offre est notée (le serveur lance la notation au premier élément du profil).
const completing = ref(false);
// La partie du profil que le panneau ouvre : tout (« Compléter mon profil »), ou la seule qu'une action de
// « Pour faire monter la note » vise (PR 18).
const completionSections = ref<CompletionSection[]>(["experiences", "languages", "identity"]);
function raiseNote(action: TipAction): void {
  compatOpen.value = false;
  if (action === "skills") void router.push({ path: "/profil", query: { onglet: "parcours" } });
  else if (action === "criteria") void router.push({ path: "/profil" });
  else {
    completionSections.value = action === "experience" ? ["experiences"] : ["languages"];
    completing.value = true;
  }
}
// « Réessayer » : un essai tout de suite ; la fiche se recharge avec la note, ou avec l'attente si l'essai échoue.
const retrying = ref(false);
async function retryScore(): Promise<void> {
  if (retrying.value) return;
  retrying.value = true;
  try {
    await api.POST("/api/offers/{offer_id}/retry-score", { params: { path: { offer_id: props.offer.id } } });
    emit("changed");
  } finally {
    retrying.value = false;
  }
}
// « Pas encore notée » (planche OffreNonNotee du 18.11 ; Kevin, 17.11, Q2) : l'anneau pointillé des cartes, la phrase,
// puis « Noter maintenant » (environ 10 secondes, compte dans la formule ; le coût au survol pour l'exploitant seul).
// Jamais sur une offre écartée, sans profil ou dont la note a échoué (ces cas ont leur propre phrase).
const unrated = computed(() => !scored.value && !setAside.value && !finalCause.value && !needsProfile.value);
const { aiNote } = usePlan();
const scoringNow = ref(false);
const scoreNowError = ref("");
async function scoreNow(): Promise<void> {
  if (scoringNow.value) return;
  scoringNow.value = true;
  scoreNowError.value = "";
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/score-now", { params: { path: { offer_id: props.offer.id } } });
    if (data?.limit) scoreNowError.value = data.limit;
    else if (data?.score === null || data?.score === undefined) scoreNowError.value = "La note n’a pas pu être calculée : réessaie dans un moment.";
    emit("changed", true);
  } catch {
    scoreNowError.value = "API injoignable : réessaie dans un moment.";
  } finally {
    scoringNow.value = false;
  }
}
watch(
  () => props.offer.id,
  () => (scoreNowError.value = ""),
);
async function profileSaved(): Promise<void> {
  completing.value = false;
  await refreshProfile();
}
const matchSub = computed(() => {
  const o = props.offer;
  if (needsProfile.value) return "Il manque ton profil pour noter cette offre.";
  if (finalCause.value === "sans_texte") return "L’annonce est trop courte pour être notée.";
  if (finalCause.value) return "La note n’a pas pu être calculée.";
  if (!scored.value) return setAside.value ? "Pas de note : jobA1 ne note pas les offres écartées." : "jobA1 n’a pas encore comparé cette offre à ton profil.";
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
// « Le poste » (planche Offre du 18.11) : les compétences des points forts (« Kubernetes : … ») surlignées dans le
// résumé, et leur nombre dans la légende « n passages qui correspondent à ton profil ».
const strengthKeys = computed(() => [
  ...new Set((props.offer.strengths ?? []).map((p) => pointParts(p.text).key.trim()).filter((k) => k.length >= 2)),
]);
const markedParts = computed(() => {
  const keys = [...strengthKeys.value].sort((a, b) => b.length - a.length).map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  // Téléphone seulement : la planche de l'ordinateur (CandidaturesOrdinateurB) ne surligne rien.
  const found = keys.length && sub.value ? new RegExp(`(?<![\\p{L}\\p{N}])(${keys.join("|")})(?![\\p{L}\\p{N}])`, "giu") : null;
  return summaryParts.value.map((text) =>
    (found ? text.split(found) : [text]).map((part, i) => ({ text: part, mark: i % 2 === 1 })).filter((part) => part.text),
  );
});
const markCount = computed(() => markedParts.value.flat().filter((part) => part.mark).length);
// « Autres offres chez … » (planche Offre) : les offres de la même entreprise, lues avec la recherche de la liste ;
// trois au plus, le nombre total dans le titre. Rien si l'entreprise n'est pas connue ou n'a pas d'autre offre.
type Sibling = Pick<Offer, "id" | "title" | "company" | "location" | "rate_min" | "rate_max" | "score" | "status" | "first_seen_at">;
const SIBLINGS_MAX = 3;
const siblings = ref<Sibling[]>([]);
const companyKey = (name: string | null | undefined) => (name ?? "").trim().toLocaleLowerCase("fr");
async function loadSiblings() {
  const offer = props.offer;
  const key = companyKey(offer.company);
  siblings.value = [];
  // Téléphone seulement : la planche de l'ordinateur n'a pas cette carte.
  if (!key || !sub.value) return;
  const { data } = await api.GET("/api/offers", { params: { query: { q: offer.company!.trim(), view: "all", sort: "recent", limit: 50 } } });
  if (props.offer.id !== offer.id) return;
  siblings.value = (data?.items ?? []).filter((o) => o.id !== offer.id && companyKey(o.company) === key);
}
watch(() => [props.offer.id, props.offer.company, sub.value], () => void loadSiblings().catch(() => (siblings.value = [])), { immediate: true });
// « Lausanne · 100 % · 16 nov. » : la date suit la règle des dates de l'app (la planche écrit « il y a 5 j »).
function siblingLine(o: Sibling): string {
  return [cityOnly(o.location), rateText(o.rate_min, o.rate_max), o.first_seen_at ? dateInList(o.first_seen_at) : ""].filter(Boolean).join(" · ");
}
// Note provisoire : l'offre n'a que l'extrait de l'alerte (pas de texte complet). Ses manques sont alors
// génériques (« Exigences », « Données », « Conseil ») : la lecture de l'annonce complète les remplace.
// « Donner l’annonce pour la noter » (tête à plat, §11 du 15 novembre) déplie « Donner l’annonce » de la carte Candidature.
const textNotice = ref<InstanceType<typeof OfferTextNotice> | null>(null);
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
  const rows = [
    { label: "Lieu", value: o.location || "Non précisé", test: "brief-place" },
    { label: "Contrat", value: o.employment_type || "Non précisé", test: "brief-contract" },
    { label: "Taux d’activité", value: rateText(o.rate_min, o.rate_max) || "Non précisé", test: "brief-rate" },
    { label: "Reçue", value: receivedText.value, test: "brief-received" },
  ];
  // Un champ manquant se dit en gris, sans gras (§11 du 15 novembre).
  return rows.map((row) => ({ ...row, missing: row.value === "Non précisé" }));
});
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
  if (o.status === "later") items.push({ label: "Remettre dans Nouvelles", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
  else if (o.status !== "applied") items.push({ label: "Garder pour plus tard", test: "later", icon: "clock", run: () => emit("status", "later") });
  if (shareUrl.value) items.push({ label: "Copier le lien", test: "copy-link", icon: "link", run: () => void copyLink() });
  if (withBar.value && scored.value) {
    items.push({ label: "Signaler une erreur dans l’offre", test: "score-correction-menu", icon: "flag", separator: true, run: () => (correcting.value = true) });
  }
  // Après « Signaler une erreur dans l'offre », dans le même groupe ; seul, il ouvre le groupe par un trait.
  items.push(...markAgency.value.map((item) => ({ ...item, separator: !(withBar.value && scored.value) })));
  if (o.status !== "applied") {
    items.push({ label: "J’ai postulé", test: "mark-applied", icon: "check-circle", separator: true, run: () => emit("applied") });
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "clock-off", run: () => emit("expiry", true) },
    );
  }
  if (assistant.available.value) items.push({ label: "Demander à l’assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  items.unshift(...nearbyItem.value);
  return items;
});
const menuItems = computed<MoreMenuItem[]>(() => {
  if (wide.value) return desktopItems.value;
  const o = props.offer;
  const items: MoreMenuItem[] = [];
  items.push(...nearbyItem.value);
  if (o.status !== "applied") {
    items.push({ label: "J’ai déjà postulé", test: "mark-applied", icon: "check-circle", run: () => emit("applied") });
    // « Remettre dans Nouvelles » seulement pour une offre gardée ou écartée (Kevin, 17.11, planche ActionsOffre).
  if (o.status === "later" || o.status === "ignored") {
      items.push({ label: "Remettre dans Nouvelles", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
    } else {
      items.push({ label: "Plus tard", test: "later", icon: "clock", run: () => emit("status", "later") });
      // Un seul mot pour une action (étape 6, O8) : « Écarter », comme dans la feuille de la liste.
      items.push({ label: "Écarter", test: "ignore", icon: "x-circle", run: () => emit("status", "ignored") });
    }
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "clock-off", run: () => emit("expiry", true) },
    );
  }
  if (withBar.value && scored.value) {
    items.push({ label: "Cette note ne me correspond pas", test: "score-correction-menu", icon: "thumbs-down", run: () => (correcting.value = true) });
  }
  items.push(...markAgency.value);
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
  const items: MoreMenuItem[] = [...nearbyItem.value];
  // « Remettre dans Nouvelles » seulement pour une offre gardée ou écartée (Kevin, 17.11, planche ActionsOffre).
  if (o.status === "later" || o.status === "ignored") {
    items.push({ label: "Remettre dans Nouvelles", test: "back-to-review", icon: "refresh", run: () => emit("status", "to_review") });
  }
  if (o.status !== "applied") {
    items.push(
      o.expired_at
        ? { label: "Pas expirée", test: "not-expired", icon: "refresh", run: () => emit("expiry", false) }
        : { label: "Signaler comme expirée", test: "flag-expired", icon: "clock-off", run: () => emit("expiry", true) },
    );
  }
  if (scored.value) items.push({ label: "Cette note ne me correspond pas", test: "score-correction-menu", icon: "thumbs-down", run: () => (correcting.value = true) });
  items.push(...markAgency.value);
  // Lot 18 (maquette Offre) : l'en-tête n'a plus que retour, garder et « … » ; Partager passe dans la feuille.
  if (shareUrl.value) items.push({ label: "Partager", test: "share", icon: "share-nodes", run: () => void share() });
  if (assistant.available.value) items.push({ label: "Demander à l’assistant", test: "ask-assistant", icon: "ai", run: askAssistant });
  return items;
});
// Sauvegarder (O2) : l'état « Plus tard », qui existe déjà ; le signet est plein quand l'offre y est.
const saved = computed(() => props.offer.status === "later");
const canSave = computed(() => ["to_review", "later"].includes(props.offer.status));
function toggleSaved(): void {
  emit("status", saved.value ? "to_review" : "later");
  saidAloud.value = saved.value ? "Offre remise dans Nouvelles." : "Offre gardée pour plus tard.";
}
// Partager (O2) : le lien public de l'annonce (employeur, puis site source), jamais l'adresse jobA1, qui est
// privée. La feuille de partage du téléphone, sinon le lien copié.
const shareUrl = computed(() => props.offer.employer_url || props.offer.links.find((l) => l.url)?.url || null);
const saidAloud = ref("");
async function share(): Promise<void> {
  const url = shareUrl.value;
  if (!url) return;
  const title = [displayTitle(props.offer.title, props.offer), props.offer.company].filter(Boolean).join(" · ");
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
// Offre expirée (O7) : « Voir des offres proches », par le titre du poste, dans le « ⋯ » ; la barre dit « Écrire
// quand même » (planche OffreExpiree du 18.11, Kevin le 18.11 : le lien reste dans le menu).
const nearbyLink = computed(() => ({ path: "/candidatures/offres", query: { q: props.offer.title } }));
const expiredShown = computed(() => Boolean(props.offer.expired_at) && props.offer.status !== "applied");
const expiredWrite = computed(() => expiredShown.value && props.offer.status !== "preparing");
const nearbyItem = computed<MoreMenuItem[]>(() =>
  expiredWrite.value ? [{ label: "Voir des offres proches", test: "nearby", icon: "search", run: () => void router.push(nearbyLink.value) }] : [],
);
// La carte « Offre expirée » : le titre et la phrase de la planche quand la page de l'annonce a été vérifiée ; une
// expiration supposée (30 jours sans alerte) ou signalée par toi garde sa phrase, la planche ne la dessine pas.
const expiredCard = computed(() => {
  const o = props.offer;
  if (!o.expired_at) return null;
  const tail = "Tu peux encore écrire à l’entreprise.";
  if (o.expiry_source !== "page") return { title: "", text: `${expiredText(o)} ${tail}` };
  let host = "";
  try {
    host = new URL(o.links.find((l) => l.url)?.url ?? "").hostname.replace(/^www\./, "");
  } catch {
    host = "";
  }
  return { title: "L’annonce n’est plus en ligne", text: `Vérifiée ${onDay(o.expired_at)}${host ? ` sur ${host}` : ""}. ${tail}` };
});

// Partie « Entreprise » (docs/74) : l'adresse visible, les actions dans son « ⋯ ».
const canSearchEmployer = computed(
  () =>
    !employerKnown.value &&
    props.offer.employer_status !== "agency" &&
    !(props.offer.employer_url && props.offer.employer_checked_at),
);
// « Site de l'entreprise » (planche OffreAdresseTrouvee) : seulement une adresse http(s) ; le nom du site sans « www. ».
const website = computed(() => {
  const raw = props.offer.company_website;
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    return { href: url.href, host: url.hostname.replace(/^www\./, "") };
  } catch {
    return null;
  }
});
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
    notFound.value = false;
  },
);
</script>


<template>
  <article
    :class="['detail-panel', { 'offer-cards': columns, 'offer-blocks': sub, 'offer-provisional': sub && provisional }]"
    data-test="offer-detail"
  >
    <!-- La sous-page du téléphone (maquette Offre du 14 novembre, §6) : la flèche de retour à gauche ; Garder et « ⋯ » à
         droite (Partager est dans le « ⋯ »). -->
    <header
      v-if="sub"
      class="offer-subhead grille-top"
      data-test="offer-subhead"
    >
      <IconButton
        icon="arrow-left"
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

    <!-- Ordinateur dès 1 024 px (maquette du 15 novembre, §11 ; planche CandidaturesOrdinateurB, onglet Offres) : la
         tête à plat, sans carte ni logo (il est sur la carte de la liste) : l’intitulé et l’entreprise en entier, puis,
         sous un filet, la note sur une ligne avec « Voir la compatibilité ». Dessous, les cartes Candidature et L’offre
         en bref, puis l’entreprise et les contacts, gardés hors de la planche (règle 3). -->
    <template v-if="columns">
      <header
        class="oc-card oc-head"
        data-test="section-offer"
      >
        <div class="oc-head-row">
          <div class="oc-title-text">
            <h2
              tabindex="-1"
              data-test="offer-detail-title"
            >
              {{ displayTitle(offer.title, offer) }}
            </h2>
            <p
              class="oc-sub"
              data-test="detail-meta"
            >
              <span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée"
              }} · <span class="visually-hidden">Lieu : </span>{{ frenchName(offer.location) || "Lieu non précisé" }}
            </p>
          </div>
          <div class="oc-title-actions">
            <IconButton
              icon="close"
              label="Fermer le détail"
              class="detail-close"
              data-test="close-detail"
              @click="$emit('close')"
            />
            <MoreMenu
              v-if="menuItems.length"
              :items="menuItems"
              label="Plus d’actions sur l’offre"
            />
          </div>
        </div>
        <AgencyNote
          v-if="offer.agency"
          :kind="offer.agency"
          :company="offer.company"
          :duplicate="offer.agency_duplicate"
          :busy="agencyBusy"
          @correct="correctAgency(false)"
        />
        <div
          v-if="statusLabel && offer.status === 'applied'"
          class="oc-status"
        >
          <StatusPill
            :tone="pillTone"
            data-test="status-pill"
          >
            {{ statusLabel }}
          </StatusPill>
          <RouterLink
            to="/candidatures/suivi"
            class="link"
          >
            Voir le suivi
          </RouterLink>
        </div>
        <div
          class="oc-note-line"
          data-test="section-for-you"
        >
          <h3
            id="match-title"
            :class="['match-title', `is-${matchTone}`]"
            data-test="match-title"
          >
            {{ matchWord ? `${matchWord.word} · ${offer.score} sur 100` : matchTitle }}
          </h3>
          <span
            v-if="provisional"
            class="provisional-pill"
            data-test="provisional"
          >Provisoire</span>
          <button
            v-if="scored"
            type="button"
            class="oc-note-link"
            aria-haspopup="dialog"
            data-test="compat-open"
            @click="compatOpen = true"
          >
            Voir la compatibilité<AppIcon name="chevron" />
          </button>
          <template v-else-if="aside">
            <span
              class="aside-pill"
              data-test="aside-pill"
            >Pas de note</span>
            <button
              type="button"
              class="oc-note-link"
              data-test="back-to-triage"
              @click="emit('status', 'to_review')"
            >
              Remettre dans le tri<AppIcon name="chevron" />
            </button>
          </template>
          <button
            v-else-if="needsProfile"
            type="button"
            class="oc-note-link"
            aria-haspopup="dialog"
            data-test="match-profile-link"
            @click="completionSections = ['experiences', 'languages', 'identity']; completing = true"
          >
            Compléter mon profil<AppIcon name="chevron" />
          </button>
          <button
            v-else-if="retryable"
            type="button"
            class="oc-note-link"
            :disabled="retrying"
            data-test="retry-score"
            @click="retryScore"
          >
            Réessayer
          </button>
          <button
            v-else-if="partial"
            type="button"
            class="oc-note-link"
            aria-controls="offer-give-zone"
            data-test="give-to-score"
            @click="textNotice?.give()"
          >
            Donner l’annonce pour la noter<AppIcon name="chevron" />
          </button>
        </div>
        <p
          v-if="!scored && (needsProfile || finalCause || unrated)"
          class="oc-note-sub"
          data-test="match-sub"
        >
          {{ matchSub }}
        </p>
        <!-- Kevin, 18.11 : sur ordinateur, la carte « Pas encore notée » de la planche OffreNonNotee, dans le panneau. -->
        <div
          v-if="unrated"
          class="match-now oc-now"
          data-test="score-now-block"
        >
          <BusyButton
            class="match-now-button"
            :busy="scoringNow"
            busy-label="Notation en cours"
            data-test="score-now"
            @click="scoreNow"
          >
            <HoverNote :text="scoringNow ? '' : aiNote('Environ 0,01 $.')">
              Noter maintenant
            </HoverNote>
          </BusyButton>
          <span class="grey-pill">Environ 10 secondes · compte dans ta formule</span>
          <p
            v-if="scoreNowError"
            class="field-error"
            role="alert"
            data-test="score-now-error"
          >
            {{ scoreNowError }}
          </p>
        </div>
        <p
          v-if="outsideNote"
          class="oc-note-sub"
          role="status"
          aria-live="polite"
          data-test="outside-note"
        >
          {{ outsideNote }}
        </p>
        <p
          v-if="redone"
          class="redone oc-note-redone"
          role="status"
          data-test="redone"
        >
          <AppIcon name="done" />Note refaite sur l’annonce complète.
        </p>
      </header>
      <section
        v-if="expiredShown && expiredCard"
        :class="['expired-card', { 'oc-card': columns, 'detail-card': !columns, 'grille-info': sub }]"
        role="status"
        data-test="expired"
      >
        <span class="expired-pill">Offre expirée</span>
        <h3
          v-if="expiredCard.title"
          class="expired-title"
        >
          {{ expiredCard.title }}
        </h3>
        <p class="expired-text">
          {{ expiredCard.text }}
        </p>
      </section>

      <section
        class="oc-card oc-apply"
        aria-labelledby="oc-apply-title"
        data-test="section-ad"
      >
        <h3
          id="oc-apply-title"
          class="oc-card-title"
        >
          Candidature
        </h3>
        <div
          v-if="partial"
          class="oc-row oc-row-refused"
        >
          <OfferTextNotice
            ref="textNotice"
            :offer="offer"
            @changed="emit('changed', true)"
            @refresh="emit('changed')"
          />
        </div>
        <div class="oc-row oc-post">
          <div class="oc-post-head">
            <span
              id="post-title"
              class="oc-label"
            >{{ summaryParts.length && !partial ? "Le poste, résumé par jobA1" : partial ? "Le poste, extrait de l’alerte" : "Le poste" }}</span>
            <MoreMenu
              v-if="announceItems.length"
              class="section-more"
              :items="announceItems"
              label="Plus d’actions sur l’annonce"
              test-id="ad-more"
            />
          </div>
          <template v-if="summaryParts.length && !partial">
            <p
              v-for="part in summaryParts"
              :key="part"
              class="oc-text"
              data-test="summary"
            >
              {{ part }}
            </p>
          </template>
          <p
            v-else-if="!offer.description"
            class="oc-text"
          >
            {{ offer.snippet || "Pas d’extrait dans l’alerte : le texte complet est sur le site de l’employeur." }}
          </p>
          <div
            v-if="offer.description && (textOpen || !summaryParts.length)"
            ref="textEl"
            :class="['full-text', 'oc-text', { folded: !textOpen && offer.description.length > LONG_TEXT }]"
            :style="textOpen && textHeight ? { maxHeight: textHeight } : undefined"
            data-test="description"
          >
            {{ offer.description }}
          </div>
          <button
            v-if="offer.description && !textOpen && (summaryParts.length || offer.description.length > LONG_TEXT)"
            type="button"
            class="link read-more"
            data-test="read-more"
            @click="openText"
          >
            Voir l’annonce complète
          </button>
        </div>
        <ul
          v-if="facts.length"
          class="oc-row offer-facts"
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
        <div
          v-if="offer.status !== 'applied'"
          class="oc-actions"
          data-test="triage"
        >
          <RouterLink
            :to="prepareLink"
            class="button-link primary-link"
            data-test="prepare"
          >
            {{ expiredWrite ? "Écrire quand même" : offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
          </RouterLink>
          <button
            v-if="!discarded"
            type="button"
            class="secondary"
            data-test="offer-discard"
            @click="emit('status', 'ignored')"
          >
            Écarter
          </button>
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

      <section
        class="oc-card oc-brief"
        aria-labelledby="oc-brief-title"
        data-test="offer-brief"
      >
        <h3
          id="oc-brief-title"
          class="oc-card-title"
        >
          L’offre en bref
        </h3>
        <dl class="oc-brief-grid">
          <div
            v-for="row in brief"
            :key="row.test"
            :data-test="row.test"
          >
            <dt>{{ row.label }}</dt>
            <dd :class="{ 'oc-missing': row.missing }">
              {{ row.value }}
            </dd>
          </div>
        </dl>
        <a
          v-if="postLink"
          :href="postLink.url"
          target="_blank"
          rel="noopener noreferrer"
          class="oc-link-row"
          data-test="brief-link"
        ><b>{{ postLink.label }}</b><AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
      </section>
    </template>

    <!-- La tête (maquette Offre, étape 6b) : logo, poste, « Entreprise · Lieu », l'état, les étiquettes. Sur
         ordinateur, les deux actions dessous (O10) ; sur téléphone, elles sont dans la barre du bas. -->
    <section
      v-if="!columns"
      :class="['detail-offer', { 'grille-info': sub }]"
      data-test="section-offer"
    >
      <div class="detail-head">
        <CompanyLogo
          :offer="offer"
          large
          pair
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
          {{ displayTitle(offer.title, offer) }}
        </h2>
        <p
          class="detail-sub"
          data-test="detail-meta"
        >
          <span class="visually-hidden">Entreprise : </span>{{ offer.company ?? "Entreprise non indiquée"
          }} · <span class="visually-hidden">Lieu : </span>{{ (sub ? cityOnly(offer.location) : frenchName(offer.location)) || "Lieu non précisé"
          }}<template v-if="sub && receivedLine">
            · {{ receivedLine }}
          </template>
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
      <!-- Téléphone (planche Offre du 18.11) : Taux, Contrat et Télétravail en grille ; la date passe sur la ligne de
           l'entreprise. -->
      <dl
        v-if="sub"
        class="offer-grid"
        data-test="offer-grid"
      >
        <div
          v-for="cell in gridCells"
          :key="cell.test"
          :data-test="`grid-${cell.test}`"
        >
          <dt>{{ cell.label }}</dt>
          <dd>{{ cell.value }}</dd>
        </div>
      </dl>
      <ul
        v-else
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
      <AgencyNote
        v-if="offer.agency"
        :kind="offer.agency"
        :company="offer.company"
        :duplicate="offer.agency_duplicate"
        :busy="agencyBusy"
        @correct="correctAgency(false)"
      />
      <div
        v-if="offer.status !== 'applied' && !sub"
        class="detail-actions"
        data-test="triage"
      >
        <RouterLink
          :to="prepareLink"
          class="button-link primary-link"
          data-test="prepare"
        >
          {{ expiredWrite ? "Écrire quand même" : offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
        </RouterLink>
        <button
          v-if="!discarded"
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
      :verdict="columns ? (matchWord?.word ?? matchTitle) : matchTitle"
      :tone="matchTone"
      :subtitle="`${displayTitle(offer.title, offer)} · ${offer.company ?? 'Entreprise non indiquée'}`"
      :note="columns ? matchSub : undefined"
      :strengths="compatStrengths"
      :gaps="compatGaps"
      :how="compatHow"
      :parts="offer.score_parts ?? []"
      :tip="offer.score_tip ?? null"
      :scored-at="offer.scored_at ?? null"
      @close="compatOpen = false"
      @tip="raiseNote"
    />
    <!-- La barre du bas de la sous-page (O8) : « Écarter » (avec « Annuler » 6 s) et l'action principale ;
         une offre expirée mène aux offres proches (O7). -->
    <div
      v-if="withBar"
      class="offer-bar grille-bar"
      data-test="offer-bar"
    >
      <button
        v-if="!discarded"
        type="button"
        class="secondary action-2 offer-bar-discard"
        data-test="offer-discard"
        @click="emit('status', 'ignored')"
      >
        Écarter
      </button>
      <RouterLink
        :to="prepareLink"
        class="button-link primary-link offer-bar-main"
        data-test="prepare"
      >
        {{ expiredWrite ? "Écrire quand même" : offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
      </RouterLink>
    </div>

    <!-- La correspondance (O3, O4) : l'anneau sans chiffre (D3), le mot en titre, « 92 sur 100 » dessous
         (docs/121) ; une ligne par point fort (coche) et par manque (gris chaud, D5 : un manque n’est pas une
         action) ; le détail de la note replié. -->
    <component
      :is="layout"
      v-if="!columns"
      v-bind="layoutProps"
    >
      <template #main>
        <section
          v-if="expiredShown && expiredCard"
          :class="['expired-card', { 'oc-card': columns, 'detail-card': !columns, 'grille-info': sub }]"
          role="status"
          data-test="expired"
        >
          <span class="expired-pill">Offre expirée</span>
          <h3
            v-if="expiredCard.title"
            class="expired-title"
          >
            {{ expiredCard.title }}
          </h3>
          <p class="expired-text">
            {{ expiredCard.text }}
          </p>
        </section>
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
            <svg
              v-else-if="unrated"
              class="match-unrated"
              viewBox="0 0 100 100"
              aria-hidden="true"
              focusable="false"
              data-test="match-unrated"
            ><circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke-width="9"
              stroke-dasharray="12 9.99"
            /><path
              d="M38 50H62"
              stroke-width="9"
              stroke-linecap="round"
            /></svg>
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
                v-if="matchSub"
                class="match-sub"
                data-test="match-sub"
              >
                {{ matchSub }}
              </p>
              <p
                v-if="outsideNote"
                class="match-sub"
                role="status"
                aria-live="polite"
                data-test="outside-note"
              >
                {{ outsideNote }}
              </p>
              <button
                v-if="retryable"
                type="button"
                class="match-profile-link"
                :disabled="retrying"
                data-test="retry-score"
                @click="retryScore"
              >
                Réessayer
              </button>
              <button
                v-if="needsProfile"
                type="button"
                class="match-profile-link"
                aria-haspopup="dialog"
                data-test="match-profile-link"
                @click="completionSections = ['experiences', 'languages', 'identity']; completing = true"
              >
                Compléter mon profil<AppIcon name="chevron" />
              </button>
            </div>
          </div>
          <div
            v-if="unrated"
            class="match-now"
            data-test="score-now-block"
          >
            <BusyButton
              class="match-now-button"
              :busy="scoringNow"
              busy-label="Notation en cours"
              data-test="score-now"
              @click="scoreNow"
            >
              <HoverNote :text="scoringNow ? '' : aiNote('Environ 0,01 $.')">
                Noter maintenant
              </HoverNote>
            </BusyButton>
            <span class="grey-pill">Environ 10 secondes · compte dans ta formule</span>
            <p
              v-if="scoreNowError"
              class="field-error"
              role="alert"
              data-test="score-now-error"
            >
              {{ scoreNowError }}
            </p>
          </div>
          <ul
            v-if="matchLines.length && (sub ? provisional : !columns)"
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
            @changed="emit('changed', true)"
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
            v-if="(sub || columns) && scored || aside"
            type="button"
            class="compat-open"
            :aria-haspopup="scored ? 'dialog' : undefined"
            :data-test="scored ? 'compat-open' : 'back-to-triage'"
            @click="scored ? (compatOpen = true) : emit('status', 'to_review')"
          >
            <!-- « Voir la compatibilité » sur téléphone comme sur ordinateur (décision de Kevin du 15.11) ; sur téléphone,
                 aligné sur le contenu de la carte, chevron à droite, que la note soit provisoire ou non. Offre écartée
                 sans note (§30 du 16.11) : « Remettre dans le tri », même style. -->
            {{ scored ? "Voir la compatibilité" : "Remettre dans le tri" }}
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
            <!-- Téléphone (planche Offre du 18.11) : pas de « Résumé par jobA1 » ; les compétences des points forts
                 surlignées, et leur légende. -->
            <p
              v-if="!sub"
              class="post-by"
              data-test="summary-by"
            >
              Résumé par jobA1
            </p>
            <p
              v-for="(parts, index) in markedParts"
              :key="index"
              class="post-summary"
              data-test="summary"
            >
              <template
                v-for="(part, j) in parts"
                :key="j"
              >
                <mark v-if="part.mark">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
              </template>
            </p>
            <p
              v-if="markCount"
              class="post-legend"
              data-test="summary-legend"
            >
              <span aria-hidden="true" />{{ markCount }} {{ markCount > 1 ? "passages qui correspondent" : "passage qui correspond" }} à ton profil
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
              v-if="postLink && !columns && offer.status !== 'applied'"
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
        <!-- « Autres offres chez … » (planche Offre du 18.11) : trois au plus, la note ou « Envoyée », vers leur fiche. -->
        <section
          v-if="siblings.length"
          :class="['company-offers', { 'detail-section': columns }]"
          aria-labelledby="company-offers-title"
          data-test="company-offers"
        >
          <h3 id="company-offers-title">
            Autres offres chez {{ offer.company }} · {{ siblings.length }}
          </h3>
          <RouterLink
            v-for="other in siblings.slice(0, SIBLINGS_MAX)"
            :key="other.id"
            :to="`/candidatures/offres/${other.id}`"
            class="company-offer"
            data-test="company-offer"
          >
            <span class="company-offer-text">
              <b>{{ displayTitle(other.title, other) }}</b>
              <span>{{ siblingLine(other) }}</span>
            </span>
            <span
              v-if="other.status === 'applied'"
              class="company-offer-pill"
            >Envoyée</span>
            <span
              v-else-if="other.score != null"
              :class="['company-offer-pill', scoreWord(other.score).tone]"
            ><span class="visually-hidden">Note </span>{{ other.score }}</span>
            <AppIcon name="chevron" />
          </RouterLink>
        </section>
      </template>
    </component>
    <!-- Entreprise et Contacts (O7, O9) : deux lignes repliables, hors de la maquette, gardées. -->
    <div :class="['detail-more-rows', { 'oc-card oc-company': columns }]">
      <!-- Récapitulatif du 11 novembre, PR 33 point 4 (cible_entreprise) : plus de bandeau bleu ni de ligne
           repliable ; le libellé gris au-dessus, la valeur en gras dessous, le bouton copier à droite. -->
      <section
        v-if="!(sub && provisional) || offer.company || offer.company_address"
        class="offer-company"
        aria-labelledby="offer-company-title"
        data-test="company-section"
      >
        <div class="offer-company-head">
          <h3
            id="offer-company-title"
            class="offer-company-cap"
          >
            L’entreprise
          </h3>
          <MoreMenu
            v-if="companyItems.length"
            class="section-more"
            :items="companyItems"
            label="Plus d’actions sur l’entreprise"
            test-id="company-more"
          />
        </div>
        <!-- Planche OffreAdresseTrouvee (18.11) : le titre « L'entreprise » au-dessus d'une carte (Nom, Adresse,
             « Modifier l'adresse »), puis la carte « Site de l'entreprise ». -->
        <div class="company-card">
          <CopyField
            label="Nom"
            :value="offer.company ?? ''"
          />
          <div
            class="block-field"
            data-test="address"
          >
            <div class="block-field-text">
              <div class="block-field-label">
                Adresse
              </div>
              <form
                v-if="editingAddress"
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
              <p
                v-else-if="searching"
                class="block-field-value offer-busy address-busy"
                role="status"
                data-test="registry-busy"
              >
                <span
                  class="offer-busy-ring"
                  aria-hidden="true"
                />Recherche de l’adresse…
              </p>
              <template v-else-if="offer.company_address">
                <div class="block-field-value address-lines">
                  {{ offer.company_address }}
                </div>
                <span
                  v-if="offer.company_address_source === 'registry'"
                  class="grey-pill address-pill"
                  data-test="address-registry"
                >Trouvée au registre du commerce</span>
                <div
                  v-else
                  class="hint"
                >
                  {{ ADDRESS_SOURCE[offer.company_address_source ?? "manual"] }}
                </div>
              </template>
              <template v-else>
                <div class="block-field-value block-field-none">
                  Non renseignée
                </div>
                <span
                  v-if="notFound"
                  class="grey-pill address-pill"
                  data-test="address-not-found"
                >Pas trouvée au registre</span>
              </template>
            </div>
            <CopyButton
              v-if="offer.company_address && !editingAddress && !searching"
              :value="offer.company_address.split('\n').join(', ')"
              label="Copier : adresse"
              test-id="address-copy"
            />
          </div>
          <!-- « Modifier l'adresse » ou « Ajouter l'adresse » : une ligne avec chevron sous l'adresse (planches
             OffreAdresseTrouvee et OffreAdresseNonTrouvee du 18.11). -->
          <button
            v-if="!editingAddress && !searching"
            type="button"
            class="address-row"
            data-test="add-address"
            @click="startAddress"
          >
            {{ offer.company_address ? "Modifier l’adresse" : "Ajouter l’adresse" }}<AppIcon name="chevron" />
          </button>
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
              class="offer-busy"
              role="status"
            ><span
              class="offer-busy-ring"
              aria-hidden="true"
            />Recherche chez l’employeur en cours (jusqu’à 30 s)…</span>
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
        </div>
        <a
          v-if="website"
          class="company-card company-site"
          :href="website.href"
          target="_blank"
          rel="noopener noreferrer"
          data-test="company-website"
        >
          <span>
            <b>Site de l’entreprise</b>
            <span class="company-site-host">{{ website.host }}</span>
          </span>
          <AppIcon name="chevron" />
        </a>
      </section>
      <div
        v-if="offer.company"
        class="disclosure-list offer-company-contacts"
      >
        <DisclosureRow
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
    </div>
    <ProfileCompletionPanel
      :open="completing"
      title="Compléter mon profil"
      :sections="completionSections"
      @close="completing = false"
      @saved="profileSaved"
    />
  </article>
</template>

<style>
/* « Compléter mon profil » sous la phrase, quand le profil manque : le style du lien « Ce qui part à l’IA ». */
.match-profile-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); padding: 0; border: 0; background: none; font: inherit; cursor: pointer; color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-bold); text-decoration: none; }
.match-profile-link:hover { text-decoration: underline; }
.match-profile-link .icon { width: 14px; height: 14px; }
/* Ordinateur, maquette du 15 novembre (§18 ; HTML de CandidaturesOrdinateurB, onglet Offres) : la tête en carte, 24 px
   sous le haut de la zone (marges 22 / 28 / 8 / 24), intitulé 24/30 800, entreprise 15 grise à 4 px ; la note sur une ligne,
   sous un filet de 1 px à 12 px, « Voir la compatibilité » à droite. Puis les cartes blanches, trait de 1 px --line,
   coins de 24 : titre 18/24, lignes à 12 / 24 séparées d'un filet, étiquette 13 px grise au-dessus d'une valeur 15/700 ;
   pied de pilules de 52 px à 12 px d'écart (§7), le secondaire en trait gris. */
.offer-cards {
  --oc-x: 24px; --oc-title-x: 28px; --oc-head-top: 18.5px; --oc-h2: 24px; --oc-h2-lh: 30px; --oc-card-title: 18px; --oc-card-lh: 24px;
  --oc-label: 13px; --oc-label-lh: 16px; --oc-text-lh: 22px; --oc-pill: 52px; --oc-pill-r: 22px; --oc-r: 24px; --oc-2: 2px; --oc-6: 6px;
  --oc-10: 10px; --oc-14: 14px; --oc-20: 20px; --oc-22: 22px; --oc-row-min: 64px; --oc-chip-r: 6px;
}
.oc-card { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: var(--oc-r); color: var(--text); }
.oc-head { margin-top: var(--space-6); padding: var(--oc-22) var(--oc-title-x) var(--space-2) var(--space-6); }
.oc-head-row { display: flex; align-items: flex-start; gap: var(--space-4); }
.oc-title-text { flex: 1; min-width: 0; }
.oc-title-text h2 { margin: 0; font-size: var(--oc-h2); line-height: var(--oc-h2-lh); font-weight: var(--weight-heavy); letter-spacing: 0; }
.oc-sub { margin: var(--space-1) 0 0; font-size: var(--font-label); line-height: normal; color: var(--text-secondary); }
.oc-title-actions { flex: none; display: flex; align-items: center; }
.oc-head > .oc-status { margin: var(--space-3) 0 0; }
.oc-status { display: flex; align-items: center; gap: var(--space-3); }
.oc-note-line { display: flex; align-items: center; gap: var(--oc-10); margin-top: var(--space-3); padding-top: var(--space-1); border-top: 1px solid var(--line); }
.oc-note-line .match-title { margin: 0; font-size: var(--font-label); font-weight: var(--weight-bold); }
.oc-note-line .match-title.is-none { color: var(--text-secondary); }
/* §30 : la pastille neutre « Pas de note » d'une offre écartée, celle des cartes de la liste (ListCard). */
.aside-pill { background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-lead); font-size: var(--font-caption); }
.oc-note-line > span { flex: none; padding: var(--oc-2) var(--space-2); border-radius: var(--oc-chip-r); font-weight: var(--weight-semibold); }
.oc-note-sub { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.oc-note-link { flex: none; display: inline-flex; align-items: center; gap: var(--oc-2); min-height: var(--target-min); margin-left: auto; padding: 0; border: 0; background: none; font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer; }
.oc-note-link:hover { text-decoration: underline; }
.oc-note-link .icon { width: 18px; height: 18px; }
/* Audit du 17.11, K8 : le bandeau « Note refaite » finit à 24 px du bord de la carte, comme sur les côtés (8 de la carte
   + 16 ici), au lieu de 8. */
/* « Pas encore notée » (planche OffreNonNotee du 18.11) : l'anneau pointillé des cartes (60 px), puis sous un trait,
   « Noter maintenant » tonal pleine largeur (52 px) et la pastille grise centrée, 10 px dessous. */
.match-unrated { flex: none; width: 60px; height: 60px; }
.match-unrated circle { stroke: var(--linked-line); }
.match-unrated path { stroke: var(--unrated-dash); }
.match-now { --now-gap: 10px; --now-top: 14px; display: flex; flex-direction: column; align-items: center; gap: var(--now-gap); margin: var(--space-4) calc(-1 * var(--space-4)) 0; padding: var(--now-top) var(--space-4) 0; border-top: 1px solid var(--line-soft); }
.match-now-button { width: 100%; height: 52px; min-height: 52px; border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-body); font-weight: var(--weight-bold); }
.grey-pill { --pill-pad: 5px; --pill-radius: 15px; --pill-size: 13px; display: inline-flex; align-items: center; min-height: 30px; padding: var(--pill-pad) var(--space-3); border-radius: var(--pill-radius); background: var(--line-soft); color: var(--text-lead); font-size: var(--pill-size); font-weight: var(--weight-semibold); text-align: center; }
.oc-now { margin: var(--space-4) 0 0; padding-left: 0; padding-right: 0; }
/* « Offre expirée » (planche OffreExpiree du 18.11) : la pastille orange, le titre 17 px gras 10 px dessous, la
   phrase 15/21 px grise 4 px dessous. */
.expired-card { --exp-gap: 10px; --exp-title: 17px; --exp-text-gap: 4px; --exp-lh: 21px; --exp-pill-pad: 3px; --exp-pill-radius: 13px; }
.expired-pill { justify-self: start; display: inline-flex; align-items: center; min-height: 26px; padding: var(--exp-pill-pad) var(--space-3); border-radius: var(--exp-pill-radius); background: var(--orange-soft); color: var(--orange-text); font-size: var(--font-caption); font-weight: var(--weight-bold); }
.expired-card .expired-title { margin: var(--exp-gap) 0 0; font-size: var(--exp-title); font-weight: var(--weight-bold); }
.expired-card .expired-text { margin: var(--exp-text-gap) 0 0; color: var(--text-secondary); font-size: var(--font-label); line-height: var(--exp-lh); }
.match-now .field-error { align-self: stretch; margin: 0; }
/* L'adresse (planches OffreAdresse du 18.11) : sur deux lignes, la pastille grise 10 px dessous ; « Modifier » ou
   « Ajouter l'adresse » en ligne pleine largeur sous un trait, texte bleu gras 15 px, chevron gris. */
.address-lines { white-space: pre-line; }
.address-pill { --pill-gap: 10px; margin-top: var(--pill-gap); }
.address-busy { display: flex; align-items: center; color: var(--text-secondary); }
.address-row { display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: var(--target-min); padding: var(--space-3) 0; border: 0; border-top: 1px solid var(--line-soft); background: none; color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; }
.address-row .icon { flex: none; color: var(--text-secondary); }
.oc-note-redone { margin: var(--space-2) 0 var(--space-4); }
.oc-card-title { margin: 0; padding: var(--oc-head-top) var(--oc-x) var(--oc-14); font-size: var(--oc-card-title); line-height: var(--oc-card-lh); font-weight: var(--weight-bold); }
.oc-row { margin: 0; padding: var(--space-3) var(--oc-x); border-top: 1px solid var(--line); }
.oc-post { padding-bottom: var(--space-4); }
.oc-post-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--oc-6); }
.oc-post-head .section-more { margin: calc(-1 * var(--space-3)) 0; }
.oc-label { display: block; font-size: var(--oc-label); line-height: var(--oc-label-lh); color: var(--text-secondary); }
.oc-text { margin: 0; font-size: var(--font-label); line-height: var(--oc-text-lh); color: var(--text); }
.oc-text + .oc-text { margin-top: var(--space-2); }
.oc-post .read-more { display: inline-flex; align-items: center; min-height: var(--target-min); font-weight: var(--weight-bold); color: var(--primary-text); }
.oc-row.offer-facts { list-style: none; }
.oc-row-refused .offer-give-zone { margin: var(--space-3) calc(-1 * var(--oc-x)) calc(-1 * var(--space-3)); padding: var(--space-5) var(--space-5) var(--space-2); border-top: 1px solid var(--line); }
.oc-row-refused .offer-reading { min-height: var(--target-min); }
.oc-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); padding: var(--oc-14) var(--oc-x) var(--oc-head-top); border-top: 1px solid var(--line); }
.oc-actions > :is(a, button) { display: inline-flex; align-items: center; justify-content: center; min-height: var(--oc-pill); padding: 0 var(--oc-22); border-radius: var(--oc-pill-r); font-size: var(--font-label); white-space: nowrap; }
.oc-actions > .button-link.primary-link { padding: 0 var(--space-6); border: 0; background: var(--action); color: var(--on-action); font-weight: var(--weight-bold); }
.oc-actions > button.secondary { border: var(--action-line, 1.5px) solid var(--button-outline); background: var(--surface); color: var(--text); font-weight: var(--weight-semibold); }
.oc-brief .oc-card-title { padding-bottom: var(--space-2); }
.oc-brief-grid { display: grid; grid-template-columns: 1fr 1fr; margin: 0; padding-bottom: var(--space-2); }
.oc-brief-grid > div { box-sizing: border-box; min-height: var(--oc-row-min); padding: var(--space-3) var(--oc-x); }
.oc-brief-grid dt { font-size: var(--oc-label); line-height: var(--oc-label-lh); color: var(--text-secondary); }
.oc-brief-grid dd { margin: var(--oc-2) 0 0; font-size: var(--font-label); line-height: var(--oc-20); font-weight: var(--weight-bold); }
.oc-brief-grid dd.oc-missing { font-weight: var(--weight-medium, 500); color: var(--text-secondary); }
.oc-link-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); box-sizing: border-box; min-height: var(--oc-row-min); padding: var(--space-3) var(--oc-x); border-top: 1px solid var(--line); color: var(--text); text-decoration: none; }
.oc-link-row b { font-size: var(--font-label); line-height: var(--oc-20); }
.oc-link-row:hover b { text-decoration: underline; }
.oc-link-row .icon { flex: none; width: 20px; height: 20px; }
.oc-company { padding: var(--oc-head-top) var(--oc-x); }
/* Recherche en cours (audit du 17.11, K6) : le cercle qui tourne des écrans de chargement (LoadingSteps, étape en
   cours), à la taille du texte, devant la phrase ; immobile si le mouvement est réduit. */
.offer-busy { display: flex; align-items: center; gap: var(--space-2); }
.offer-busy-ring { flex: none; box-sizing: border-box; width: 1em; height: 1em; border: 2px solid var(--line-strong); border-right-color: var(--primary-graphic); border-radius: var(--radius-pill); animation: offer-busy-turn 0.9s linear infinite; }
@keyframes offer-busy-turn { to { transform: rotate(360deg); } }
/* « L'entreprise » (planche OffreAdresseTrouvee du 18.11) : titre en casse normale, 18/800 ; la carte du site dessous. */
.offer-company .offer-company-cap { font-size: var(--font-title); font-weight: var(--weight-heavy); letter-spacing: 0; text-transform: none; color: var(--text); }
.company-site { --site-min: 56px; display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); min-height: var(--site-min); padding: var(--space-3) 0; border-top: 1px solid var(--line-soft); color: var(--text); text-decoration: none; }
.company-site b { display: block; font-size: var(--font-body); font-weight: var(--weight-semibold); }
.company-site-host { display: block; margin-top: var(--space-1); font-size: var(--font-small); color: var(--text-secondary); }
.company-site .icon { flex: none; color: var(--text-secondary); }
/* Planche Offre du 18.11 : la grille Taux · Contrat · Télétravail, les passages surlignés et « Autres offres chez … ». */
.offer-grid { --grid-r: 12px; --grid-pad-y: 10px; --grid-pad-x: 4px; --grid-label: 12px; --grid-label-lh: 16px; --grid-value-lh: 20px; --grid-gap: 2px;
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: var(--space-4) 0 0; border: 1px solid var(--line); border-radius: var(--grid-r); }
.offer-grid > div { padding: var(--grid-pad-y) var(--grid-pad-x); text-align: center; }
.offer-grid > div + div { border-left: 1px solid var(--line); }
.offer-grid dt { font-size: var(--grid-label); line-height: var(--grid-label-lh); color: var(--text-secondary); }
.offer-grid dd { margin: var(--grid-gap) 0 0; font-size: var(--font-label); line-height: var(--grid-value-lh); font-weight: var(--weight-bold); }
.detail-post { --mark-bg: #FFE9A8; --mark-r: 4px; --mark-x: 4px; --legend-w: 24px; --legend-h: 12px; --legend-font: 13px; }
.post-summary mark { padding: 0 var(--mark-x); border-radius: var(--mark-r); background: var(--mark-bg); color: inherit; }
.post-legend { display: flex; align-items: center; gap: var(--space-2); margin: var(--space-3) 0 var(--space-1); font-size: var(--legend-font); color: var(--text-secondary); }
.post-legend > span { flex: none; width: var(--legend-w); height: var(--legend-h); border-radius: var(--mark-r); background: var(--mark-bg); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .detail-post { --mark-bg: #5C4A14; } }
:root[data-theme="dark"] .detail-post { --mark-bg: #5C4A14; }
.company-offers { --co-title: 17px; --co-title-lh: 22px; --co-line: 13px; --co-line-lh: 18px; --co-pill-y: 4px; --co-pill-x: 10px; --co-chevron: 20px; }
.company-offers h3 { margin: 0 0 var(--space-1); font-size: var(--co-title); line-height: var(--co-title-lh); font-weight: var(--weight-bold); }
.company-offer { display: flex; align-items: center; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-3) 0; color: inherit; text-decoration: none; }
.company-offer + .company-offer { border-top: 1px solid var(--line); }
.company-offer-text { flex: 1; min-width: 0; }
.company-offer-text b { display: block; overflow: hidden; font-size: var(--font-label); line-height: var(--co-title-lh); white-space: nowrap; text-overflow: ellipsis; }
.company-offer-text > span { display: block; margin-top: var(--grid-gap, 2px); font-size: var(--co-line); line-height: var(--co-line-lh); color: var(--text-secondary); }
.company-offer-pill { flex: none; padding: var(--co-pill-y) var(--co-pill-x); border-radius: var(--radius-pill); background: var(--surface-muted); color: var(--text-tertiary); font-size: var(--co-line); font-weight: var(--weight-bold); }
.company-offer-pill:is(.very-close, .close) { background: var(--success-soft); color: var(--success); }
.company-offer > .icon { flex: none; width: var(--co-chevron); height: var(--co-chevron); color: var(--primary-text); }
@media (prefers-reduced-motion: reduce) { .offer-busy-ring { animation: none; } }
/* Audit du 17.11, N27 : sur ordinateur, chaque lien seul de la fiche a une cible de 24 px de haut au moins (WCAG 2.5.8),
   sans rien déplacer : un lien dans le texte prend la marge en haut et en bas, un bouton-lien la reprend en négatif. */
.offer-cards .contacts-searches a.link { padding-block: var(--space-1); }
.offer-cards :is(.oc-company .more-direct, [data-test="contact-add"]) { min-height: var(--space-6); margin-block: calc((var(--space-5) - var(--space-6)) / 2); }
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
  /* Maquette du 14 novembre (Offre, OffreProvisoire, §6) : retour, marque-page et « ⋯ » dans des boutons de 48 px, couleur
     du texte, la flèche de retour de 24 px ; la barre à 12 px du haut, 8 px des bords, 4 px dessous ; offre sûre ou
     provisoire, la même barre. */
  .offer-blocks .offer-subhead { --ob-8: 8px; --ob-4: 4px; margin: 0; padding: var(--ob-12) var(--ob-8) var(--ob-4); background: var(--bg); }
  .offer-blocks .offer-subhead .icon-button { width: var(--ob-48); height: var(--ob-48); color: var(--text); }
  .offer-blocks .offer-subhead .icon-button > .icon { width: var(--ob-24); height: var(--ob-24); }
  .offer-blocks > .detail-offer, .offer-blocks .match-card, .offer-blocks .expired-card {
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
  .offer-blocks .detail-offer .status-line { margin-top: var(--ob-gap); }
  .offer-blocks .match-card, .offer-blocks .expired-card { display: block; }
  .offer-blocks .match-head { gap: var(--ob-gap); padding: 0; }
  .offer-blocks .match-head .score-ring.large { width: var(--ob-56); height: var(--ob-56); }
  .offer-blocks .match-title { font-size: var(--font-title); line-height: var(--ob-24); font-weight: var(--weight-bold); }
  .offer-blocks .match-sub { margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--ob-21); color: var(--text-secondary); }
  /* « Voir la compatibilité » (prompt du 10 novembre, PR 15 ; libellé du 15.11) : toute la ligne est le bouton, le texte au même retrait que
     le contenu de la carte (18,5 px, pas le retrait du verdict ni les 98,5 px de l'ordinateur), le chevron à droite. */
  .offer-blocks .compat-open {
    display: flex; align-items: center; justify-content: space-between; gap: var(--ob-gap); width: calc(100% + 2 * var(--ob-pad)); max-width: none; min-height: var(--ob-56);
    margin: var(--ob-gap) calc(-1 * var(--ob-pad)) calc(-1 * var(--ob-pad)); padding: 0 var(--ob-pad); border: 0; border-top: 1px solid var(--line-soft);
    border-radius: 0 0 var(--radius-card) var(--radius-card); background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer;
  }
  .offer-blocks .compat-open > .icon { flex: none; width: var(--ob-24); height: var(--ob-24); }
  /* Offre provisoire (OffreProvisoire, §17 du 15 novembre) : l'en-tête sans carte, sur le fond : logo de 56 px, 12 px, titre
     28/34, entreprise et lieu 16 px, pastilles à contour (trait de 1 px, rayon 8) ; dans la carte de la note, les points
     tirés de l'extrait (coche de 18 px, 15/20) et « Voir la compatibilité » en bleu comme partout (décision de Kevin du 16.11). « L'entreprise » en section
     comme « Le poste » (titre 16/700, texte 15 px ; décision de Kevin du 15.11). */
  .offer-provisional > .detail-offer { display: flex; flex-direction: column; align-items: flex-start; gap: var(--ob-12); margin: var(--space-1) var(--ob-margin) 0; padding: 0; background: none; border: 0; }
  .offer-provisional .detail-title h2 { font-size: var(--ob-28); line-height: var(--title-block); font-weight: var(--weight-bold); }
  .offer-provisional .detail-title .detail-sub { font-size: var(--font-body); line-height: var(--ob-24); }
  .offer-provisional .offer-tags { margin-top: 0; }
  .offer-provisional .offer-tags li { padding: var(--space-1) var(--space-2); background: var(--surface); border: 1px solid var(--line); }
  .offer-provisional .match-card { margin-top: var(--space-5); }
  .offer-provisional .match-lines { margin-top: var(--ob-gap); font-size: var(--font-label); line-height: var(--space-5); }
  .offer-provisional .compat-open { width: 100%; margin: var(--ob-gap) 0 calc(-1 * var(--ob-gap)); padding: 0; }
  .offer-provisional .compat-open > .icon { width: var(--space-5); height: var(--space-5); }
  .offer-provisional .offer-company-cap { font-size: var(--font-body); font-weight: var(--weight-bold); letter-spacing: 0; text-transform: none; color: var(--text); }
  /* Lecture de l'annonce complète (prompt du 10 novembre, PR 13 ; OffreProvisoire) : tout reste DANS la carte, au
     retrait du contenu, jamais en pleine largeur. La ligne « jobA1 lit l'annonce complète… » 16 px sous le verdict ; le
     refus séparé par un filet, 16 px dessus (14 dans la maquette, sur la grille de 4), 12 px entre ses lignes ; puis
     « Voir la compatibilité » sans vide. */
  .offer-blocks .match-card .offer-reading, .offer-blocks .match-card .redone { margin-top: var(--ob-gap); }
  .offer-blocks .match-card .offer-text-refused { margin-top: var(--ob-gap); padding-top: var(--ob-gap); border-top: 1px solid var(--line-soft); }
  .offer-blocks .detail-post { display: block; }
  .offer-blocks .detail-post-head h3 { font-size: var(--font-title); line-height: var(--ob-24); }
  .offer-blocks .post-summary, .offer-blocks .detail-snippet { margin: var(--space-1) 0 0; font-size: var(--font-label); line-height: var(--ob-23); color: var(--text-tertiary); }
  .offer-blocks .post-links { margin-top: var(--space-2); }
  .offer-blocks .post-links .link { color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); }
  /* §7 du 14 novembre : 12 px entre « Écarter » et « Préparer ma candidature ». */
  .offer-blocks .offer-bar { z-index: 40; gap: var(--space-3); padding: var(--ob-12) var(--ob-margin) calc(var(--space-4) + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line); }
  .offer-blocks .offer-bar-discard { flex: none; min-height: var(--ob-48); padding: 0 var(--ob-margin); font-size: var(--font-label); font-weight: var(--weight-bold); }
  .offer-blocks .offer-bar-main { flex: 1; min-height: var(--ob-52); background: var(--action); border-color: var(--action); color: var(--on-action); }
  /* §2.9 : chaque lien de la sous-page est une cible de 44 px de haut, et rien n'est poussé par une marge « auto »
     (hors de la grille de 4) : l’en-tête de section et le repliable répartissent la place eux-mêmes. */
  .offer-blocks :is(.link, .more-direct) { display: inline-flex; align-items: center; min-height: var(--target-min); }
  .offer-blocks .section-more, .offer-blocks .disclosure-chevron { margin-left: 0; }
  .offer-blocks .disclosure-row { justify-content: space-between; }
  /* « L'entreprise » sur téléphone (OffreAdresseTrouvee) : le titre hors de la carte, puis deux cartes (Nom et adresse ;
     site), séparateurs intérieurs. */
  .offer-blocks .detail-more-rows:has(.company-card) { --co-card-gap: 12px; padding-top: 0; border-top: 0; }
  .offer-blocks .offer-company-head { min-height: 0; margin: 0 0 var(--space-3); border-bottom: 0; }
  .offer-blocks .company-card { margin-bottom: var(--co-card-gap); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); overflow: hidden; }
  .offer-blocks .company-card > :is(.block-field, .address-row, .registry-proposals, .employer-line) { padding-inline: var(--space-4); }
  .offer-blocks .company-card > :first-child { border-top: 0; }
  .offer-blocks .company-site { padding: var(--space-3) var(--space-4); }
  /* « Autres offres chez … » en carte, comme l'en-tête et la compatibilité (planche Offre). */
  .offer-blocks .company-offers { --co-pad-top: 14px; --co-pad-bottom: 6px; margin: var(--ob-12) var(--ob-margin) var(--space-6); padding: var(--co-pad-top) var(--ob-pad) var(--co-pad-bottom);
    background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
  .offer-blocks .post-summary { font-size: var(--font-label); }
}
</style>
