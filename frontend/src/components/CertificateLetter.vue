<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import CopyLabel from "./CopyLabel.vue";
import HoverNote from "./HoverNote.vue";
import SidePanel from "./SidePanel.vue";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// Les lettres autour des certificats (docs/87 §4, 0.69.1) : demander une correction, ou un
// certificat intermédiaire. Tu les relis, puis tu les envoies toi-même.
type Letter = components["schemas"]["CertificateLetterOut"];

const props = defineProps<{ documentId?: number; language?: "fr" | "de" }>();
const emit = defineEmits<{ close: [] }>();
const letter = ref<Letter | null>(null);
const text = ref("");
const busy = ref(false);
const failed = ref("");
const copied = ref(false);

async function load(ai = false): Promise<void> {
  busy.value = true;
  failed.value = "";
  copied.value = false;
  try {
    const path = { params: { path: { document_id: props.documentId ?? 0 } } };
    const result = !props.documentId
      ? await api.GET("/api/certificates/intermediaire", { params: { query: { langue: props.language ?? "fr" } } })
      : ai
        ? await api.POST("/api/certificates/{document_id}/correction", path)
        : await api.GET("/api/certificates/{document_id}/correction", path);
    if (result.data) {
      letter.value = result.data;
      text.value = result.data.text;
    } else {
      failed.value = (result.error as { detail?: string } | undefined)?.detail ?? "Lettre impossible pour l'instant.";
    }
  } finally {
    busy.value = false;
  }
}

async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(`${letter.value?.subject ?? ""}\n\n${text.value}`);
    copied.value = true;
  } catch {
    copied.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <SidePanel
    open
    :title="documentId ? 'Demander une correction' : 'Certificat intermédiaire'"
    @close="emit('close')"
  >
    <div
      class="calm-panel certificate-letter"
      data-test="certificate-letter"
    >
      <p
        v-if="failed"
        role="status"
        class="notice error"
      >
        {{ failed }}
      </p>
      <template v-if="letter">
        <p>
          <strong>Objet :</strong> {{ letter.subject }}
        </p>
        <textarea
          v-model="text"
          rows="14"
          aria-label="Texte de la lettre"
          data-test="certificate-letter-text"
        />
        <p
          v-if="letter.reason"
          class="hint"
          data-test="certificate-letter-reason"
        >
          Modèle simple : {{ letter.reason }}.
        </p>
        <div class="form-actions">
          <button
            type="button"
            class="secondary small"
            data-test="certificate-letter-copy"
            @click="copy"
          >
            <CopyLabel :done="copied" />
          </button>
          <button
            v-if="documentId && !letter.ai"
            type="button"
            class="link"
            :disabled="busy"
            data-test="certificate-letter-ai"
            @click="load(true)"
          >
            <HoverNote :text="aiNote('Environ 0,02 CHF.', undefined, 'Le certificat part sans ton nom ni les personnes citées.')">
              <span class="with-icon"><AppIcon name="ai" />{{ busy ? "L'IA rédige…" : "Rédiger avec l'IA" }}</span>
            </HoverNote>
          </button>
        </div>
        <p class="hint">
          Pour un désaccord, parle-en à ton conseiller ORP ou à un service juridique.
        </p>
      </template>
    </div>
  </SidePanel>
</template>
