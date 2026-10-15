<script setup lang="ts">
import AppIcon from "../AppIcon.vue";
import Sparkline from "./Sparkline.vue";

// Tuile d'Aujourd'hui (docs/54 §2) : pictogramme dans une bulle, nom, courbe ; en bas, une
// petite tendance et le grand chiffre. Toute la tuile mène à sa page.
type Icon = InstanceType<typeof AppIcon>["$props"]["name"];
defineProps<{
  to: string | Record<string, unknown>;
  icon: Icon;
  label: string;
  value: string;
  trend?: string;
  rising?: boolean;
  tone?: "accent" | "mint" | "warn";
  values?: number[];
}>();
</script>

<template>
  <RouterLink
    :to="to"
    :class="['dash-tile', tone]"
  >
    <span class="dash-tile-head">
      <span class="dash-bubble">
        <AppIcon :name="icon" />
      </span>
      <span class="dash-tile-label">{{ label }}</span>
      <Sparkline
        v-if="values?.length"
        :values="values"
      />
    </span>
    <span class="dash-tile-foot">
      <span
        v-if="trend"
        class="dash-trend"
      >
        {{ trend }}
        <AppIcon
          v-if="rising"
          name="trend"
        />
      </span>
      <strong class="dash-value">{{ value }}</strong>
      <slot />
    </span>
  </RouterLink>
</template>
