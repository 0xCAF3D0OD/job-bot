<script setup lang="ts">
import { SUN, WAVE } from "../moodShapes";

// Les animations du logo (maquette Animations, docs/139 étape 12) : le visage du 1 dans sa forme
// d'humeur, un geste joué une fois à l'apparition (l'attente seule tourne en boucle). Jamais entre deux
// pages ni dans les en-têtes ; le trait garde son épaisseur ; rien avec « réduire les animations »,
// où chaque forme montre son état final. Décoratif : le texte à côté dit tout.
// - loupe : aucune offre avec ces filtres (3 s) ;
// - cloche : tout est lu (2,8 s) ;
// - hochement : connexion perdue, « oups, non » (0,6 s) ;
// - attente : un chargement, le feston tourne, l'œil et la bille pâlissent ;
// - envoyee : « J'ai postulé », la bouche fait une barre, recule et prend son élan (1,2 s) ;
// - objectif : objectif ORP atteint, accroupi, saut, rayons (1,8 s).
export type MoodKind = "loupe" | "cloche" | "hochement" | "attente" | "envoyee" | "objectif";
defineProps<{ kind: MoodKind }>();
</script>

<template>
  <svg
    :class="['mood', `mood-${kind}`]"
    :viewBox="kind === 'loupe' ? '13 15 74 74' : '0 0 100 100'"
    aria-hidden="true"
    focusable="false"
    :data-mood-animation="kind"
  >
    <!-- Loupe : la loupe passe d'un œil à l'autre, chacun grossit dessous. -->
    <template v-if="kind === 'loupe'">
      <path
        class="line"
        d="M43 33L54 24V58"
      />
      <circle
        class="eye box mag-l"
        cx="24"
        cy="46"
        r="10"
      />
      <circle
        class="spark box mag-r"
        cx="76"
        cy="44"
        r="10"
      />
      <path
        class="line"
        d="M34 75H66"
      />
      <g class="loupe">
        <circle
          class="loupe-glass"
          cx="24"
          cy="46"
          r="16"
        />
        <path
          class="loupe-handle"
          d="M35.5 57.5 46 68"
        />
      </g>
    </template>

    <!-- Cloche : la bille s'efface, une cloche pêche sonne à sa place, puis la bille revient. -->
    <template v-else-if="kind === 'cloche'">
      <path
        class="arch"
        d="M5 84V58A45 45 0 0 1 95 58V84Q95 91 88 91H12Q5 91 5 84Z"
      />
      <g transform="translate(50 60) scale(0.54) translate(-50 -52)">
        <path
          class="line"
          d="M43 33L54 24V58"
        />
        <circle
          class="eye"
          cx="24"
          cy="46"
          r="10"
        />
        <circle
          class="spark box dot"
          cx="76"
          cy="44"
          r="10"
        />
        <path
          class="line"
          d="M32 74C42 80 58 80 68 74"
        />
        <g transform="translate(0 2)">
          <g class="box pop">
            <g class="top ring">
              <path
                class="bell-stem"
                d="M76 24V27"
              />
              <path
                class="bell"
                d="M66 48Q66 28 76 27Q86 28 86 48L89 51H63Z"
              />
              <circle
                class="bell-clapper"
                cx="76"
                cy="55"
                r="3.5"
              />
            </g>
          </g>
        </g>
      </g>
    </template>

    <!-- Hochement : le triangle dit « non » de la tête, une fois. -->
    <g
      v-else-if="kind === 'hochement'"
      class="no"
    >
      <path
        class="triangle"
        d="M56.77 22.25L85.23 73.75Q92 86 78 86H22Q8 86 14.77 73.75L43.23 22.25Q50 10 56.77 22.25Z"
      />
      <g transform="translate(50 63) scale(0.5) translate(-50 -52)">
        <path
          class="line"
          d="M43 33L54 24V58"
        />
        <circle
          class="eye"
          cx="24"
          cy="46"
          r="10"
        />
        <circle
          class="spark"
          cx="76"
          cy="44"
          r="10"
        />
        <path
          class="line"
          d="M36 77H64"
        />
      </g>
    </g>

    <!-- En attente : le feston tourne, l'œil et la bille pâlissent tour à tour. -->
    <template v-else-if="kind === 'attente'">
      <g class="box spin">
        <path
          class="arch"
          :d="WAVE"
        />
      </g>
      <g transform="translate(50 52) scale(0.56) translate(-50 -52)">
        <path
          class="line"
          d="M43 33L54 24V58"
        />
        <circle
          class="eye pulse"
          cx="24"
          cy="46"
          r="10"
        />
        <circle
          class="spark pulse late"
          cx="76"
          cy="44"
          r="10"
        />
        <path
          class="line"
          d="M34 75H66"
        />
      </g>
    </template>

    <!-- Candidature envoyée : la bouche se tend en barre, recule, part avec un élan, revient en sourire. -->
    <g
      v-else-if="kind === 'envoyee'"
      class="tilt"
    >
      <path
        class="arch"
        d="M5 84V58A45 45 0 0 1 95 58V84Q95 91 88 91H12Q5 91 5 84Z"
      />
      <g transform="translate(50 60) scale(0.54) translate(-50 -52)">
        <path
          class="line"
          d="M43 33L54 24V58"
        />
        <circle
          class="eye"
          cx="24"
          cy="46"
          r="10"
        />
        <circle
          class="spark box s-spark"
          cx="76"
          cy="44"
          r="10"
        />
        <path
          class="line box s-smile"
          d="M32 74C42 80 58 80 68 74"
        />
        <path
          class="line s-bar"
          d="M36 77H64"
        />
        <g class="s-lines">
          <path d="M4 70H22" />
          <path d="M8 80H26" />
          <path d="M2 88H18" />
        </g>
        <g class="s-vib">
          <path d="M92 32Q99 44 92 56" />
          <path d="M60 32Q53 44 60 56" />
        </g>
      </g>
    </g>

    <!-- Objectif atteint : le soleil s'accroupit, saute, retombe ; rayons et étincelles. -->
    <template v-else>
      <g class="g-lines">
        <path d="M38 100V110" />
        <path d="M50 102V114" />
        <path d="M62 100V110" />
      </g>
      <g class="g-jump">
        <path
          class="sun"
          :d="SUN"
        />
        <g transform="translate(50 52) scale(0.56) translate(-50 -52)">
          <path
            class="line"
            d="M43 33L54 24V58"
          />
          <circle
            class="eye"
            cx="24"
            cy="46"
            r="10"
          />
          <g transform="translate(0 3)">
            <path
              class="box g-rays"
              d="M90 41H95M85.9 50.9 89.4 54.4M76 55V60M66.1 50.9 62.6 54.4M62 41H57M66.1 31.1 62.6 27.6M76 27V22M85.9 31.1 89.4 27.6"
            />
          </g>
          <circle
            class="spark box g-spark"
            cx="76"
            cy="44"
            r="10"
          />
          <path
            class="line"
            d="M28 70C38 84 62 84 72 70"
          />
        </g>
      </g>
      <g transform="translate(2 6)">
        <path
          class="box sparkle sp0"
          d="M0-10Q1.8-1.8 10 0Q1.8 1.8 0 10Q-1.8 1.8-10 0Q-1.8-1.8 0-10Z"
        />
      </g>
      <g transform="translate(98 96)">
        <path
          class="box sparkle sp1"
          d="M0-10Q1.8-1.8 10 0Q1.8 1.8 0 10Q-1.8 1.8-10 0Q-1.8-1.8 0-10Z"
        />
      </g>
      <g transform="translate(98 4)">
        <path
          class="box sparkle sp2"
          d="M0-10Q1.8-1.8 10 0Q1.8 1.8 0 10Q-1.8 1.8-10 0Q-1.8-1.8 0-10Z"
        />
      </g>
    </template>
  </svg>
</template>

<style scoped>
.mood { display: block; width: var(--mood-box); height: var(--mood-box); overflow: visible; }
.mood-loupe { width: 5.2rem; height: 5.2rem; }
.line { fill: none; stroke: var(--logo-line); stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }
.eye { fill: var(--logo-line); }
.spark { fill: var(--logo-spark); }
.arch, .triangle, .sun { stroke-width: 1.5; vector-effect: non-scaling-stroke; }
.arch { fill: var(--primary-soft); stroke: var(--water); }
.triangle { fill: var(--warning-soft); stroke: color-mix(in srgb, var(--spark) 70%, var(--warning-soft)); }
.sun { fill: var(--peach-soft); stroke: var(--peach); }
.box { transform-box: fill-box; transform-origin: 50% 50%; }
.top { transform-box: fill-box; transform-origin: 50% 0; }
.loupe-glass { fill: color-mix(in srgb, var(--text) 8%, transparent); stroke: var(--text); stroke-width: 4.5; }
.loupe-handle { stroke: var(--text); stroke-width: 7; stroke-linecap: round; }
.bell, .bell-clapper { fill: var(--logo-spark); }
.bell { stroke: var(--logo-spark); stroke-width: 2.5; stroke-linejoin: round; }
.bell-stem { stroke: var(--logo-spark); stroke-width: 4; stroke-linecap: round; }
.s-lines, .g-lines { stroke: var(--logo-line); stroke-linecap: round; }
.s-lines { stroke-width: 4; }
.g-lines { stroke-width: 2.5; }
.s-vib, .g-rays { fill: none; stroke: var(--logo-spark); stroke-width: 4; stroke-linecap: round; }
.sparkle { fill: var(--scribble); }

@media (prefers-reduced-motion: no-preference) {
  .loupe { animation: loupe 3s cubic-bezier(.6, 0, .3, 1) .4s both; }
  .mag-l { animation: mag-l 3s ease-out .4s both; }
  .mag-r { animation: mag-r 3s ease-out .4s both; }
  .dot { animation: dot-out 2.8s cubic-bezier(.4, 0, .2, 1) .4s both; }
  .pop { animation: pop-in 2.8s cubic-bezier(.2, .9, .3, 1.2) .4s both; }
  .ring { animation: ring 2.8s ease-in-out .4s both; }
  .no { transform-box: fill-box; transform-origin: 50% 86%; animation: no .6s cubic-bezier(.2, 0, 0, 1) .25s both; }
  .spin { animation: spin 3s linear infinite; }
  .pulse { animation: pulse 1.2s ease-in-out infinite; }
  .pulse.late { animation-delay: .6s; }
  .tilt { transform-box: fill-box; transform-origin: 50% 100%; animation: s-tilt 1.2s ease-in-out both; }
  .s-smile { animation: s-smile 1.2s cubic-bezier(.3, 0, .2, 1) both; }
  .s-bar { animation: s-bar 1.2s linear both; }
  .s-lines { animation: s-lines 1.2s ease-out both; }
  .s-spark { animation: s-spark 1.2s ease-out both; }
  .s-vib { animation: s-vib 1.2s linear both; }
  .g-jump { animation: g-jump 1.8s cubic-bezier(.3, 0, .2, 1) both; }
  .g-lines { animation: g-lines 1.8s linear both; }
  .g-rays { animation: g-rays 1.8s ease-out both; }
  .g-spark { animation: g-spark 1.8s ease-out both; }
  .sparkle { animation: g-sp .9s ease-out .85s both; }
  .sp0 { --dx: -8px; --dy: -8px; }
  .sp1 { --dx: 8px; --dy: 8px; animation-delay: .97s; }
  .sp2 { --dx: 8px; --dy: -8px; animation-delay: 1.09s; }
}
/* Moins d'animations : l'état final, sans les traits de mouvement ni ce qui ne fait que passer. */
@media (prefers-reduced-motion: reduce) {
  .loupe, .pop, .s-bar, .s-lines, .s-vib, .g-lines, .g-rays, .sparkle { display: none; }
}

@keyframes loupe {
  0% { opacity: 0; transform: translate(40px, 40px); }
  15%, 35% { opacity: 1; transform: translate(0, 0); }
  55%, 75% { opacity: 1; transform: translate(52px, -4px); }
  95%, 100% { opacity: 0; transform: translate(70px, 30px); }
}
@keyframes mag-l { 0%, 13% { transform: scale(1); } 18%, 33% { transform: scale(1.35); } 38%, 100% { transform: scale(1); } }
@keyframes mag-r { 0%, 53% { transform: scale(1); } 58%, 73% { transform: scale(1.35); } 78%, 100% { transform: scale(1); } }
@keyframes dot-out { 0%, 10% { transform: scale(1); } 20%, 80% { transform: scale(0); } 92%, 100% { transform: scale(1); } }
@keyframes pop-in { 0%, 14% { transform: scale(0); } 28%, 76% { transform: scale(1); } 88%, 100% { transform: scale(0); } }
@keyframes ring {
  0%, 28% { transform: rotate(0); }
  36% { transform: rotate(16deg); }
  44% { transform: rotate(-14deg); }
  52% { transform: rotate(10deg); }
  60% { transform: rotate(-6deg); }
  68%, 100% { transform: rotate(0); }
}
@keyframes no { 25% { transform: rotate(-6deg); } 50% { transform: rotate(5deg); } 75% { transform: rotate(-2deg); } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 50% { opacity: .3; } }
@keyframes s-smile {
  0%, 12% { opacity: 1; transform: none; }
  13%, 28% { opacity: 0; transform: translateX(-6px); }
  29% { opacity: 1; transform: translateX(0); }
  48% { opacity: 0; transform: translateX(40px) rotate(-14deg); }
  62% { opacity: 0; transform: translateX(-10px) scale(.8); }
  80%, 100% { opacity: 1; transform: none; }
}
@keyframes s-bar { 0%, 12% { opacity: 0; transform: none; } 13% { opacity: 1; transform: none; } 28% { opacity: 1; transform: translateX(-9px); } 29%, 100% { opacity: 0; } }
@keyframes s-lines { 0%, 28% { opacity: 0; transform: none; } 36% { opacity: 1; } 50%, 100% { opacity: 0; transform: translateX(24px); } }
@keyframes s-tilt { 0%, 28% { transform: none; } 40% { transform: rotate(4deg); } 55%, 100% { transform: none; } }
@keyframes s-spark { 0%, 75% { transform: scale(1); } 84% { transform: scale(1.3); } 92% { transform: scale(1.1); } 100% { transform: scale(1); } }
@keyframes s-vib { 0%, 76% { opacity: 0; } 82%, 94% { opacity: 1; } 100% { opacity: 0; } }
@keyframes g-jump {
  0% { transform: translateY(0); }
  12% { transform: translateY(5px); }
  30% { transform: translateY(-22px); }
  45% { transform: translateY(0); }
  51% { transform: translateY(-4px); }
  57%, 100% { transform: translateY(0); }
}
@keyframes g-lines { 0%, 14% { opacity: 0; } 20% { opacity: 1; } 32%, 100% { opacity: 0; } }
@keyframes g-rays {
  0%, 44% { opacity: 0; transform: scale(.6) rotate(0); }
  55% { opacity: 1; transform: scale(1) rotate(20deg); }
  90% { opacity: 1; transform: scale(1) rotate(90deg); }
  100% { opacity: 0; transform: scale(1) rotate(100deg); }
}
@keyframes g-spark { 0%, 44% { transform: scale(1); } 52% { transform: scale(1.25); } 62%, 100% { transform: scale(1); } }
@keyframes g-sp {
  0% { transform: scale(0) translate(0, 0); opacity: 1; }
  30% { transform: scale(1) translate(0, 0); opacity: 1; }
  100% { transform: scale(.8) translate(var(--dx), var(--dy)); opacity: 0; }
}
</style>
