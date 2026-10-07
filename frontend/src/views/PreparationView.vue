<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api, type Letter, type LetterLanguage, type Offer } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import { applicationBody } from "../applicationBody";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import CvPanel from "../components/CvPanel.vue";
import PageHero from "../components/PageHero.vue";
import { printSheet } from "../composables/usePrint";
import { expiredText } from "../format";

const route = useRoute();
const offerId = Number(route.params.id);
const tab = computed(() => (route.query.doc === "cv" ? "cv" : "letter"));

// Barre « Postuler · Marquer comme envoyée · Télécharger » (docs/13 §1).
const SITE_NAMES: Record<string, string> = { jobup: "jobup", indeed: "Indeed", jobroom: "Job-Room" };
const applyLink = computed(() => {
  const o = offer.value;
  if (!o) return null;
  if (o.apply_url) {
    return { url: o.apply_url, label: o.apply_kind === "external" ? "Postuler chez l'employeur" : "Postuler sur jobup" };
  }
  const link = o.links[0];
  return link ? { url: link.url, label: `Ouvrir l'annonce sur ${SITE_NAMES[link.source] ?? link.source}` } : null;
});
const currentCvId = ref<number | null>(null);
const currentLetterId = computed(() => current(letters.value)?.id ?? null);
const applying = ref<ApplicationFormValue | null>(null);
const applyError = ref("");
const applyNotice = ref("");

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
    applyError.value = typeof message === "string" ? message : "Vérifie les champs obligatoires.";
    return;
  }
  applying.value = null;
  applyNotice.value = `Candidature chez ${data.company} enregistrée, avec ta lettre et ton CV.`;
  const refreshed = await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: offerId } } });
  if (refreshed.data) offer.value = refreshed.data;
}

const offer = ref<Offer | null>(null);
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

async function write(): Promise<void> {
  if (dirty.value && !window.confirm("Tu as des modifications non enregistrées dans cette version. Rédiger quand même une nouvelle version ?")) {
    return;
  }
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
    if (!data) {
      error.value = detail(err, "La rédaction a échoué, réessaie.");
      return;
    }
    letters.value = [data, ...letters.value];
    instruction.value = "";
    select(data);
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

function print(): void {
  const sheet = document.querySelector<HTMLElement>(".letter-sheet");
  if (sheet) printSheet(sheet, { title: `Lettre - ${offer.value?.company ?? offer.value?.title ?? "candidature"}` });
}

function edited(): void {
  dirty.value = true;
}

function resize(el: HTMLTextAreaElement): void {
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
  const when = new Date(letter.edited_at ?? letter.created_at).toLocaleString("fr-CH", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  const what = letter.instruction ? `« ${letter.instruction} »` : "première rédaction";
  return `v${letter.version} · ${LANGUAGES[letter.language]} · ${what} · ${letter.edited_at ? "modifiée" : "rédigée"} ${when}`;
}

onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Préparation"
    :title="offer?.title ?? (notFound ? 'Offre introuvable' : 'Chargement…')"
    :subtitle="offer ? [offer.company, offer.location].filter(Boolean).join(' · ') : undefined"
  />

  <section class="band">
    <div class="container">
      <p
        v-if="notFound"
        class="notice error"
      >
        Cette offre n'existe plus. <RouterLink to="/candidatures/offres">
          Retour aux offres
        </RouterLink>
      </p>

      <p
        v-if="offer?.expired_at && offer.status !== 'applied'"
        class="notice expired-notice"
        data-test="expired"
      >
        {{ expiredText(offer) }} Vérifie avant d'envoyer ta candidature.
      </p>
      <div
        v-if="offer"
        class="apply-bar"
        data-test="apply-bar"
      >
        <template v-if="offer.status === 'applied'">
          <span class="status-pill applied">Candidature envoyée</span>
          <RouterLink
            to="/candidatures/suivi"
            class="link"
          >
            Voir le suivi
          </RouterLink>
        </template>
        <template v-else>
          <a
            v-if="applyLink"
            :href="applyLink.url"
            target="_blank"
            rel="noopener noreferrer"
            class="button-link primary-link"
            data-test="apply"
          >{{ applyLink.label }} <AppIcon name="chevron" /></a>
          <button
            type="button"
            class="secondary small"
            data-test="mark-applied"
            @click="openApplication"
          >
            Marquer comme envoyée
          </button>
        </template>
        <span class="spacer" />
        <a
          v-if="currentLetterId"
          class="link"
          :href="`/api/letters/${currentLetterId}/docx`"
          download
          data-test="bar-letter"
        >Lettre (Word)</a>
        <a
          v-if="currentCvId"
          class="link"
          :href="`/api/cvs/${currentCvId}/docx`"
          download
          data-test="bar-cv"
        >CV (Word)</a>
      </div>
      <p
        v-if="applyNotice"
        class="notice"
        role="status"
      >
        {{ applyNotice }}
      </p>
      <nav
        v-if="offer"
        class="prep-tabs"
        aria-label="Documents"
      >
        <RouterLink
          :to="{ query: {} }"
          :class="{ active: tab === 'letter' }"
          data-test="tab-letter"
        >
          Lettre de motivation
        </RouterLink>
        <RouterLink
          :to="{ query: { doc: 'cv' } }"
          :class="{ active: tab === 'cv' }"
          data-test="tab-cv"
        >
          CV adapté
        </RouterLink>
      </nav>

      <CvPanel
        v-if="offer && tab === 'cv'"
        :offer="offer"
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
            <RouterLink to="/reglages">
              complète tes coordonnées
            </RouterLink>.
          </p>

          <div
            v-if="!selected && !writing"
            class="empty-detail prep-empty"
            data-test="no-letter"
          >
            <p>Aucune lettre pour cette offre.</p>
            <p class="hint">
              L'IA rédige l'objet et le corps à partir de tes blocs de profil (≈ 0,10 $). Tes coordonnées ne
              lui sont pas envoyées : la plateforme les ajoute à l'en-tête.
            </p>
          </div>
          <div
            v-else-if="writing && !selected"
            class="empty-detail prep-empty"
            role="status"
          >
            Rédaction en cours, compte une trentaine de secondes…
          </div>

          <article
            v-if="doc && draft"
            class="letter-sheet print-sheet"
            :class="{ busy: writing }"
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
                class="screen-only"
                aria-label="Objet de la lettre"
                data-test="subject"
                @input="edited"
              >
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

        <aside class="prep-side">
          <div class="side-card">
            <h2>{{ selected ? "Nouvelle version" : "Rédiger la lettre" }}</h2>
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
            <button
              type="button"
              class="primary"
              :disabled="writing"
              data-test="write"
              @click="write"
            >
              {{ writing ? "Rédaction…" : selected ? "Rédiger une nouvelle version" : "Rédiger la lettre" }}
              <AppIcon name="chevron" />
            </button>
          </div>

          <div
            v-if="selected"
            class="side-card"
          >
            <h2>Cette version</h2>
            <button
              type="button"
              class="secondary"
              :disabled="!dirty || saving"
              data-test="save-letter"
              @click="save"
            >
              {{ dirty ? "Enregistrer mes modifications" : "Aucune modification" }}
            </button>
            <button
              type="button"
              class="secondary"
              :disabled="dirty"
              data-test="print"
              @click="print"
            >
              Télécharger en PDF
            </button>
            <div
              v-if="!dirty"
              class="actions"
            >
              <a
                class="secondary"
                :href="`/api/letters/${selected.id}/docx`"
                download
                data-test="docx"
              >Télécharger en Word</a>
            </div>
            <p
              v-if="dirty"
              class="hint"
            >
              Enregistre d'abord tes modifications pour les télécharger.
            </p>
            <p class="hint">
              PDF : choisis « Enregistrer au format PDF » dans la fenêtre d'impression.
            </p>
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

          <div class="side-card">
            <p class="hint">
              Postule avec le bouton en haut de la page, puis « Marquer comme envoyée » : la candidature
              rejoint le suivi avec cette lettre et ton CV.
            </p>
            <RouterLink
              :to="{ path: '/candidatures/offres', query: { statut: 'in_progress' } }"
              class="link"
            >
              Retour aux offres en cours
            </RouterLink>
          </div>
        </aside>
      </div>
    </div>
  </section>

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
