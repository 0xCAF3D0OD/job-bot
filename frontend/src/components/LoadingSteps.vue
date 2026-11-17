<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

// Les écrans de chargement (LISEZMOI §53, planches ChargementCV et ChargementLettre du 17.11) : le titre manuscrit sur
// deux lignes, une barre de 8 px, puis les étapes (coche verte faite, cercle qui tourne en cours, cercle vide à venir).
// Le serveur ne dit pas où il en est : les étapes avancent avec le temps habituel de chacune (`everyMs`), la dernière
// reste en cours jusqu'à la réponse, et la barre s'arrête à 90 % ; la fin vient toujours du serveur (le parent retire
// le composant). La classe `loading-steps-full`, posée par la page : l'écran plein des premiers pas sur téléphone
// (le logo en slot) ; sinon, le bloc dans sa carte.
// L'étape en cours est dite par aria-current, les faites par « : fait » (contenu CSS).
// `quiet` : dans une zone déjà annoncée (la carte « Mon CV »), la liste n'est pas une seconde zone d'état.
const props = defineProps<{ lines: string[]; steps: string[]; everyMs: number; label: string; quiet?: boolean }>();

// Une étape de plus à chaque `everyMs` ; la barre glisse d'un cran à l'autre en 5 s (aria-valuemin et max : 0 et 100
// par défaut).
const tick = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
onMounted(() => (timer = setInterval(() => tick.value++, props.everyMs)));
onBeforeUnmount(() => clearInterval(timer));
const current = computed(() => Math.min(tick.value, props.steps.length - 1));
// 10 % au départ, puis un cran par étape, sans dépasser 90 % : la fin vient du serveur.
const progress = computed(() => 10 + (Math.min(tick.value, props.steps.length) / props.steps.length) * 80);
</script>

<template>
  <div class="loading-steps">
    <!-- Le logo de 64 px de l'écran plein, donné par la page (elle a déjà BrandMark). -->
    <slot />
    <p class="loading-steps-title">
      <span>{{ lines[0] }}</span><span class="loading-steps-sub">{{ lines[1] }}</span>
    </p>
    <div
      class="loading-steps-bar"
      role="progressbar"
      :aria-label="label"
      :aria-valuenow="progress"
    >
      <i :style="{ width: `${progress}%` }" />
    </div>
    <ol
      class="loading-steps-list"
      :role="quiet ? undefined : 'status'"
    >
      <li
        v-for="(step, index) in steps"
        :key="step"
        :class="index < current ? 'is-done' : index === current ? 'is-current' : 'is-todo'"
        :aria-current="index === current ? 'step' : undefined"
      >
        <!-- La marque : coche verte, cercle qui tourne ou cercle vide, dessinée en CSS (moins de code à charger). -->
        <i class="loading-steps-mark" />{{ step }}
      </li>
    </ol>
  </div>
</template>

<style>
/* Chargé avec le composant (allègement du 16.11, issue #797) : rien dans style.css, même pas son jeton, la taille du titre
   manuscrit de ChargementCV (38 px). */
.loading-steps { --title-hand-load: 38px; display: flex; flex-direction: column; color: var(--text); }
.loading-steps-full { box-sizing: border-box; min-height: 100dvh; justify-content: center; padding: var(--space-8) calc(var(--space-8) + var(--space-1)); background: var(--bg); }
.loading-steps-full .loading-steps-title { margin-top: calc(var(--space-6) + var(--space-1)); }
.loading-steps-title { margin: 0; font-family: var(--font-hand); font-size: var(--title-hand-load); font-weight: var(--weight-regular); line-height: var(--leading-none); letter-spacing: 0; color: var(--primary-text); }
.loading-steps-title span { display: block; width: fit-content; transform: rotate(-2deg); transform-origin: left center; }
.loading-steps-title .loading-steps-sub { margin-top: var(--space-1); color: var(--peach-text); }
.loading-steps-bar { margin-top: calc(var(--space-6) + var(--space-1)); height: var(--space-2); border-radius: var(--space-1); background: var(--line); overflow: hidden; }
.loading-steps-bar i { display: block; height: 100%; border-radius: var(--space-1); background: var(--primary-graphic); transition: width 5s linear; }
.loading-steps-list { list-style: none; margin: var(--space-8) 0 0; padding: 0; display: flex; flex-direction: column; gap: calc(var(--space-4) + var(--space-1) / 2); }
.loading-steps-list li { display: flex; gap: calc(var(--space-3) + var(--space-1) / 2); align-items: flex-start; font-size: calc(var(--font-body) * 1.0625); line-height: calc(var(--space-6) + var(--space-1) / 2); font-weight: calc(var(--weight-regular) + 100); }
.loading-steps-mark { flex: none; box-sizing: border-box; width: var(--space-6); height: var(--space-6); margin-top: 1px; border-radius: var(--radius-pill); border: 2px solid var(--line-strong); }
.is-done .loading-steps-mark { position: relative; border: 0; background: var(--success); }
.is-done .loading-steps-mark::after { content: ""; position: absolute; left: 0.47rem; top: 0.3rem; width: 0.3rem; height: 0.6rem; border: solid var(--surface); border-width: 0 2px 2px 0; transform: rotate(45deg); }
.is-current .loading-steps-mark { border-width: 2.5px; border-right-color: var(--primary-graphic); animation: loading-steps-turn 0.9s linear infinite; }
@keyframes loading-steps-turn { to { transform: rotate(360deg); } }
/* « : fait », lu par les lecteurs d'écran et caché à l'œil (en CSS : moins de code à charger). */
.loading-steps-list .is-done::after { content: " : fait"; position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.loading-steps-list .is-current { font-weight: var(--weight-bold); }
.loading-steps-list .is-todo { color: var(--text-secondary); }
@media (prefers-reduced-motion: reduce) {
  .is-current .loading-steps-mark { animation: none; }
  .loading-steps-bar i { transition: none; }
}
</style>
