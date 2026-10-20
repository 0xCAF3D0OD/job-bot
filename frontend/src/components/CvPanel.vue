<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, type Cv, type LetterLanguage, type Offer } from "../api/client";
import OfferBrief from "./OfferBrief.vue";
import AiWriting from "./AiWriting.vue";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import HoverNote from "./HoverNote.vue";
import InlineConfirm from "./InlineConfirm.vue";

// `primary` : le CV est la prochaine étape de la préparation (docs/29 §1.3).
const props = defineProps<{ offer: Offer; primary?: boolean }>();
// Version affichée, pour le lien « CV (Word) » de la barre de la page.
const emit = defineEmits<{ current: [id: number | null] }>();

const LANGUAGES: Record<LetterLanguage, string> = { fr: "Français", en: "English", de: "Deutsch" };
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
    const text = instruction.value.trim();
    const { data, error: err } = await api.POST("/api/offers/{offer_id}/cvs", {
      params: { path: { offer_id: props.offer.id } },
      body: {
        language: language.value || null,
        instruction: text || null,
        base_draft_id: text && selectedId.value ? selectedId.value : null,
      },
    });
    if (!data) {
      error.value = detail(err, "La préparation du CV a échoué, réessaie.");
      return;
    }
    cvs.value = [data, ...cvs.value];
    instruction.value = "";
    show(data);
    fresh.value = true;
    setTimeout(() => (fresh.value = false), 1000);
  } catch {
    error.value = "API injoignable.";
  } finally {
    writing.value = false;
  }
}

async function save(chunkIds?: number[]): Promise<void> {
  const cv = selected.value;
  if (!cv) return;
  saving.value = true;
  error.value = "";
  try {
    const { data, error: err } = await api.PUT("/api/cvs/{draft_id}", {
      params: { path: { draft_id: cv.id } },
      body: { headline: edit.value.headline, summary: edit.value.summary, chunk_ids: chunkIds ?? cv.chunk_ids },
    });
    if (!data) {
      error.value = detail(err, "Enregistrement refusé.");
      return;
    }
    cvs.value = cvs.value.map((c) => (c.id === data.id ? data : c));
    show(data);
  } finally {
    saving.value = false;
  }
}

function toggle(id: number, checked: boolean): void {
  const ids = selected.value?.chunk_ids ?? [];
  if (!checked && ids.length === 1) {
    error.value = "Garde au moins un bloc dans le CV.";
    return;
  }
  void save(checked ? [...ids, id] : ids.filter((i) => i !== id));
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
  const when = new Date(cv.edited_at ?? cv.created_at).toLocaleString("fr-CH", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  const what = cv.instruction ? `« ${cv.instruction} »` : "première version";
  return `v${cv.version} · ${LANGUAGES[cv.language]} · ${what} · ${cv.edited_at ? "modifiée" : "préparée"} ${when}`;
}

onMounted(() => void load());
</script>

<template>
  <div class="prep-layout">
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
        v-if="loaded && !selected && !writing"
        class="empty-detail prep-empty"
        data-test="no-cv"
      >
        <p>Aucun CV adapté pour cette offre.</p>
      </div>
      <AiWriting
        v-else-if="writing && !selected"
        kind="cv"
      />

      <article
        v-if="doc && selected"
        class="cv-sheet print-sheet"
        :class="{ 'fresh-lines': fresh, busy: writing || saving }"
        :lang="doc.language"
        data-test="cv"
      >
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
        <p class="print-only">
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
            class="cv-item"
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
    </div>

    <aside class="prep-side">
      <OfferBrief :offer="offer" />
      <div class="side-card">
        <h2>
          {{ selected ? "Nouvelle version" : "Préparer le CV" }}
        </h2>
        <label>Langue du titre et du résumé
          <select
            v-model="language"
            data-test="cv-language"
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
            placeholder="mets le projet personnel en premier…"
            data-test="cv-instruction"
          />
        </label>
        <div class="mobile-dock">
          <button
            type="button"
            :class="primary ? 'primary' : 'secondary'"
            :disabled="writing"
            data-test="write-cv"
            @click="write()"
          >
            <HoverNote :text="writing ? '' : 'Environ 0,05 $.'">
              <span class="with-icon"><AppIcon name="ai" />{{ writing ? "Préparation…" : selected ? "Nouvelle version" : "Préparer le CV" }}</span>
            </HoverNote>
          </button>
        </div>
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
      >
        <h2>
          Blocs du CV
        </h2>
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
                  @change="toggle(block.id, ($event.target as HTMLInputElement).checked)"
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
      </div>

      <div
        v-if="selected"
        class="side-card"
      >
        <h2>Télécharger</h2>
        <template v-if="dirty">
          <button
            type="button"
            class="secondary"
            :disabled="saving"
            data-test="save-cv"
            @click="save()"
          >
            Enregistrer le titre et le résumé
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
            :href="`/api/cvs/${selected.id}/pdf`"
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
        v-if="cvs.length > 1"
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
    </aside>
  </div>
</template>
