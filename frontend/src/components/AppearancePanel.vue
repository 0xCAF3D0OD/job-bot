<script setup lang="ts">
import { computed, ref } from "vue";

import { useTextSize, type TextSize } from "../composables/useTextSize";
import { useTheme, type Theme } from "../composables/useTheme";
import AppIcon from "./AppIcon.vue";
import ChoiceMenu from "./ChoiceMenu.vue";
import ChoicePanel from "./ChoicePanel.vue";
import ChoiceSheet from "./ChoiceSheet.vue";
import LanguagePanel from "./LanguagePanel.vue";
import { lang } from "../lang";
import { LANGUAGES } from "../languages";

// Apparence (maquette Réglages, « Affichage ») : Clair, Sombre, Auto ; Auto par défaut, la page suit le
// téléphone ou l'ordinateur (ModeSombre). Le choix vaut pour cet appareil.
// `detailed` (ordinateur, maquette ReglagesOrdinateur, MODIFICATIONS_9 §2.10) : deux lignes de plus, Langue et Taille
// du texte, la valeur et un chevron ; chacune ouvre son panneau à boutons radio.
// LISEZMOI §56 du 17.11 (planches Reglages, ReglagesOrdinateur) : « Apparence » devient une ligne comme Langue et Taille
// du texte, la valeur actuelle et un chevron, dans la même carte. Sur téléphone (`phone`), la ligne ouvre une feuille à
// boutons radio (Clair, Sombre, Auto « Comme le téléphone ») ; sur ordinateur, un menu.
const props = withDefaults(defineProps<{ detailed?: boolean; phone?: boolean }>(), { detailed: false, phone: false });
const { theme, setTheme } = useTheme();
const OPTIONS = [
  { value: "light", label: "Clair", test: "theme-light" },
  { value: "dark", label: "Sombre", test: "theme-dark" },
  { value: "auto", label: "Auto", hint: "Comme le téléphone", test: "theme-auto" },
];
const themeLabel = computed(() => OPTIONS.find((option) => option.value === theme.value)?.label ?? "");
const model = computed({
  get: () => theme.value,
  set: (value: string) => setTheme(value as Theme),
});

// La langue de jobA1 (§62, docs/147) : la valeur de la ligne est le nom de la langue choisie, écrit dans sa langue.
const language = computed(() => LANGUAGES.find((l) => l.code === lang.value) ?? LANGUAGES[0]);
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
const panel = ref<"" | "language" | "size" | "theme">("");
</script>

<template>
  <div
    :class="['appearance', { 'appearance-phone': phone }]"
    data-test="appearance-panel"
  >
    <div class="rg-list appearance-card">
      <button
        v-if="phone"
        type="button"
        class="rg-link-row"
        aria-haspopup="dialog"
        data-test="appearance-row"
        @click="panel = 'theme'"
      >
        <span
          id="appearance-title"
          class="rg-label"
        >Apparence</span>
        <span class="rg-value">{{ themeLabel }}</span>
        <AppIcon name="chevron" />
      </button>
      <div
        v-else
        class="appearance-row"
        data-test="appearance-row"
      >
        <span
          id="appearance-title"
          class="rg-label"
        >Apparence</span>
        <ChoiceMenu
          v-model="model"
          label="Apparence"
          :choices="OPTIONS"
          test-id="appearance-menu"
        />
      </div>
      <template v-if="detailed">
        <button
          type="button"
          class="rg-link-row"
          aria-haspopup="dialog"
          data-test="language-row"
          @click="panel = 'language'"
        >
          <span class="rg-label">Langue</span>
          <span
            class="rg-value"
            :lang="language.code"
          >{{ language.name }}</span>
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
  </div>
  <ChoiceSheet
    v-if="phone"
    v-model="model"
    :open="panel === 'theme'"
    title="Apparence"
    :choices="OPTIONS"
    @close="panel = ''"
  />
  <template v-if="detailed">
    <LanguagePanel
      :open="panel === 'language'"
      :sheet="phone"
      @close="panel = ''"
    />
    <ChoicePanel
      v-model="size"
      :open="panel === 'size'"
      :sheet="phone"
      title="Taille du texte"
      heading="Taille du texte"
      :choices="SIZES"
      @close="panel = ''"
    />
  </template>
</template>
