<script lang="ts">
import type { IconName } from "../icons";

// Une petite icône au trait devant le titre, de la famille de la navigation (docs/62 §1) ;
// plus d'illustration dans un formulaire. Le sommaire des Réglages reprend les mêmes (docs/101).
// La seule table : la liste des Réglages et le titre de chaque rubrique lisent les mêmes icônes.
export const SETTINGS_ICONS: Record<string, IconName> = {
  recherche: "briefcase",
  rythme: "calendar",
  notifications: "bell",
  ia: "ai",
  compte: "user",
  outils: "plug",
  plateforme: "shield",
};
</script>

<script setup lang="ts">
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";

// Section des Réglages, comme les CFF (docs/110) : le titre de la section au-dessus de sa carte.
// Sur ordinateur, une rubrique à la fois (docs/48 §2) ; sur téléphone, toutes l'une sous l'autre,
// une longue page parcourue par les marqueurs du haut. `value` résume la rubrique (marqueurs).
// `cards` (1.6.65, planche « 5. Réglages ») : une carte par réglage (SettingCard), empilées,
// au lieu d'une seule carte pour la rubrique.
withDefaults(defineProps<{ id: string; title: string; value?: string; active?: boolean; cards?: boolean }>(), {
  value: "",
  active: true,
  cards: false,
});
const { phone } = usePhone();
</script>

<template>
  <section
    v-if="active || phone"
    :id="id"
    class="settings-section"
    :data-test="`section-${id}`"
  >
    <h2 class="section-title">
      <AppIcon
        v-if="SETTINGS_ICONS[id] && !phone"
        :name="SETTINGS_ICONS[id]!"
      />
      {{ title }}
    </h2>
    <!-- Une rubrique, une carte (docs/106 §1) : les cartes du contenu y perdent leur cadre. -->
    <div
      :class="cards ? 'setting-cards' : 'settings-card'"
      data-test="settings-card"
    >
      <slot />
    </div>
  </section>
</template>
