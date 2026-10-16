<script setup lang="ts">
import Illustration, { type IllustrationName } from "./Illustration.vue";

// Illustration en grand sur ordinateur (docs/60 §1) : l'image à gauche (260 px), le contenu à
// droite. Sur téléphone, rien ne change : l'image disparaît, ou reste petite au-dessus
// (`phone="small"`, pour les réussites et les pages vides).
// `side="right"` (docs/61 §3) : un bloc trop large garde une largeur de lecture, l'image à droite
// (quand la gauche est déjà prise, par la liste des Réglages par exemple).
withDefaults(defineProps<{ name: IllustrationName; phone?: "hide" | "small"; side?: "left" | "right" }>(), {
  phone: "hide",
  side: "left",
});
</script>

<template>
  <div :class="['illustrated', `phone-${phone}`, `side-${side}`]">
    <Illustration
      :key="name"
      :name="name"
    />
    <div class="illustrated-body">
      <slot />
    </div>
  </div>
</template>
