<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import { usePageReady } from "../composables/usePageTransition";

// La jauge du profil, dans Profil seulement (docs/121 §C.4) : cinq parties qui rendent la note
// et les lettres justes ; une ligne, des segments, et ce qui manque en premier. Elle part
// quand tout est là, comme les guides d'Aujourd'hui (docs/95).
type Part = { key: string; done: boolean; action: string; tab: string | null };

const parts = ref<Part[] | null>(null);
// La jauge charge le profil, les critères et les coordonnées : la page Profil est prête avec elle.
usePageReady("profile", () => parts.value !== null);

onMounted(async () => {
  const [chunks, criteria, identity] = await Promise.all([
    api.GET("/api/profile-chunks"),
    api.GET("/api/criteria"),
    api.GET("/api/identity"),
  ]);
  const active = (chunks.data ?? []).filter((c) => c.active);
  const count = (kind: string) => active.filter((c) => c.kind === kind).length;
  parts.value = [
    { key: "experience", done: count("experience") >= 1, action: "Ajouter une expérience", tab: "parcours" },
    { key: "competence", done: count("competence") >= 2, action: "Ajouter des compétences", tab: "parcours" },
    { key: "formation", done: count("formation") >= 1, action: "Ajouter une formation", tab: "parcours" },
    { key: "criteria", done: !!criteria.data?.saved_at, action: "Régler les critères", tab: null },
    { key: "identity", done: !!(identity.data?.name && identity.data?.city), action: "Saisir les coordonnées", tab: "coordonnees" },
  ];
});

const done = computed(() => parts.value?.filter((p) => p.done).length ?? 0);
const next = computed(() => parts.value?.find((p) => !p.done) ?? null);
</script>

<template>
  <div
    v-if="parts && next"
    class="profile-gauge"
    data-test="profile-gauge"
  >
    <span class="profile-gauge-count">Profil · {{ done }} sur {{ parts.length }}</span>
    <span
      class="segments"
      role="img"
      :aria-label="`${done} parties sur ${parts.length}`"
    >
      <span
        v-for="part in parts"
        :key="part.key"
        :class="['segment', { done: part.done }]"
      />
    </span>
    <RouterLink
      :to="{ query: next.tab ? { onglet: next.tab } : {} }"
      class="profile-gauge-next"
      data-test="profile-gauge-next"
    >
      {{ next.action }}
    </RouterLink>
  </div>
</template>
