<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// Une carte de lignes de 56 px (§8.1 et §8.3) : « Ce que tu as envoyé » et « Trouver un contact », dans la colonne de
// droite sur ordinateur ou dans leur feuille sur téléphone. Un téléchargement ou un lien externe par ligne.
export type SentRow = { label: string; sub: string; href: string; download: boolean; test: string };
defineProps<{ rows: SentRow[]; title?: string }>();
</script>

<template>
  <section :class="['sent-card', 'sent-rows', { 'sent-rows-bare': !title }]">
    <h3 v-if="title">
      {{ title }}
    </h3>
    <a
      v-for="row in rows"
      :key="row.test"
      :href="row.href"
      :download="row.download || undefined"
      :target="row.download ? undefined : '_blank'"
      :rel="row.download ? undefined : 'noopener noreferrer'"
      :data-test="row.test"
    >
      <span class="sent-row-text"><b>{{ row.label }}</b><span>{{ row.sub }}</span></span>
      <AppIcon :name="row.download ? 'download' : 'external'" />
      <span
        v-if="!row.download"
        class="visually-hidden"
      > (nouvel onglet)</span>
    </a>
  </section>
</template>
