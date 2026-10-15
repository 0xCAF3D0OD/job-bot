<script setup lang="ts">
import Illustration from "../components/Illustration.vue";

// Page introuvable (docs/59 §5) : une adresse qui ne mène nulle part le dit, au lieu de
// renvoyer sans un mot vers Aujourd'hui.
</script>

<template>
  <section class="band not-found">
    <div class="container empty-state">
      <Illustration name="page-eaten" />
      <h1>Page introuvable</h1>
      <p>Cette adresse ne mène à rien dans la plateforme, peut-être un ancien lien.</p>
      <RouterLink
        to="/aujourdhui"
        class="button-link"
      >
        Revenir à Aujourd'hui
      </RouterLink>
    </div>
  </section>
</template>
