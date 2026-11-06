<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Letter, type LetterLanguage, type Offer, type OrpMonth } from "../api/client";
import CvPanel from "../components/CvPanel.vue";
import DocPreview from "../components/DocPreview.vue";
import TemplatePicker from "../components/TemplatePicker.vue";
import { pdfHref, useDocTemplate } from "../composables/useDocTemplate";
import OfferBrief from "../components/OfferBrief.vue";
import PrepCertificates from "../components/PrepCertificates.vue";
import FormSheet from "../components/FormSheet.vue";
import PageHero from "../components/PageHero.vue";
import ActionBar from "../components/ActionBar.vue";
import AiWriting from "../components/AiWriting.vue";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import BusyButton from "../components/BusyButton.vue";
import FaceState from "../components/FaceState.vue";
import GoalReached from "../components/GoalReached.vue";
import FalseClaimSheet, { type FalseClaimMode } from "../components/FalseClaimSheet.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import FormField from "../components/FormField.vue";
import GroupedList from "../components/GroupedList.vue";
import GroupedRow from "../components/GroupedRow.vue";
import LiquidCircle from "../components/LiquidCircle.vue";
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
import { useJobsMemory } from "../composables/useJobsMemory";
import { dateInSentence, dateWithTime } from "../dates";
import { expiredText, ofMonth } from "../format";
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
const EMPLOYER = { label: "Postuler chez l'employeur", where: "chez l'employeur", reopen: "Rouvrir le site de l'employeur" };
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
  if (link.source === "manual") return { url: link.url, label: "Ouvrir l'annonce", where: "", reopen: "Rouvrir l'annonce" };
  const site = SITE_NAMES[link.source] ?? link.source;
  return { url: link.url, label: `Postuler sur ${site}`, where: `sur ${site}`, reopen: `Rouvrir ${site}` };
});
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
// L'écran « Candidature notée » (C9) : le poste, où, et ce qui reste pour l'objectif ORP du mois.
type Sent = { id: number; company: string; title: string; where: string; month: string; count: number | null; target: number | null };
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
      applyError.value = detail(err, "Enregistrement impossible pour l'instant : réessaie.");
      return;
    }
    useJobsMemory().sent(offerId);
    // Le mois ORP d'abord : s'il atteint l'objectif, « C'est fait ! » s'affiche tout de suite, sans passer par
    // « Candidature notée ».
    const orp = (await api.GET("/api/orp", { params: { query: { month: data.orp_month } } }).catch(() => null))?.data;
    goal.value = orp && firstGoal(data.orp_month, orp.count, orp.target) ? { ...orp, month: data.orp_month } : null;
    sent.value = { id: data.id, company: data.company, title: data.job_title, where: applyLink.value?.where ?? "", month: data.orp_month, count: orp?.count ?? null, target: orp?.target ?? null };
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
  // L'offre revient en préparation : le menu Candidatures y ramène de nouveau.
  useJobsMemory().remember(`/candidatures/offres/${offerId}/preparer?doc=postuler`);
  void offerUndo({
    message: "Candidature retirée : l'offre revient en préparation.",
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
      useJobsMemory().sent(offerId);
    },
  });
}

const orpLine = computed(() => {
  const s = sent.value;
  if (!s || s.count === null) return "";
  if (!s.target) return `${s.count} ${s.count === 1 ? "recherche" : "recherches"} ce mois`;
  const left = s.target - s.count;
  return left > 0 ? `Encore ${left} ${left === 1 ? "recherche" : "recherches"}` : "Objectif atteint";
});

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
// La ligne de l'entreprise (maquette Preparer) : « Alpstack · Lausanne », sans le canton.
function cityOnly(location: string | null | undefined): string {
  return (location || "").replace(/,\s*[A-Z]{2}$/, "");
}
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
const shownLanguage = computed<string>({
  get: () => language.value || selected.value?.document?.language || "",
  set: (value) => {
    language.value = value as LetterLanguage;
  },
});
// Le bouton plein de la barre (C3) : « Rédiger… » quand il y a quelque chose à rédiger, sinon rien
// (« Continuer vers le CV » prend la place).
const LANGUAGE_IN: Record<LetterLanguage, string> = { fr: "français", de: "allemand", en: "anglais" };
const writeLabel = computed(() => {
  const chosen = language.value;
  if (!selected.value) return chosen ? `Rédiger en ${LANGUAGE_IN[chosen]}` : "Rédiger la lettre";
  if (chosen && chosen !== selected.value.language) return `Rédiger à nouveau en ${LANGUAGE_IN[chosen]}`;
  if (instruction.value.trim()) return "Rédiger la nouvelle version";
  return "";
});
// « Modifier le texte » (C4) : la consigne s'ouvre dans la carte (téléphone) ou prend le focus à côté.
const instructionOpen = ref(false);
const instructionEl = ref<HTMLInputElement | null>(null);
function openInstruction(): void {
  if (!phone.value) {
    document.querySelector<HTMLTextAreaElement>(".side-instruction")?.focus();
    return;
  }
  instructionOpen.value = true;
  void nextTick(() => instructionEl.value?.focus());
}
// « J'ai relu la lettre » (C11) : gardé avec la version, pour un autre appareil.
const readBusy = ref(false);
// En cas d'échec (démo, réseau), la case reprend l'état enregistré.
async function markRead(box: HTMLInputElement): Promise<void> {
  const letter = selected.value;
  if (!letter) return;
  readBusy.value = true;
  try {
    const { data } = await api.PUT("/api/letters/{draft_id}/read", { params: { path: { draft_id: letter.id } }, body: { read: box.checked } });
    if (data) letters.value = letters.value.map((l) => (l.id === data.id ? data : l));
    else box.checked = !!letter.read_at;
  } finally {
    readBusy.value = false;
  }
}
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
    useJobsMemory().forget(route.fullPath);
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
  select(current(letters.value));
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
  writing.value = true;
  error.value = "";
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
      else if (!reached("letter")) error.value = detail(err, "La rédaction a échoué, réessaie.");
      return;
    }
    // La relecture avant l'affichage (rédacteur, puis relecteur) : la lettre s'affiche relue.
    phase.value = "review";
    const reviewed = await reviewLetter(data);
    letters.value = [reviewed, ...letters.value];
    instruction.value = "";
    instructionOpen.value = false;
    select(reviewed);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
  } catch {
    error.value = "API injoignable.";
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
      error.value = detail(err, "Enregistrement refusé : l'objet et au moins un paragraphe sont nécessaires.");
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
      message: "Phrase retirée. jobA1 ne l'écrira plus.",
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
      message: "Phrase réécrite d'après ton profil.",
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
  <!-- « Candidature notée » (C9) : un écran entier à la place de la page, comme dans la maquette. -->
  <section
    v-else-if="sent"
    class="band prep-sent"
    data-test="sent-moment"
  >
    <FaceState
      title="Candidature notée"
      heading="h1"
      mood="ravi"
      animation="envoyee"
      role="status"
    >
      <p>{{ sent.title }} chez {{ sent.company }}{{ sent.where ? `, postulée ${sent.where}` : "" }}.</p>
    </FaceState>
    <RouterLink
      v-if="orpLine"
      to="/bilan"
      class="prep-sent-orp"
      data-test="sent-orp"
    >
      <LiquidCircle
        v-if="sent.target"
        :count="sent.count ?? 0"
        :target="sent.target"
        :size="64"
      />
      <span><strong>{{ orpLine }}</strong><span>Objectif ORP {{ ofMonth(sent.month) }}</span></span>
      <AppIcon name="chevron" />
    </RouterLink>
    <div class="prep-sent-actions">
      <RouterLink
        to="/candidatures/offres"
        class="button-link primary-link"
        data-test="next-offer"
      >
        Offre suivante
      </RouterLink>
      <button
        type="button"
        class="link prep-sent-cancel"
        data-test="cancel-applied"
        @click="cancelApplied"
      >
        Je n'ai pas postulé
      </button>
    </div>
  </section>
  <!-- La tête (maquette Preparer, étape 7a) : le retour à l'offre, « Ma candidature », puis l'offre en une
       ligne (logo, poste, « Entreprise · Lieu », l'anneau sans chiffre, D3) et les étapes. -->
  <PageHero
    v-else
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
        <AppIcon name="arrow-left" /><span class="prep-back-text">Retour à l'offre</span>
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
        <span class="prep-offer-sub">{{ [offer.company, cityOnly(offer.location)].filter(Boolean).join(" · ") }}</span>
      </p>
      <ScoreRing
        v-if="offer.score !== null && offer.score !== undefined"
        :score="offer.score"
        :stale="offer.score_stale"
        bare
      />
    </div>
    <StepTabs
      v-if="offer"
      :steps="steps"
      :current="tab"
      label="Étapes de la candidature"
    />
  </PageHero>

  <section
    v-if="!sent"
    class="band"
  >
    <div class="container">
      <!-- Offre introuvable (planche « Illustrations ») : retirée par l'employeur, peut-être. -->
      <FaceState
        v-if="notFound"
        title="Offre introuvable"
        illustration="introuvable"
        data-test="offer-not-found"
      >
        <p>Elle a peut-être été retirée par l'employeur.</p>
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
        {{ expiredText(offer) }} Vérifie avant d'envoyer ta candidature.
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

      <!-- Postuler (C7) : où l'annonce se postule et les pièces, ce qu'on recopie, puis un contact. -->
      <div
        v-if="offer && tab === 'apply'"
        class="prep-layout"
        data-test="apply-steps"
      >
        <div
          v-if="offer.status !== 'applied'"
          class="prep-main apply-cards"
        >
          <section
            class="doc-card"
            aria-labelledby="apply-where-title"
            data-test="apply-where"
          >
            <h2 id="apply-where-title">
              {{ applyLink?.where ? `L'annonce se postule ${applyLink.where}` : "L'annonce" }}
            </h2>
            <p
              v-if="applyLink"
              class="apply-where-text"
            >
              Le formulaire s'ouvre dans un nouvel onglet. Reviens ici ensuite pour marquer l'envoi.
            </p>
            <PrepCertificates>
              <a
                v-if="currentLetterId"
                :href="pdfHref(`/api/letters/${currentLetterId}/pdf`, template)"
                download
                data-test="sheet-letter"
              ><AppIcon name="file" />Lettre.pdf</a>
              <a
                v-if="currentCvId"
                :href="pdfHref(`/api/cvs/${currentCvId}/pdf`, template)"
                download
                data-test="sheet-cv"
              ><AppIcon name="file" />CV.pdf</a>
            </PrepCertificates>
          </section>
          <section
            class="doc-card apply-copy"
            aria-labelledby="apply-copy-title"
            data-test="apply-sheet"
          >
            <h2 id="apply-copy-title">
              À recopier sur le formulaire
            </h2>
            <FormSheet :letter-text="currentLetterText" />
          </section>
          <RouterLink
            v-if="offer.company"
            :to="`/candidatures/offres/${offer.id}#contacts`"
            class="apply-contact"
            data-test="find-contact"
          >
            <span>Trouver un contact chez {{ offer.company }}</span><AppIcon name="chevron" />
          </RouterLink>
          <!-- La barre du bas (C6, C8) : d'abord le formulaire ; une fois ouvert, « J'ai postulé ». -->
          <ActionBar class="prep-bar apply-actions">
            <p
              v-if="applyError"
              class="notice error"
              role="alert"
            >
              {{ applyError }}
            </p>
            <a
              v-if="applyLink && !opened"
              :href="applyLink.url"
              target="_blank"
              rel="noopener noreferrer"
              class="button-link primary-link prep-bar-main"
              data-test="apply"
              @click="opened = true"
            ><span class="with-icon">{{ applyLink.label }}<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span></a>
            <!-- Déjà fait ailleurs (page rechargée, e-mail, téléphone) : sans rouvrir le formulaire. -->
            <BusyButton
              v-if="applyLink && !opened"
              class="link apply-already"
              :busy="applyBusy"
              busy-label="Enregistrement…"
              data-test="already-applied"
              @click="markApplied"
            >
              J'ai déjà postulé
            </BusyButton>
            <template v-else>
              <BusyButton
                class="primary prep-bar-main"
                :busy="applyBusy"
                busy-label="Enregistrement…"
                data-test="mark-applied"
                @click="markApplied"
              >
                J'ai postulé
              </BusyButton>
              <a
                v-if="applyLink"
                :href="applyLink.url"
                target="_blank"
                rel="noopener noreferrer"
                class="link apply-reopen"
                data-test="apply"
              >{{ applyLink.reopen }}<span class="visually-hidden"> (nouvel onglet)</span></a>
            </template>
          </ActionBar>
        </div>
        <section
          v-if="!phone"
          class="prep-side"
        >
          <OfferBrief :offer="offer" />
        </section>
      </div>

      <CvPanel
        v-else-if="offer && tab === 'cv'"
        :offer="offer"
        :primary="nextStep === 'cv'"
        @current="currentCvId = $event"
      />

      <div
        v-else-if="offer"
        class="prep-layout"
      >
        <div class="prep-main">
          <p
            v-if="error"
            class="notice error"
            role="alert"
          >
            {{ error }}
          </p>
          <p
            v-if="doc && doc.missing_identity.length"
            class="notice"
            data-test="missing-identity"
          >
            En-tête incomplet ({{ doc.missing_identity.join(", ") }}) :
            <RouterLink to="/profil?onglet=coordonnees">complète tes coordonnées</RouterLink>.
          </p>

          <TemplatePicker
            v-if="phone"
            :name="doc?.sender[0]"
          />
          <!-- La carte de la lettre (maquette Preparer, étape 7b) : le titre et la langue en tête (C3 : choisir
               ne rédige rien, le bouton du bas le propose), la lettre entière et modifiable (C4), « Modifier le
               texte » qui ouvre la consigne, puis « J'ai relu la lettre » (C11). -->
          <section
            class="doc-card"
            aria-labelledby="letter-card-title"
            data-test="letter-card"
          >
            <div class="doc-card-head">
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
              data-test="no-letter"
            />
            <div
              v-else-if="!selected && !writing"
              class="empty-detail prep-empty"
              data-test="no-letter"
            >
              <p>Aucune lettre pour cette offre.</p>
            </div>
            <AiWriting
              v-else-if="writing && !selected"
              kind="letter"
            />

            <!-- La consigne entière de la version affichée : au toucher il n'y a pas de survol. -->
            <p
              v-if="selected?.instruction"
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
              @open="letterOpen = true"
            />
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
            <p
              class="review-line"
              aria-live="polite"
              data-test="review-line"
            >
              {{ reviewLine }}
            </p>
            <p
              v-if="pageLine"
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
              v-if="selected?.review"
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
            <template v-if="selected && !claim">
              <button
                v-if="!instructionOpen"
                type="button"
                class="secondary doc-card-edit"
                data-test="edit-text"
                @click="openInstruction"
              >
                {{ phone ? "Modifier le texte avec l'Assistant" : "Modifier le texte" }}
              </button>
              <div
                v-else-if="phone"
                class="doc-card-instruction"
              >
                <input
                  ref="instructionEl"
                  v-model="instruction"
                  class="prep-instruction-line"
                  maxlength="500"
                  aria-label="Consigne pour la nouvelle version"
                  placeholder="Consigne : plus court, insiste sur Kubernetes"
                  data-test="instruction"
                  @input="instructionNote = ''"
                >
                <p
                  v-if="instructionNote"
                  class="hint"
                  aria-live="polite"
                  data-test="instruction-note"
                >
                  {{ instructionNote }}
                </p>
              </div>
              <label class="doc-card-read">
                <input
                  type="checkbox"
                  :checked="!!selected.read_at"
                  :disabled="writing || readBusy"
                  data-test="letter-read"
                  @change="markRead($event.target as HTMLInputElement)"
                >
                <span>J'ai relu la lettre</span>
              </label>
            </template>
          </section>
        </div>

        <section
          v-if="!phone"
          class="prep-side"
        >
          <OfferBrief :offer="offer" />
          <div class="side-card">
            <h2>
              {{ selected ? "Nouvelle version" : "Rédiger la lettre" }}
            </h2>
            <FormField
              v-if="selected"
              v-slot="field"
              label="Consigne"
              optional
            >
              <textarea
                :id="field.id"
                v-model="instruction"
                rows="2"
                maxlength="500"
                placeholder="plus court, insiste sur Kubernetes"
                :aria-describedby="field.describedby"
                class="side-instruction"
                data-test="instruction"
                @input="instructionNote = ''"
              />
            </FormField>
            <p
              class="hint instruction-note"
              aria-live="polite"
              data-test="instruction-note"
            >
              {{ instructionNote }}
            </p>
            <div class="mobile-dock">
              <BusyButton
                :class="nextStep === 'letter' ? 'primary' : 'secondary'"
                :busy="writing"
                :busy-label="phase === 'review' ? 'Relecture…' : 'Rédaction…'"
                :disabled="reached('letter')"
                data-test="write"
                @click="write()"
              >
                <HoverNote :text="writing ? '' : aiNote('Environ 0,10 $.', 'letter')">
                  <span class="with-icon"><AppIcon name="ai" />{{ writeLabel || (selected ? "Rédiger la nouvelle version" : "Rédiger la lettre") }}</span>
                </HoverNote>
              </BusyButton>
            </div>
            <PlanLimit usage="letter" />
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
          </div>

          <div
            v-if="selected"
            class="side-card"
            data-test="download-card"
          >
            <h2>Télécharger</h2>
            <template v-if="dirty">
              <button
                type="button"
                class="secondary"
                :disabled="saving"
                data-test="save-letter"
                @click="save"
              >
                Enregistrer mes modifications
              </button>
              <p class="hint">
                Enregistre d'abord tes modifications pour les télécharger.
              </p>
            </template>
            <div
              v-else
              class="actions download-actions"
            >
              <a
                class="secondary"
                :href="pdfHref(`/api/letters/${selected.id}/pdf`, template)"
                download
                data-test="pdf"
              ><span class="with-icon"><AppIcon name="download" />PDF</span></a>
              <a
                class="secondary"
                :href="pdfHref(`/api/letters/${selected.id}/docx`, template)"
                download
                data-test="docx"
              ><span class="with-icon"><AppIcon name="download" />Word</span></a>
            </div>
          </div>

          <div
            v-if="letters.length > 1"
          >
            <GroupedList
              title="Versions"
              :level="2"
              class="versions"
            >
              <GroupedRow
                v-for="letter in letters"
                :key="letter.id"
                :title="versionName(letter)"
                :description="versionDescription(letter)"
                button
                :chevron="false"
                :current="letter.id === selectedId"
                data-test="version"
                @click="select(letter)"
              />
            </GroupedList>
          </div>
        </section>
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
          <RouterLink
            v-else-if="selected?.read_at"
            :to="{ query: { doc: 'cv' } }"
            class="button-link primary-link prep-bar-main"
            data-test="next-step"
          >
            Continuer vers le CV
          </RouterLink>
          <!-- Pas encore relue : le bouton reste là, inactif, et dit pourquoi ; l'étape CV reste ouverte. -->
          <template v-else>
            <button
              type="button"
              class="prep-bar-main prep-bar-waiting"
              aria-disabled="true"
              aria-describedby="prep-bar-hint"
              data-test="next-step"
            >
              Continuer vers le CV
            </button>
            <p
              id="prep-bar-hint"
              class="action-bar-note prep-bar-hint"
              data-test="next-step-hint"
            >
              Relis la lettre pour continuer.
            </p>
          </template>
        </ActionBar>
        <BottomSheet
          v-if="phone && selected"
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
            Enregistre d'abord tes modifications pour les télécharger.
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
      </div>
    </div>
  </section>

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
</template>
