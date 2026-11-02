<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import { useAssistant } from "../composables/useAssistant";
import { useJobsMemory } from "../composables/useJobsMemory";
import AppIcon from "./AppIcon.vue";
import AssistantMascot from "./AssistantMascot.vue";
import CountBadge from "./CountBadge.vue";

// La barre du bas du téléphone (docs/139, D1 et D4 du 2026-11-02) : cinq onglets, Accueil, Candidatures, Assistant,
// Bilan, Compte, libellés toujours visibles. L'onglet actif est un rond bleu plein posé dans un creux de la barre
// (seule exception à la pastille teintée) ; une zone vide de 22 px au-dessus de la barre (--nav-spacer) garde le
// rond loin du texte. Candidatures porte le nombre d'offres à examiner. Les écrans de travail (Préparer, le tri,
// l'accueil des nouveaux comptes) la cachent (docs/75, 1.6.50).
// En attendant leurs écrans (docs/139 §5) : Assistant ouvre le panneau de l'assistant ; Compte mène aux Réglages
// et reste actif sur le Profil.
const HIDDEN = new Set(["preparation", "welcome", "triage"]);

const route = useRoute();
const { last: lastJobsPage } = useJobsMemory();
const { available: assistantAvailable, open: assistantOpen } = useAssistant();
const toReview = ref(0);

const visible = computed(() => !HIDDEN.has(String(route.name)) && !route.meta.bare);

type Tab = { name: string; label: string; icon?: "home" | "briefcase" | "trend" | "user"; to?: string; active: boolean };
const tabs = computed<Tab[]>(() => {
  const onPage = !assistantOpen.value;
  const list: Tab[] = [
    { name: "today", label: "Accueil", icon: "home", to: "/aujourdhui", active: onPage && route.path.startsWith("/aujourdhui") },
    { name: "jobs", label: "Candidatures", icon: "briefcase", to: lastJobsPage.value, active: onPage && route.path.startsWith("/candidatures") },
  ];
  if (assistantAvailable.value) list.push({ name: "assistant", label: "Assistant", active: assistantOpen.value });
  list.push(
    { name: "bilan", label: "Bilan", icon: "trend", to: "/bilan", active: onPage && route.path.startsWith("/bilan") },
    {
      name: "account",
      label: "Compte",
      icon: "user",
      to: "/reglages",
      active: onPage && (route.path.startsWith("/reglages") || route.path.startsWith("/profil")),
    },
  );
  return list;
});
// Le creux suit l'onglet actif : son centre, en part de la largeur (les onglets se partagent la largeur).
const notch = computed(() => {
  const index = tabs.value.findIndex((tab) => tab.active);
  return index < 0 ? null : `${((index + 0.5) * 100) / tabs.value.length}%`;
});

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/today");
    toReview.value = data?.to_review ?? 0;
  } catch {
    // Silencieux : le nombre n'est qu'un repère.
  }
}

watch(() => route.name, () => void refresh());
onMounted(() => void refresh());
</script>

<template>
  <nav
    v-if="visible"
    class="tab-bar"
    :class="{ 'has-notch': notch }"
    :style="notch ? { '--notch-x': notch } : undefined"
    aria-label="Pages"
    data-test="tab-bar"
  >
    <template
      v-for="tab in tabs"
      :key="tab.name"
    >
      <RouterLink
        v-if="tab.to"
        :to="tab.to"
        :class="{ active: tab.active }"
        :aria-current="tab.active ? 'page' : undefined"
        :data-test="`tab-${tab.name}`"
        @click="assistantOpen = false"
      >
        <span class="tab-bar-icon">
          <AppIcon :name="tab.icon!" />
          <CountBadge
            v-if="tab.name === 'jobs' && toReview"
            class="tab-bar-count"
            :count="toReview > 9 ? '9+' : toReview"
          />
        </span>
        <span class="tab-bar-label">{{ tab.label }}</span>
      </RouterLink>
      <button
        v-else
        type="button"
        :class="{ active: tab.active }"
        :aria-pressed="tab.active"
        :data-test="`tab-${tab.name}`"
        @click="assistantOpen = !assistantOpen"
      >
        <span class="tab-bar-icon">
          <AssistantMascot :size="tab.active ? 30 : 28" />
        </span>
        <span class="tab-bar-label">{{ tab.label }}</span>
      </button>
    </template>
  </nav>
</template>
