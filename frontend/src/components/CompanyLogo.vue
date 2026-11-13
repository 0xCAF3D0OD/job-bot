<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Offer } from "../api/client";
import { usePhone } from "../composables/usePhone";
import { isBlankLogo } from "../logoImage";
import { colorIndex, initials } from "../format";

// Logo de l'entreprise servi par la plateforme (docs/14 §4) ; la lettre en secours, deux initiales sur
// téléphone (maquettes Accueil et Offre, comme la Ligne d'offre) et, avec « pair », aussi sur ordinateur (le livre
// du tri et la fin du tri, maquettes TrierOffresOrdinateurV2 et FinDuTriOrdinateur).
const props = defineProps<{ offer: Offer; large?: boolean; pair?: boolean }>();

const failed = ref(false);
watch(
  () => props.offer.id,
  () => {
    failed.value = false;
  },
);

const name = computed(() => props.offer.company ?? props.offer.title);
const { phone } = usePhone();
const initial = computed(() => (phone.value || props.pair ? initials(name.value) : name.value.trim().charAt(0).toUpperCase() || "?"));
const showImage = computed(() => Boolean(props.offer.has_logo) && !failed.value);
</script>

<template>
  <span
    :class="['logo', { large, image: showImage }, showImage ? '' : `c${colorIndex(name)}`]"
    aria-hidden="true"
    data-test="company-logo"
  >
    <img
      v-if="showImage"
      :src="`/api/offers/${offer.id}/logo`"
      alt=""
      loading="lazy"
      @load="failed = isBlankLogo($event.target as HTMLImageElement)"
      @error="failed = true"
    >
    <template v-else>{{ initial }}</template>
  </span>
</template>
