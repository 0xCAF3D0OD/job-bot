<script setup lang="ts">
import Illustration, { type IllustrationName } from "./Illustration.vue";

// Illustration en grand sur ordinateur (docs/60 §1) : l'image à gauche (260 px), le contenu à
// droite. Sur téléphone, rien ne change : l'image disparaît, ou reste petite au-dessus
// (`phone="small"`, pour les réussites et les pages vides).
withDefaults(defineProps<{ name: IllustrationName; phone?: "hide" | "small" }>(), { phone: "hide" });
</script>

<template>
  <div :class="['illustrated', `phone-${phone}`]">
    <Illustration
      :key="name"
      :name="name"
    />
    <div class="illustrated-body">
      <slot />
    </div>
  </div>
</template>
