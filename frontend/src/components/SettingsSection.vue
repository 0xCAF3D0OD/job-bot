<script setup lang="ts">
// Une rubrique des Réglages, seule sur sa page (docs/139 étape 10b) : son titre, lu par les lecteurs d'écran
// (le titre visible est celui de la page), puis ses cartes. `cards` (1.6.65, planche « 5. Réglages ») : une
// carte par réglage (SettingCard), empilées, au lieu d'une seule carte pour la rubrique.
withDefaults(defineProps<{ id: string; title: string; cards?: boolean }>(), { cards: false });
</script>

<template>
  <section
    :id="id"
    class="settings-section"
    :data-test="`section-${id}`"
  >
    <h2 class="section-title">
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
