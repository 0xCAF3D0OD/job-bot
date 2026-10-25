<script setup lang="ts">
import { computed } from "vue";

import { useCountUp } from "../../composables/useIntro";
import AppIcon from "../AppIcon.vue";
import Sparkline from "./Sparkline.vue";

// Tuile du Bilan (docs/54 §2) : pictogramme dans une bulle, courbe ; puis le grand chiffre
// d'abord, et sa précision dessous, en une phrase (« 26 · candidatures, sur 33 offres gardées »,
// 1.6.26). Toute la tuile mène à sa page, si elle en a une.
type Icon = InstanceType<typeof AppIcon>["$props"]["name"];
const props = defineProps<{
  to?: string | Record<string, unknown>;
  icon: Icon;
  label: string;
  value: string;
  trend?: string;
  rising?: boolean;
  tone?: "accent" | "mint" | "warn";
  values?: number[];
}>();

// Un compte (« 21 », « 4 / 10 ») monte jusqu'à sa valeur à la première ouverture (docs/60 §3) ;
// une date (« 5 octobre ») ne bouge pas.
const parts = computed(() => /^(\d+)( \/ .*)?$/.exec(props.value));
const counted = useCountUp(`tile:${props.label}`, () => Number(parts.value?.[1] ?? 0));
const display = computed(() => (parts.value ? `${counted.value}${parts.value[2] ?? ""}` : props.value));
</script>

<template>
  <component
    :is="to ? 'RouterLink' : 'div'"
    v-bind="to ? { to } : {}"
    :class="['dash-tile', tone, { static: !to }]"
  >
    <span class="dash-tile-head">
      <span class="dash-bubble">
        <AppIcon :name="icon" />
      </span>
      <Sparkline
        v-if="values?.length"
        :values="values"
      />
    </span>
    <span class="dash-tile-foot">
      <strong class="dash-value">{{ display }}</strong>
      <span
        class="dash-trend"
        data-test="tile-caption"
      >
        {{ trend ? `${label}, ${trend}` : label }}
        <AppIcon
          v-if="rising"
          name="trend"
        />
      </span>
      <slot />
    </span>
  </component>
</template>
