<script setup lang="ts">
import { ICONS, type IconName } from "../icons";

// Une icône de l'iconographie (docs/101) : 24 px, trait de 1,8 px, couleur du texte.
// Décorative : le texte à côté, ou le nom du bouton (IconButton), dit ce qu'elle veut dire.
defineProps<{ name: IconName }>();
</script>

<!-- eslint-disable vue/no-v-html -- les tracés sont des constantes de src/icons.ts, jamais une donnée -->
<template>
  <svg
    class="icon"
    :class="`icon-${name}`"
    viewBox="0 0 24 24"
    width="16"
    height="16"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    :data-icon="name"
    v-html="ICONS[name]"
  />
</template>
