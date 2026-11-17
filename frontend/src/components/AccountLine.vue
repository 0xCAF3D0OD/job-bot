<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import type { IconName } from "../icons";
import AppIcon from "./AppIcon.vue";

// Une ligne du Compte (LISEZMOI §51 du 17.11, planches Compte et CompteSombre) : une seule ligne de texte, 56 px,
// l'icône de section à gauche (sa couleur : `tone`), la valeur utile à droite en gris, puis le chevron du §49.
// Toute la ligne est le lien (`to`, ou `href` pour un lien externe), sinon un bouton.
defineProps<{
  title: string;
  icon: IconName;
  tone?: "violet" | "blue" | "green" | "peach";
  value?: string;
  to?: RouteLocationRaw;
  href?: string;
}>();
defineEmits<{ click: [] }>();
</script>

<template>
  <component
    :is="to ? 'RouterLink' : href ? 'a' : 'button'"
    v-bind="to ? { to } : href ? { href } : { type: 'button' }"
    class="account-line"
    @click="to || href ? undefined : $emit('click')"
  >
    <AppIcon
      :name="icon"
      :class="['account-line-icon', tone]"
    />
    <span class="account-line-title">{{ title }}</span>
    <span
      v-if="value"
      class="account-line-value"
    ><span class="visually-hidden">, </span>{{ value }}</span>
    <span
      class="account-line-chevron"
      aria-hidden="true"
    ><AppIcon :name="href ? 'external' : 'chevron'" /></span>
  </component>
</template>
