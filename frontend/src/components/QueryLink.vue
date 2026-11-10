<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

// Un lien vers une autre vue de la même page (?onglet=…) : RouterLink le marquerait « page en cours »
// (aria-current="page"), le chemin étant le même ; celui-ci ne le fait pas (prompt du 10 novembre, PR 20).
// `text` : le libellé sans espace autour, quand une ponctuation le suit.
defineProps<{ to: RouteLocationRaw; text?: string }>();
</script>

<template>
  <RouterLink
    v-slot="{ href, navigate }"
    :to="to"
    custom
  >
    <a
      :href="href"
      @click="navigate"
    ><slot>{{ text }}</slot></a>
  </RouterLink>
</template>
