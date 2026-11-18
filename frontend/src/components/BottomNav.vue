<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import { useAssistant } from "../composables/useAssistant";
import { useFocusMode } from "../composables/useFocusMode";
import { useJobsMemory } from "../composables/useJobsMemory";
import AppIcon from "./AppIcon.vue";
import CountBadge from "./CountBadge.vue";

// La barre du bas du téléphone (docs/139, D1 et D4 du 2026-11-02) : cinq onglets, Accueil, Candidatures, Assistant,
// Bilan, Compte, libellés toujours visibles. L'onglet actif est un rond plein posé dans un creux de la barre,
// à l'encre (crème en sombre ; LISEZMOI du 17.11, §55), seule exception à la pastille teintée ; une zone vide de 22 px au-dessus de la barre (--nav-spacer) garde le
// rond loin du texte. Candidatures porte le nombre d'offres à examiner. Les écrans de travail (Préparer, le tri,
// l'accueil des nouveaux comptes) la cachent (docs/75, 1.6.50), comme les Réglages et les Notifications (Kevin, 6.11).
// Assistant mène à sa page (étape 11a), seulement quand l'IA est branchée ; la barre attend de le savoir pour se
// dessiner (AS8). Compte mène à la page Compte (étape 10a) et reste actif sur le Profil et les Réglages.
const HIDDEN = new Set(["preparation", "welcome", "triage", "settings", "notifications"]);

const route = useRoute();
const { menuLink } = useJobsMemory();
const { available: assistantAvailable, known: assistantKnown } = useAssistant();
const toReview = ref(0);

const { focus } = useFocusMode();
const visible = computed(() => assistantKnown.value && !HIDDEN.has(String(route.name)) && !route.meta.bare && !focus.value);

type Tab = { name: string; label: string; icon: "home" | "briefcase" | "assistant" | "trend" | "user"; to: string; active: boolean };
const tabs = computed<Tab[]>(() => {
  const list: Tab[] = [
    { name: "today", label: "Accueil", icon: "home", to: "/aujourdhui", active: route.path.startsWith("/aujourdhui") },
    { name: "jobs", label: "Candidatures", icon: "briefcase", to: menuLink(route.path), active: route.path.startsWith("/candidatures") },
  ];
  if (assistantAvailable.value) list.push({ name: "assistant", label: "Assistant", icon: "assistant", to: "/assistant", active: route.name === "assistant" });
  list.push(
    { name: "bilan", label: "Bilan", icon: "trend", to: "/bilan", active: route.path.startsWith("/bilan") },
    {
      name: "account",
      label: "Compte",
      icon: "user",
      to: "/compte",
      active: ["/compte", "/reglages", "/profil"].some((path) => route.path.startsWith(path)),
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
    // Le nombre du segment « À traiter » (docs/139, C2), sans les offres « Loin » que la liste du téléphone cache.
    toReview.value = data?.pending_near ?? 0;
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
        :to="tab.to"
        :class="{ active: tab.active }"
        :aria-current="tab.active ? 'page' : undefined"
        :data-test="`tab-${tab.name}`"
      >
        <span class="tab-bar-icon">
          <AppIcon
            :name="tab.icon"
          />
          <CountBadge
            v-if="tab.name === 'jobs' && toReview"
            class="tab-bar-count"
            :count="toReview > 9 ? '9+' : toReview"
          />
        </span>
        <span class="tab-bar-label">{{ tab.label }}</span>
      </RouterLink>
    </template>
  </nav>
</template>

<style>
/* Le bouton rond de Candidatures dépasse de la barre du bas : il ne se masque pas au défilement, et un élément qui
   reçoit le focus s'arrête au-dessus de lui, jamais dessous (Kevin, 17.11, point 7 ; WCAG 2.4.11). */
@media (max-width: 820px) {
  :root:has(.tab-bar) { scroll-padding-bottom: calc(var(--tabbar-h) + var(--nav-spacer) + var(--space-2) + env(safe-area-inset-bottom)); }
}
</style>
