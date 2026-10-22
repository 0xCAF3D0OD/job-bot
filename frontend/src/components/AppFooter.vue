<script setup lang="ts">
// Le pied de page (docs/126 §4) : qui est derrière jobA1 et ce qu'il fait des données, à un
// clic de chaque page (nLPD). Une ligne de liens, sans cadre.
const LINKS = [
  { to: "/tes-donnees", label: "Données personnelles" },
  { to: "/conditions", label: "Conditions d'utilisation" },
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
