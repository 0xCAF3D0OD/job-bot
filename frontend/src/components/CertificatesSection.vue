<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import CertificateLetter from "./CertificateLetter.vue";
import HoverNote from "./HoverNote.vue";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// Les certificats de travail, décodés (docs/87) : la note, les formules codées, ce qui
// dessert, le conseil ; la lecture de l'IA sur demande.
type Page = components["schemas"]["CertificatesPage"];
type Certificate = Page["certificates"][number];

// `documents` : des documents existent ; sans certificat, une phrase dit comment en marquer un.
const props = defineProps<{ version: number; documents?: number }>();
const emit = defineEmits<{ loaded: [count: number] }>();
const page = ref<Page | null>(null);
const reading = ref<number | null>(null);
const message = ref("");
const open = ref<number | null>(null);
// La lettre ouverte (0.69.1) : la correction d'un certificat, ou le certificat intermédiaire (0).
const letter = ref<{ documentId?: number; language?: "fr" | "de" } | null>(null);

async function load(): Promise<void> {
  const { data } = await api.GET("/api/certificates");
  page.value = data ?? null;
  emit("loaded", data?.certificates.length ?? 0);
}

async function readInDetail(item: Certificate): Promise<void> {
  reading.value = item.document_id;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/certificates/{document_id}/lecture", {
      params: { path: { document_id: item.document_id } },
    });
    if (data) {
      page.value = data;
      open.value = item.document_id;
    } else {
      message.value = (error as { detail?: string } | undefined)?.detail ?? "Lecture impossible pour l'instant.";
    }
  } finally {
    reading.value = null;
  }
}

watch(() => props.version, () => void load());
onMounted(() => void load());
</script>

<template>
  <p
    v-if="page && !page.certificates.length && documents"
    class="hint certificates-hint"
    data-test="certificates-hint"
  >
    Un certificat parmi tes documents ? Ouvre-le, puis ⋯ › « C'est un certificat de travail ». Encore en poste ?
    <button
      type="button"
      class="link"
      data-test="interim-letter"
      @click="letter = {}"
    >
      Demander un certificat intermédiaire
    </button>
  </p>
  <section
    v-if="page?.certificates.length"
    class="certificates"
    data-test="certificates"
  >
    <h2 class="section-title">
      Certificats de travail
    </h2>
    <p
      v-if="page.summary"
      class="certificates-summary"
      data-test="certificates-summary"
    >
      {{ page.summary }}
    </p>
    <p
      v-if="message"
      role="status"
      class="notice error"
    >
      {{ message }}
    </p>
    <p class="hint">
      Encore en poste ou en préavis ?
      <button
        type="button"
        class="link"
        data-test="interim-letter"
        @click="letter = {}"
      >
        Demander un certificat intermédiaire
      </button>
    </p>
    <article
      v-for="item in page.certificates"
      :key="item.document_id"
      :class="['certificate', `advice-${item.advice}`]"
      :data-test="`certificate-${item.document_id}`"
    >
      <header class="certificate-head">
        <h3>{{ item.filename.replace(/\.[^.]+$/, "") }}</h3>
        <span
          v-if="item.grade_label"
          :class="['badge', `grade-${item.grade}`, { warn: item.grade === 1 }]"
          data-test="certificate-grade"
        >{{ item.grade_label }}</span>
      </header>
      <p v-if="!item.readable">
        Texte non lisible : dépose une version PDF avec du texte (pas une photo).
      </p>
      <template v-else>
        <p data-test="certificate-explanation">
          {{ item.explanation }}
        </p>
        <p
          class="certificate-advice"
          data-test="certificate-advice"
        >
          <strong>{{ item.advice_label.charAt(0).toUpperCase() + item.advice_label.slice(1) }}</strong><template v-if="item.ai?.advice_text">
            : {{ item.ai.advice_text }}
          </template>
        </p>
        <button
          type="button"
          class="link"
          :aria-expanded="open === item.document_id"
          :data-test="`certificate-details-${item.document_id}`"
          @click="open = open === item.document_id ? null : item.document_id"
        >
          <HoverNote text="Une lecture reste une interprétation : la phrase d'origine fait foi.">
            <span class="with-icon">{{ open === item.document_id ? "Masquer le détail" : "Voir phrase par phrase" }}<AppIcon name="chevron-down" /></span>
          </HoverNote>
        </button>
        <div
          v-if="open === item.document_id"
          class="certificate-details"
        >
          <ul
            v-if="item.passages.length"
            class="certificate-passages"
          >
            <li
              v-for="passage in item.passages"
              :key="passage.text"
              :class="passage.tone"
            >
              <mark>« {{ passage.text }} »</mark>
              <span>{{ passage.meaning }}</span>
            </li>
          </ul>
          <ul
            v-if="item.notes.length || item.ai?.missing.length || item.ai?.order"
            class="certificate-notes"
          >
            <li
              v-for="note in item.notes"
              :key="note.text"
              :class="note.tone"
            >
              {{ note.text }}
            </li>
            <li
              v-for="line in item.ai?.missing ?? []"
              :key="line"
              class="bad"
            >
              {{ line }}
            </li>
            <li
              v-if="item.ai?.order"
              class="neutral"
            >
              {{ item.ai.order }}
            </li>
          </ul>
        </div>
        <div class="form-actions">
          <button
            type="button"
            class="secondary small"
            :disabled="reading !== null"
            :data-test="`certificate-read-${item.document_id}`"
            @click="readInDetail(item)"
          >
            <HoverNote :text="aiNote('Environ 0,03 CHF.')">
              <span class="with-icon"><AppIcon name="ai" />{{ reading === item.document_id ? "L'IA lit le certificat…" : item.ai ? "Relire en détail" : "Lire en détail" }}</span>
            </HoverNote>
          </button>
          <button
            v-if="item.advice !== 'attach'"
            type="button"
            class="link"
            :data-test="`certificate-correction-${item.document_id}`"
            @click="letter = { documentId: item.document_id }"
          >
            <span class="with-icon"><AppIcon name="mail" />Demander une correction</span>
          </button>
        </div>
      </template>
    </article>
    <p class="hint">
      <HoverNote text="Les personnes citées en signature sont retirées aussi ; un nom seul dans une phrase peut rester.">
        Avant l'IA, ton nom est retiré.
      </HoverNote>
    </p>
  </section>
  <CertificateLetter
    v-if="letter"
    :document-id="letter.documentId"
    :language="letter.language"
    @close="letter = null"
  />
</template>
