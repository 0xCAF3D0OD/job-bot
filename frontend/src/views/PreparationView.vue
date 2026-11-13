<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Letter, type LetterLanguage, type Offer, type OrpMonth } from "../api/client";
import CvPanel from "../components/CvPanel.vue";
import ProfileCompletionPanel from "../components/ProfileCompletionPanel.vue";
import DocPreview from "../components/DocPreview.vue";
import LayoutSheetLink from "../components/LayoutSheetLink.vue";
import { DOC_TEMPLATES, pdfHref, useDocTemplate } from "../composables/useDocTemplate";
import ApplyActions from "../components/ApplyActions.vue";
import ContactsPanel from "../components/ContactsPanel.vue";
import OfferCompatSheet from "../components/OfferCompatSheet.vue";
import LayoutCard from "../components/LayoutCard.vue";
import PrepCertificates from "../components/PrepCertificates.vue";
import FormSheet from "../components/FormSheet.vue";
import PageHero from "../components/PageHero.vue";
import ActionBar from "../components/ActionBar.vue";
import AiWriting from "../components/AiWriting.vue";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import BusyButton from "../components/BusyButton.vue";
import FaceState from "../components/FaceState.vue";
import ApplicationSent from "../components/ApplicationSent.vue";
import GoalReached from "../components/GoalReached.vue";
import FalseClaimSheet, { type FalseClaimMode } from "../components/FalseClaimSheet.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import GroupedList from "../components/GroupedList.vue";
import GroupedRow from "../components/GroupedRow.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import HoverNote from "../components/HoverNote.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import IconButton from "../components/IconButton.vue";
import ScoreRing from "../components/ScoreRing.vue";
import StepTabs, { type Step } from "../components/StepTabs.vue";
import { firstGoal, forgetGoal } from "../composables/useGoalMoment";
import { usePhone } from "../composables/usePhone";
import { useAssistant } from "../composables/useAssistant";
import Composer from "../components/Composer.vue";
import SuggestionChips from "../components/SuggestionChips.vue";
import { MATCH_TITLE, pointParts } from "../compat";
import { dateInSentence, dateWithTime } from "../dates";
import { companyPlace, expiredText, scoreWord } from "../format";
import StatusPill from "../components/StatusPill.vue";
import InlineConfirm from "../components/InlineConfirm.vue";
import { usePlan } from "../composables/usePlan";
import { offerUndo } from "../composables/useUndo";
import { sentencesAt, withoutSentence } from "../letterSentences";
import PlanLimit from "../components/PlanLimit.vue";

const { aiNote, reached, refresh: refreshPlan } = usePlan();

const route = useRoute();
const router = useRouter();
const offerId = Number(route.params.id);
// Trois étapes (docs/47 §2) : Lettre, CV, Postuler. L'ancienne étape « Suivre » (Q1, étape 7c) mène à
// Postuler, qui rappelle l'envoi et renvoie au suivi.
const tab = computed(() =>
  route.query.doc === "cv" ? "cv" : route.query.doc === "postuler" || route.query.doc === "suivre" ? "apply" : "letter",
);

// « Postuler sur … » (docs/13 §1), dans l'onglet Postuler : le lien, où il mène (« sur jobup »), et
// le lien secondaire une fois ouvert (C8, « Rouvrir jobup »).
const SITE_NAMES: Record<string, string> = { jobup: "jobup", indeed: "Indeed", jobroom: "Job-Room" };
type ApplyLink = { url: string; label: string; where: string; reopen: string };
const EMPLOYER = { label: "Postuler chez l’employeur", where: "chez l’employeur", reopen: "Rouvrir le site de l’employeur" };
const applyLink = computed<ApplyLink | null>(() => {
  const o = offer.value;
  if (!o) return null;
  // Annonce trouvée chez l'employeur (docs/20 §2) : c'est là qu'on postule.
  if (o.employer_url) return { url: o.employer_url, ...EMPLOYER };
  if (o.apply_url) {
    return o.apply_kind === "external"
      ? { url: o.apply_url, ...EMPLOYER }
      : { url: o.apply_url, label: "Postuler sur jobup", where: "sur jobup", reopen: "Rouvrir jobup" };
  }
  const link = o.links[0];
  if (!link) return null;
  if (link.source === "manual") return { url: link.url, label: "Ouvrir l’annonce", where: "", reopen: "Rouvrir l’annonce" };
  const site = SITE_NAMES[link.source] ?? link.source;
  return { url: link.url, label: `Postuler sur ${site}`, where: `sur ${site}`, reopen: `Rouvrir ${site}` };
});
// Postuler sur ordinateur (§2.4) : le site en titre (« Sur LinkedIn »), puis l'entreprise à droite, son adresse sur
// deux lignes avec d'où elle vient, le site de l'employeur s'il est connu, et ses contacts dans un panneau.
const whereTitle = computed(() => {
  const where = applyLink.value?.where;
  if (!where) return phone.value ? "L’annonce" : "L’annonce";
  return phone.value ? `L’annonce se postule ${where}` : `${where.charAt(0).toUpperCase()}${where.slice(1)}`.replace(/'/g, "’");
});
const ADDRESS_FROM: Record<string, string> = {
  page: "Relevée dans l’annonce",
  registry: "Trouvée dans le registre IDE",
  web: "Trouvée sur Internet",
  letter: "Relevée dans l’annonce",
  manual: "Saisie par toi",
};
const addressLines = computed(() =>
  (offer.value?.company_address ?? "").split(/\s*[,\n]\s*/).map((line) => line.trim()).filter(Boolean),
);
const siteHost = computed(() => {
  const url = offer.value?.employer_url;
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
});
const contactsOpen = ref(false);
const contactsCount = ref(0);
// « Tout télécharger » : chaque pièce de la ligne « À joindre » qui se télécharge (Lettre.pdf, CV.pdf).
const attachRow = ref<HTMLElement | null>(null);
function downloadAll(): void {
  attachRow.value?.querySelectorAll<HTMLAnchorElement>("a[download]").forEach((link) => link.click());
}
// Le formulaire ouvert : « J'ai postulé » devient le bouton plein (maquette, étape 7c).
const opened = ref(false);
const currentCvId = ref<number | null>(null);
const currentLetterId = computed(() => current(letters.value)?.id ?? null);
// Corps de la lettre, pour les formulaires qui le demandent en texte (docs/25 §5).
const currentLetterText = computed(() => current(letters.value)?.paragraphs.map((p) => p.text).join("\n\n") ?? null);
// Un seul bouton plein (docs/29 §1.3) : la prochaine étape — la lettre, puis le CV, puis postuler.
const nextStep = computed<"letter" | "cv" | "apply">(() =>
  !currentLetterId.value ? "letter" : !currentCvId.value ? "cv" : "apply",
);
const applyError = ref("");
const applyBusy = ref(false);
// L'écran « Candidature envoyée. » (docs/141, 8) : le poste, ce qui compte pour l'ORP, la relance prévue.
type Sent = { id: number; company: string; title: string; month: string; count: number | null; target: number | null; followUpOn: string | null };
const sent = ref<Sent | null>(null);
// « C'est fait ! » (B10) : le mois ORP que cette candidature vient de compléter, une fois par mois.
const goal = ref<OrpMonth | null>(null);
// Une candidature déjà envoyée (Q1) : la date, rappelée en tête avec le lien vers le suivi.
const sentOn = ref("");

// « J'ai postulé » (C8) : enregistré tout de suite, à la date du jour et avec les valeurs de l'annonce ;
// la date se corrige ensuite dans le suivi.
async function markApplied(): Promise<void> {
  applyError.value = "";
  applyBusy.value = true;
  try {
    const prefill = await api.GET("/api/offers/{offer_id}/application-prefill", { params: { path: { offer_id: offerId } } });
    const { data, error: err } = prefill.data ? await api.POST("/api/applications", { body: prefill.data }) : { data: null, error: prefill.error };
    if (!data) {
      applyError.value = detail(err, "Enregistrement impossible pour l’instant : réessaie.");
      return;
    }
    // Le mois ORP d'abord : s'il atteint l'objectif, « C'est fait ! » s'affiche tout de suite, sans passer par
    // « Candidature notée ».
    const orp = (await api.GET("/api/orp", { params: { query: { month: data.orp_month } } }).catch(() => null))?.data;
    goal.value = orp && firstGoal(data.orp_month, orp.count, orp.target) ? { ...orp, month: data.orp_month } : null;
    sent.value = { id: data.id, company: data.company, title: data.job_title, month: data.orp_month, count: orp?.count ?? null, target: orp?.target ?? null, followUpOn: data.follow_up_on ?? null };
    sentOn.value = data.sent_at;
    if (offer.value) offer.value = { ...offer.value, status: "applied" };
    window.scrollTo?.({ top: 0 });
  } finally {
    applyBusy.value = false;
  }
}

// « Je n'ai pas postulé » (C9, revue de la PR 479) : l'offre revient en préparation tout de suite ; la candidature
// n'est effacée qu'après 6 s, sauf « Annuler » (comme « Écarter »).
function cancelApplied(): void {
  const done = sent.value;
  const before = offer.value;
  if (!done || !before) return;
  const won = goal.value;
  sent.value = null;
  goal.value = null;
  if (won) forgetGoal(won.month);
  offer.value = { ...before, status: "preparing" };
  opened.value = false;
  void offerUndo({
    message: "Candidature retirée : l’offre revient en préparation.",
    commit: async (keepalive) => {
      const { response } = await api.DELETE("/api/applications/{application_id}", {
        params: { path: { application_id: done.id } },
        keepalive,
      });
      return response.ok;
    },
    restore: () => {
      sent.value = done;
      if (won && firstGoal(won.month, won.count, won.target)) goal.value = won;
      offer.value = before;
    },
  });
}

const offer = ref<Offer | null>(null);
// Les étapes (C2) : Lettre, CV, Postuler (Q1 : plus de « Suivre »).
const steps = computed<Step[]>(() => {
  const o = offer.value;
  return [
    { key: "letter", label: "Lettre", to: { query: {} }, done: !!current(letters.value)?.read_at, test: "tab-letter" },
    { key: "cv", label: "CV", to: { query: { doc: "cv" } }, done: !!currentCvId.value, test: "tab-cv" },
    { key: "apply", label: "Postuler", to: { query: { doc: "postuler" } }, done: o?.status === "applied", test: "tab-apply" },
  ];
});
// Le retour à l'offre (C1) : par l'historique quand on vient de la fiche (même défilement, mêmes
// filtres, geste de retour d'iOS) ; sinon le lien ouvre la fiche.
function backToOffer(event: MouseEvent): void {
  const back = (window.history.state as { back?: string } | null)?.back ?? "";
  if (back.startsWith(`/candidatures/offres/${offerId}`) && !back.includes("/preparer")) {
    event.preventDefault();
    router.back();
  }
}
const assistant = useAssistant();
watch(offer, (o) => {
  if (o) assistant.setFocus({ offerId: o.id, label: `préparation : ${o.title}${o.company ? ` chez ${o.company}` : ""}` });
});
onUnmounted(() => assistant.setFocus(null));
const letters = ref<Letter[]>([]);
const chunkTitles = ref<Record<number, string>>({});
const selectedId = ref<number | null>(null);
const draft = ref<{ subject: string; paragraphs: { text: string; chunk_ids: number[] }[] } | null>(null);
const dirty = ref(false);
const language = ref<LetterLanguage | "">("");
const instruction = ref("");
const writing = ref(false);
const saving = ref(false);
const error = ref("");
const notFound = ref(false);

const LANGUAGES: Record<LetterLanguage, string> = { fr: "Français", en: "English", de: "Deutsch" };

const selected = computed(() => letters.value.find((l) => l.id === selectedId.value) ?? null);

// Sous 820 px (le seuil unique), la mise en page du téléphone (étape 7a) : la langue et la consigne
// au-dessus de la lettre, les versions et le téléchargement dans le « ⋯ » de la tête (une feuille du
// bas), un seul bouton plein dans la barre du bas. Sans choix, la langue affichée est celle de la
// lettre ; sans lettre, aucune : elle sera celle de l'annonce.
const { phone } = usePhone();
const versionsOpen = ref(false);
// Le modèle (maquette Preparer, Kevin 2026-11-05) : sur téléphone, la lettre se montre en aperçu dans le
// modèle choisi ; l'aperçu touché ouvre la lettre entière, modifiable.
const { template } = useDocTemplate();
const letterOpen = ref(false);
const previewName = computed(() => doc.value?.sender[0] || "Ton nom");
// « 1020 Renens » devient « Renens » sous le nom.
const previewSub = computed(() => {
  const line = doc.value?.sender.find((l) => /^\d{4}\s/.test(l));
  return line ? line.replace(/^\d{4}\s+/, "") : null;
});
const previewParagraphs = computed(() =>
  draft.value && doc.value ? [doc.value.salutation, ...draft.value.paragraphs.map((p) => p.text)].filter(Boolean) : [],
);
const LANGUAGE_OPTIONS = (["fr", "de", "en"] as LetterLanguage[]).map((code) => ({ value: code, label: code.toUpperCase(), name: LANGUAGES[code], test: `language-${code}` }));
// Dans la feuille « Mise en page et langue » du téléphone (§9) : les trois langues en toutes lettres.
const SHEET_LANGUAGE_OPTIONS = LANGUAGE_OPTIONS.map((option) => ({ ...option, label: option.name }));
// Les puces de retouche n'apparaissent qu'avec le focus dans la zone de saisie ; l'aperçu passe alors à 300 px (§9).
const composing = ref(false);
function leaveComposer(event: FocusEvent): void {
  const next = event.relatedTarget as Node | null;
  if (!next || !(event.currentTarget as HTMLElement).contains(next)) composing.value = false;
}
const shownLanguage = computed<string>({
  get: () => language.value || selected.value?.document?.language || "",
  set: (value) => {
    language.value = value as LetterLanguage;
  },
});
// Le bouton plein de la barre (C3) : « Rédiger… » quand il y a quelque chose à rédiger, sinon rien
// (« Continuer vers le CV » prend la place).
const LANGUAGE_IN: Record<LetterLanguage, string> = { fr: "français", de: "allemand", en: "anglais" };
// Sous Lettre.pdf / CV.pdf (maquette Preparer) : le modèle choisi et la langue de la lettre, « Modèle Moderne, en
// français. » ; sans lettre, le modèle seul.
const templateNote = computed(() => {
  if (!currentLetterId.value && !currentCvId.value) return "";
  const name = DOC_TEMPLATES.find((t) => t.value === template.value)?.label ?? "";
  const language = current(letters.value)?.language;
  return language ? `Modèle ${name}, en ${LANGUAGE_IN[language]}.` : `Modèle ${name}.`;
});
const writeLabel = computed(() => {
  const chosen = language.value;
  if (!selected.value) return chosen ? `Rédiger en ${LANGUAGE_IN[chosen]}` : "Rédiger la lettre";
  if (chosen && chosen !== selected.value.language) return `Rédiger à nouveau en ${LANGUAGE_IN[chosen]}`;
  if (instruction.value.trim()) return "Rédiger la nouvelle version";
  return "";
});
// Retoucher la lettre (maquette du 8 novembre, PreparerOrdinateur) : des pastilles de suggestion, puis la zone de
// saisie commune d'une ligne, « Demander une modification de la lettre ». Le bouton « Modifier le texte avec
// l'Assistant » disparaît. « Insister sur … » prend la première compétence du profil citée par l'annonce (les points
// forts de la note) ; sans elle, trois pastilles seulement.
const revision = ref("");
const insist = computed(() => {
  const first = offer.value?.strengths?.[0];
  const key = first ? /^([^:]{1,40}?)\s?:\s+/.exec(first.text.trim())?.[1] : undefined;
  return key ? `Insister sur ${key}` : "";
});
const suggestions = computed(() => {
  const list = ["Plus court", "Plus formel"];
  if (insist.value) list.push(insist.value);
  return list;
});
function revise(text: string): void {
  const asked = text.trim();
  if (!asked || writing.value) return;
  if (asked === "En allemand") {
    language.value = "de";
    instruction.value = "";
  } else {
    instruction.value = asked;
  }
  void write();
}
const readBusy = ref(false);
function pickVersion(letter: Letter): void {
  select(letter);
  versionsOpen.value = false;
}
const doc = computed(() => selected.value?.document ?? null);
// « Objet : » (fr) ou « Subject: » (en), ajouté par la plateforme devant l'objet.
const subjectPrefix = computed(() => {
  const line = doc.value?.subject_line ?? "";
  const subject = selected.value?.subject ?? "";
  return line.endsWith(subject) ? line.slice(0, line.length - subject.length) : "";
});

function select(letter: Letter | null): void {
  selectedId.value = letter?.id ?? null;
  draft.value = letter
    ? { subject: letter.subject, paragraphs: letter.paragraphs.map((p) => ({ ...p, chunk_ids: [...(p.chunk_ids ?? [])] })) }
    : null;
  dirty.value = false;
  void nextTick(resizeAll);
}

// La version qui compte : la dernière modifiée, sinon la dernière rédigée (docs/08 §3).
function current(list: Letter[]): Letter | null {
  const stamp = (l: Letter) => Date.parse(l.edited_at ?? l.created_at);
  return [...list].sort((a, b) => stamp(b) - stamp(a) || b.version - a.version)[0] ?? null;
}

function detail(err: unknown, fallback: string): string {
  const value = (err as { detail?: unknown } | undefined)?.detail;
  if (typeof value !== "string") return fallback;
  const text = value.charAt(0).toUpperCase() + value.slice(1);
  return /[.!?]$/.test(text) ? text : `${text}.`;
}

async function load(): Promise<void> {
  const [o, l, c] = await Promise.all([
    api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: offerId } } }),
    api.GET("/api/offers/{offer_id}/letters", { params: { path: { offer_id: offerId } } }),
    api.GET("/api/profile-chunks"),
  ]);
  if (!o.data) {
    notFound.value = true;
    return;
  }
  offer.value = o.data;
  if (o.data.status === "applied") {
    const apps = await api.GET("/api/applications", { params: { query: { offer: offerId } } });
    sentOn.value = apps.data?.[0]?.sent_at ?? "";
  }
  const cvs = await api.GET("/api/offers/{offer_id}/cvs", { params: { path: { offer_id: offerId } } });
  const list = cvs.data ?? [];
  const stamp = (c: (typeof list)[number]) => Date.parse(c.edited_at ?? c.created_at);
  currentCvId.value = [...list].sort((a, b) => stamp(b) - stamp(a) || b.version - a.version)[0]?.id ?? null;
  letters.value = l.data ?? [];
  chunkTitles.value = Object.fromEntries((c.data ?? []).map((chunk) => [chunk.id, chunk.title]));
  noProfile.value = !!c.data && !c.data.some((chunk) => chunk.active);
  select(current(letters.value));
  launchFromOffer();
}

// « Préparer ma candidature » (MODIFICATIONS du 9 novembre, §7 n° 1 et §7.1) : l'arrivée avec ?ecrire=1 lance
// l'écriture de la lettre tout de suite, et le CV adapté se prépare en même temps. La relecture reste obligatoire.
// En cas d'échec (§7.3), la page le dit avec « Réessayer ».
const letterFailed = ref("");
// Sans bloc de profil actif, la lettre ne peut pas s'écrire (409 du serveur) : au lieu de « Réessayer », qui ne
// peut pas aboutir, la page envoie vers Profil › Expériences, le formulaire du bloc déjà ouvert (test du 10 novembre).
const noProfile = ref(false);
// « Ajouter une expérience » ouvre le formulaire des premiers pas en panneau (PR 17, point 5) ; au retour, la
// préparation repart (lettre et CV adapté). Le même panneau demande le nom et l'adresse avant une lettre.
const completion = ref<"" | "profile" | "identity">("");
const identityAsked = ref(false);
let pendingForce = false;
const COMPLETION_SECTIONS = { profile: ["experiences", "languages", "identity"], identity: ["identity"] } as const;
async function completionSaved(): Promise<void> {
  const was = completion.value;
  completion.value = "";
  if (was === "profile") {
    noProfile.value = false;
    identityAsked.value = true;
    if (!letters.value.length) void write();
    if (!currentCvId.value) void prepareCv();
  } else void write(pendingForce);
}
function completionClosed(): void {
  const was = completion.value;
  completion.value = "";
  if (was === "identity") void write(pendingForce);
}
const NO_PROFILE_TEXT = "Ajoute au moins une expérience pour écrire une lettre sans invention.";
// Sur ordinateur, la carte d'échec dit déjà ces messages génériques ; un motif précis du serveur reste affiché.
const GENERIC_FAILURES = new Set(["La rédaction a échoué, réessaie.", "API injoignable."]);
const cvState = ref<"" | "busy" | "failed">("");
async function prepareCv(): Promise<void> {
  cvState.value = "busy";
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/cvs", {
      params: { path: { offer_id: offerId } },
      // Le CV prend la langue de la lettre (§14) ; elle se change à part, à l'étape CV.
      body: { language: current(letters.value)?.language ?? null, instruction: null, base_draft_id: null },
    });
    await refreshPlan();
    cvState.value = data ? "" : "failed";
    if (data) currentCvId.value = data.id;
  } catch {
    cvState.value = "failed";
  }
}
// La ligne « CV adapté » de « Ta candidature » : prêt, en préparation (§7.1), en échec (§7.3) ou à préparer.
const cvRow = computed<{ text: string; tone: string }>(() => {
  if (currentCvId.value) return { text: "Prêt, à relire à l’étape 2", tone: "ok" };
  if (cvState.value === "busy") return { text: "En préparation", tone: "busy" };
  if (cvState.value === "failed") return { text: "Pas pu être préparé, à refaire à l’étape 2", tone: "todo" };
  return { text: "À préparer à l’étape 2", tone: "" };
});
function launchFromOffer(): void {
  if (route.query.ecrire !== "1") return;
  const rest = { ...route.query };
  delete rest.ecrire;
  void router.replace({ query: rest });
  if (offer.value?.status === "applied") return;
  if (noProfile.value) return;
  if (!letters.value.length && !reached("letter")) void write();
  if (!currentCvId.value && !reached("cv")) void prepareCv();
}

// Le texte qui vient d'arriver de l'IA apparaît ligne à ligne (docs/59 §4).
const fresh = ref(false);
// Des modifications non enregistrées : le choix se fait dans la page (docs/108 §1).
const choosingWrite = ref(false);
async function saveThenWrite(): Promise<void> {
  choosingWrite.value = false;
  await save();
  await write(true);
}
// La rédaction, puis la relecture : le bouton dit ce qui se passe vraiment (BusyButton).
const phase = ref<"write" | "review">("write");
async function reviewLetter(letter: Letter): Promise<Letter> {
  try {
    const { data } = await api.POST("/api/letters/{draft_id}/review", { params: { path: { draft_id: letter.id } } });
    return data ?? letter;
  } catch {
    return letter;
  }
}
// « Relue : 6/7. À renforcer : précision, conclusion. »
// La carte « Ta candidature » et le panneau Relecture sur ordinateur (§2.2) : « 7 sur 7, rien à renforcer » en vert ;
// sinon « 6 sur 7, 1 point à renforcer », sans le ton erreur (comme les pastilles « À revoir »).
const reviewOpen = ref(false);
const reviewSummary = computed(() => {
  const review = selected.value?.review;
  if (!review) return { text: "", tone: "" };
  const passed = review.criteria.filter((c) => c.ok).length;
  const weak = review.criteria.length - passed;
  const head = `${passed} sur ${review.criteria.length}`;
  return weak ? { text: `${head}, ${weak} point${weak > 1 ? "s" : ""} à renforcer`, tone: "todo" } : { text: `${head}, rien à renforcer`, tone: "ok" };
});
const reviewGroups = computed(() => {
  const criteria = selected.value?.review?.criteria ?? [];
  return [
    { key: "weak", title: "À renforcer", ok: false, items: criteria.filter((c) => !c.ok) },
    { key: "ok", title: "Vérifié", ok: true, items: criteria.filter((c) => c.ok) },
  ].filter((g) => g.items.length);
});
// « Actuelle : plus courte, 9 nov. 14 h 02 » : la consigne de la version (ou son nom) et son heure.
const currentVersionLine = computed(() => {
  const letter = selected.value;
  if (!letter) return "";
  const what = letter.instruction?.trim() || letter.name;
  return `${what}, ${dateWithTime(letter.edited_at ?? letter.created_at)}`;
});
const reviewLine = computed(() => {
  const review = selected.value?.review;
  if (!review) return "";
  const passed = review.criteria.filter((c) => c.ok);
  const weak = review.criteria.filter((c) => !c.ok).map((c) => c.label.toLowerCase());
  const head = `Relue : ${passed.length}/${review.criteria.length}.`;
  return weak.length ? `${head} À renforcer : ${weak.join(", ")}.` : `${head} Rien à renforcer.`;
});

// Le retour sur la consigne (aria-live) : ce que l'IA ne peut pas changer, ou qu'il n'y a rien à changer.
const instructionNote = ref("");
async function write(force = false): Promise<void> {
  if (dirty.value && !force) {
    choosingWrite.value = true;
    return;
  }
  choosingWrite.value = false;
  // Nom ou adresse manquants (PR 17, point 5) : demandés une fois avant la génération ; « Annuler » écrit quand même.
  if (!identityAsked.value) {
    identityAsked.value = true;
    const { data } = await api.GET("/api/identity").catch(() => ({ data: null }));
    if (data && (!data.name?.trim() || !data.street?.trim())) {
      pendingForce = force;
      completion.value = "identity";
      return;
    }
  }
  writing.value = true;
  error.value = "";
  letterFailed.value = "";
  instructionNote.value = "";
  try {
    const { data, error: err, response } = await api.POST("/api/offers/{offer_id}/letters", {
      params: { path: { offer_id: offerId } },
      body: {
        language: language.value || null,
        instruction: instruction.value.trim() || null,
        base_draft_id: instruction.value.trim() && selectedId.value ? selectedId.value : null,
        // La lettre doit tenir sur une page A4 dans ce modèle (mesurée sur le PDF par le serveur).
        modele: template.value,
      },
    });
    // Le compteur de la formule suit ; à la limite, la ligne grise dit pourquoi (docs/125 §4).
    await refreshPlan();
    if (!data) {
      // Une consigne hors de portée, ou qui ne change rien : une ligne sous la consigne, gardée.
      if (response?.status === 422) instructionNote.value = detail(err, "Cette consigne ne change rien à la lettre.");
      else if (response?.status === 409 && /aucun bloc de profil/i.test(detail(err, ""))) noProfile.value = true;
      else if (!reached("letter")) {
        error.value = detail(err, "La rédaction a échoué, réessaie.");
        letterFailed.value = "L’écriture a été interrompue. Rien n’est perdu : jobA1 reprend avec ton CV et l’annonce.";
      }
      return;
    }
    // La relecture avant l'affichage (rédacteur, puis relecteur) : la lettre s'affiche relue.
    phase.value = "review";
    const reviewed = await reviewLetter(data);
    letters.value = [reviewed, ...letters.value];
    instruction.value = "";
    revision.value = "";
    select(reviewed);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
  } catch {
    error.value = "API injoignable.";
    letterFailed.value = "La connexion a coupé pendant l’écriture. Rien n’est perdu : jobA1 reprend avec ton CV et l’annonce.";
  } finally {
    writing.value = false;
    phase.value = "write";
  }
}

async function save(): Promise<void> {
  if (!selected.value || !draft.value) return;
  saving.value = true;
  error.value = "";
  try {
    const { data, error: err } = await api.PUT("/api/letters/{draft_id}", {
      params: { path: { draft_id: selected.value.id } },
      body: { subject: draft.value.subject, paragraphs: draft.value.paragraphs.filter((p) => p.text.trim()) },
    });
    if (!data) {
      error.value = detail(err, "Enregistrement refusé : l’objet et au moins un paragraphe sont nécessaires.");
      return;
    }
    letters.value = letters.value.map((l) => (l.id === data.id ? data : l));
    select(data);
  } finally {
    saving.value = false;
  }
}

function edited(): void {
  dirty.value = true;
}

function resize(el: HTMLTextAreaElement): void {
  // Champ masqué (l'objet « téléphone » sur ordinateur) : rien à mesurer.
  if (!el.offsetParent) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

function resizeAll(): void {
  document.querySelectorAll<HTMLTextAreaElement>(".letter-sheet textarea").forEach(resize);
}

function onInput(event: Event): void {
  resize(event.target as HTMLTextAreaElement);
  edited();
}

// « Pas vrai » (demande de Kevin du 30.10.2026, repères de Design). Sur ordinateur, une sélection dans
// un paragraphe s'étend aux phrases entières et un bouton « Pas vrai » paraît sous le paragraphe
// (Maj + flèches pour sélectionner, puis Tab). Sur téléphone, la sélection native ouvre le menu du
// système : toucher une phrase la choisit, et l'action passe dans le panneau. Puis la feuille
// « Pas vrai » : retirer la phrase, ou la réécrire d'après le profil ; « Annuler » pendant 6 s.
const claim = ref<{ index: number; sentence: string } | null>(null);
const claimOpen = ref(false);
const claimBusy = ref(false);
const claimError = ref("");
const flashed = ref<number | null>(null);
function onSelect(index: number, event: Event): void {
  const el = event.target as HTMLTextAreaElement;
  const { selectionStart: from, selectionEnd: to, value } = el;
  if (!phone.value && from === to) {
    if (claim.value?.index === index) claim.value = null;
    return;
  }
  const sentence = sentencesAt(value, from, to);
  claim.value = sentence ? { index, sentence } : null;
}
function clearClaim(): void {
  claim.value = null;
  claimOpen.value = false;
  claimError.value = "";
}
// La seule phrase de la lettre ne se retire pas : elle se réécrit.
const onlySentence = computed(() => {
  const paragraphs = draft.value?.paragraphs.filter((p) => p.text.trim()) ?? [];
  return paragraphs.length === 1 && paragraphs[0]!.text.trim() === claim.value?.sentence;
});
function flash(index: number): void {
  flashed.value = index;
  setTimeout(() => (flashed.value = null), 1200);
}
async function confirmClaim(mode: FalseClaimMode): Promise<void> {
  const letter = selected.value;
  const chosen = claim.value;
  if (!letter || !chosen || !draft.value) return;
  claimError.value = "";
  if (mode === "remove") {
    const paragraph = draft.value.paragraphs[chosen.index]!;
    const before = { ...paragraph };
    const rest = withoutSentence(before.text, chosen.sentence);
    // Un paragraphe vidé disparaît ; « Annuler » le remet à sa place.
    if (rest) paragraph.text = rest;
    else draft.value.paragraphs.splice(chosen.index, 1);
    const wasDirty = dirty.value;
    clearClaim();
    if (rest) flash(chosen.index);
    void nextTick(resizeAll);
    await offerUndo({
      message: "Phrase retirée. jobA1 ne l’écrira plus.",
      commit: async (keepalive) => {
        const { data } = await api.POST("/api/letters/{draft_id}/false-claim", {
          params: { path: { draft_id: letter.id } },
          body: { sentence: chosen.sentence, mode: "remove" },
          keepalive,
        });
        if (!data) return false;
        letters.value = letters.value.map((l) => (l.id === data.letter.id ? data.letter : l));
        // Sans autre modification en cours, la version enregistrée devient celle affichée.
        if (!wasDirty && !dirty.value && selectedId.value === data.letter.id) select(data.letter);
        return true;
      },
      restore: () => {
        if (selectedId.value !== letter.id || !draft.value) return;
        if (rest) draft.value.paragraphs[chosen.index]!.text = before.text;
        else draft.value.paragraphs.splice(chosen.index, 0, before);
        void nextTick(resizeAll);
      },
    });
    return;
  }
  claimBusy.value = true;
  try {
    const { data, error: err } = await api.POST("/api/letters/{draft_id}/false-claim", {
      params: { path: { draft_id: letter.id } },
      body: { sentence: chosen.sentence, mode: "rewrite" },
    });
    if (!data) {
      claimError.value = detail(err, "La réécriture a échoué, réessaie.");
      return;
    }
    const reviewed = await reviewLetter(data.letter);
    letters.value = [reviewed, ...letters.value];
    clearClaim();
    select(reviewed);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
    void offerUndo({
      message: "Phrase réécrite d’après ton profil.",
      commit: () => true,
      restore: async () => {
        select(letter);
        await api.DELETE("/api/forbidden-claims/{claim_id}", { params: { path: { claim_id: data.claim_id } } });
      },
    });
  } finally {
    claimBusy.value = false;
  }
}

function sources(ids: number[]): string {
  return ids
    .map((id) => chunkTitles.value[id])
    .filter(Boolean)
    .join(", ");
}

// Une page A4 (6.11.2026) : le serveur construit le PDF dans le modèle choisi et compte ses pages. La ligne
// dit « Tient sur une page A4 » ou de combien la lettre déborde, et l'aperçu marque la fin de la page 1.
type LetterPage = { fits: boolean; overflow_lines: number; break_paragraph: number | null; break_word: number | null };
const page = ref<LetterPage | null>(null);
let pageRequest = 0;
async function loadPage(): Promise<void> {
  const letter = selected.value;
  const ticket = ++pageRequest;
  if (!letter) {
    page.value = null;
    return;
  }
  try {
    const { data } = await api.GET("/api/letters/{draft_id}/page", { params: { path: { draft_id: letter.id }, query: { modele: template.value } } });
    if (ticket === pageRequest) page.value = data ?? null;
  } catch {
    if (ticket === pageRequest) page.value = null;
  }
}
watch(() => [selected.value?.id, selected.value?.edited_at, template.value], () => void loadPage());
// Sur ordinateur (lot 15.1), la ligne de la page va dans « Mise en page » : « Tient sur une page A4 · 248 mots ».
const words = computed(() => (draft.value?.paragraphs ?? []).reduce((n, p) => n + (p.text.match(/\S+/g)?.length ?? 0), 0));
const layoutNote = computed(() => {
  const value = page.value;
  if (!value || dirty.value || !draft.value) return "";
  const count = `${words.value} mot${words.value > 1 ? "s" : ""}`;
  return value.fits ? `Tient sur une page A4 · ${count}` : `Déborde de ${value.overflow_lines} ligne${value.overflow_lines > 1 ? "s" : ""} · ${count}`;
});
// Le panneau Compatibilité depuis la note de l'en-tête (§2.2) : les mêmes familles que la fiche de l'offre.
const compatOpen = ref(false);
const compat = computed(() => {
  const o = offer.value;
  const point = (text: string) => {
    const parts = pointParts(text);
    return { key: parts.key, value: parts.rest };
  };
  return {
    strengths: (o?.strengths ?? []).map((p) => point(p.text)),
    gaps: [...(o?.gaps ?? []).map((p) => point(p.text)), ...(o?.level && o.level_detail ? [{ key: "Niveau", value: o.level_detail }] : [])],
    how: [o?.why].filter((t): t is string => !!t?.trim()),
  };
});
// Le verdict à côté de l'anneau de l'en-tête (D5 : Proche --success, À creuser --score-dig, Loin --neutral).
const verdict = computed(() => (offer.value?.score === null || offer.value?.score === undefined ? null : scoreWord(Math.round(offer.value.score))));
// « Ma candidature » ne s'affiche plus sur ordinateur ; il reste dans le titre de l'onglet (lot 15.1).
watch([offer, () => route.fullPath], ([o]) => {
  if (o) void nextTick(() => (document.title = `Ma candidature, ${o.title}, jobA1`));
});
// « J'ai relu la lettre » sur ordinateur (lot 15.1) et « J'ai relu, continuer » sur téléphone (§9) : un bouton plein.
// Il note la relecture, gardée avec la version pour un autre appareil, puis passe au CV ; un refus le dit et reste là.
async function readThenNext(): Promise<void> {
  const letter = selected.value;
  if (!letter || writing.value || readBusy.value) return;
  if (!letter.read_at) {
    readBusy.value = true;
    try {
      const { data, error: err } = await api.PUT("/api/letters/{draft_id}/read", { params: { path: { draft_id: letter.id } }, body: { read: true } });
      if (!data) {
        error.value = detail(err, "La relecture n’a pas été enregistrée, réessaie.");
        return;
      }
      error.value = "";
      letters.value = letters.value.map((l) => (l.id === data.id ? data : l));
    } finally {
      readBusy.value = false;
    }
  }
  await router.push({ query: { doc: "cv" } });
}
const pageLine = computed(() => {
  const value = page.value;
  if (!value || dirty.value) return "";
  if (value.fits) return "Tient sur une page A4.";
  return `Déborde de ${value.overflow_lines} ligne${value.overflow_lines > 1 ? "s" : ""} :`;
});
// La marque de fin de page : après le paragraphe où la page 1 se termine (-1 : avant le premier).
const pageEnd = computed<{ after: number; text: string } | null>(() => {
  const value = page.value;
  if (!value || value.fits || dirty.value || value.break_paragraph === null || !draft.value) return null;
  const paragraphs = draft.value.paragraphs;
  const index = value.break_paragraph;
  if (index >= paragraphs.length) return { after: paragraphs.length - 1, text: "Fin de la page A4 : la suite passe en page 2." };
  const words = paragraphs[index]?.text.split(/\s+/).filter(Boolean) ?? [];
  const kept = value.break_word ?? 0;
  if (kept <= 0) return { after: index - 1, text: "Fin de la page A4 : la suite passe en page 2." };
  const last = words.slice(Math.max(0, kept - 4), kept).join(" ");
  return { after: index, text: `Fin de la page A4 dans ce paragraphe, après «\u00a0${last}\u00a0».` };
});
function shorten(): void {
  instruction.value = "Raccourcir pour tenir sur une page A4";
  void write();
}

// Le nom d'une version : un nom court donné par le serveur (« Version 3 », « Plus courte » pour une
// consigne de longueur) ; la consigne entière en sous-titre, jamais coupée au milieu d'un mot (6.11.2026).
function versionName(letter: Letter): string {
  return letter.name;
}
function versionDescription(letter: Letter): string {
  return letter.instruction?.trim() || versionMeta(letter);
}
function versionMeta(letter: Letter): string {
  // L'heure compte : plusieurs versions le même jour (« modifiée aujourd'hui à 14 h 05 »).
  const when = dateWithTime(letter.edited_at ?? letter.created_at);
  return `v${letter.version} · ${LANGUAGES[letter.language]} · ${letter.edited_at ? "modifiée" : "rédigée"} ${when}`;
}

onMounted(() => void load());
</script>

<template>
  <!-- « C'est fait ! » (B10) : à la place de « Candidature notée » quand l'objectif du mois est atteint. -->
  <GoalReached
    v-if="sent && goal"
    :data="goal"
    @cancel="cancelApplied"
  />
  <!-- « Candidature envoyée. » (maquette CandidatureEnvoyee, docs/141, 8) : un écran entier à la place de la page. -->
  <ApplicationSent
    v-else-if="sent"
    :title="sent.title"
    :company="sent.company"
    :count="sent.count"
    :target="sent.target"
    :follow-up-on="sent.followUpOn"
    cancellable
    @cancel="cancelApplied"
  />
  <!-- La tête (maquette Preparer, étape 7a) : le retour à l'offre, « Ma candidature », puis l'offre en une
       ligne (logo, poste, « Entreprise · Lieu », l’anneau sans chiffre, D3) et les étapes. -->
  <PageHero
    v-else-if="phone"
    class="prep-head"
    :title="notFound ? 'Offre introuvable' : 'Ma candidature'"
  >
    <template #back>
      <RouterLink
        :to="`/candidatures/offres/${offerId}`"
        class="back-link prep-back"
        data-test="back-to-offer"
        @click="backToOffer"
      >
        <AppIcon name="arrow-left" /><span class="prep-back-text">Retour à l’offre</span>
      </RouterLink>
    </template>
    <template #actions>
      <IconButton
        v-if="phone && tab === 'letter' && selected"
        icon="more"
        label="Versions et téléchargement"
        class="prep-more"
        data-test="versions-open"
        @click="versionsOpen = true"
      />
    </template>
    <div
      v-if="offer"
      class="prep-offer"
      data-test="prep-offer"
    >
      <CompanyLogo :offer="offer" />
      <p class="prep-offer-text">
        <span
          class="prep-offer-title"
          data-test="prep-offer-title"
        >{{ offer.title }}</span>
        <span class="prep-offer-sub">{{ companyPlace(offer.company, offer.location, true) }}</span>
      </p>
    </div>
    <StepTabs
      v-if="offer"
      :steps="steps"
      :current="tab"
      label="Étapes de la candidature"
    />
  </PageHero>
  <!-- Ordinateur (lot 15.1, capture PreparerOrdinateur) : une ligne de 64 px. Le retour, un trait, le logo, le poste en
       H1 avec l’entreprise et le lieu, l’anneau de 48 avec le verdict, puis les étapes. « Ma candidature » ne reste
       que dans le titre de l’onglet. -->
  <header
    v-else
    class="container prep-desk-head"
    data-test="prep-desk-head"
  >
    <RouterLink
      :to="`/candidatures/offres/${offerId}`"
      class="prep-desk-back"
      data-test="back-to-offer"
      @click="backToOffer"
    >
      <AppIcon name="chevron-left" />Retour à l’offre
    </RouterLink>
    <span
      class="prep-desk-rule"
      aria-hidden="true"
    />
    <CompanyLogo
      v-if="offer"
      :offer="offer"
    />
    <div class="prep-desk-title">
      <h1 data-test="prep-offer-title">
        {{ notFound ? "Offre introuvable" : offer?.title ?? "" }}
      </h1>
      <p v-if="offer">
        {{ companyPlace(offer.company, offer.location, true) }}
      </p>
    </div>
    <!-- La note (§2.2) : l'anneau, « Proche de ton profil » puis « Voir la compatibilité › », qui ouvre le panneau. -->
    <button
      v-if="offer && verdict && offer.score !== null && offer.score !== undefined"
      type="button"
      class="prep-desk-score"
      aria-haspopup="dialog"
      data-test="prep-score"
      @click="compatOpen = true"
    >
      <ScoreRing
        :score="offer.score"
        :stale="offer.score_stale"
        bare
      />
      <span class="prep-desk-score-text">
        <span :class="['prep-verdict', verdict.tone]">{{ MATCH_TITLE[verdict.tone] }}</span>
        <span class="prep-desk-compat">Voir la compatibilité<AppIcon name="chevron" /></span>
      </span>
    </button>
    <StepTabs
      v-if="offer"
      :steps="steps"
      :current="tab"
      label="Étapes de la candidature"
      numbered
    />
  </header>

  <section
    v-if="!sent"
    :class="['band', { 'prep-desk-band': !phone }]"
  >
    <div class="container">
      <!-- Offre introuvable : retirée par l'employeur, peut-être. Un écran de travail : le visage, jamais le
           personnage (docs/141 §1). -->
      <FaceState
        v-if="notFound"
        title="Offre introuvable"
        mood="attentif"
        data-test="offer-not-found"
      >
        <p>Elle a peut-être été retirée par l’employeur.</p>
        <div class="face-state-actions">
          <RouterLink
            to="/candidatures/offres"
            class="button-link"
          >
            <span class="with-icon"><AppIcon name="arrow-left" />Retour aux offres</span>
          </RouterLink>
        </div>
      </FaceState>
      <!-- Le chargement : des blocs gris, pas de « Chargement… » à l'écran (règles §4). -->
      <LoadingBlocks v-else-if="!offer" />

      <p
        v-if="offer?.expired_at && offer.status !== 'applied'"
        class="notice expired-notice"
        data-test="expired"
      >
        {{ expiredText(offer) }} Vérifie avant d’envoyer ta candidature.
      </p>
      <!-- Une candidature déjà envoyée (Q1) : le rappel de l'envoi et le lien vers le suivi. -->
      <p
        v-if="offer?.status === 'applied'"
        class="notice prep-sent-notice"
        data-test="applied-notice"
      >
        <span>Envoyée{{ sentOn ? ` ${dateInSentence(`${sentOn}T12:00:00`)}` : "" }}.</span>
        <RouterLink to="/candidatures/suivi">
          Voir le suivi
        </RouterLink>
      </p>

      <!-- Postuler (C7) : où l'annonce se postule et les pièces, ce qu'on recopie, puis un contact. Sur ordinateur
           (MODIFICATIONS du 9 novembre, §2.4 ; maquette PreparerOrdinateurPostuler) : les actions au pied de la carte
           « Où postuler », et à droite l’entreprise (avec ses contacts) et ce qui suit l’envoi. -->
      <div
        v-if="offer && tab === 'apply'"
        :class="['prep-layout', { 'prep-desk': !phone }]"
        data-test="apply-steps"
      >
        <div
          v-if="offer.status !== 'applied'"
          class="prep-main apply-cards"
        >
          <section
            :class="phone ? 'doc-card' : 'apply-card'"
            aria-labelledby="apply-where-title"
            data-test="apply-where"
          >
            <p
              v-if="!phone"
              class="apply-cap"
            >
              Où postuler
            </p>
            <h2 id="apply-where-title">
              {{ whereTitle }}
            </h2>
            <p
              v-if="applyLink"
              class="apply-where-text"
            >
              {{ phone ? "Le formulaire s’ouvre dans un nouvel onglet. Reviens ici ensuite pour marquer l’envoi." : "Le formulaire s’ouvre dans un nouvel onglet. Reviens ici ensuite pour marquer l’envoi." }}
            </p>
            <div
              ref="attachRow"
              class="apply-attach"
            >
              <span
                v-if="!phone"
                class="apply-attach-label"
              >À joindre</span>
              <PrepCertificates>
                <a
                  v-if="currentLetterId"
                  :href="pdfHref(`/api/letters/${currentLetterId}/pdf`, template)"
                  download
                  data-test="sheet-letter"
                ><AppIcon name="file" />Lettre.pdf<AppIcon
                  v-if="!phone"
                  name="download"
                /></a>
                <a
                  v-if="currentCvId"
                  :href="pdfHref(`/api/cvs/${currentCvId}/pdf`, template)"
                  download
                  data-test="sheet-cv"
                ><AppIcon name="file" />CV.pdf<AppIcon
                  v-if="!phone"
                  name="download"
                /></a>
              </PrepCertificates>
              <button
                v-if="!phone && currentLetterId && currentCvId"
                type="button"
                class="apply-all"
                data-test="download-all"
                @click="downloadAll"
              >
                <AppIcon name="download" />Tout télécharger
              </button>
            </div>
            <p
              v-if="phone && templateNote"
              class="apply-where-text apply-template-note"
              data-test="apply-template-note"
            >
              {{ templateNote }}
            </p>
            <div
              v-if="!phone"
              class="apply-go"
            >
              <ApplyActions
                :link="applyLink"
                :opened="opened"
                :busy="applyBusy"
                :error="applyError"
                @open="opened = true"
                @mark="markApplied"
              />
            </div>
          </section>
          <section
            :class="phone ? 'doc-card apply-copy' : 'apply-card apply-copy-desk'"
            aria-labelledby="apply-copy-title"
            data-test="apply-sheet"
          >
            <h2 id="apply-copy-title">
              À recopier sur le formulaire
            </h2>
            <p
              v-if="!phone"
              class="apply-where-text"
            >
              Le bouton copie la valeur, tu la colles dans le formulaire.
            </p>
            <FormSheet :letter-text="currentLetterText" />
          </section>
          <RouterLink
            v-if="phone && offer.company"
            :to="`/candidatures/offres/${offer.id}#contacts`"
            class="apply-contact"
            data-test="find-contact"
          >
            <span>Trouver un contact chez {{ offer.company }}</span><AppIcon name="chevron" />
          </RouterLink>
          <!-- La barre du bas (C6, C8) : d'abord le formulaire ; une fois ouvert, « J'ai postulé ». -->
          <ActionBar
            v-if="phone"
            class="prep-bar apply-actions"
          >
            <ApplyActions
              :link="applyLink"
              :opened="opened"
              :busy="applyBusy"
              :error="applyError"
              @open="opened = true"
              @mark="markApplied"
            />
          </ActionBar>
        </div>
        <aside
          v-if="!phone"
          class="prep-side prep-aside"
          data-test="apply-aside"
        >
          <section
            class="side-card apply-company"
            aria-labelledby="apply-company-title"
            data-test="apply-company"
          >
            <p
              id="apply-company-title"
              class="apply-cap"
            >
              Entreprise
            </p>
            <dl class="apply-facts">
              <div>
                <dt>Nom</dt>
                <dd :class="{ 'apply-empty': !offer.company }">
                  {{ offer.company || "Non renseigné" }}
                </dd>
              </div>
              <div>
                <dt>Adresse</dt>
                <dd
                  v-if="addressLines.length"
                  data-test="apply-address"
                >
                  <span
                    v-for="line in addressLines"
                    :key="line"
                  >{{ line }}</span>
                </dd>
                <dd
                  v-else
                  class="apply-empty"
                >
                  Non renseignée
                </dd>
                <dd
                  v-if="addressLines.length"
                  class="apply-source"
                >
                  {{ ADDRESS_FROM[offer.company_address_source ?? "manual"] }}
                </dd>
              </div>
              <div v-if="siteHost">
                <dt>Site</dt>
                <dd>
                  <a
                    :href="offer.employer_url ?? ''"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="apply-site"
                    data-test="apply-site"
                  >{{ siteHost }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
                </dd>
              </div>
            </dl>
            <button
              v-if="offer.company"
              type="button"
              class="prep-file-row"
              aria-haspopup="dialog"
              data-test="contacts-open"
              @click="contactsOpen = true"
            >
              <span class="prep-file-text">
                <b>Contacts{{ contactsCount ? ` · ${contactsCount}` : "" }}</b>
                <span class="prep-file-sub">{{ contactsCount ? "Voir à qui écrire" : `Trouver un contact chez ${offer.company}` }}</span>
              </span>
              <AppIcon name="chevron" />
            </button>
          </section>
          <section
            v-if="offer.status !== 'applied'"
            class="side-card apply-after"
            data-test="apply-after"
          >
            <p class="apply-cap">
              Après l’envoi
            </p>
            <p class="apply-after-text">
              Marque l’envoi : jobA1 prépare la déclaration ORP et te rappelle de relancer dans 7 jours.
            </p>
          </section>
        </aside>
        <BottomSheet
          v-if="!phone && offer.company"
          :open="contactsOpen"
          :title="`Contacts chez ${offer.company}`"
          data-test="contacts-sheet"
          @close="contactsOpen = false"
        >
          <ContactsPanel
            :key="offer.id"
            :offer-id="offer.id"
            @count="contactsCount = $event"
          />
        </BottomSheet>
      </div>

      <CvPanel
        v-else-if="offer && tab === 'cv'"
        :offer="offer"
        :primary="nextStep === 'cv'"
        :preparing="cvState === 'busy'"
        :failed="cvState === 'failed'"
        :letter-language="current(letters)?.language ?? null"
        @current="currentCvId = $event"
      />

      <div
        v-else-if="offer"
        :class="['prep-layout', { 'prep-desk': !phone }]"
      >
        <div class="prep-main">
          <p
            v-if="error && (phone || !letterFailed || !!selected || !GENERIC_FAILURES.has(error))"
            class="notice error"
            role="alert"
          >
            {{ error }}
          </p>
          <p
            v-if="phone && noProfile && !selected"
            class="notice"
            role="alert"
            data-test="no-profile-note"
          >
            {{ NO_PROFILE_TEXT }}
          </p>
          <p
            v-if="doc && doc.missing_identity.length"
            class="notice"
            data-test="missing-identity"
          >
            En-tête incomplet ({{ doc.missing_identity.join(", ") }}) :
            <RouterLink to="/profil?onglet=coordonnees">complète tes coordonnées</RouterLink>.
          </p>

          <!-- La carte de la lettre (maquette Preparer, étape 7b) : le titre et la langue en tête (C3 : choisir
               ne rédige rien, le bouton du bas le propose), la lettre entière et modifiable (C4), « Modifier le
               texte » qui ouvre la consigne, puis « J’ai relu la lettre » (C11). -->
          <section
            class="doc-card"
            aria-labelledby="letter-card-title"
            data-test="letter-card"
          >
            <!-- Téléphone (§9) : « Moderne · Français » sous le titre et « Changer », qui ouvre la feuille ; plus de
                 FR / DE / EN sur l’écran. Sur ordinateur, FR / DE / EN reste en haut du document. -->
            <LayoutSheetLink
              v-if="phone"
              v-model="shownLanguage"
              title="Lettre de motivation"
              title-id="letter-card-title"
              :name="doc?.sender[0]"
              :options="SHEET_LANGUAGE_OPTIONS"
              language-label="Langue de la lettre"
            />
            <div
              v-else
              class="doc-card-head"
            >
              <h2 id="letter-card-title">
                Lettre de motivation
              </h2>
              <SegmentedControl
                v-if="!claim"
                v-model="shownLanguage"
                :options="LANGUAGE_OPTIONS"
                label="Langue de la lettre"
                class="doc-language"
              />
            </div>
            <!-- Sur téléphone, pas encore de lettre : l'aperçu vide du modèle ; « Rédiger la lettre » est en bas. -->
            <DocPreview
              v-if="phone && !selected && !writing"
              :template="template"
              :name="previewName"
              :sub="previewSub"
              :paragraphs="[]"
              label="Aperçu vide de la lettre"
              class="doc-preview-tall"
              data-test="no-letter"
            />
            <div
              v-else-if="!selected && !writing"
              class="prep-empty-page"
              data-test="no-letter"
            >
              <!-- Pas encore de lettre (§2.2) : la page A4 en lignes grisées, et au centre la carte avec le bouton plein,
                   visible sans défiler. -->
              <div
                class="prep-empty-sheet"
                aria-hidden="true"
              >
                <i
                  v-for="(w, i) in [45, 96, 92, 94, 60, 0, 95, 90, 93, 88, 40, 0, 70]"
                  :key="i"
                  :style="{ width: `${w}%` }"
                />
              </div>
              <div
                class="prep-empty-card"
                :role="letterFailed || noProfile ? 'alert' : undefined"
                :data-test="noProfile ? 'no-profile' : letterFailed ? 'letter-failed' : undefined"
              >
                <p class="prep-empty-title">
                  {{ noProfile ? "Il manque ton profil" : letterFailed ? "La lettre n’a pas pu être écrite" : "Pas encore de lettre pour cette offre" }}
                </p>
                <p class="prep-empty-text">
                  {{ noProfile ? NO_PROFILE_TEXT : letterFailed || "jobA1 l’écrit avec ton CV et l’annonce, dans le modèle choisi. Tu la relis avant qu’elle parte." }}
                </p>
                <button
                  v-if="noProfile"
                  type="button"
                  class="primary"
                  data-test="no-profile-link"
                  @click="completion = 'profile'"
                >
                  Ajouter une expérience
                </button>
                <PlanLimit
                  v-if="!noProfile"
                  usage="letter"
                />
                <BusyButton
                  v-if="!noProfile"
                  class="primary"
                  :busy="writing"
                  busy-label="Rédaction…"
                  :disabled="reached('letter')"
                  data-test="write"
                  @click="write()"
                >
                  <span v-if="letterFailed">Réessayer</span>
                  <HoverNote
                    v-else
                    :text="writing ? '' : aiNote('Environ 0,10 $.', 'letter')"
                  >
                    <span class="with-icon"><AppIcon name="ai" />{{ writeLabel === "Rédiger la lettre" ? "Générer la lettre" : writeLabel }}</span>
                  </HoverNote>
                </BusyButton>
                <RouterLink
                  :to="{ path: '/tes-donnees', hash: '#ia' }"
                  class="prep-ai-link"
                  data-test="prep-ai-link"
                >
                  Ce qui part à l’IA<AppIcon name="chevron" />
                </RouterLink>
              </div>
            </div>
            <!-- Pendant l'écriture, sur ordinateur (§7.1, PreparerOrdinateurGeneration) : le bandeau bleu en haut du
                 document, puis la page A4 du modèle en lignes grisées. -->
            <div
              v-else-if="writing && !selected && !phone"
              class="prep-writing"
              data-test="letter-writing"
            >
              <p
                class="prep-writing-band"
                role="status"
              >
                <span
                  class="prep-spin"
                  aria-hidden="true"
                />
                <span>{{ phase === "review" ? "Je relis ta lettre…" : "J’écris ta lettre… environ 20 secondes" }}</span>
                <span
                  v-if="cvState === 'busy'"
                  class="prep-writing-cv"
                >Le CV adapté se prépare en même temps</span>
              </p>
              <div class="prep-empty-page">
                <div
                  class="prep-empty-sheet"
                  aria-hidden="true"
                >
                  <i
                    v-for="(w, i) in [45, 96, 92, 94, 60, 0, 95, 90, 93, 88, 40, 0, 70]"
                    :key="i"
                    :style="{ width: `${w}%` }"
                  />
                </div>
              </div>
            </div>
            <AiWriting
              v-else-if="writing && !selected"
              kind="letter"
            />

            <!-- La consigne entière de la version affichée : au toucher il n'y a pas de survol. -->
            <p
              v-if="phone && selected?.instruction"
              class="hint version-instruction screen-only"
              data-test="version-instruction"
            >
              Consigne : {{ selected.instruction }}
            </p>
            <DocPreview
              v-if="phone && doc && draft && !letterOpen"
              :template="template"
              :name="previewName"
              :sub="previewSub"
              :paragraphs="previewParagraphs"
              label="Ouvrir la lettre entière pour la modifier"
              :class="['doc-preview-tall', { 'doc-preview-composing': composing }]"
              @open="letterOpen = true"
            />
            <!-- Retoucher (§9) : la zone de saisie juste sous l'aperçu ; les puces au-dessus seulement avec le focus,
                 plus de libellé « Retoucher la lettre ». Pas de « + » ni de micro : la question de la PR 577 reste
                 ouverte (envoi de fichiers à l’IA, service de dictée). -->
            <div
              v-if="phone && selected && !claim"
              class="prep-revise"
              data-test="prep-revise"
              @focusin="composing = true"
              @focusout="leaveComposer"
            >
              <SuggestionChips
                v-if="composing"
                :items="suggestions"
                label="Retouches proposées"
                @mousedown.prevent
                @pick="revise"
              />
              <Composer
                v-model="revision"
                placeholder="Que changer ?"
                send-label="Envoyer la demande"
                :busy="writing"
                @send="revise"
              />
              <p
                v-if="instructionNote"
                class="hint"
                aria-live="polite"
                data-test="instruction-note"
              >
                {{ instructionNote }}
              </p>
            </div>
            <article
              v-if="doc && draft && (!phone || letterOpen)"
              class="letter-sheet print-sheet"
              :class="{ 'fresh-lines': fresh, busy: writing }"
              :lang="doc.language"
              data-test="letter"
            >
              <div class="letter-sender">
                <span
                  v-for="line in doc.sender"
                  :key="line"
                >{{ line }}</span>
              </div>
              <div class="letter-recipient">
                <span
                  v-for="line in doc.recipient"
                  :key="line"
                >{{ line }}</span>
              </div>
              <p class="letter-date">
                {{ doc.place_date }}
              </p>
              <p class="letter-subject">
                <span v-if="subjectPrefix.trim()">{{ subjectPrefix.trim() }}</span>
                <input
                  v-model="draft.subject"
                  class="screen-only subject-wide"
                  aria-label="Objet de la lettre"
                  data-test="subject"
                  @input="edited"
                >
                <!-- Sur téléphone, l'objet passe à la ligne (docs/51 n° 2). -->
                <textarea
                  v-model="draft.subject"
                  class="screen-only subject-phone"
                  rows="1"
                  aria-label="Objet de la lettre"
                  data-test="subject-phone"
                  @input="onInput"
                  @keydown.enter.prevent
                />
                <span class="print-only">{{ draft.subject }}</span>
              </p>
              <p>{{ doc.salutation }}</p>
              <p
                v-if="pageEnd?.after === -1"
                class="page-end screen-only"
                data-test="page-end"
              >
                {{ pageEnd.text }}
              </p>
              <div
                v-for="(paragraph, index) in draft.paragraphs"
                :key="index"
                class="letter-paragraph"
              >
                <textarea
                  v-model="paragraph.text"
                  :class="['screen-only', { 'claim-flash': flashed === index }]"
                  rows="3"
                  :aria-label="`Paragraphe ${index + 1}`"
                  data-test="paragraph"
                  @input="onInput"
                  @select="onSelect(index, $event)"
                  @mouseup="onSelect(index, $event)"
                  @keyup="onSelect(index, $event)"
                  @click="phone && onSelect(index, $event)"
                />
                <button
                  v-if="!phone && claim?.index === index"
                  type="button"
                  class="secondary small false-claim-button screen-only"
                  data-test="false-claim"
                  @mousedown.prevent
                  @click="claimOpen = true"
                >
                  Pas vrai
                </button>
                <p class="print-only">
                  {{ paragraph.text }}
                </p>
                <span
                  v-if="sources(paragraph.chunk_ids)"
                  class="chunk-refs screen-only"
                >Blocs : {{ sources(paragraph.chunk_ids) }}</span>
                <p
                  v-if="pageEnd && pageEnd.after === index"
                  class="page-end screen-only"
                  data-test="page-end"
                >
                  {{ pageEnd.text }}
                </p>
              </div>
              <p>{{ doc.closing }}</p>
              <p class="letter-signature">
                {{ doc.signature }}
              </p>
              <p class="letter-enclosure">
                {{ doc.enclosure }}
              </p>
            </article>
            <!-- La relecture (décision de Kevin) : une ligne, puis le détail repliable, un critère par
               ligne avec sa pastille (« Réussi » ou « À revoir », jamais le ton erreur). -->
            <!-- Sur ordinateur, la relecture est dans la carte « Ta candidature » (§2.2) ; la ligne reste pour les lecteurs
                 d’écran. -->
            <p
              :class="['review-line', { 'visually-hidden': !phone }]"
              aria-live="polite"
              data-test="review-line"
            >
              {{ reviewLine }}
            </p>
            <p
              v-if="phone && pageLine && page && !page.fits"
              class="page-line"
              aria-live="polite"
              data-test="page-line"
            >
              <span>{{ pageLine }}</span>
              <button
                v-if="page && !page.fits"
                type="button"
                class="link"
                data-test="shorten"
                :aria-disabled="writing ? 'true' : undefined"
                @click="!writing && shorten()"
              >
                Raccourcir
              </button>
            </p>
            <DisclosureRow
              v-if="phone && selected?.review"
              title="Détail de la relecture"
              :value="selected.review.corrected ? 'corrigée une fois' : ''"
              class="review-detail"
              data-test="review-detail"
            >
              <ul class="review-criteria">
                <li
                  v-for="criterion in selected.review.criteria"
                  :key="criterion.key"
                  :data-test="`review-${criterion.key}`"
                >
                  <span class="review-criterion-text">
                    <strong>{{ criterion.label }}</strong>
                    <span class="hint">{{ criterion.reason }}</span>
                  </span>
                  <StatusPill :tone="criterion.ok ? 'ok' : 'todo'">
                    {{ criterion.ok ? "Réussi" : "À revoir" }}
                  </StatusPill>
                </li>
              </ul>
            </DisclosureRow>
          </section>
          <!-- Retoucher, sur ordinateur (§2.2) : les puces et la zone de saisie collées en bas de la colonne gauche ; pas de
               « + » (on modifie, on ne joint rien). -->
          <div
            v-if="!phone && (selected || writing) && !claim"
            :class="['prep-desk-bottom', { 'prep-desk-bottom-off': !selected }]"
            :inert="!selected"
            data-test="prep-desk-bottom"
          >
            <div
              class="prep-revise"
              data-test="prep-revise"
            >
              <SuggestionChips
                :items="suggestions"
                label="Retouches proposées"
                @pick="revise"
              />
              <Composer
                v-model="revision"
                :placeholder="selected ? 'Demander une modification de la lettre' : 'Tu pourras retoucher la lettre dès qu’elle est écrite'"
                send-label="Envoyer la demande"
                :busy="writing"
                @send="revise"
              />
              <p
                v-if="instructionNote"
                class="hint"
                aria-live="polite"
                data-test="instruction-note"
              >
                {{ instructionNote }}
              </p>
            </div>
          </div>
        </div>

        <!-- Colonne de droite sur ordinateur (MODIFICATIONS du 9 novembre, §2.2 et §7.2 ; maquette PreparerOrdinateur) :
             la mise en page, la carte « Ta candidature » (Relecture, Versions, CV adapté, chaque ligne ouvre un panneau
             ou l’étape), puis le seul bouton plein. Elle reste en place quand la page défile. -->
        <aside
          v-if="!phone"
          class="prep-side prep-aside"
          data-test="prep-aside"
        >
          <LayoutCard :note="layoutNote">
            <button
              v-if="page && !page.fits && !dirty"
              type="button"
              class="link"
              data-test="shorten"
              :aria-disabled="writing ? 'true' : undefined"
              @click="!writing && shorten()"
            >
              Raccourcir
            </button>
          </LayoutCard>
          <section
            v-if="selected || writing"
            class="side-card prep-file"
            aria-labelledby="prep-file-title"
            data-test="prep-file"
          >
            <h2 id="prep-file-title">
              Ta candidature
            </h2>
            <!-- Pendant l'écriture (§7.1) : la lettre « En cours d’écriture », avec l'indicateur qui tourne. -->
            <div
              v-if="!selected"
              class="prep-file-row prep-file-busy"
              data-test="letter-row"
            >
              <span class="prep-file-text">
                <b>Lettre</b>
                <span class="prep-file-sub busy">En cours d’écriture</span>
              </span>
              <span
                class="prep-spin"
                aria-hidden="true"
              />
            </div>
            <button
              v-if="selected?.review"
              type="button"
              class="prep-file-row"
              aria-haspopup="dialog"
              data-test="review-open"
              @click="reviewOpen = true"
            >
              <span class="prep-file-text">
                <b>Relecture</b>
                <span :class="['prep-file-sub', reviewSummary.tone]">{{ reviewSummary.text }}</span>
              </span>
              <AppIcon name="chevron" />
            </button>
            <button
              v-if="selected"
              type="button"
              class="prep-file-row"
              aria-haspopup="dialog"
              data-test="versions-open"
              @click="versionsOpen = true"
            >
              <span class="prep-file-text">
                <b>Versions · {{ letters.length }}</b>
                <span class="prep-file-sub">Actuelle : {{ currentVersionLine }}</span>
              </span>
              <AppIcon name="chevron" />
            </button>
            <button
              type="button"
              class="prep-file-row"
              data-test="cv-row"
              @click="router.push({ query: { doc: 'cv' } })"
            >
              <span class="prep-file-text">
                <b>CV adapté</b>
                <span :class="['prep-file-sub', cvRow.tone]">{{ cvRow.text }}</span>
              </span>
              <span
                v-if="cvRow.tone === 'busy'"
                class="prep-spin"
                aria-hidden="true"
              />
              <AppIcon
                v-else
                name="chevron"
              />
            </button>
          </section>
          <InlineConfirm
            v-if="choosingWrite"
            message="Tu as des modifications non enregistrées dans cette version."
            confirm-label="Enregistrer, puis rédiger"
            alt-label="Rédiger sans enregistrer"
            cancel-label="Garder"
            :danger="false"
            :busy="writing"
            @confirm="saveThenWrite"
            @alt="write(true)"
            @cancel="choosingWrite = false"
          />
          <!-- Des corrections à la main : les enregistrer avant de télécharger ou de passer à la suite. -->
          <button
            v-if="selected && dirty"
            type="button"
            class="secondary prep-aside-main"
            :disabled="saving"
            data-test="save-letter"
            @click="save"
          >
            Enregistrer mes modifications
          </button>
          <template v-if="selected && !claim">
            <PlanLimit
              v-if="writeLabel"
              usage="letter"
            />
            <!-- Une langue choisie ou une consigne écrite change le bouton en « Rédiger… » (C3) ; sinon la relecture. -->
            <BusyButton
              v-if="writeLabel || writing"
              class="primary prep-aside-main"
              :busy="writing"
              :busy-label="phase === 'review' ? 'Relecture…' : 'Rédaction…'"
              :disabled="reached('letter')"
              data-test="write"
              @click="write()"
            >
              <span class="with-icon"><AppIcon name="ai" />{{ writeLabel }}</span>
            </BusyButton>
            <button
              v-else
              type="button"
              class="primary prep-aside-main"
              :disabled="readBusy"
              data-test="letter-read"
              @click="readThenNext"
            >
              J’ai relu, continuer
            </button>
          </template>
          <!-- Pendant l'écriture (§7.1) : le bouton attend la lettre. -->
          <button
            v-else-if="writing && !claim"
            type="button"
            class="primary prep-aside-main"
            disabled
            data-test="letter-read"
          >
            J’ai relu, continuer
          </button>
        </aside>
        <!-- La barre du bas du téléphone (C6) : un seul bouton plein, la prochaine chose à faire. Une langue
             choisie ou une consigne écrite le change en « Rédiger… » (C3) : rien ne part sans cet appui. -->
        <ActionBar
          v-if="phone"
          class="prep-bar"
        >
          <InlineConfirm
            v-if="choosingWrite"
            message="Tu as des modifications non enregistrées dans cette version."
            confirm-label="Enregistrer, puis rédiger"
            alt-label="Rédiger sans enregistrer"
            cancel-label="Garder"
            :danger="false"
            :busy="writing"
            @confirm="saveThenWrite"
            @alt="write(true)"
            @cancel="choosingWrite = false"
          />
          <PlanLimit
            v-if="writeLabel"
            usage="letter"
          />
          <template v-if="claim">
            <p
              class="action-bar-note false-claim-chosen"
              data-test="false-claim-chosen"
            >
              « {{ claim.sentence }} »
            </p>
            <div class="action-bar-row">
              <button
                type="button"
                class="secondary"
                data-test="false-claim-cancel"
                @click="clearClaim"
              >
                Annuler
              </button>
              <button
                type="button"
                class="primary"
                data-test="false-claim-open"
                @click="claimOpen = true"
              >
                Pas vrai
              </button>
            </div>
          </template>
          <button
            v-else-if="noProfile && !selected"
            type="button"
            class="primary prep-bar-main"
            data-test="no-profile-link"
            @click="completion = 'profile'"
          >
            Ajouter une expérience
          </button>
          <BusyButton
            v-else-if="writeLabel || writing"
            class="primary prep-bar-main"
            :busy="writing"
            :busy-label="phase === 'review' ? 'Relecture…' : 'Rédaction…'"
            :disabled="reached('letter')"
            data-test="write"
            @click="write()"
          >
            <span class="with-icon"><AppIcon name="ai" />{{ writeLabel }}</span>
          </BusyButton>
          <!-- Plus de case « J'ai relu la lettre » (§9) : un seul bouton, qui note la relecture puis passe au CV. -->
          <button
            v-else-if="selected"
            type="button"
            class="primary prep-bar-main"
            :disabled="readBusy"
            data-test="next-step"
            @click="readThenNext"
          >
            J’ai relu, continuer
          </button>
        </ActionBar>
        <BottomSheet
          v-if="selected"
          :open="versionsOpen"
          title="Versions et téléchargement"
          data-test="versions-sheet"
          @close="versionsOpen = false"
        >
          <GroupedList
            title="Versions"
            :level="3"
            class="versions"
          >
            <GroupedRow
              v-for="letter in letters"
              :key="letter.id"
              :title="versionName(letter)"
              :description="versionDescription(letter)"
              button
              :current="letter.id === selectedId"
              data-test="sheet-version"
              @click="pickVersion(letter)"
            />
          </GroupedList>
          <p
            v-if="dirty"
            class="hint"
          >
            Enregistre d’abord tes modifications pour les télécharger.
          </p>
          <template #actions>
            <button
              v-if="dirty"
              type="button"
              class="primary"
              :disabled="saving"
              data-test="save-letter"
              @click="save"
            >
              Enregistrer mes modifications
            </button>
            <template v-else>
              <a
                class="button-link prep-download"
                :href="pdfHref(`/api/letters/${selected.id}/pdf`, template)"
                download
                data-test="pdf"
              ><span class="with-icon"><AppIcon name="download" />Lettre (PDF)</span></a>
              <a
                class="button-link prep-download"
                :href="pdfHref(`/api/letters/${selected.id}/docx`, template)"
                download
                data-test="docx"
              ><span class="with-icon"><AppIcon name="download" />Lettre (Word)</span></a>
            </template>
          </template>
        </BottomSheet>
        <!-- Le panneau Relecture (§2.2, maquette PreparerOrdinateurRelecture) : le résultat, puis chaque critère, son
             libellé au-dessus de ce que la relecture a vu, avec un cercle de 24 px (coche verte ou point à renforcer). -->
        <BottomSheet
          v-if="!phone && selected?.review"
          :open="reviewOpen"
          title="Relecture"
          data-test="review-sheet"
          @close="reviewOpen = false"
        >
          <div class="review-sum">
            <b :class="reviewSummary.tone">{{ reviewSummary.text }}</b>
            <span>Relue {{ dateWithTime(selected.created_at) }}{{ selected.review.corrected ? ", corrigée une fois" : "" }}</span>
          </div>
          <section
            v-for="group in reviewGroups"
            :key="group.key"
            class="review-group"
          >
            <h3>{{ group.title }} · {{ group.items.length }}</h3>
            <ul>
              <li
                v-for="criterion in group.items"
                :key="criterion.key"
                :data-test="`review-${criterion.key}`"
              >
                <AppIcon
                  :name="group.ok ? 'check-circle' : 'alert-circle'"
                  :class="group.ok ? 'ok' : 'todo'"
                />
                <span>
                  <span class="review-k">{{ criterion.label }}</span>
                  <span class="review-v">{{ criterion.reason }}</span>
                </span>
              </li>
            </ul>
          </section>
        </BottomSheet>
      </div>
    </div>
  </section>

  <OfferCompatSheet
    v-if="offer && !phone && verdict"
    :open="compatOpen"
    :score="offer.score ?? null"
    :stale="offer.score_stale"
    :verdict="MATCH_TITLE[verdict.tone] ?? ''"
    :tone="verdict.tone"
    :subtitle="`${offer.title} · ${offer.company ?? 'Entreprise non indiquée'}`"
    :strengths="compat.strengths"
    :gaps="compat.gaps"
    :how="compat.how"
    @close="compatOpen = false"
  />
  <FalseClaimSheet
    v-if="selected && claim"
    :open="claimOpen"
    :sentence="claim?.sentence ?? ''"
    :busy="claimBusy"
    :error="claimError"
    :only-sentence="onlySentence"
    @close="claimOpen = false; claimError = ''"
    @confirm="confirmClaim"
  />
  <ProfileCompletionPanel
    :open="!!completion"
    :title="completion === 'identity' ? 'Avant ta lettre' : 'Ajouter une expérience'"
    :sections="completion ? [...COMPLETION_SECTIONS[completion]] : undefined"
    @close="completionClosed"
    @saved="completionSaved"
  />
</template>

<style>
/* Conteneur de 1280 (D18), 24 de marge entre 821 et 1327 px. */
.prep-desk-head.container, .prep-desk-band > .container { --prep-max: 1280px; max-width: calc(var(--prep-max) + 2 * var(--space-6)); }
/* Préparer sur ordinateur (MODIFICATIONS du 8 novembre au soir, lot 15.1 ; captures PreparerOrdinateur et
   --colonne-bas) : en-tête de 64 px, grille 1fr + 360 à 24 d’écart, colonne de droite qui défile seule, cartes de
   20/24, lettre sur --surface-muted, bas de page en grille qui reste en bas de l’écran. */
.prep-desk-head { --prep-22: 22px; --prep-20: 20px; --prep-32: 32px; --prep-44: 44px; --prep-48: 48px; --prep-64: 64px; --prep-24: 24px; display: flex; align-items: center; gap: var(--prep-20); min-height: var(--prep-64); padding-top: var(--space-4); padding-bottom: var(--space-2); }
.prep-desk-back { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--prep-44); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; white-space: nowrap; }
.prep-desk-back:hover { text-decoration: underline; }
.prep-desk-back .icon { width: 18px; height: 18px; }
.prep-desk-rule { flex: none; width: 1px; height: var(--prep-32); background: var(--line); }
.prep-desk-head > .logo { flex: none; width: var(--prep-44); height: var(--prep-44); }
.prep-desk-title { flex: 1; min-width: 0; }
.prep-desk-title h1 { margin: 0; font-size: var(--prep-24); font-weight: var(--weight-heavy); line-height: var(--leading-tight); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.prep-desk-title p { margin: 0; font-size: var(--font-label); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
/* La note (§2.2) : anneau de 48, 12 px, puis le verdict 15/20 700 et, 6 px dessous, « Voir la compatibilité » 14/20 700
   (ici 4 px et une ligne de 22, même hauteur, grille de 4). */
.prep-desk-score { flex: none; display: flex; align-items: center; gap: var(--space-3); min-height: var(--prep-48); padding: 0; border: 0; background: transparent; color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.prep-desk-score .score-ring { width: var(--prep-48); height: var(--prep-48); }
.prep-desk-score-text { display: flex; flex-direction: column; align-items: flex-start; gap: var(--space-1); line-height: var(--space-5); }
.prep-desk-compat { display: inline-flex; align-items: center; gap: var(--space-1); line-height: var(--prep-22); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--primary-text); }
.prep-desk-compat .icon { width: 14px; height: 14px; }
.prep-desk-score:hover .prep-desk-compat { text-decoration: underline; }
.prep-verdict { font-size: var(--font-label); font-weight: var(--weight-bold); }
.prep-verdict:is(.very-close, .close) { color: var(--success); }
.prep-verdict.dig { color: var(--score-dig); }
.prep-verdict.far { color: var(--neutral); }
.prep-desk-head > .step-tabs { flex: none; width: auto; }

.prep-layout.prep-desk { --prep-360: 360px; --prep-24: 24px; --prep-20: 20px; --prep-28: 28px; --prep-52: 52px; --prep-48: 48px; --prep-sheet: 520px; --prep-bottom: 150px; --prep-side-top: 5.5rem; grid-template-columns: minmax(0, 1fr) var(--prep-360); gap: var(--prep-24); }
/* Une seule zone défile, la page (§1) : la colonne de droite reste en place, sans défilement à elle. */
.prep-desk .prep-side { gap: var(--space-4); }
.prep-desk .side-card { gap: var(--space-1); padding: var(--prep-20) var(--prep-24); }
.prep-desk .offer-brief-group h3 { margin-top: var(--space-4); }
.prep-desk .side-card > h2 { font-size: var(--font-title); font-weight: var(--weight-bold); }
.prep-desk .doc-card { gap: 0; padding: 0; overflow: hidden; background: var(--surface-muted); }
.prep-desk .doc-card-head { padding: var(--prep-20) var(--prep-24); background: var(--surface); border-bottom: 1px solid var(--line-soft); }
.prep-desk .doc-card-head h2 { font-size: var(--font-title); }
.prep-desk .doc-card > :not(.doc-card-head, .letter-sheet, .cv-sheet, .prep-writing, .prep-empty-page) { margin-left: var(--prep-24); margin-right: var(--prep-24); }
.prep-desk .doc-card > .letter-sheet { width: min(var(--prep-sheet), calc(100% - 2 * var(--prep-24))); margin: var(--prep-28) auto; border: 0; }
.prep-desk .doc-card > .review-line:empty { display: none; }
/* Le CV prêt (§14, PreparerOrdinateurCVPret) : une page A4 de 560 px sur le fond grisé, à 32 px du haut et 40 du bas ;
   nom 20/800, titre 12/700 bleu, coordonnées 10,5, rubriques 10 en capitales bleues soulignées, texte 10,5/15. */
.prep-desk .doc-card > .cv-sheet {
  --cv-page: 560px; --cv-pad: 56px; --cv-32: 32px; --cv-40: 40px; --cv-20: 20px; --cv-12: 12px; --cv-10-5: 10.5px; --cv-10: 10px; --cv-11-5: 11.5px; --cv-15: 15px;
  /* La page reste blanche en sombre : ses couleurs sont celles du papier (maquette), pas celles du thème. */
  --cv-accent: #2445C2; --cv-rule: #E5E2D9; --cv-muted: #596070; --cv-ink: #1B1F2A;
  color: var(--cv-ink);
  width: min(var(--cv-page), calc(100% - 2 * var(--prep-24))); max-width: none; margin: var(--cv-32) auto var(--cv-40); padding: var(--cv-pad); box-sizing: border-box;
  border: 0; border-radius: 0; background: var(--logo-paper); font-size: var(--cv-10-5); line-height: var(--cv-15);
}
.prep-desk .cv-sheet .cv-name { font-size: var(--cv-20); font-weight: var(--weight-heavy); line-height: var(--space-6); }
.prep-desk .cv-sheet .cv-headline { font-size: var(--cv-12); font-weight: var(--weight-bold); color: var(--cv-accent); padding: 0; margin: 0; min-height: var(--space-6); }
.prep-desk .cv-sheet .cv-contacts { color: var(--cv-muted); font-size: var(--cv-10-5); margin: 0 0 var(--space-4); }
.prep-desk .cv-sheet h3 { margin: var(--space-4) 0 var(--space-2); padding-bottom: var(--space-1); font-size: var(--cv-10); font-weight: var(--weight-heavy); letter-spacing: .08em; color: var(--cv-accent); border-bottom-color: var(--cv-rule); }
.prep-desk .cv-sheet .cv-item { margin-bottom: var(--space-2); }
.prep-desk .cv-sheet .cv-item-title { font-size: var(--cv-11-5); }
.prep-desk .cv-sheet :is(input, textarea) { min-height: 0; padding: 0; border: 1px dashed transparent; border-radius: var(--space-1); background: transparent; color: inherit; box-shadow: none; }
.prep-desk .cv-sheet .cv-headline { height: var(--space-6); }
.prep-desk .cv-sheet .kw { padding: 0; border: 0; background: none; color: inherit; font-size: inherit; font-weight: var(--weight-bold); }
/* Le panneau « Adapté pour cette offre » (PreparerOrdinateurCVChangements) : la phrase 15/22, puis un bloc par changement
   (16 au-dessus et dessous, trait --line-soft), titre 16/22, « Avant » 14/20 gris, « Maintenant » 14/20, le lien 44 px. */
.cv-changes-intro, .cv-changes { --cv-22: 22px; }
.cv-changes-intro { margin: 0 0 var(--space-2); font-size: var(--font-label); line-height: var(--cv-22); color: var(--text-secondary); }
.cv-changes { list-style: none; margin: 0; padding: 0; }
.cv-changes > li { display: flex; flex-direction: column; align-items: flex-start; padding: var(--space-4) 0; border-top: 1px solid var(--line-soft); }
.cv-changes b { font-size: var(--font-body); line-height: var(--cv-22); }
.cv-change-before { margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.cv-change-now { font-size: var(--font-small); line-height: var(--space-5); color: var(--text); }
.cv-change-undo { min-height: var(--target-min); margin-top: var(--space-1); padding: 0; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); }
.cv-changes-note { margin: var(--space-6) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.prep-ai-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); justify-self: start; color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-bold); text-decoration: none; }
.prep-ai-link:hover { text-decoration: underline; }
.prep-ai-link .icon { width: 14px; height: 14px; }
/* Retoucher (§2.2) : collé en bas de la colonne gauche, 16 au-dessus et 20 dessous, sur un fondu vers le fond. */
.prep-desk-bottom { position: sticky; bottom: 0; z-index: 5; padding: var(--space-4) 0 var(--space-5); background: linear-gradient(transparent, var(--bg) var(--prep-24)); }
.prep-desk-bottom .prep-revise { gap: var(--space-3); }
/* « Ta candidature » (§2.2, §7.2) : titre 18/24 et 12 px dessous ; lignes de 56 px pleine largeur, trait --line au-dessus,
   libellé 15/20 700 et état 14/20 gris (vert « rien à renforcer », pêche « à renforcer »), chevron à droite. */
.prep-desk .prep-file { --prep-15: 15px; --prep-56: 56px; gap: 0; padding-bottom: 0; }
.prep-file > h2 { margin: 0 0 var(--space-3); line-height: var(--prep-24); }
.prep-file-row {
  display: flex; align-items: center; gap: var(--space-4); width: calc(100% + 2 * var(--prep-24)); max-width: none; min-height: var(--prep-56); margin: 0 calc(-1 * var(--prep-24)); padding: var(--space-2) var(--prep-24); box-sizing: border-box;
  border: 0; border-top: 1px solid var(--line); background: transparent; color: var(--text); font: inherit; text-align: left; text-decoration: none; cursor: pointer;
}
.prep-file-row:hover { background: var(--selected-bg); }
.prep-file-row:last-child { border-radius: 0 0 var(--radius-card) var(--radius-card); }
.prep-file-row > .icon { flex: none; width: var(--space-5); height: var(--space-5); color: var(--primary-text); }
.prep-file-text { flex: 1; min-width: 0; }
.prep-file-text b { display: block; font-size: var(--prep-15); line-height: var(--space-5); }
.prep-file-sub { display: block; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.prep-file-sub:is(.ok, .todo) { font-weight: var(--weight-bold); }
.prep-file-sub.ok { color: var(--success); }
.prep-file-sub.todo { color: var(--peach-text); }
.prep-aside-main { display: inline-flex; justify-content: center; width: 100%; min-height: var(--prep-48); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
/* Pas encore de lettre (§2.2) : la page A4 de 560 en lignes grisées, la carte au centre, à 32 px des bords. */
.prep-empty-page { --prep-150: 150px; --prep-56: 56px; --prep-10: 10px; --prep-32: 32px; --prep-22: 22px; --prep-sheet-h: 36rem; --prep-sk: #E5E2D9; position: relative; width: min(var(--prep-sheet), calc(100% - 2 * var(--prep-24))); margin: var(--prep-28) auto; }
.prep-empty-sheet { display: grid; gap: var(--prep-10); min-height: var(--prep-sheet-h); padding: var(--prep-56); background: var(--logo-paper); box-shadow: var(--paper-shadow); }
.prep-empty-sheet i { display: block; height: var(--space-2); border-radius: var(--radius-pill); background: var(--prep-sk); }
/* La page reste blanche en sombre (§12) : ses lignes grisées aussi. */
.prep-empty-card {
  position: absolute; left: var(--prep-32); right: var(--prep-32); top: var(--prep-150); display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--prep-28) var(--prep-24); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); background: var(--surface); box-shadow: var(--shadow-menu); text-align: center;
}
.prep-empty-title { margin: 0; font-size: var(--font-title); line-height: var(--prep-24); font-weight: var(--weight-bold); }
.prep-empty-text { margin: 0; font-size: var(--font-label); line-height: var(--prep-22); color: var(--text-secondary); }
.prep-empty-card .primary { min-height: var(--prep-48); margin-top: var(--space-2); padding: 0 var(--prep-24); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.prep-empty-card .prep-ai-link { justify-self: center; }
/* Postuler sur ordinateur (§2.4, maquette PreparerOrdinateurPostuler) : cartes de 20/24 comme la colonne ; libellé en
   capitales 13/16 700, titre 18/24 8 px dessous, texte 14/20 gris. « À joindre » après un trait, à 16 px : pastilles de 40
   (fichier bleu, nom 15/600, téléchargement), « Tout télécharger » à droite en contour de 40 ; 20 px plus bas le bouton
   plein de 48 et « J’ai déjà postulé » à 20 px. */
.prep-desk .apply-cards { gap: var(--space-4); }
.apply-card { --apply-15: 15px; --apply-22: 22px; --apply-24: 24px; --apply-40: 40px; --apply-48: 48px; --apply-56: 56px; display: grid; gap: 0; min-width: 0; padding: var(--space-5) var(--space-6); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.apply-cap { margin: 0; font-size: var(--label-caps); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.apply-cards .apply-card h2 { margin: 0; font-size: var(--font-title); line-height: var(--apply-24); }
.apply-card > .apply-cap + h2 { margin-top: var(--space-2); }
.apply-card > .apply-where-text { margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); }
.apply-card .apply-attach { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin-top: var(--space-4); padding-top: var(--space-4); border-top: 1px solid var(--line); }
.apply-attach-label { font-size: var(--apply-15); font-weight: var(--weight-bold); }
.apply-card .apply-files { display: flex; flex: 1; flex-wrap: wrap; gap: var(--space-3); }
.apply-card .apply-files > a { min-height: var(--apply-40); font-size: var(--apply-15); border-radius: var(--radius-pill); }
.apply-card .apply-files .icon-download { color: var(--primary-text); }
.apply-card .apply-attach > .hint { order: 1; flex-basis: 100%; margin: 0; }
.apply-all { display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--apply-40); padding: 0 var(--space-4); border: 1.5px solid var(--primary-graphic); border-radius: var(--radius-pill); background: transparent; color: var(--primary-text); font: inherit; font-size: var(--apply-15); font-weight: var(--weight-bold); cursor: pointer; }
.apply-all:hover { background: var(--selected-bg); }
.apply-go { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-5); margin-top: var(--space-5); }
.apply-go > .notice { flex-basis: 100%; margin: 0; }
.apply-go > .prep-bar-main { min-height: var(--apply-48); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.apply-go > :is(.apply-already, .apply-reopen) { min-height: var(--target-min); display: inline-flex; align-items: center; font-weight: var(--weight-bold); }
/* À recopier (§1) : lignes de 56, trait --line, libellé 13/16 gris au-dessus de la valeur 16/22 600 ; copier en cercle de 40
   bordé ; la lettre en texte sur 2 lignes, 15 regular. */
.apply-copy-desk > .apply-where-text { margin-bottom: var(--space-3); }
.apply-copy-desk { padding-bottom: var(--space-1); }
.apply-copy-desk .form-sheet-row { min-height: var(--apply-56); padding: var(--space-1) 0; gap: 0 var(--space-4); border-top-color: var(--line); }
.apply-copy-desk .form-sheet dt { font-size: var(--label-caps); line-height: var(--space-4); }
.apply-copy-desk .form-sheet dd { font-size: var(--font-body); line-height: var(--apply-22); }
.apply-copy-desk .form-sheet dd.form-sheet-long { font-size: var(--apply-15); font-weight: var(--weight-regular); }
.apply-copy-desk .copy-button { width: var(--apply-40); height: var(--apply-40); color: var(--primary-text); }
.apply-copy-desk .form-sheet > .hint { padding: var(--space-3) 0; }
/* Entreprise (§2.4) : libellé 13/16 gris, valeur 16/22 700 à 2 px (ici dans une ligne de 20 + 22), 12 px entre les champs ;
   la source de l’adresse 13/18 grise ; « Contacts · n » en ligne de 56 qui ouvre le panneau. */
.apply-company { --apply-22: 22px; --apply-15: 15px; --apply-56: 56px; --prep-15: 15px; --prep-56: 56px; grid-template-columns: minmax(0, 1fr); padding-bottom: 0; }
.apply-facts { display: grid; gap: var(--space-3); margin: var(--space-3) 0 var(--space-4); }
.apply-facts dt { font-size: var(--label-caps); line-height: var(--space-5); color: var(--text-secondary); }
.apply-facts dd { margin: 0; font-size: var(--font-body); line-height: var(--apply-22); font-weight: var(--weight-bold); overflow-wrap: anywhere; }
.apply-facts dd > span { display: block; }
.apply-facts dd.apply-empty { font-weight: var(--weight-regular); color: var(--text-secondary); }
.apply-facts dd.apply-source { font-size: var(--label-caps); line-height: var(--space-5); font-weight: var(--weight-regular); color: var(--text-secondary); }
.apply-site { display: inline-flex; align-items: center; gap: var(--space-1); color: var(--primary-text); text-decoration: none; }
.apply-site:hover { text-decoration: underline; }
.apply-company > .prep-file-row:last-child { border-radius: 0 0 var(--radius-card) var(--radius-card); }
/* Le panneau des contacts sur ordinateur : chaque lien et bouton texte garde une cible de 24 px (§1, WCAG 2.5.8). */
[data-test=contacts-sheet] .link { display: inline-flex; align-items: center; min-height: var(--space-6); }
.apply-after-text { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text); }
/* Pendant l'écriture (§7.1, PreparerOrdinateurGeneration) : bandeau --selected-bg en haut du document, 15/700 en
   --primary-text, indicateur de 18 px qui tourne (arrêté si prefers-reduced-motion), « Le CV adapté se prépare en même
   temps » à droite en 600 ; puces et saisie grisées. */
.prep-writing-band { display: flex; align-items: center; gap: var(--space-3); margin: 0; padding: var(--space-3) var(--prep-24); background: var(--selected-bg); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.prep-writing-cv { margin-left: auto; font-weight: var(--weight-semibold); color: var(--text-secondary); }
.prep-spin { --prep-18: 18px; flex: none; width: var(--prep-18); height: var(--prep-18); box-sizing: border-box; border: 2.5px solid var(--card-line); border-top-color: var(--primary-graphic); border-radius: var(--radius-pill); animation: prep-spin 1s linear infinite; }
@keyframes prep-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .prep-spin { animation: none; } }
.prep-file-sub.busy { font-weight: var(--weight-bold); color: var(--primary-text); }
.prep-file-busy { cursor: default; }
.prep-file-busy:hover { background: transparent; }
.prep-desk-bottom-off .prep-revise { opacity: .5; }
/* Les versions dans le panneau : 4 px entre le nom et sa ligne (grille de 4). */
.sheet .versions .grouped-text { gap: var(--space-1); }
/* Le panneau Relecture (PreparerOrdinateurRelecture) : résultat 18/24, date 14/20 ; familles en capitales 13/16 ;
   critères en cascade, cercle de 24 puis 16 px, libellé 13/16 gris au-dessus de la valeur 15/20 700. */
.review-sum { display: grid; gap: var(--space-1); padding-bottom: var(--space-5); border-bottom: 1px solid var(--line); }
.review-sum b { font-size: var(--font-title); line-height: var(--space-6); }
.review-sum b.ok { color: var(--success); }
.review-sum b.todo { color: var(--peach-text); }
.review-sum span { font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.review-group { padding-top: var(--space-5); }
.review-group h3 { margin: 0; font-size: var(--label-caps); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.review-group ul { margin: var(--space-2) 0 0; padding: 0; list-style: none; }
.review-group li { display: flex; align-items: flex-start; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--line); }
.review-group li > .icon { flex: none; width: var(--space-6); height: var(--space-6); margin-top: var(--space-2); }
.review-group li > .icon.ok { color: var(--success); }
.review-group li > .icon.todo { color: var(--peach-text); }
.review-k { display: block; font-size: var(--label-caps); line-height: var(--space-4); color: var(--text-secondary); }
.review-v { display: block; margin-top: var(--space-1); font-size: var(--font-label); line-height: var(--space-5); font-weight: var(--weight-bold); }
</style>
