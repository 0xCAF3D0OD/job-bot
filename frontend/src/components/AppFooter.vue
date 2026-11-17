<script setup lang="ts">
// Le pied de page (docs/126 §4) : qui est derrière jobA1 et ce qu'il fait des données, à un
// clic de chaque page (nLPD). Une ligne de liens, sans cadre.
const LINKS = [
  { to: "/tes-donnees", label: "Données personnelles" },
  { to: "/conditions", label: "Conditions d’utilisation" },
  { to: "/accessibilite", label: "Accessibilité" },
  { to: "/a-propos", label: "À propos" },
];
</script>

<template>
  <footer
    class="app-footer"
    data-test="app-footer"
  >
    <nav aria-label="Informations">
      <RouterLink
        v-for="link in LINKS"
        :key="link.to"
        :to="link.to"
      >
        {{ link.label }}
      </RouterLink>
    </nav>
  </footer>
</template>

<style>
/* Avant la première page, le contenu est vide : le pied de page attend, au lieu de s'afficher en haut de l'écran puis de
   redescendre quand la page arrive (saut au chargement, lot 4 de l'audit du 17.11). */
#contenu:empty + .app-footer { display: none; }
</style>
