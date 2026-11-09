<script setup lang="ts">
import { computed } from "vue";

import { avatarSrc, type ImageChoice } from "../composables/useProfileImage";

// L'image de profil (maquette du 8 novembre, docs/143) : initiales, avatar ou photo, dans un rond avec un contour de
// 1 px --line. Tailles : en-tête 40 px, panneau Compte 48 px, carte de la page Compte 52 px, Profil 72 px (et 64 px dans la grille du choix).
// Décorative : le bouton ou le nom à côté dit à qui elle est.
const props = withDefaults(defineProps<{ choice: ImageChoice; initials: string; size?: 40 | 44 | 48 | 52 | 64 | 72 }>(), { size: 40 });
const src = computed(() => {
  if (props.choice.kind === "photo") return props.choice.src;
  if (props.choice.kind === "avatar") return avatarSrc(props.choice.avatar, props.size > 48 ? 256 : 128);
  return "";
});
</script>

<template>
  <span
    :class="['profile-image', `profile-image-${size}`]"
    aria-hidden="true"
    data-test="profile-image"
  >
    <img
      v-if="src"
      :src="src"
      :width="size"
      :height="size"
      alt=""
      decoding="async"
    >
    <span
      v-else
      class="profile-image-initials"
    >{{ initials }}</span>
  </span>
</template>
