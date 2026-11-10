<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { LOGO_EYE, LOGO_ONE, LOGO_SMILE, LOGO_SPARK, LOGO_VIEWBOX } from "../brandPaths";

// L'attente (MODIFICATIONS du 9 novembre, §15) : sous 1 s rien ; de 1 à 10 s, les 4 morceaux du logo sautent l'un
// après l'autre (le point bleu, le « 1 », le sourire, le point orange) ; au-delà, ils se posent et `slowText` dit ce
// qui se passe. `label` : le nom de ce qui charge, dessous. Annoncé une fois (role="status") ; sans animation avec
// « réduire les animations » (le logo immobile).
const props = withDefaults(defineProps<{ label?: string; slowText?: string; delay?: number }>(), {
  label: "",
  slowText: "",
  delay: 1000,
});

type LoaderStage = "hidden" | "jumping" | "slow";
const SLOW_AFTER_MS = 10_000;
const stage = ref<LoaderStage>(props.delay > 0 ? "hidden" : "jumping");
const timers: ReturnType<typeof setTimeout>[] = [];
onMounted(() => {
  if (props.delay > 0) timers.push(setTimeout(() => (stage.value = "jumping"), props.delay));
  timers.push(setTimeout(() => (stage.value = "slow"), SLOW_AFTER_MS));
});
onUnmounted(() => timers.forEach(clearTimeout));
</script>

<template>
  <div
    class="troupe-loader"
    :class="`troupe-loader-${stage}`"
    role="status"
    data-test="troupe-loader"
    :data-stage="stage"
  >
    <template v-if="stage !== 'hidden'">
      <svg
        class="troupe-loader-mark"
        :viewBox="LOGO_VIEWBOX"
        aria-hidden="true"
        focusable="false"
      >
        <circle
          class="troupe-loader-part troupe-loader-eye"
          :cx="LOGO_EYE.x"
          :cy="LOGO_EYE.y"
          :r="LOGO_EYE.r"
        />
        <path
          class="troupe-loader-part troupe-loader-line"
          :d="LOGO_ONE"
        />
        <path
          class="troupe-loader-part troupe-loader-line troupe-loader-smile"
          :d="LOGO_SMILE"
        />
        <circle
          class="troupe-loader-part troupe-loader-spark"
          :cx="LOGO_SPARK.x"
          :cy="LOGO_SPARK.y"
          :r="LOGO_SPARK.r"
        />
      </svg>
      <p
        v-if="label"
        class="troupe-loader-label"
      >
        {{ label }}
      </p>
      <p
        v-if="stage === 'slow' && slowText"
        class="troupe-loader-slow"
        data-test="troupe-loader-slow"
      >
        {{ slowText }}
      </p>
      <span
        v-if="!label"
        class="visually-hidden"
      >Chargement…</span>
    </template>
  </div>
</template>

<style scoped>
.troupe-loader { --loader-size: 4rem; --loader-jump: -12px; display: flex; flex-direction: column; align-items: center; gap: var(--space-3); text-align: center; }
.troupe-loader-mark { display: block; width: var(--loader-size); height: var(--loader-size); overflow: visible; }
.troupe-loader-line { fill: none; stroke: var(--logo-line); stroke-width: 14; stroke-linecap: round; stroke-linejoin: round; }
.troupe-loader-eye { fill: var(--logo-line); }
.troupe-loader-spark { fill: var(--logo-spark); }
.troupe-loader-label { margin: 0; font-size: var(--font-title); font-weight: var(--weight-bold); color: var(--text); }
.troupe-loader-slow { margin: 0; max-width: 20rem; font-size: var(--font-body); color: var(--text-secondary); }
/* Un saut de 1,2 s chacun son tour (0, 0,15, 0,3 et 0,45 s), puis l'attente du tour suivant. */
.troupe-loader-jumping .troupe-loader-part { animation: troupe-jump 1.2s cubic-bezier(0.3, 0, 0.2, 1) infinite; }
.troupe-loader-jumping .troupe-loader-line:not(.troupe-loader-smile) { animation-delay: 0.15s; }
.troupe-loader-jumping .troupe-loader-smile { animation-delay: 0.3s; }
.troupe-loader-jumping .troupe-loader-spark { animation-delay: 0.45s; }
@keyframes troupe-jump {
  0%, 40%, 100% { transform: translateY(0); }
  20% { transform: translateY(var(--loader-jump)); }
}
@media (prefers-reduced-motion: reduce) { .troupe-loader-jumping .troupe-loader-part { animation: none; } }
</style>
