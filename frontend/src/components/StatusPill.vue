<script setup lang="ts">
// La pastille d'état (1.6.74, planche « Pastille d'état et dates », règle §4) : un état en
// quelques mots, au bout de la ligne qu'il qualifie. Quatre tons : neutre, à faire (orange, il y a
// une action), réussi, erreur (rouge, seulement une vraie erreur). Le point et le mot disent
// l'état, jamais la couleur seule (WCAG 1.4.1). Sans point : une étiquette (« Spontanée »),
// toujours neutre. Un état dans une phrase, sous un titre, reste du texte coloré.
withDefaults(defineProps<{ tone?: "neutral" | "todo" | "ok" | "error"; dot?: boolean }>(), {
  tone: "neutral",
  dot: true,
});
</script>

<template>
  <span
    :class="['state-pill', tone, { tag: !dot }]"
    data-test="state-pill"
  >
    <span
      v-if="dot"
      class="state-pill-dot"
      aria-hidden="true"
    />
    <slot />
  </span>
</template>
