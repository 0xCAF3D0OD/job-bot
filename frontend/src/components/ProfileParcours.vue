<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import {
  api,
  type Chunk,
  type ChunkIn,
  type ChunkKind,
  type ChunkProposal,
  type DocumentOut,
  type DocumentText,
} from "../api/client";
import AppIcon from "./AppIcon.vue";
import ChunkProposals from "./ChunkProposals.vue";
import TagInput from "./TagInput.vue";
import { formatDate } from "../format";

const KINDS: { value: ChunkKind; label: string; hint: string }[] = [
  { value: "experience", label: "Expérience", hint: "Un poste, une mission, avec dates et réalisations." },
  { value: "competence", label: "Compétence", hint: "Un savoir-faire, un outil, un niveau." },
  { value: "formation", label: "Formation", hint: "Diplôme, certification, cours." },
  { value: "preference", label: "Préférence", hint: "Ce que tu recherches : équipe, rythme, télétravail…" },
  { value: "redhibitoire", label: "Rédhibitoire", hint: "Ce que tu refuses." },
  { value: "ton", label: "Ton", hint: "Comment tes lettres doivent sonner." },
];
const kindLabel = Object.fromEntries(KINDS.map((k) => [k.value, k.label])) as Record<ChunkKind, string>;

type ChunkForm = Required<ChunkIn>;
const EMPTY_CHUNK: ChunkForm = {
  kind: "experience",
  title: "",
  content: "",
  tags: [],
  active: true,
  document_id: null,
};

const documents = ref<DocumentOut[]>([]);
const chunks = ref<Chunk[]>([]);
const openText = ref<DocumentText | null>(null);
const openDocument = computed(() => documents.value.find((d) => d.id === openText.value?.id) ?? null);
const textBox = ref<HTMLElement | null>(null);
const filter = ref<ChunkKind | "all">("all");
const editing = ref<{ id: number | null; form: ChunkForm } | null>(null);
const uploading = ref(false);
const proposing = ref<number | null>(null);
const proposal = ref<{ doc: DocumentOut; items: ChunkProposal[] } | null>(null);
const message = ref("");

const visibleChunks = computed(() =>
  filter.value === "all" ? chunks.value : chunks.value.filter((c) => c.kind === filter.value),
);

function kindCount(kind: ChunkKind): number {
  return chunks.value.filter((c) => c.kind === kind).length;
}

function sizeText(size: number): string {
  return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} Ko` : `${(size / 1024 / 1024).toFixed(1)} Mo`;
}

async function loadDocuments(): Promise<void> {
  const { data } = await api.GET("/api/documents");
  documents.value = data ?? [];
}

async function loadChunks(): Promise<void> {
  const { data } = await api.GET("/api/profile-chunks");
  chunks.value = data ?? [];
}

async function onFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  uploading.value = true;
  message.value = "";
  try {
    const { data, error, response } = await api.POST("/api/documents", {
      body: { file: "" },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    if (data) {
      await loadDocuments();
      await showText(data.id);
      message.value = data.text_status === "ok" ? "" : "Document déposé, mais son texte n'est pas lisible (PDF scanné ?).";
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Refusé : ${detail}.` : `Refusé (HTTP ${response.status}).`;
    }
  } catch {
    message.value = "API injoignable.";
  } finally {
    uploading.value = false;
  }
}

async function showText(id: number): Promise<void> {
  const { data } = await api.GET("/api/documents/{document_id}/text", {
    params: { path: { document_id: id } },
  });
  openText.value = data ?? null;
}

async function propose(doc: DocumentOut): Promise<void> {
  proposing.value = doc.id;
  message.value = "";
  try {
    const { data, error, response } = await api.POST("/api/documents/{document_id}/propose-chunks", {
      params: { path: { document_id: doc.id } },
    });
    if (data) {
      if (data.length) proposal.value = { doc, items: data };
      else message.value = "L'IA n'a rien trouvé à proposer dans ce document.";
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Impossible : ${detail}.` : `Échec (HTTP ${response.status}).`;
    }
  } catch {
    message.value = "API injoignable.";
  } finally {
    proposing.value = null;
  }
}

async function onProposalsSaved(count: number): Promise<void> {
  proposal.value = null;
  message.value = `${count} bloc(s) ajouté(s) à ton profil.`;
  await Promise.all([loadChunks(), loadDocuments()]);
}

async function removeDocument(doc: DocumentOut): Promise<void> {
  if (!window.confirm(`Supprimer « ${doc.filename} » ? Les blocs créés à partir de lui sont gardés.`)) return;
  await api.DELETE("/api/documents/{document_id}", { params: { path: { document_id: doc.id } } });
  if (openText.value?.id === doc.id) openText.value = null;
  await Promise.all([loadDocuments(), loadChunks()]);
}

function newChunk(content = "", documentId: number | null = null): void {
  editing.value = { id: null, form: { ...EMPTY_CHUNK, content, document_id: documentId } };
}

function chunkFromSelection(): void {
  const selection = window.getSelection();
  const selected = selection?.toString().trim() ?? "";
  const inside = selection?.anchorNode && textBox.value?.contains(selection.anchorNode);
  if (!selected || !inside) {
    message.value = "Sélectionne d'abord un passage dans le texte du document.";
    return;
  }
  message.value = "";
  newChunk(selected, openText.value?.id ?? null);
}

function editChunk(chunk: Chunk): void {
  editing.value = {
    id: chunk.id,
    form: {
      kind: chunk.kind,
      title: chunk.title,
      content: chunk.content,
      tags: [...(chunk.tags ?? [])],
      active: chunk.active ?? true,
      document_id: chunk.document_id ?? null,
    },
  };
}

async function saveChunk(): Promise<void> {
  if (!editing.value) return;
  const { id, form } = editing.value;
  const result = id === null
    ? await api.POST("/api/profile-chunks", { body: form })
    : await api.PUT("/api/profile-chunks/{chunk_id}", { params: { path: { chunk_id: id } }, body: form });
  if (result.data) {
    editing.value = null;
    await Promise.all([loadChunks(), loadDocuments()]);
  } else {
    message.value = "Bloc refusé : titre et contenu sont obligatoires.";
  }
}

async function removeChunk(chunk: Chunk): Promise<void> {
  if (!window.confirm(`Supprimer le bloc « ${chunk.title} » ?`)) return;
  await api.DELETE("/api/profile-chunks/{chunk_id}", { params: { path: { chunk_id: chunk.id } } });
  await Promise.all([loadChunks(), loadDocuments()]);
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape") return;
  editing.value = null;
  proposal.value = null;
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  void Promise.all([loadDocuments(), loadChunks()]);
});
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div class="panel">
    <p
      v-if="message"
      class="notice"
      role="status"
    >
      {{ message }}
    </p>

    <h2 class="section-title first">
      Documents
    </h2>
    <div class="profile-docs">
      <div class="doc-column">
        <label
          class="drop-zone"
          :class="{ busy: uploading }"
        >
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md"
            data-test="file-input"
            @change="onFile"
          >
          <span class="drop-title">{{ uploading ? "Envoi…" : "Déposer un document" }}</span>
          <span class="detail">PDF, DOCX, TXT ou MD · 10 Mo au plus · stocké en local, jamais dans git</span>
        </label>

        <ul class="doc-list">
          <li
            v-for="doc in documents"
            :key="doc.id"
            :class="['doc-card', { selected: openText?.id === doc.id }]"
            data-test="document"
          >
            <span :class="['logo', 'c' + (doc.doc_type === 'pdf' ? 0 : doc.doc_type === 'docx' ? 3 : 2)]">
              {{ doc.doc_type.toUpperCase().slice(0, 3) }}
            </span>
            <div class="doc-info">
              <span class="job-title">{{ doc.filename }}</span>
              <span class="job-company">
                {{ sizeText(doc.size) }} · {{ formatDate(doc.uploaded_at) }} · {{ doc.chunk_count }} bloc(s)
              </span>
              <span
                v-if="doc.text_status !== 'ok'"
                class="badge reason"
              >{{ doc.text_status === "empty" ? "aucun texte" : "texte non lisible" }}</span>
            </div>
            <div class="doc-actions">
              <button
                type="button"
                class="secondary small"
                @click="showText(doc.id)"
              >
                Texte
              </button>
              <button
                v-if="doc.text_status === 'ok'"
                type="button"
                class="primary small"
                :disabled="proposing !== null"
                :data-test="`propose-${doc.id}`"
                @click="propose(doc)"
              >
                {{ proposing === doc.id ? "L'IA lit le document… (≈ 30 s)" : "Proposer des blocs" }}
              </button>
              <a
                class="link"
                :href="`/api/documents/${doc.id}/file`"
                target="_blank"
                rel="noopener noreferrer"
              >Ouvrir</a>
              <button
                type="button"
                class="link danger"
                :aria-label="`Supprimer ${doc.filename}`"
                @click="removeDocument(doc)"
              >
                Supprimer
              </button>
            </div>
          </li>
        </ul>
        <p
          v-if="!documents.length"
          class="muted"
        >
          Aucun document pour l'instant : commence par ton CV.
        </p>
      </div>

      <article
        v-if="openText"
        class="detail-panel text-panel"
        data-test="document-text"
      >
        <div class="text-head">
          <h3>{{ openDocument?.filename }}</h3>
          <button
            type="button"
            class="primary small"
            :disabled="openText.text_status !== 'ok'"
            data-test="chunk-from-selection"
            @click="chunkFromSelection"
          >
            Créer un bloc avec la sélection <AppIcon name="chevron" />
          </button>
        </div>
        <div
          ref="textBox"
          class="doc-text"
        >
          {{ openText.text || "Aucun texte n'a pu être extrait de ce document." }}
        </div>
      </article>
      <div
        v-else
        class="detail-panel empty-detail"
      >
        Choisis « Texte » sur un document pour le lire ici et en tirer des blocs.
      </div>
    </div>

    <div class="chunks-head">
      <h2 class="section-title">
        Blocs de profil
      </h2>
      <button
        type="button"
        class="primary"
        data-test="new-chunk"
        @click="newChunk()"
      >
        Nouveau bloc <AppIcon name="chevron" />
      </button>
    </div>
    <div
      class="tabs kind-tabs"
      role="tablist"
      aria-label="Types de blocs"
    >
      <button
        type="button"
        role="tab"
        :aria-selected="filter === 'all'"
        @click="filter = 'all'"
      >
        Tous <span class="tab-count">{{ chunks.length }}</span>
      </button>
      <button
        v-for="kind in KINDS"
        :key="kind.value"
        type="button"
        role="tab"
        :aria-selected="filter === kind.value"
        @click="filter = kind.value"
      >
        {{ kind.label }} <span class="tab-count">{{ kindCount(kind.value) }}</span>
      </button>
    </div>

    <ul class="chunk-grid">
      <li
        v-for="chunk in visibleChunks"
        :key="chunk.id"
        :class="['job-card', 'chunk-card', { inactive: !chunk.active }]"
        data-test="chunk"
      >
        <div class="chunk-top">
          <span class="badge">{{ kindLabel[chunk.kind] }}</span>
          <span
            v-if="!chunk.active"
            class="badge reason"
          >inactif</span>
        </div>
        <span class="job-title">{{ chunk.title }}</span>
        <p class="job-snippet chunk-content">
          {{ chunk.content }}
        </p>
        <div class="job-meta">
          <span
            v-for="tag in chunk.tags"
            :key="tag"
          >#{{ tag }}</span>
          <span class="chunk-actions">
            <button
              type="button"
              class="link"
              @click="editChunk(chunk)"
            >Modifier</button>
            <button
              type="button"
              class="link danger"
              @click="removeChunk(chunk)"
            >Supprimer</button>
          </span>
        </div>
      </li>
    </ul>
    <p
      v-if="!visibleChunks.length"
      class="muted empty"
    >
      Aucun bloc ici. Crée-en un, ou sélectionne un passage dans un document.
    </p>
  </div>

  <ChunkProposals
    v-if="proposal"
    :document-id="proposal.doc.id"
    :document-name="proposal.doc.filename"
    :proposals="proposal.items"
    :existing="chunks"
    @close="proposal = null"
    @saved="onProposalsSaved"
  />

  <div
    v-if="editing"
    class="overlay"
    @click.self="editing = null"
  >
    <form
      class="form-card editor"
      data-test="chunk-form"
      @submit.prevent="saveChunk"
    >
      <h3>{{ editing.id === null ? "Nouveau bloc" : "Modifier le bloc" }}</h3>
      <fieldset>
        <legend><label for="chunk-kind">Type</label></legend>
        <select
          id="chunk-kind"
          v-model="editing.form.kind"
        >
          <option
            v-for="kind in KINDS"
            :key="kind.value"
            :value="kind.value"
          >
            {{ kind.label }}
          </option>
        </select>
        <span class="hint">{{ KINDS.find((k) => k.value === editing?.form.kind)?.hint }}</span>
      </fieldset>
      <fieldset>
        <legend><label for="chunk-title">Titre</label></legend>
        <input
          id="chunk-title"
          v-model="editing.form.title"
          type="text"
          maxlength="200"
          required
        >
      </fieldset>
      <fieldset>
        <legend><label for="chunk-content">Contenu</label></legend>
        <textarea
          id="chunk-content"
          v-model="editing.form.content"
          rows="7"
          required
        />
      </fieldset>
      <fieldset>
        <legend>Étiquettes</legend>
        <TagInput
          id="chunk-tags"
          v-model="editing.form.tags"
          placeholder="infra, linux…"
        />
      </fieldset>
      <label class="check">
        <input
          v-model="editing.form.active"
          type="checkbox"
        >
        Actif : l'IA peut s'en servir
      </label>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          data-test="save-chunk"
        >
          Enregistrer <AppIcon name="chevron" />
        </button>
        <button
          type="button"
          class="secondary"
          @click="editing = null"
        >
          Annuler
        </button>
      </div>
    </form>
  </div>
</template>
