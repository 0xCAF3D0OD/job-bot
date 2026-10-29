<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";

// Les certificats à joindre (docs/87 §4, 0.69.1), dans « Postuler » : ceux marqués « à joindre »,
// les plus récents d'abord ; ceux à faire corriger, rappelés à part.
type Page = components["schemas"]["CertificatesPage"];
const page = ref<Page | null>(null);

const attach = computed(() => page.value?.certificates.filter((c) => c.advice === "attach") ?? []);
const toCorrect = computed(() => page.value?.certificates.filter((c) => c.advice === "correct") ?? []);
const label = (filename: string) => filename.replace(/\.[^.]+$/, "");

onMounted(async () => {
  const { data } = await api.GET("/api/certificates");
  page.value = Array.isArray(data?.certificates) ? data : null;
});
</script>

<template>
  <div
    v-if="attach.length || toCorrect.length"
    class="prep-certificates"
    data-test="prep-certificates"
  >
    <p v-if="attach.length">
      Certificats à joindre :
      <template
        v-for="(item, index) in attach"
        :key="item.document_id"
      >
        <a
          :href="`/api/documents/${item.document_id}/file`"
          target="_blank"
          rel="noopener noreferrer"
          :data-test="`prep-certificate-${item.document_id}`"
        ><span class="with-icon"><AppIcon name="download" />{{ label(item.filename) }}</span><span class="visually-hidden"> (nouvel onglet)</span></a>{{ index < attach.length - 1 ? ", " : "." }}
      </template>
    </p>
    <p
      v-if="toCorrect.length"
      class="hint"
    >
      Pas encore {{ toCorrect.map((c) => `« ${label(c.filename)} »`).join(", ") }} : à faire corriger d'abord, dans
      <RouterLink to="/profil?onglet=parcours">Profil › Parcours</RouterLink>.
    </p>
  </div>
</template>
