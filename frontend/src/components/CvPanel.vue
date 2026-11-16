<script setup lang="ts">
import FormField from "./FormField.vue";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api, type Cv, type LetterLanguage, type Offer } from "../api/client";
import { onDayAt } from "../format";
import OfferBrief from "./OfferBrief.vue";
import LayoutCard from "./LayoutCard.vue";
import AiWriting from "./AiWriting.vue";
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";
import IconButton from "./IconButton.vue";
import HoverNote from "./HoverNote.vue";
import InlineConfirm from "./InlineConfirm.vue";
import { usePlan } from "../composables/usePlan";
import PlanLimit from "./PlanLimit.vue";
import SavedStatus from "./SavedStatus.vue";
import ActionBar from "./ActionBar.vue";
import DisclosureRow from "./DisclosureRow.vue";
import DocPreview from "./DocPreview.vue";
import LayoutSheetLink from "./LayoutSheetLink.vue";
import { pdfHref, useDocTemplate } from "../composables/useDocTemplate";
import { usePhone } from "../composables/usePhone";
import BottomSheet from "./BottomSheet.vue";
import Composer from "./Composer.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import SegmentedControl from "./SegmentedControl.vue";
import SuggestionChips from "./SuggestionChips.vue";
import { cvChanges, type CvChange } from "../cvChanges";
import DocSearch from "./DocSearch.vue";
import { highlight, type Segment } from "../newsLabels";

// Un bloc ajouté ou retiré : « Enregistré », annoncé (WCAG 4.1.3).
const savedAt = ref(0);

const { aiNote, reached, refresh: refreshPlan } = usePlan();

// `primary` : le CV est la prochaine étape de la préparation (docs/29 §1.3).
// `preparing` et `failed` : le CV adapté lancé avec la lettre (MODIFICATIONS du 9 novembre, §7 n° 1), en cours ou en échec.
// `letterLanguage` : la langue de la lettre, celle du CV tant qu'aucune autre n'est choisie (§14).
const props = defineProps<{ offer: Offer; primary?: boolean; preparing?: boolean; failed?: boolean; letterLanguage?: LetterLanguage | null }>();
// Version affichée, pour le lien « CV (Word) » de la barre de la page.
const emit = defineEmits<{ current: [id: number | null] }>();

const LANGUAGES: Record<LetterLanguage, string> = { fr: "Français", en: "English", de: "Deutsch" };
// La page A4 grisée du CV (PreparerOrdinateurCV) : le nom, puis les sections en lignes.
const CV_LINES = [40, 60, 0, 30, 96, 92, 88, 0, 30, 94, 90, 70, 0, 30, 85, 60];
const SECTIONS: Record<string, string> = {
  experience: "Expériences",
  competence: "Compétences",
  formation: "Formation",
  langues: "Langues",
};

const cvs = ref<Cv[]>([]);
const selectedId = ref<number | null>(null);
const edit = ref({ headline: "", summary: "" });
const dirty = ref(false);
const language = ref<LetterLanguage | "">("");
const instruction = ref("");
const writing = ref(false);
const saving = ref(false);
const error = ref("");
const loaded = ref(false);

const selected = computed(() => cvs.value.find((c) => c.id === selectedId.value) ?? null);
const doc = computed(() => selected.value?.document ?? null);
// Les mots-clés de l'offre que l'adaptation a mis en avant (en gras dans le CV), cinq au plus.
const highlights = computed(() => [...new Set((selected.value?.keywords ?? []).map((word) => word.trim()).filter(Boolean))].slice(0, 5));
const blocksBySection = computed(() => {
  const groups: Record<string, Cv["blocks"]> = {};
  for (const block of selected.value?.blocks ?? []) (groups[block.section] ??= []).push(block);
  return Object.keys(SECTIONS)
    .filter((key) => groups[key]?.length)
    .map((key) => ({ key, label: SECTIONS[key], blocks: groups[key] ?? [] }));
});

function show(cv: Cv | null): void {
  selectedId.value = cv?.id ?? null;
  emit("current", selectedId.value);
  edit.value = { headline: cv?.headline ?? "", summary: cv?.summary ?? "" };
  dirty.value = false;
  void nextTick(resizeAll);
}

function current(list: Cv[]): Cv | null {
  const stamp = (c: Cv) => Date.parse(c.edited_at ?? c.created_at);
  return [...list].sort((a, b) => stamp(b) - stamp(a) || b.version - a.version)[0] ?? null;
}

function detail(err: unknown, fallback: string): string {
  const value = (err as { detail?: unknown } | undefined)?.detail;
  return typeof value === "string" ? value.charAt(0).toUpperCase() + value.slice(1) + "." : fallback;
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/offers/{offer_id}/cvs", { params: { path: { offer_id: props.offer.id } } });
  cvs.value = data ?? [];
  show(current(cvs.value));
  loaded.value = true;
}

// Le CV préparé en même temps que la lettre est arrivé : on le montre.
watch(
  () => props.preparing,
  (now, before) => {
    if (before && !now) void load();
  },
);
// Sur ordinateur, sans CV adapté (§2.3, §7.3, PreparerOrdinateurCV) : la page A4 grisée et une carte au centre. En échec,
// « Le CV adapté n’a pas pu être préparé » et « Réessayer » ; sinon « Pas encore de CV adapté à cette offre ».
const cvFailed = ref(false);
const emptyCard = computed(() =>
  props.failed || cvFailed.value
    ? { title: "Le CV adapté n’a pas pu être préparé", text: "La préparation a été interrompue. Ton CV d’origine ne change pas.", action: "Réessayer" }
    : { title: "Pas encore de CV adapté à cette offre", text: "jobA1 l’adapte à l’annonce, dans le modèle choisi. Ton CV d’origine ne change pas.", action: "Générer le CV adapté" },
);
const deskEmpty = computed(() => !phone.value && loaded.value && !selected.value);

// Le texte qui vient d'arriver de l'IA apparaît ligne à ligne (docs/59 §4).
const fresh = ref(false);
// Des modifications non enregistrées : le choix se fait dans la page (docs/108 §1).
const choosingWrite = ref(false);
async function saveThenWrite(): Promise<void> {
  choosingWrite.value = false;
  await save();
  await write(true);
}
async function write(force = false): Promise<void> {
  if (writing.value) return;
  if (dirty.value && !force) {
    choosingWrite.value = true;
    return;
  }
  choosingWrite.value = false;
  writing.value = true;
  error.value = "";
  try {
    const text = instruction.value.trim();
    const { data, error: err } = await api.POST("/api/offers/{offer_id}/cvs", {
      params: { path: { offer_id: props.offer.id } },
      body: {
        language: language.value || selected.value?.language || props.letterLanguage || null,
        instruction: text || null,
        base_draft_id: text && selectedId.value ? selectedId.value : null,
      },
    });
    // Le compteur de la formule suit ; à la limite, la ligne grise dit pourquoi (docs/125 §4).
    await refreshPlan();
    if (!data) {
      if (!reached("cv")) {
        error.value = detail(err, "La préparation du CV a échoué, réessaie.");
        cvFailed.value = true;
      }
      return;
    }
    cvFailed.value = false;
    cvs.value = [data, ...cvs.value];
    instruction.value = "";
    show(data);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
  } catch {
    error.value = "API injoignable.";
    cvFailed.value = true;
  } finally {
    writing.value = false;
  }
}

async function save(chunkIds?: number[]): Promise<boolean> {
  const cv = selected.value;
  if (!cv) return false;
  saving.value = true;
  error.value = "";
  try {
    const { data, error: err } = await api.PUT("/api/cvs/{draft_id}", {
      params: { path: { draft_id: cv.id } },
      body: { headline: edit.value.headline, summary: edit.value.summary, chunk_ids: chunkIds ?? cv.chunk_ids },
    });
    if (!data) {
      error.value = detail(err, "Enregistrement refusé.");
      return false;
    }
    cvs.value = cvs.value.map((c) => (c.id === data.id ? data : c));
    show(data);
    return true;
  } finally {
    saving.value = false;
  }
}

async function toggle(id: number, checked: boolean): Promise<void> {
  const ids = selected.value?.chunk_ids ?? [];
  if (!checked && ids.length === 1) {
    error.value = "Garde au moins un bloc dans le CV.";
    return;
  }
  if (await save(checked ? [...ids, id] : ids.filter((i) => i !== id))) savedAt.value = Date.now();
}

// Déplace un bloc coché avant ou après le bloc coché voisin de la même rubrique.
function move(id: number, section: string, delta: -1 | 1): void {
  const cv = selected.value;
  if (!cv) return;
  const sameSection = cv.blocks.filter((b) => b.selected && b.section === section).map((b) => b.id);
  const neighbour = sameSection[sameSection.indexOf(id) + delta];
  if (neighbour === undefined) return;
  const ids = [...cv.chunk_ids];
  const a = ids.indexOf(id);
  const b = ids.indexOf(neighbour);
  [ids[a], ids[b]] = [neighbour, id];
  void save(ids);
}

function canMove(id: number, section: string, delta: -1 | 1): boolean {
  const ids = (selected.value?.blocks ?? []).filter((b) => b.selected && b.section === section).map((b) => b.id);
  const index = ids.indexOf(id);
  return index >= 0 && ids[index + delta] !== undefined;
}

function resize(el: HTMLTextAreaElement): void {
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

function resizeAll(): void {
  document.querySelectorAll<HTMLTextAreaElement>(".cv-sheet textarea").forEach(resize);
}

function onInput(event: Event): void {
  if (event.target instanceof HTMLTextAreaElement) resize(event.target);
  dirty.value = true;
}

function versionLabel(cv: Cv): string {
  const when = onDayAt(cv.edited_at ?? cv.created_at);
  const what = cv.instruction ? `« ${cv.instruction} »` : "première version";
  return `v${cv.version} · ${LANGUAGES[cv.language]} · ${what} · ${cv.edited_at ? "modifiée" : "préparée"} ${when}`;
}

// Sur téléphone (§37 du 16.11, planche MaCandidatureCV) : la rangée d'outils, le CV entier, « Demander une
// modification du CV », puis « J’ai relu, continuer » en bas.
const { phone } = usePhone();
const { template } = useDocTemplate();
// Le bouton plein du téléphone : préparer le CV, ou à nouveau dans une autre langue ; sinon « J’ai relu, continuer ».
// La langue en FR / DE / EN en tête de la carte (maquette Preparer, Kevin 2026-11-06) : sans choix, celle du CV
// affiché ; une autre langue propose de préparer le CV à nouveau.
const LANGUAGE_OPTIONS = (["fr", "de", "en"] as LetterLanguage[]).map((code) => ({ value: code, label: code.toUpperCase(), name: LANGUAGES[code], test: `cv-language-${code}` }));
const SHEET_LANGUAGE_OPTIONS = LANGUAGE_OPTIONS.map((option) => ({ ...option, label: option.name }));
const LANGUAGE_IN: Record<LetterLanguage, string> = { fr: "français", de: "allemand", en: "anglais" };
const shownLanguage = computed<string>({
  get: () => language.value || selected.value?.language || "",
  set: (value) => {
    language.value = value as LetterLanguage;
  },
});
const writeLabel = computed(() => {
  const chosen = language.value;
  if (!selected.value) return chosen ? `Préparer le CV en ${LANGUAGE_IN[chosen]}` : "Préparer le CV";
  if (chosen && chosen !== selected.value.language) return `Préparer à nouveau en ${LANGUAGE_IN[chosen]}`;
  return instruction.value.trim() ? "Préparer la nouvelle version" : "";
});
// « Blocs du CV » replié sur téléphone (Kevin, 6.11) : le nombre de blocs gardés en résumé.
const blocksSummary = computed(() => {
  const blocks = selected.value?.blocks ?? [];
  return `${blocks.filter((b) => b.selected).length} sur ${blocks.length}`;
});
// Les mots du CV affiché, pour « Mise en page » (lot 15.1).
const words = computed(() => {
  const d = doc.value;
  if (!d) return 0;
  const texts = [edit.value.headline, edit.value.summary, ...d.sections.flatMap((s) => s.items.flatMap((i) => [i.title, ...i.content.map((c) => c.text)]))];
  return texts.reduce((n, t) => n + (t?.match(/\S+/g)?.length ?? 0), 0);
});

// L'étape CV prête sur ordinateur (MODIFICATIONS du 9 novembre, §14 ; maquettes PreparerOrdinateurCVPret et
// PreparerOrdinateurCVChangements) : la structure de l'étape Lettre. FR / DE / EN en tête du CV, retouche en bas, et à
// droite « Mise en page », la carte « Ce CV » puis le seul bouton plein.
const router = useRouter();
const deskReady = computed(() => !phone.value && !!selected.value);
const suggestions = computed(() => {
  const first = highlights.value[0];
  return ["Plus court", ...(first ? [`Mettre ${first} en avant`] : []), "Tenir sur une page"];
});
const revision = ref("");
function revise(text: string): void {
  const asked = text.trim();
  if (!asked || writing.value) return;
  instruction.value = asked;
  revision.value = "";
  void write();
}
const changes = computed<CvChange[]>(() => (selected.value ? cvChanges(selected.value) : []));
const changesOpen = ref(false);
// §34 du 16.11 (PreparerOrdinateurCVChangementsVus, PreparerOrdinateurCVRecherche) : la loupe ouvre la recherche ;
// « Voir les changements · N » surligne dans l'aperçu ce que l'adaptation a changé (résumé, bloc déplacé).
const searchOpen = ref(false);
const searchButton = ref<HTMLButtonElement | null>(null);
const showChanges = ref(false);
const marked = computed(() => new Set<unknown>(showChanges.value ? changes.value.map((c) => c.mark).filter((m) => m !== undefined) : []));
function closeSearch(): void {
  searchOpen.value = false;
  void nextTick(() => searchButton.value?.focus());
}
const versionsOpen = ref(false);
const changesLine = computed(() => {
  const n = changes.value.length;
  return n ? `${n} changement${n > 1 ? "s" : ""}, à vérifier` : "Aucun changement";
});
const currentVersionLine = computed(() => {
  const cv = selected.value;
  if (!cv) return "";
  return `Actuelle : ${cv.instruction ? `« ${cv.instruction} »` : "adaptée"}, ${onDayAt(cv.edited_at ?? cv.created_at)}`;
});
// « jobA1 a ajusté ton CV pour l’annonce d’Alpstack » : « d’ » devant une voyelle.
const forCompany = computed(() => {
  const name = props.offer.company?.trim();
  if (!name) return "pour cette annonce";
  return `pour l’annonce ${/^[aeiouyàâéèêîôûh]/i.test(name) ? "d’" : "de "}${name}`;
});
async function undo(change: CvChange): Promise<void> {
  if (change.undo && (await save(change.undo))) savedAt.value = Date.now();
}
// Téléphone (§37 du 16.11, planches MaCandidatureCV et MaCandidatureCVPourquoi) : toucher un passage surligné ouvre la
// feuille « Changement N sur M » : Avant, Maintenant, Pourquoi (la ligne du serveur, mots de l'annonce surlignés),
// « Annuler ce changement », précédent et suivant.
const changeAt = ref<number | null>(null);
const changeOf = computed(() => (changeAt.value === null ? null : (changes.value[changeAt.value] ?? null)));
function openChange(event: Event): void {
  if (!phone.value || !showChanges.value) return;
  const passage = (event.target as HTMLElement).closest<HTMLElement>("[data-change]");
  if (!passage) return;
  const target = passage.dataset.change === "summary" ? "summary" : Number(passage.dataset.change);
  const at = changes.value.findIndex((c) => c.mark === target);
  if (at >= 0) changeAt.value = at;
}
function stepChange(by: number): void {
  const n = changes.value.length;
  if (changeAt.value === null || !n) return;
  changeAt.value = (changeAt.value + by + n) % n;
}
async function undoShown(): Promise<void> {
  const change = changeOf.value;
  if (!change) return;
  await undo(change);
  changeAt.value = null;
}
// « Pourquoi » : le texte du serveur, les mots de l'annonce qu'il renvoie avec la raison (`quotes`) surlignés comme
// dans « Le poste », sans dépendre des guillemets (Kevin, 16.11) ; « Demandé par toi » pour un changement demandé
// par l'utilisateur ; rien sans raison.
const why = computed<Segment[]>(() => {
  const change = changeOf.value;
  const reason = change ? selected.value?.reasons?.find((r) => r.target === change.target) : null;
  if (!reason) return [];
  if (reason.origin === "user") return [{ text: "Demandé par toi.", hit: false }];
  const text = reason.text?.trim() ?? "";
  return text ? highlight(text, (reason.quotes ?? []).filter(Boolean)) : [];
});
function pickVersion(cv: Cv): void {
  show(cv);
  versionsOpen.value = false;
}
// Le nombre de pages A4 du CV affiché, mesuré sur la page à l'écran (même modèle que le PDF).
const sheet = ref<HTMLElement | null>(null);
const pages = ref(1);
function measure(): void {
  const el = sheet.value;
  if (!el || !el.clientWidth) return;
  pages.value = Math.max(1, Math.ceil(el.scrollHeight / ((el.clientWidth * 297) / 210) - 0.02));
}
let observer: ResizeObserver | null = null;
watch(sheet, (el) => {
  observer?.disconnect();
  if (el && typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(measure);
    observer.observe(el);
  }
  measure();
});
onBeforeUnmount(() => observer?.disconnect());
const layoutNote = computed(() => {
  if (deskEmpty.value) return "Le CV suivra ce modèle.";
  if (deskReady.value) return `Même modèle que la lettre · ${pages.value} page${pages.value > 1 ? "s" : ""}`;
  return words.value ? `${words.value} mots` : undefined;
});
const readThenBusy = ref(false);
// « J’ai relu, continuer » : la relecture est notée avec la version, puis Postuler ; un refus le dit et reste là.
async function readThenNext(): Promise<void> {
  const cv = selected.value;
  if (!cv || writing.value || readThenBusy.value) return;
  if (!cv.read_at) {
    readThenBusy.value = true;
    try {
      const { data, error: err } = await api.PUT("/api/cvs/{draft_id}/read", { params: { path: { draft_id: cv.id } }, body: { read: true } });
      if (!data) {
        error.value = detail(err, "La relecture n’a pas été enregistrée, réessaie.");
        return;
      }
      error.value = "";
      cvs.value = cvs.value.map((c) => (c.id === data.id ? data : c));
    } finally {
      readThenBusy.value = false;
    }
  }
  await router.push({ query: { doc: "postuler" } });
}

onMounted(() => void load());
</script>

<template>
  <div :class="['prep-layout', { 'prep-desk': !phone }]">
    <div class="prep-main">
      <p
        v-if="error && !(deskEmpty && cvFailed && ['La préparation du CV a échoué, réessaie.', 'API injoignable.'].includes(error))"
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
      <!-- La carte du CV (maquette Preparer, étape 7b, C5) : le CV entier et modifiable, et dessus ce que
           l’adaptation a mis en avant (ses mots-clés). -->
      <section
        :class="['doc-card', { 'cv-phone-ready': phone && selected }]"
        aria-labelledby="cv-card-title"
        data-test="cv-card"
      >
        <!-- Téléphone (§9) : « Moderne · Français » sous le titre et « Changer », qui ouvre la feuille « Mise en page
             et langue » ; plus de FR / DE / EN sur l’écran. -->
        <LayoutSheetLink
          v-if="phone && !selected"
          v-model="shownLanguage"
          title="CV adapté"
          title-id="cv-card-title"
          :name="doc?.name"
          :options="SHEET_LANGUAGE_OPTIONS"
          language-label="Langue du titre et du résumé"
        />
        <!-- Téléphone, CV prêt (§37 du 16.11, planche MaCandidatureCV) : la rangée d'outils sous les étapes,
             « Changements · N », la loupe et « Modèle » (la feuille Mise en page et langue). La recherche la remplace. -->
        <template v-else-if="phone">
          <h2
            id="cv-card-title"
            class="visually-hidden"
          >
            CV adapté
          </h2>
          <div
            v-if="!searchOpen"
            class="cv-phone-tools"
            data-test="cv-phone-tools"
          >
            <button
              v-if="changes.length"
              type="button"
              class="doc-tool"
              :aria-pressed="showChanges"
              data-test="cv-changes-show"
              @click="showChanges = !showChanges"
            >
              <i
                class="doc-tool-mark"
                aria-hidden="true"
              />Changements · {{ changes.length }}
            </button>
            <button
              ref="searchButton"
              type="button"
              class="doc-tool doc-tool-round cv-phone-search"
              aria-label="Chercher dans le CV"
              :aria-expanded="searchOpen"
              data-test="cv-search-open"
              @click="searchOpen = true"
            >
              <AppIcon name="search" />
            </button>
            <LayoutSheetLink
              v-model="shownLanguage"
              compact
              title="CV adapté"
              title-id="cv-card-title"
              :name="doc?.name"
              :options="SHEET_LANGUAGE_OPTIONS"
              language-label="Langue du titre et du résumé"
            />
          </div>
          <DocSearch
            v-else
            class="cv-phone-find"
            :target="sheet"
            label="Chercher dans le CV"
            @close="closeSearch"
          />
        </template>
        <div
          v-else
          class="doc-card-head"
        >
          <h2 id="cv-card-title">
            CV adapté
          </h2>
          <div
            v-if="selected"
            class="doc-tools"
          >
            <button
              ref="searchButton"
              type="button"
              class="doc-tool doc-tool-round"
              aria-label="Chercher dans le CV"
              :aria-expanded="searchOpen"
              data-test="cv-search-open"
              @click="searchOpen ? closeSearch() : (searchOpen = true)"
            >
              <AppIcon name="search" />
            </button>
            <button
              v-if="changes.length"
              type="button"
              class="doc-tool"
              :aria-pressed="showChanges"
              data-test="cv-changes-show"
              @click="showChanges = !showChanges"
            >
              <i
                class="doc-tool-mark"
                aria-hidden="true"
              />Voir les changements · {{ changes.length }}
            </button>
            <SegmentedControl
              v-model="shownLanguage"
              :options="LANGUAGE_OPTIONS"
              label="Langue du CV"
              class="doc-language"
            />
          </div>
        </div>
        <DocSearch
          v-if="!phone && selected && searchOpen"
          :target="sheet"
          label="Chercher dans le CV"
          @close="closeSearch"
        />
        <DocPreview
          v-if="phone && loaded && !selected && !writing"
          :template="template"
          name="Ton nom"
          :paragraphs="[]"
          label="Aperçu vide du CV"
          class="doc-preview-tall"
          data-test="no-cv"
        />
        <div
          v-else-if="deskEmpty && (writing || preparing)"
          class="prep-writing"
          data-test="cv-writing"
        >
          <p
            class="prep-writing-band"
            role="status"
          >
            <span
              class="prep-spin"
              aria-hidden="true"
            />
            <span>Je prépare ton CV adapté… environ 20 secondes</span>
          </p>
          <div class="prep-empty-page">
            <div
              class="prep-empty-sheet"
              aria-hidden="true"
            >
              <i
                v-for="(w, i) in CV_LINES"
                :key="i"
                :style="{ width: `${w}%` }"
              />
            </div>
          </div>
        </div>
        <div
          v-else-if="deskEmpty"
          class="prep-empty-page"
          :data-test="emptyCard.action === 'Réessayer' ? 'cv-failed' : 'no-cv'"
        >
          <div
            class="prep-empty-sheet"
            aria-hidden="true"
          >
            <i
              v-for="(w, i) in CV_LINES"
              :key="i"
              :style="{ width: `${w}%` }"
            />
          </div>
          <div
            class="prep-empty-card"
            :role="emptyCard.action === 'Réessayer' ? 'alert' : undefined"
          >
            <p class="prep-empty-title">
              {{ emptyCard.title }}
            </p>
            <p class="prep-empty-text">
              {{ emptyCard.text }}
            </p>
            <PlanLimit usage="cv" />
            <BusyButton
              class="primary"
              :busy="writing"
              busy-label="Préparation…"
              :disabled="reached('cv')"
              data-test="write-cv"
              @click="write()"
            >
              {{ emptyCard.action }}
            </BusyButton>
          </div>
        </div>
        <div
          v-else-if="loaded && !selected && !writing && !preparing"
          class="empty-detail prep-empty"
          data-test="no-cv"
        >
          <p>Aucun CV adapté pour cette offre.</p>
        </div>
        <AiWriting
          v-else-if="(writing || preparing) && !selected"
          kind="cv"
        />

        <article
          v-if="doc && selected"
          ref="sheet"
          class="cv-sheet print-sheet"
          :class="[`tpl-${template}`, { 'fresh-lines': fresh, busy: writing || saving, 'doc-reading': searchOpen || showChanges }]"
          :data-template="template"
          :lang="doc.language"
          data-test="cv"
          @click="openChange"
          @keydown.enter="openChange"
        >
          <!-- L’en-tête (le nom et le titre) que le modèle habille : bande, bandeau ou filet, comme dans le PDF. -->
          <div class="doc-head cv-head">
            <p class="cv-name">
              {{ doc.name || "Ton nom" }}
            </p>
            <input
              v-model="edit.headline"
              class="cv-headline screen-only"
              aria-label="Titre du profil"
              data-test="headline"
              @input="dirty = true"
            >
            <p class="cv-headline print-only">
              {{ edit.headline }}
            </p>
          </div>
          <p class="cv-contacts">
            {{ doc.contacts.join(" · ") }}
          </p>
          <h3>{{ doc.summary_heading }}</h3>
          <textarea
            v-model="edit.summary"
            class="screen-only"
            rows="2"
            aria-label="Résumé du profil"
            data-test="summary"
            @input="onInput"
          />
          <p
            :class="['print-only', { 'cv-changed': marked.has('summary') }]"
            v-bind="phone && marked.has('summary') ? { 'data-change': 'summary', role: 'button', tabindex: 0 } : {}"
          >
            {{ edit.summary }}
          </p>
          <template
            v-for="section in doc.sections"
            :key="section.key"
          >
            <h3>{{ section.heading }}</h3>
            <div
              v-for="item in section.items"
              :key="item.chunk_id"
              :class="['cv-item', { 'cv-changed': marked.has(item.chunk_id) }]"
              v-bind="phone && marked.has(item.chunk_id) ? { 'data-change': item.chunk_id, role: 'button', tabindex: 0 } : {}"
              data-test="cv-item"
            >
              <strong
                v-if="item.title"
                class="cv-item-title"
              >{{ item.title }}</strong>
              <p>
                <span
                  v-for="(segment, index) in item.content"
                  :key="index"
                  :class="{ kw: segment.strong }"
                  v-text="segment.text"
                />
              </p>
            </div>
          </template>
        </article>
      </section>
      <!-- Téléphone (§37 du 16.11) : la retouche sous le CV, comme sur ordinateur. -->
      <Composer
        v-if="phone && selected"
        v-model="revision"
        class="cv-phone-composer"
        placeholder="Demander une modification du CV"
        send-label="Envoyer la demande"
        :busy="writing"
        @send="revise"
      />
      <!-- Retoucher (§14, comme la lettre) : les puces et la zone de saisie collées en bas de la colonne gauche. -->
      <div
        v-if="deskReady"
        class="prep-desk-bottom"
        data-test="cv-desk-bottom"
      >
        <div class="prep-revise">
          <SuggestionChips
            :items="suggestions"
            label="Retouches proposées"
            @pick="revise"
          />
          <Composer
            v-model="revision"
            placeholder="Demander une modification du CV"
            send-label="Envoyer la demande"
            :busy="writing"
            @send="revise"
          />
        </div>
      </div>
      <!-- La barre du bas du téléphone : un seul bouton plein, la prochaine chose à faire. -->
      <ActionBar
        v-if="phone && loaded"
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
          usage="cv"
        />
        <BusyButton
          v-if="writeLabel || writing"
          class="primary prep-bar-main"
          :busy="writing"
          busy-label="Préparation…"
          :disabled="reached('cv')"
          data-test="write-cv"
          @click="write()"
        >
          <span class="with-icon"><AppIcon name="ai" />{{ writeLabel || "Préparer le CV" }}</span>
        </BusyButton>
        <!-- §37 du 16.11 : « J’ai relu, continuer » note la relecture puis passe à Postuler, comme sur ordinateur. -->
        <BusyButton
          v-else
          class="primary prep-bar-main"
          :busy="readThenBusy"
          busy-label="Enregistrement…"
          data-test="next-step"
          @click="readThenNext"
        >
          J’ai relu, continuer
        </BusyButton>
      </ActionBar>
    </div>

    <section class="prep-side">
      <!-- Lot 15.1 : « Mise en page » aussi à l'étape CV, le nombre de mots dessous (la mesure de la page A4 n'existe
           que pour la lettre). -->
      <LayoutCard
        v-if="!phone"
        :note="layoutNote"
      />
      <!-- « Ce CV » (§14, remplace « Ta candidature ») : les changements à vérifier (panneau), les versions (panneau) et le
           CV d’origine, qui ne change pas. -->
      <section
        v-if="deskReady && selected"
        class="side-card prep-file"
        aria-labelledby="cv-file-title"
        data-test="cv-file"
      >
        <h2 id="cv-file-title">
          Ce CV
        </h2>
        <button
          type="button"
          class="prep-file-row"
          aria-haspopup="dialog"
          :aria-label="`Adapté pour cette offre, ${changesLine}`"
          data-test="cv-changes-open"
          @click="changesOpen = true"
        >
          <span class="prep-file-text">
            <b>Adapté pour cette offre</b>
            <span :class="['prep-file-sub', { warn: changes.length }]">{{ changesLine }}</span>
          </span>
          <AppIcon name="chevron" />
        </button>
        <button
          type="button"
          class="prep-file-row"
          aria-haspopup="dialog"
          :aria-label="`Versions · ${cvs.length}, ${currentVersionLine}`"
          data-test="cv-versions-open"
          @click="versionsOpen = true"
        >
          <span class="prep-file-text">
            <b>Versions · {{ cvs.length }}</b>
            <span class="prep-file-sub">{{ currentVersionLine }}</span>
          </span>
          <AppIcon name="chevron" />
        </button>
        <RouterLink
          to="/profil?onglet=parcours"
          class="prep-file-row"
          data-test="cv-origin"
        >
          <span class="prep-file-text">
            <b>CV d’origine</b>
            <span class="prep-file-sub">Ne change pas, sert de base</span>
          </span>
          <AppIcon name="chevron" />
        </RouterLink>
      </section>
      <template v-if="deskReady">
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
        <button
          v-if="dirty"
          type="button"
          class="secondary prep-aside-main"
          :disabled="saving"
          data-test="save-cv"
          @click="save()"
        >
          Enregistrer mes modifications
        </button>
        <PlanLimit
          v-if="writeLabel"
          usage="cv"
        />
        <BusyButton
          v-if="writeLabel || writing"
          class="primary prep-aside-main"
          :busy="writing"
          busy-label="Préparation…"
          :disabled="reached('cv')"
          data-test="write-cv"
          @click="write()"
        >
          <span class="with-icon"><AppIcon name="ai" />{{ writeLabel || "Préparer le CV" }}</span>
        </BusyButton>
        <button
          v-else
          type="button"
          class="primary prep-aside-main"
          :disabled="readThenBusy"
          data-test="cv-read-next"
          @click="readThenNext"
        >
          J’ai relu, continuer
        </button>
      </template>
      <!-- Sans CV adapté (PreparerOrdinateurCV) : la carte « Ce CV » dit qu'il se prépare pendant la relecture de la
           lettre. -->
      <section
        v-if="deskEmpty"
        class="side-card"
        aria-labelledby="cv-side-title"
        data-test="cv-side"
      >
        <h2 id="cv-side-title">
          Ce CV
        </h2>
        <p class="layout-card-help">
          Le CV adapté se prépare normalement pendant que tu relis la lettre.
        </p>
      </section>
      <OfferBrief
        v-if="!phone && !deskEmpty && !deskReady"
        :offer="offer"
      />
      <div
        v-if="!phone && !deskEmpty && !deskReady"
        class="side-card"
      >
        <h2>
          {{ selected ? "Nouvelle version" : "Préparer le CV" }}
        </h2>
        <FormField
          v-slot="f"
          label="Langue du titre et du résumé"
        >
          <select
            :id="f.id"
            v-model="language"
            :aria-describedby="f.describedby"
            data-test="cv-language"
          >
            <option value="">
              Celle de l’annonce
            </option>
            <option
              v-for="(label, code) in LANGUAGES"
              :key="code"
              :value="code"
            >
              {{ label }}
            </option>
          </select>
        </FormField>
        <FormField
          v-if="selected"
          v-slot="f"
          label="Consigne (facultative)"
          hint="Ex. : mets le projet personnel en premier…"
        >
          <textarea
            :id="f.id"
            v-model="instruction"
            :aria-describedby="f.describedby"
            rows="2"
            maxlength="500"
           
            data-test="cv-instruction"
          />
        </FormField>
        <div class="mobile-dock">
          <BusyButton
            :class="primary ? 'primary action-1' : 'secondary action-2'"
            :busy="writing"
            busy-label="Préparation…"
            :disabled="reached('cv')"
            data-test="write-cv"
            @click="write()"
          >
            <HoverNote :text="writing ? '' : aiNote('Environ 0,05 $.', 'cv')">
              <span class="with-icon"><AppIcon name="ai" />{{ selected ? "Nouvelle version" : "Préparer le CV" }}</span>
            </HoverNote>
          </BusyButton>
        </div>
        <PlanLimit usage="cv" />
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
        v-if="selected && phone"
        :class="phone ? 'cv-blocks-phone' : 'side-card'"
        data-test="cv-blocks-card"
      >
        <h2 v-if="!phone">
          Blocs du CV
        </h2>
        <component
          :is="phone ? DisclosureRow : 'div'"
          v-bind="phone ? { title: 'Blocs du CV', value: blocksSummary } : {}"
          :class="{ 'cv-blocks-disclosure': phone }"
        >
          <ul class="cv-blocks">
            <template
              v-for="group in blocksBySection"
              :key="group.key"
            >
              <li class="section-label">
                {{ group.label }}
              </li>
              <li
                v-for="block in group.blocks"
                :key="block.id"
                class="cv-block"
              >
                <label>
                  <input
                    type="checkbox"
                    :checked="block.selected"
                    :disabled="saving"
                    data-test="block-toggle"
                    @change="void toggle(block.id, ($event.target as HTMLInputElement).checked)"
                  >
                  {{ block.title }}
                </label>
                <template v-if="block.selected">
                  <IconButton
                    icon="arrow-up"
                    :label="`Monter ${block.title}`"
                    :disabled="saving || !canMove(block.id, block.section, -1)"
                    data-test="move-up"
                    @click="move(block.id, block.section, -1)"
                  />
                  <IconButton
                    icon="arrow-down"
                    :label="`Descendre ${block.title}`"
                    :disabled="saving || !canMove(block.id, block.section, 1)"
                    data-test="move-down"
                    @click="move(block.id, block.section, 1)"
                  />
                </template>
              </li>
            </template>
          </ul>
        </component>
        <SavedStatus :at="savedAt" />
      </div>

      <div
        v-if="selected && phone"
        class="side-card"
      >
        <h2>Télécharger</h2>
        <template v-if="dirty">
          <BusyButton
            class="secondary"
            :busy="saving"
            busy-label="Enregistrement…"
            data-test="save-cv"
            @click="save()"
          >
            Enregistrer le titre et le résumé
          </BusyButton>
          <p class="hint">
            Enregistre d’abord tes modifications pour les télécharger.
          </p>
        </template>
        <div
          v-else
          class="actions download-actions"
        >
          <a
            class="secondary"
            :href="pdfHref(`/api/cvs/${selected.id}/pdf`, template)"
            download
            data-test="cv-pdf"
          ><span class="with-icon"><AppIcon name="download" />PDF</span></a>
          <a
            class="secondary"
            :href="`/api/cvs/${selected.id}/docx`"
            download
            data-test="cv-docx"
          ><span class="with-icon"><AppIcon name="download" />Word</span></a>
        </div>
      </div>

      <div
        v-if="cvs.length > 1 && phone"
        class="side-card"
      >
        <h2>Versions</h2>
        <ul class="versions">
          <li
            v-for="cv in cvs"
            :key="cv.id"
          >
            <button
              type="button"
              :class="['link', { active: cv.id === selectedId }]"
              data-test="cv-version"
              @click="show(cv)"
            >
              {{ versionLabel(cv) }}
            </button>
          </li>
        </ul>
      </div>
    </section>

    <!-- Téléphone (§37 du 16.11, planche MaCandidatureCVPourquoi) : un changement à la fois. -->
    <BottomSheet
      v-if="phone"
      :open="!!changeOf"
      :title="changeOf?.title ?? ''"
      :eyebrow="changeOf ? `Changement ${(changeAt ?? 0) + 1} sur ${changes.length}` : ''"
      data-test="cv-change-sheet"
      @close="changeAt = null"
    >
      <div
        v-if="changeOf"
        class="cv-why-body"
      >
        <p class="cv-why-before">
          {{ changeOf.before }}
        </p>
        <p class="cv-why-now">
          {{ changeOf.now }}
        </p>
        <p
          v-if="why.length"
          class="cv-why"
          data-test="cv-why"
        >
          <AppIcon name="target" />
          <span><b>Pourquoi :</b> <template
            v-for="(part, i) in why"
            :key="i"
          ><mark
            v-if="part.hit"
            class="cv-why-quote"
          >{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
        </p>
        <div class="cv-why-actions">
          <button
            v-if="changeOf.undo"
            type="button"
            class="secondary cv-why-undo"
            :disabled="saving"
            data-test="cv-change-undo"
            @click="undoShown"
          >
            Annuler ce changement
          </button>
          <button
            type="button"
            class="cv-why-step"
            aria-label="Changement précédent"
            :disabled="changes.length < 2"
            data-test="cv-change-prev"
            @click="stepChange(-1)"
          >
            <AppIcon name="chevron-left" />
          </button>
          <button
            type="button"
            class="cv-why-step next"
            aria-label="Changement suivant"
            :disabled="changes.length < 2"
            data-test="cv-change-next"
            @click="stepChange(1)"
          >
            <AppIcon name="chevron" />
          </button>
        </div>
      </div>
    </BottomSheet>
    <!-- Le panneau « Adapté pour cette offre » (PreparerOrdinateurCVChangements) : un bloc par changement, « Avant »,
         « Maintenant » et « Annuler ce changement ». -->
    <BottomSheet
      v-if="deskReady"
      :open="changesOpen"
      title="Adapté pour cette offre"
      data-test="cv-changes"
      @close="changesOpen = false"
    >
      <p class="cv-changes-intro">
        jobA1 a ajusté ton CV {{ forCompany }}. Vérifie chaque point : rien n’est inventé, tout vient de ton CV d’origine.
      </p>
      <ul class="cv-changes">
        <li
          v-for="change in changes"
          :key="change.key"
          data-test="cv-change"
        >
          <b>{{ change.title }}</b>
          <span class="cv-change-before">{{ change.before }}</span>
          <span class="cv-change-now">{{ change.now }}</span>
          <button
            v-if="change.undo"
            type="button"
            class="link cv-change-undo"
            :disabled="saving"
            data-test="cv-change-undo"
            @click="undo(change)"
          >
            Annuler ce changement
          </button>
        </li>
      </ul>
      <p class="cv-changes-note">
        Ton CV d’origine ne change pas. Ces changements valent pour cette candidature seulement.
      </p>
      <SavedStatus :at="savedAt" />
    </BottomSheet>
    <BottomSheet
      v-if="deskReady && selected"
      :open="versionsOpen"
      title="Versions et téléchargement"
      data-test="cv-versions"
      @close="versionsOpen = false"
    >
      <GroupedList
        title="Versions"
        :level="3"
        class="versions"
      >
        <GroupedRow
          v-for="cv in cvs"
          :key="cv.id"
          :title="`Version ${cv.version}`"
          :description="versionLabel(cv)"
          button
          :current="cv.id === selectedId"
          data-test="cv-version"
          @click="pickVersion(cv)"
        />
      </GroupedList>
      <p
        v-if="dirty"
        class="hint"
      >
        Enregistre d’abord tes modifications pour les télécharger.
      </p>
      <template #actions>
        <template v-if="!dirty">
          <a
            class="button-link prep-download"
            :href="pdfHref(`/api/cvs/${selected.id}/pdf`, template)"
            download
            data-test="cv-pdf"
          ><span class="with-icon"><AppIcon name="download" />CV (PDF)</span></a>
          <a
            class="button-link prep-download"
            :href="`/api/cvs/${selected.id}/docx`"
            download
            data-test="cv-docx"
          ><span class="with-icon"><AppIcon name="download" />CV (Word)</span></a>
        </template>
      </template>
    </BottomSheet>
  </div>
</template>
