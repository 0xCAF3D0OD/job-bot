<script setup lang="ts">
import AppIcon from "../components/AppIcon.vue";
import IllustratedSide from "../components/IllustratedSide.vue";

// Page introuvable (docs/59 §5) : une adresse qui ne mène nulle part le dit, au lieu de
// renvoyer sans un mot vers Aujourd'hui.
</script>

<template>
  <section class="band not-found">
    <div class="container">
      <IllustratedSide
        name="lecture-calme"
        phone="small"
        class="empty-state"
      >
        <h1>Page introuvable</h1>
        <p>Cette adresse ne mène à rien dans la plateforme, peut-être un ancien lien.</p>
        <RouterLink
          to="/aujourdhui"
          class="button-link"
        >
          <span class="with-icon"><AppIcon name="arrow-left" />Revenir à Aujourd'hui</span>
        </RouterLink>
      </IllustratedSide>
    </div>
  </section>
</template>
