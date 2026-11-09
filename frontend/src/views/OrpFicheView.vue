<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import OrpFiche from "../components/OrpFiche.vue";

// « Pour l'ORP » sur téléphone (MODIFICATIONS du 8 novembre au soir, lot 18, §10.3 ; maquettes OrpFiche et
// OrpFicheSombre) : l'en-tête avec le retour, puis la fiche (components/OrpFiche.vue).
const route = useRoute();
const router = useRouter();
const id = computed(() => Number(route.params.id));
const month = computed(() => (typeof route.query.mois === "string" ? route.query.mois : undefined));

function back(): void {
  if (window.history.state?.back) router.back();
  else void router.push({ path: "/bilan/orp", query: month.value ? { mois: month.value } : {} });
}
</script>

<template>
  <section
    class="blocks-page orp-fiche"
    aria-labelledby="orp-fiche-title"
    data-test="orp-fiche"
  >
    <header class="orp-fiche-head">
      <button
        type="button"
        class="icon-button icon-only"
        aria-label="Retour"
        data-test="orp-fiche-back"
        @click="back"
      >
        <AppIcon name="arrow-left" />
      </button>
      <h1 id="orp-fiche-title">
        Pour l’ORP
      </h1>
    </header>
    <OrpFiche
      :application-id="id"
      :month="month"
      @declared="back"
    />
  </section>
</template>
