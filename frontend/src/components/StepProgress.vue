<script setup lang="ts">
import { computed } from "vue";

// La progression pas à pas (règles §4) : « 1 sur 5 » puis une barre en segments, un par élément ; ceux
// déjà vus en --accent. Pour le tri des offres du jour et les relances une à une. Au-delà de 10, les
// segments seraient trop fins : une barre continue. Le texte dit tout ; la barre est décorative.
const props = defineProps<{ current: number; total: number }>();
const SEGMENTS_MAX = 10;
const shown = computed(() => Math.min(Math.max(props.current, 0), props.total));
const segmented = computed(() => props.total <= SEGMENTS_MAX);
const percent = computed(() => (props.total > 0 ? (shown.value / props.total) * 100 : 0));
</script>

<template>
  <div
    class="step-progress"
    data-test="step-progress"
  >
    <p
      class="step-progress-text"
      aria-live="polite"
    >
      {{ shown }} sur {{ total }}
    </p>
    <span
      :class="['step-progress-bar', { continuous: !segmented }]"
      aria-hidden="true"
    >
      <template v-if="segmented">
        <span
          v-for="index in total"
          :key="index"
          :class="['step-progress-segment', { done: index <= shown }]"
        />
      </template>
      <span
        v-else
        class="step-progress-segment done"
        :style="{ width: `${percent}%` }"
      />
    </span>
  </div>
</template>
