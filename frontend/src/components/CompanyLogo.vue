<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Offer } from "../api/client";
import { colorIndex } from "../format";

// Logo de l'entreprise servi par la plateforme (docs/14 §4) ; la lettre en secours.
const props = defineProps<{ offer: Offer; large?: boolean }>();

const failed = ref(false);
watch(
  () => props.offer.id,
  () => {
    failed.value = false;
  },
);

const name = computed(() => props.offer.company ?? props.offer.title);
const initial = computed(() => name.value.trim().charAt(0).toUpperCase() || "?");
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
      @error="failed = true"
    >
    <template v-else>{{ initial }}</template>
  </span>
</template>
