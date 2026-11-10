<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";

// Les certificats à joindre (docs/87 §4, 0.69.1), dans « Postuler » : ceux marqués « à joindre »,
// les plus récents d'abord, à côté de Lettre.pdf et CV.pdf (le slot, C7) ; ceux à faire corriger,
// rappelés à part.
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
  <p
    v-if="$slots.default || attach.length"
    class="apply-files"
    data-test="prep-certificates"
  >
    <slot />
    <a
      v-for="item in attach"
      :key="item.document_id"
      :href="`/api/documents/${item.document_id}/file`"
      target="_blank"
      rel="noopener noreferrer"
      :data-test="`prep-certificate-${item.document_id}`"
    ><AppIcon name="file" />{{ label(item.filename) }}<span class="visually-hidden"> (certificat, nouvel onglet)</span></a>
  </p>
  <p
    v-if="toCorrect.length"
    class="hint"
  >
    Pas encore {{ toCorrect.map((c) => `« ${label(c.filename)} »`).join(", ") }} : à faire corriger d’abord, dans
    <RouterLink to="/profil?onglet=parcours">
      Profil › Parcours
    </RouterLink>.
  </p>
</template>
