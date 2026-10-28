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
import ChunkProposals from "./ChunkProposals.vue";
import SidePanel from "./SidePanel.vue";
import TagInput from "./TagInput.vue";
import { dateInList } from "../dates";
import { plural } from "../format";

import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import CertificatesSection from "./CertificatesSection.vue";
import { offerUndo } from "../composables/useUndo";
import CountBadge from "./CountBadge.vue";
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
// Les certificats de travail (docs/87) : la section se recharge quand un document change.
const certificatesVersion = ref(0);

async function setCertificate(doc: DocumentOut, certificate: boolean): Promise<void> {
  await api.PUT("/api/documents/{document_id}/kind", {
    params: { path: { document_id: doc.id } },
    body: { kind: certificate ? "certificate" : null },
  });
  openText.value = null;
  await loadDocuments();
  certificatesVersion.value += 1;
}
const chunks = ref<Chunk[]>([]);
// Un seul bouton plein (docs/29 §1.3) : tant qu'il n'y a aucun bloc, « Proposer des blocs » sur
// le premier document lisible ; ensuite, aucun d'office.
const firstReadable = computed(() =>
  chunks.value.length ? null : (documents.value.find((d) => d.text_status === "ok")?.id ?? null),
);
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
// Filtres (docs/49 §3) : seulement les types qui ont des blocs (et celui choisi).
const usedKinds = computed(() => KINDS.filter((k) => kindCount(k.value) || filter.value === k.value));

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
  message.value = `${plural(count, "bloc ajouté", "blocs ajoutés")} à ton profil.`;
  await Promise.all([loadChunks(), loadDocuments()]);
}

// Retiré tout de suite, « Annuler » pendant 6 s (docs/108 §1) ; les blocs créés à partir de lui restent.
async function removeDocument(doc: DocumentOut): Promise<void> {
  const before = documents.value;
  documents.value = before.filter((d) => d.id !== doc.id);
  if (openText.value?.id === doc.id) openText.value = null;
  await offerUndo({
    message: `« ${doc.filename} » supprimé`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/documents/{document_id}", { params: { path: { document_id: doc.id } }, keepalive });
      if (error !== undefined) return false;
      await Promise.all([loadDocuments(), loadChunks()]);
    },
    restore: () => {
      documents.value = before;
    },
  });
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

// Retiré tout de suite, « Annuler » pendant 6 s (docs/108 §1).
async function removeChunk(chunk: Chunk): Promise<void> {
  editing.value = null;
  const before = chunks.value;
  chunks.value = before.filter((c) => c.id !== chunk.id);
  await offerUndo({
    message: `Bloc « ${chunk.title} » supprimé`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/profile-chunks/{chunk_id}", { params: { path: { chunk_id: chunk.id } }, keepalive });
      if (error !== undefined) return false;
      await Promise.all([loadChunks(), loadDocuments()]);
    },
    restore: () => {
      chunks.value = before;
    },
  });
}

// Échap ferme les propositions ; les panneaux latéraux se ferment d'eux-mêmes.
function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") proposal.value = null;
}
const editedChunk = computed(() => chunks.value.find((c) => c.id === editing.value?.id) ?? null);
function chunkFoot(chunk: Chunk): string {
  const tags = chunk.tags?.length ? plural(chunk.tags.length, "mot-clé", "mots-clés") : "";
  // Ajouté en corrigeant une note (docs/114) : la personne voit d'où il vient.
  const origin = chunk.origin === "correction" ? "ajouté en corrigeant une note" : "";
  return [kindLabel[chunk.kind], tags, origin].filter(Boolean).join(" · ");
}

// Ce qui manque à l'IA pour noter et rédiger (docs/21 §6), affiché en premier.
const ready = ref(false);
const missingProfile = computed(() => {
  if (!ready.value) return "";
  // Sans document, l'encart de dépôt le dit déjà (docs/49 §2).
  if (!documents.value.length) return "";
  if (!chunks.value.some((c) => c.active)) {
    return "Il manque tes blocs de profil : « Proposer des blocs » les prépare à partir de ton CV.";
  }
  return "";
});

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  void Promise.all([loadDocuments(), loadChunks()]).then(() => {
    ready.value = true;
  });
});
onUnmounted(() => window.removeEventListener("keydown", onKeydown));

// Le document ouvert : « Créer un bloc » visible, le reste dans « ⋯ » (docs/74).
const documentItems = computed<MoreMenuItem[]>(() => {
  const doc = openDocument.value;
  if (!doc) return [];
  const certificate = doc.kind === "certificate";
  return [
    { label: "Ouvrir le fichier", test: "open-document-file", href: `/api/documents/${doc.id}/file` },
    {
      label: certificate ? "Ce n'est pas un certificat de travail" : "C'est un certificat de travail",
      test: "toggle-certificate",
      icon: "file",
      run: () => void setCertificate(doc, !certificate),
    },
    { label: "Supprimer ce document", test: "remove-document", danger: true, run: () => void removeDocument(doc) },
  ];
});
</script>

<template>
  <div class="panel">
    <p
      v-if="missingProfile"
      class="notice"
      data-test="profile-missing"
    >
      {{ missingProfile }}
    </p>
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
    <!-- Lignes calmes (docs/49 §2) : une action, le texte et « Supprimer » dans le panneau. -->
    <ul
      v-if="documents.length"
      class="calm-list doc-list"
    >
      <li
        v-for="doc in documents"
        :key="doc.id"
        data-test="document"
      >
        <button
          type="button"
          class="calm-row"
          :data-test="`open-document-${doc.id}`"
          @click="showText(doc.id)"
        >
          <strong>{{ doc.filename }}</strong>
          <span class="hint">
            {{ sizeText(doc.size) }} · {{ dateInList(doc.uploaded_at) }} · {{ doc.kind === "certificate" ? "certificat de travail" : plural(doc.chunk_count, "bloc", "blocs") }}<template v-if="doc.text_status !== 'ok'">
              · <span class="danger">{{ doc.text_status === "empty" ? "aucun texte" : "texte non lisible" }}</span>
            </template>
          </span>
        </button>
        <button
          v-if="doc.text_status === 'ok' && doc.kind !== 'certificate'"
          type="button"
          :class="[doc.id === firstReadable ? 'primary' : 'secondary', 'small']"
          :disabled="proposing !== null"
          :data-test="`propose-${doc.id}`"
          @click="propose(doc)"
        >
          <span class="with-icon"><AppIcon name="ai" />{{ proposing === doc.id ? "L'IA lit le document… (≈ 30 s)" : "Proposer des blocs" }}</span>
        </button>
      </li>
    </ul>
    <label
      :class="['drop-zone', { busy: uploading, 'drop-zone-first': !documents.length }]"
      data-test="drop-zone"
    >
      <input
        type="file"
        accept=".pdf,.docx,.txt,.md"
        data-test="file-input"
        @change="onFile"
      >
      <span class="drop-title with-icon"><AppIcon name="upload" />{{ uploading ? "Envoi…" : documents.length ? "Déposer un document" : "Dépose ton CV" }}</span>
      <span class="detail">
        PDF, DOCX, TXT ou MD · 10 Mo au plus{{ documents.length ? "" : " : l'IA en tire tes premiers blocs." }}
      </span>
    </label>

    <CertificatesSection
      :version="certificatesVersion"
      :documents="documents.length"
    />

    <SidePanel
      v-if="openText"
      open
      :title="openDocument?.filename ?? 'Document'"
      @close="openText = null"
    >
      <div
        class="calm-panel"
        data-test="document-text"
      >
        <p class="panel-section-links doc-actions">
          <button
            type="button"
            class="link"
            :disabled="openText.text_status !== 'ok'"
            data-test="chunk-from-selection"
            @click="chunkFromSelection"
          >
            <span class="with-icon"><AppIcon name="plus" />Créer un bloc avec la sélection</span>
          </button>
          <MoreMenu
            v-if="documentItems.length"
            class="section-more"
            :items="documentItems"
            label="Actions sur le document"
            test-id="document-more"
          />
        </p>
        <div
          ref="textBox"
          class="doc-text"
        >
          {{ openText.text || "Aucun texte n'a pu être extrait de ce document." }}
        </div>
      </div>
    </SidePanel>

    <div class="chunks-head">
      <h2 class="section-title">
        Blocs de profil
      </h2>
      <button
        type="button"
        class="pill"
        data-test="new-chunk"
        @click="newChunk()"
      >
        <span class="with-icon"><AppIcon name="plus" />Nouveau bloc</span>
      </button>
    </div>
    <div
      v-if="chunks.length"
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
        Tous <CountBadge
          class="tab-count"
          :count="chunks.length"
        />
      </button>
      <button
        v-for="kind in usedKinds"
        :key="kind.value"
        type="button"
        role="tab"
        :aria-selected="filter === kind.value"
        @click="filter = kind.value"
      >
        {{ kind.label }} <CountBadge
          class="tab-count"
          :count="kindCount(kind.value)"
        />
      </button>
    </div>

    <!-- Cartes calmes (docs/49 §3) : 3 lignes, le type en bas, toute la carte ouvre le bloc, avec
         survol ; 3 colonnes au plus, sans crayon (docs/130 §C). -->
    <ul class="chunk-grid">
      <li
        v-for="chunk in visibleChunks"
        :key="chunk.id"
        :class="{ inactive: !chunk.active }"
        data-test="chunk"
      >
        <button
          type="button"
          class="chunk-card"
          :data-test="`open-chunk-${chunk.id}`"
          @click="editChunk(chunk)"
        >
          <span class="job-title">{{ chunk.title }}</span>
          <span class="chunk-content">{{ chunk.content }}</span>
          <span class="chunk-foot">
            <span>{{ chunkFoot(chunk) }}<template v-if="!chunk.active"> · inactif</template></span>
          </span>
        </button>
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

  <!-- Le bloc dans le panneau latéral (docs/49 §3), comme le reste de l'application. -->
  <SidePanel
    v-if="editing"
    open
    :title="editing.id === null ? 'Nouveau bloc' : (editedChunk?.title ?? 'Bloc')"
    @close="editing = null"
  >
    <form
      class="calm-panel chunk-form"
      data-test="chunk-form"
      @submit.prevent="saveChunk"
    >
      <label>Type
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
        <!-- La description toujours visible, comme les CFF (docs/110). -->
        <span class="setting-desc">{{ KINDS.find((k) => k.value === editing?.form.kind)?.hint ?? "" }}</span>
      </label>
      <label>Titre
        <input
          id="chunk-title"
          v-model="editing.form.title"
          type="text"
          maxlength="200"
          required
        >
      </label>
      <label>Contenu
        <textarea
          id="chunk-content"
          v-model="editing.form.content"
          rows="8"
          required
        />
      </label>
      <div class="chunk-tags">
        <span class="muted">Mots-clés</span>
        <TagInput
          id="chunk-tags"
          v-model="editing.form.tags"
          placeholder="infra, linux…"
        />
      </div>
      <label class="filter-switch calm-panel-switch">
        <span>Utilisé par l'IA</span>
        <input
          v-model="editing.form.active"
          type="checkbox"
          role="switch"
        >
      </label>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          data-test="save-chunk"
        >
          Enregistrer
        </button>
      </div>
      <p
        v-if="editedChunk"
        class="calm-panel-foot"
      >
        <IconButton
          icon="trash"
          label="Supprimer ce bloc"
          danger
          data-test="remove-chunk"
          @click="removeChunk(editedChunk)"
        />
      </p>
    </form>
  </SidePanel>
</template>
