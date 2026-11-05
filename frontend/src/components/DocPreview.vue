<script setup lang="ts">
import type { DocTemplate } from "../composables/useDocTemplate";

// L'aperçu d'une lettre ou d'un CV dans le modèle choisi (maquette Preparer) : la page, son en-tête (le nom,
// une ligne dessous) et le début du texte. Vide (pas encore rédigé) : des lignes grises à la place du texte.
defineProps<{ template: DocTemplate; name: string; sub?: string | null; paragraphs: string[]; label: string }>();
defineEmits<{ open: [] }>();
</script>

<template>
  <button
    type="button"
    class="doc-preview"
    :aria-label="label"
    :data-template="template"
    data-test="doc-preview"
    @click="$emit('open')"
  >
    <span :class="['doc-preview-page', `tpl-${template}`]">
      <span class="doc-preview-head">
        <strong>{{ name }}</strong>
        <span v-if="sub">{{ sub }}</span>
      </span>
      <span
        v-if="paragraphs.length"
        class="doc-preview-body"
      >
        <span
          v-for="(text, index) in paragraphs"
          :key="index"
        >{{ text }}</span>
      </span>
      <span
        v-else
        class="doc-preview-empty"
        data-test="doc-preview-empty"
      ><i /><i /><i /><i /></span>
    </span>
  </button>
</template>
