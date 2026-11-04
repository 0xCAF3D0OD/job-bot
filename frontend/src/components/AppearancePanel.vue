<script setup lang="ts">
import { computed } from "vue";

import { useTheme, type Theme } from "../composables/useTheme";
import SegmentedControl from "./SegmentedControl.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto ; Auto par défaut, la page suit le
// téléphone ou l'ordinateur (ModeSombre). Le choix vaut pour cet appareil.
const { theme, setTheme } = useTheme();
const OPTIONS = [
  { value: "light", label: "Clair", test: "theme-light" },
  { value: "dark", label: "Sombre", test: "theme-dark" },
  { value: "auto", label: "Auto", test: "theme-auto" },
];
const model = computed({
  get: () => theme.value,
  set: (value: string) => setTheme(value as Theme),
});
</script>

<template>
  <SettingCard data-test="appearance-panel">
    <SettingRow
      title="Apparence"
      description="Auto suit l'appareil."
      stack
    >
      <SegmentedControl
        v-model="model"
        :options="OPTIONS"
        label="Apparence"
        full
      />
    </SettingRow>
  </SettingCard>
</template>
