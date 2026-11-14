<script setup lang="ts">
import { computed, ref } from "vue";

import { useTextSize, type TextSize } from "../composables/useTextSize";
import { useTheme, type Theme } from "../composables/useTheme";
import AppIcon from "./AppIcon.vue";
import ChoicePanel from "./ChoicePanel.vue";
import SegmentedControl from "./SegmentedControl.vue";

// Apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto ; Auto par défaut, la page suit le
// téléphone ou l'ordinateur (ModeSombre). Le choix vaut pour cet appareil.
// `detailed` (ordinateur, maquette ReglagesOrdinateur, MODIFICATIONS_9 §2.10) : deux lignes de plus, Langue et Taille
// du texte, la valeur et un chevron ; chacune ouvre son panneau à boutons radio.
// `phone` (planche Reglages du 14.11) : Apparence seule dans sa carte, segments pleine largeur de 44 px, puis Langue et
// Taille du texte dans une seconde carte. Sur ordinateur (ReglagesOrdinateur) : les trois lignes dans une seule carte.
const props = withDefaults(defineProps<{ detailed?: boolean; phone?: boolean }>(), { detailed: false, phone: false });
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

// La langue de jobA1 : l'interface n'existe qu'en français pour l'instant ; Deutsch et English restent visibles,
// grisés, jusqu'à leur traduction (question pour Kevin dans la PR).
const LANGUAGES = [
  { value: "fr", label: "Français", hint: "Langue actuelle" },
  { value: "de", label: "Deutsch", hint: "Allemand", disabled: true },
  { value: "en", label: "English", hint: "Anglais", disabled: true },
];
const SIZES = [
  { value: "browser", label: "Selon le navigateur", hint: "Suit le zoom de ton navigateur" },
  { value: "large", label: "Grande", hint: "Texte agrandi de 25 %" },
];
const { textSize, setTextSize } = useTextSize();
const size = computed({
  get: () => textSize.value as string,
  set: (value: string) => setTextSize(value as TextSize),
});
// Planche Reglages (téléphone) : « Selon le téléphone » ; ReglagesOrdinateur : « Selon le navigateur ».
const sizeLabel = computed(() =>
  props.phone && textSize.value === "browser"
    ? "Selon le téléphone"
    : (SIZES.find((s) => s.value === textSize.value)?.label ?? ""),
);
const panel = ref<"" | "language" | "size">("");
</script>

<template>
  <div
    :class="['appearance', { 'appearance-phone': phone }]"
    data-test="appearance-panel"
  >
    <div class="rg-list appearance-card">
      <div class="appearance-row">
        <span
          id="appearance-title"
          class="rg-label"
        >Apparence</span>
        <SegmentedControl
          v-model="model"
          :options="OPTIONS"
          label="Apparence"
          :full="phone"
        />
      </div>
      <template v-if="detailed && !phone">
        <button
          type="button"
          class="rg-link-row"
          aria-haspopup="dialog"
          data-test="language-row"
          @click="panel = 'language'"
        >
          <span class="rg-label">Langue</span>
          <span class="rg-value">Français</span>
          <AppIcon name="chevron" />
        </button>
        <button
          type="button"
          class="rg-link-row"
          aria-haspopup="dialog"
          data-test="text-size-row"
          @click="panel = 'size'"
        >
          <span class="rg-label">Taille du texte</span>
          <span class="rg-value">{{ sizeLabel }}</span>
          <AppIcon name="chevron" />
        </button>
      </template>
    </div>
    <div
      v-if="detailed && phone"
      class="rg-list"
    >
      <button
        type="button"
        class="rg-link-row"
        aria-haspopup="dialog"
        data-test="language-row"
        @click="panel = 'language'"
      >
        <span class="rg-label">Langue</span>
        <span class="rg-value">Français</span>
        <AppIcon name="chevron" />
      </button>
      <button
        type="button"
        class="rg-link-row"
        aria-haspopup="dialog"
        data-test="text-size-row"
        @click="panel = 'size'"
      >
        <span class="rg-label">Taille du texte</span>
        <span class="rg-value">{{ sizeLabel }}</span>
        <AppIcon name="chevron" />
      </button>
    </div>
  </div>
  <template v-if="detailed">
    <ChoicePanel
      :open="panel === 'language'"
      title="Langue"
      heading="Langue de jobA1"
      :choices="LANGUAGES"
      model-value="fr"
      note="La langue des lettres se choisit dans Préparer (FR, DE, EN)."
      @close="panel = ''"
    />
    <ChoicePanel
      v-model="size"
      :open="panel === 'size'"
      title="Taille du texte"
      heading="Taille du texte"
      :choices="SIZES"
      @close="panel = ''"
    />
  </template>
</template>
