<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Letter, type LetterLanguage, type Offer } from "../api/client";
import { applicationBody } from "../applicationBody";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import FollowStep from "../components/FollowStep.vue";
import ContactsPanel from "../components/ContactsPanel.vue";
import CvPanel from "../components/CvPanel.vue";
import OfferBrief from "../components/OfferBrief.vue";
import PrepCertificates from "../components/PrepCertificates.vue";
import FormSheet from "../components/FormSheet.vue";
import PageHero from "../components/PageHero.vue";
import AiWriting from "../components/AiWriting.vue";
import AppIcon from "../components/AppIcon.vue";
import BusyButton from "../components/BusyButton.vue";
import FaceState from "../components/FaceState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import SuccessCard from "../components/SuccessCard.vue";
import HoverNote from "../components/HoverNote.vue";
import { useAssistant } from "../composables/useAssistant";
import { useJobsMemory } from "../composables/useJobsMemory";
import { dateWithTime } from "../dates";
import { expiredText, ofMonth } from "../format";
import StatusPill from "../components/StatusPill.vue";
import InlineConfirm from "../components/InlineConfirm.vue";
import { usePlan } from "../composables/usePlan";
import PlanLimit from "../components/PlanLimit.vue";

const { aiNote, reached, refresh: refreshPlan } = usePlan();

const route = useRoute();
const router = useRouter();
const offerId = Number(route.params.id);
// Trois onglets numérotés (docs/47 §2) : ① Lettre, ② CV, ③ Postuler ; ④ Suivre une fois la
// candidature envoyée (docs/124 §G).
const tab = computed(() =>
  route.query.doc === "cv" ? "cv" : route.query.doc === "postuler" ? "apply" : route.query.doc === "suivre" ? "follow" : "letter",
);

// « Postuler sur … » (docs/13 §1), dans l'onglet Postuler.
const SITE_NAMES: Record<string, string> = { jobup: "jobup", indeed: "Indeed", jobroom: "Job-Room" };
const applyLink = computed(() => {
  const o = offer.value;
  if (!o) return null;
  // Annonce trouvée chez l'employeur (docs/20 §2) : c'est là qu'on postule.
  if (o.employer_url) return { url: o.employer_url, label: "Postuler chez l'employeur" };
  if (o.apply_url) {
    return { url: o.apply_url, label: o.apply_kind === "external" ? "Postuler chez l'employeur" : "Postuler sur jobup" };
  }
  const link = o.links[0];
  if (link?.source === "manual") return { url: link.url, label: "Ouvrir l'annonce" };
  return link ? { url: link.url, label: `Postuler sur ${SITE_NAMES[link.source] ?? link.source}` } : null;
});
const currentCvId = ref<number | null>(null);
const currentLetterId = computed(() => current(letters.value)?.id ?? null);
// Corps de la lettre, pour les formulaires qui le demandent en texte (docs/25 §5).
const currentLetterText = computed(() => current(letters.value)?.paragraphs.map((p) => p.text).join("\n\n") ?? null);
// Un seul bouton plein (docs/29 §1.3) : la prochaine étape — la lettre, puis le CV, puis postuler.
const nextStep = computed<"letter" | "cv" | "apply">(() =>
  !currentLetterId.value ? "letter" : !currentCvId.value ? "cv" : "apply",
);
const applying = ref<ApplicationFormValue | null>(null);
const applyError = ref("");
// Le moment « candidature envoyée », sur la carte qui vient devant (docs/61 §1) : où elle compte
// pour l'ORP.
const sent = ref<{ company: string; month: string; count: number | null; target: number | null } | null>(null);

async function openApplication(): Promise<void> {
  applyError.value = "";
  const { data } = await api.GET("/api/offers/{offer_id}/application-prefill", {
    params: { path: { offer_id: offerId } },
  });
  if (data) applying.value = { ...data, status: "en_attente" };
}

async function saveApplication(value: ApplicationFormValue): Promise<void> {
  const { data, error: err } = await api.POST("/api/applications", {
    body: { ...applicationBody(value), offer_id: offerId },
  });
  if (!data) {
    const message = (err as { detail?: unknown } | undefined)?.detail;
    applyError.value = typeof message === "string" ? message : "Enregistrement impossible pour l'instant : réessaie.";
    return;
  }
  applying.value = null;
  useJobsMemory().sent(offerId);
  sent.value = { company: data.company, month: data.orp_month, count: null, target: null };
  const orp = await api.GET("/api/orp", { params: { query: { month: data.orp_month } } }).catch(() => null);
  if (orp?.data && sent.value) sent.value = { ...sent.value, count: orp.data.count, target: orp.data.target ?? null };
  const refreshed = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: offerId } } });
  if (refreshed.data) offer.value = refreshed.data;
  // L'étape ④ Suivre s'ouvre (docs/124 §G).
  void router.replace({ query: { ...route.query, doc: "suivre" } });
}

// « Ajouter un contact » de l'étape Suivre : les contacts sont à côté.
function focusContacts(): void {
  const side = document.querySelector<HTMLElement>("[data-test=apply-contacts]");
  side?.scrollIntoView({ behavior: "smooth", block: "center" });
  side?.querySelector<HTMLElement>("button, input")?.focus({ preventScroll: true });
}

const offer = ref<Offer | null>(null);
// Sur téléphone, la barre des étapes défile : l'étape ouverte reste en vue.
watch(
  [tab, () => !!offer.value],
  () =>
    void nextTick(() =>
      document.querySelector<HTMLElement>(".prep-steps a.active")?.scrollIntoView?.({ inline: "nearest", block: "nearest" }),
    ),
  { immediate: true },
);

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
  return typeof value === "string" ? value.charAt(0).toUpperCase() + value.slice(1) + "." : fallback;
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
async function write(force = false): Promise<void> {
  if (dirty.value && !force) {
    choosingWrite.value = true;
    return;
  }
  choosingWrite.value = false;
  writing.value = true;
  error.value = "";
  try {
    const { data, error: err } = await api.POST("/api/offers/{offer_id}/letters", {
      params: { path: { offer_id: offerId } },
      body: {
        language: language.value || null,
        instruction: instruction.value.trim() || null,
        base_draft_id: instruction.value.trim() && selectedId.value ? selectedId.value : null,
      },
    });
    // Le compteur de la formule suit ; à la limite, la ligne grise dit pourquoi (docs/125 §4).
    await refreshPlan();
    if (!data) {
      if (!reached("letter")) error.value = detail(err, "La rédaction a échoué, réessaie.");
      return;
    }
    letters.value = [data, ...letters.value];
    instruction.value = "";
    select(data);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
  } catch {
    error.value = "API injoignable.";
  } finally {
    writing.value = false;
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

function sources(ids: number[]): string {
  return ids
    .map((id) => chunkTitles.value[id])
    .filter(Boolean)
    .join(", ");
}

function versionLabel(letter: Letter): string {
  // L'heure compte : plusieurs versions le même jour (« modifiée aujourd'hui à 14 h 05 »).
  const when = dateWithTime(letter.edited_at ?? letter.created_at);
  const what = letter.instruction ? `« ${letter.instruction} »` : "première rédaction";
  return `v${letter.version} · ${LANGUAGES[letter.language]} · ${what} · ${letter.edited_at ? "modifiée" : "rédigée"} ${when}`;
}

onMounted(() => void load());
</script>

<template>
  <PageHero :title="offer?.title ?? (notFound ? 'Offre introuvable' : '')">
    <!-- Toujours visible : revenir aux offres à tout moment (retour d'usage du 2026-10-07), en
         haut à gauche (0.99.1). -->
    <template #back>
      <RouterLink
        to="/candidatures/offres"
        class="back-link prep-back"
        data-test="back-to-offers"
      >
        <AppIcon name="arrow-left" />Offres
      </RouterLink>
    </template>
    <p
      v-if="offer"
      class="page-head-sub prep-sub"
    >
      {{ [offer.company, offer.location].filter(Boolean).join(" · ") }}
    </p>
    <!-- Les étapes ont la même adresse (seul `?doc=` change) : RouterLink les dirait toutes
         « page actuelle » ; seule l'étape ouverte est annoncée (WCAG 4.1.2, audit du 22.10.2026). -->
    <nav
      v-if="offer"
      class="prep-tabs prep-steps"
      aria-label="Étapes de la candidature"
    >
      <RouterLink
        :to="{ query: {} }"
        :class="{ active: tab === 'letter' }"
        :aria-current="tab === 'letter' ? 'step' : undefined"
        data-test="tab-letter"
      >
        <span class="step-number">1</span><span class="with-icon"><AppIcon name="mail" />Lettre</span><span
          v-if="currentLetterId"
          class="step-done"
          data-test="step-done"
        ><AppIcon name="done" /><span class="visually-hidden">faite</span></span>
      </RouterLink>
      <RouterLink
        :to="{ query: { doc: 'cv' } }"
        :class="{ active: tab === 'cv' }"
        :aria-current="tab === 'cv' ? 'step' : undefined"
        data-test="tab-cv"
      >
        <span class="step-number">2</span><span class="with-icon"><AppIcon name="file" />CV</span><span
          v-if="currentCvId"
          class="step-done"
          data-test="step-done"
        ><AppIcon name="done" /><span class="visually-hidden">fait</span></span>
      </RouterLink>
      <RouterLink
        :to="{ query: { doc: 'postuler' } }"
        :class="{ active: tab === 'apply' }"
        :aria-current="tab === 'apply' ? 'step' : undefined"
        data-test="tab-apply"
      >
        <span class="step-number">3</span><span class="with-icon"><AppIcon name="send" />Postuler</span><span
          v-if="offer.status === 'applied'"
          class="step-done"
          data-test="step-done"
        ><AppIcon name="done" /><span class="visually-hidden">fait</span></span>
      </RouterLink>
      <RouterLink
        v-if="offer.status === 'applied'"
        :to="{ query: { doc: 'suivre' } }"
        :class="{ active: tab === 'follow' }"
        :aria-current="tab === 'follow' ? 'step' : undefined"
        data-test="tab-follow"
      >
        <span class="step-number">4</span><span class="with-icon"><AppIcon name="clock" />Suivre</span>
      </RouterLink>
    </nav>
  </PageHero>

  <section class="band">
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
      <div
        v-if="offer?.status === 'applied'"
        class="apply-bar"
        data-test="apply-bar"
      >
        <StatusPill
          tone="ok"
          data-test="applied-pill"
        >
          Candidature envoyée
        </StatusPill>
        <RouterLink
          to="/candidatures/offres"
          class="button-link primary-link"
          data-test="next-offers"
        >
          <span class="with-icon"><AppIcon name="arrow-left" />Revenir aux offres</span>
        </RouterLink>
        <RouterLink
          to="/candidatures/suivi"
          class="link"
        >
          Voir le suivi
        </RouterLink>
      </div>


      <!-- ③ Postuler (docs/47 §2) : dans l'ordre où on le fait ; les contacts à côté. -->
      <div
        v-if="offer && (tab === 'apply' || tab === 'follow')"
        class="prep-layout"
        data-test="apply-steps"
      >
        <FollowStep
          v-if="tab === 'follow' && offer.status === 'applied'"
          class="prep-main"
          :offer-id="offer.id"
          @add-contact="focusContacts"
        />
        <div
          v-else
          class="apply-steps"
        >
          <template v-if="offer.status !== 'applied'">
            <!-- Numéros par compteur CSS : sur téléphone, « Postuler » est fixé en bas et sa
                 section disparaît, les étapes se renumérotent (docs/51 n° 4). -->
            <section class="panel-section apply-step apply-step-post">
              <h3>Postuler</h3>
              <div class="mobile-dock">
                <a
                  v-if="applyLink"
                  :href="applyLink.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="button-link primary-link"
                  data-test="apply"
                >{{ applyLink.label }}</a>
              </div>
            </section>
            <section
              class="panel-section apply-step"
              data-test="apply-sheet"
            >
              <h3>À recopier sur le site de l'employeur</h3>
              <!-- Visible aussi sur téléphone, où la section « Postuler » laisse place au bouton fixé. -->
              <PrepCertificates />
              <FormSheet
                class="reading-width"
                :letter-text="currentLetterText"
                :letter-id="currentLetterId"
                :cv-id="currentCvId"
              />
            </section>
            <section class="panel-section apply-step">
              <h3>
                <HoverNote text="Elle passe dans ton suivi et compte pour tes preuves ORP du mois.">
                  J'ai postulé
                </HoverNote>
              </h3>
              <button
                type="button"
                class="secondary small apply-done"
                data-test="mark-applied"
                @click="openApplication"
              >
                Marquer comme envoyée
              </button>
            </section>
          </template>

          <p
            v-else
            class="hint"
          >
            Candidature envoyée. <RouterLink :to="{ query: { doc: 'suivre' } }">
              Suivre
            </RouterLink>
          </p>
        </div>
        <section
          v-if="offer.company"
          class="prep-side"
        >
          <div
            class="side-card"
            data-test="apply-contacts"
          >
            <h2>Contacts chez {{ offer.company }}</h2>
            <ContactsPanel :offer-id="offer.id" />
          </div>
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

          <div
            v-if="!selected && !writing"
            class="empty-detail prep-empty"
            data-test="no-letter"
          >
            <p>Aucune lettre pour cette offre.</p>
          </div>
          <AiWriting
            v-else-if="writing && !selected"
            kind="letter"
          />

          <article
            v-if="doc && draft"
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
            <div
              v-for="(paragraph, index) in draft.paragraphs"
              :key="index"
              class="letter-paragraph"
            >
              <textarea
                v-model="paragraph.text"
                class="screen-only"
                rows="3"
                :aria-label="`Paragraphe ${index + 1}`"
                data-test="paragraph"
                @input="onInput"
              />
              <p class="print-only">
                {{ paragraph.text }}
              </p>
              <span
                v-if="sources(paragraph.chunk_ids)"
                class="chunk-refs screen-only"
              >Blocs : {{ sources(paragraph.chunk_ids) }}</span>
            </div>
            <p>{{ doc.closing }}</p>
            <p class="letter-signature">
              {{ doc.signature }}
            </p>
            <p class="letter-enclosure">
              {{ doc.enclosure }}
            </p>
          </article>
        </div>

        <section class="prep-side">
          <OfferBrief :offer="offer" />
          <div class="side-card">
            <h2>
              {{ selected ? "Nouvelle version" : "Rédiger la lettre" }}
            </h2>
            <label>Langue
              <select
                v-model="language"
                data-test="language"
              >
                <option value="">Celle de l'annonce</option>
                <option
                  v-for="(label, code) in LANGUAGES"
                  :key="code"
                  :value="code"
                >{{ label }}</option>
              </select>
            </label>
            <label v-if="selected">Consigne (facultative)
              <textarea
                v-model="instruction"
                rows="2"
                maxlength="500"
                placeholder="plus court, insiste sur Kubernetes…"
                data-test="instruction"
              />
            </label>
            <div class="mobile-dock">
              <BusyButton
                :class="nextStep === 'letter' ? 'primary' : 'secondary'"
                :busy="writing"
                busy-label="Rédaction…"
                :disabled="reached('letter')"
                data-test="write"
                @click="write()"
              >
                <HoverNote :text="writing ? '' : aiNote('Environ 0,10 $.', 'letter')">
                  <span class="with-icon"><AppIcon name="ai" />{{ selected ? "Nouvelle version" : "Rédiger la lettre" }}</span>
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
                :href="`/api/letters/${selected.id}/pdf`"
                download
                data-test="pdf"
              ><span class="with-icon"><AppIcon name="download" />PDF</span></a>
              <a
                class="secondary"
                :href="`/api/letters/${selected.id}/docx`"
                download
                data-test="docx"
              ><span class="with-icon"><AppIcon name="download" />Word</span></a>
            </div>
          </div>

          <div
            v-if="letters.length > 1"
            class="side-card"
          >
            <h2>Versions</h2>
            <ul class="versions">
              <li
                v-for="letter in letters"
                :key="letter.id"
              >
                <button
                  type="button"
                  :class="['link', { active: letter.id === selectedId }]"
                  data-test="version"
                  @click="select(letter)"
                >
                  {{ versionLabel(letter) }}
                </button>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  </section>

  <SuccessCard
    v-if="sent"
    name="suivi-envoi"
    :title="`Candidature envoyée chez ${sent.company}`"
    test-id="sent-moment"
    @close="sent = null"
  >
    <p v-if="sent.count !== null">
      Comptée pour l'ORP {{ ofMonth(sent.month) }} :
      <strong>{{ sent.count }}{{ sent.target ? ` sur ${sent.target}` : "" }}</strong>
    </p>
  </SuccessCard>
  <ApplicationForm
    v-if="applying"
    title="Candidature envoyée"
    :initial="applying"
    :with-status="false"
    :error="applyError"
    @submit="saveApplication"
    @close="applying = null"
  />
</template>
