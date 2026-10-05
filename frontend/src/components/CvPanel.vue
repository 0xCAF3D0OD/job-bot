<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, type Cv, type LetterLanguage, type Offer } from "../api/client";
import { printSheet } from "../composables/usePrint";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer }>();
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

async function write(): Promise<void> {
  if (dirty.value && !window.confirm("Tu as des modifications non enregistrées dans cette version. Rédiger quand même une nouvelle version ?")) {
    return;
  }
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

function print(): void {
  const sheet = document.querySelector<HTMLElement>(".cv-sheet");
  const who = doc.value?.name ? ` - ${doc.value.name}` : "";
  if (sheet) printSheet(sheet, { title: `CV${who} - ${props.offer.company ?? props.offer.title}` });
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
        <p class="hint">
          L'IA choisit et ordonne tes blocs de profil pour cette offre, et écrit un titre et un résumé de 2 ou 3
          lignes (≈ 0,05 $). Le texte de tes expériences n'est pas réécrit.
        </p>
      </div>
      <div
        v-else-if="writing && !selected"
        class="empty-detail prep-empty"
        role="status"
      >
        Préparation du CV en cours…
      </div>

      <article
        v-if="doc && selected"
        class="cv-sheet print-sheet"
        :class="{ busy: writing || saving }"
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
      <div class="side-card">
        <h2>{{ selected ? "Nouvelle version" : "Préparer le CV" }}</h2>
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
        <button
          type="button"
          class="primary"
          :disabled="writing"
          data-test="write-cv"
          @click="write"
        >
          {{ writing ? "Préparation…" : selected ? "Préparer une nouvelle version" : "Préparer le CV" }}
          <AppIcon name="chevron" />
        </button>
      </div>

      <div
        v-if="selected"
        class="side-card"
      >
        <h2>Blocs du CV</h2>
        <p class="hint">
          Coche, décoche et ordonne ; le CV se met à jour aussitôt. Garde-le sur une page.
        </p>
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
                <button
                  type="button"
                  class="move secondary"
                  :disabled="saving || !canMove(block.id, block.section, -1)"
                  :aria-label="`Monter ${block.title}`"
                  data-test="move-up"
                  @click="move(block.id, block.section, -1)"
                >
                  ↑
                </button>
                <button
                  type="button"
                  class="move secondary"
                  :disabled="saving || !canMove(block.id, block.section, 1)"
                  :aria-label="`Descendre ${block.title}`"
                  @click="move(block.id, block.section, 1)"
                >
                  ↓
                </button>
              </template>
            </li>
          </template>
        </ul>
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
          data-test="save-cv"
          @click="save()"
        >
          {{ dirty ? "Enregistrer le titre et le résumé" : "Aucune modification" }}
        </button>
        <button
          type="button"
          class="secondary"
          :disabled="dirty"
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
            :href="`/api/cvs/${selected.id}/docx`"
            download
            data-test="cv-docx"
          >Télécharger en Word</a>
        </div>
        <p class="hint">
          PDF : choisis « Enregistrer au format PDF » dans la fenêtre d'impression.
        </p>
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
