<script setup lang="ts">
import AppIcon from "./AppIcon.vue";
import ScoreRing from "./ScoreRing.vue";

// Un bout de la plateforme, en arrière-plan d'une scène de la présentation (docs/67, complément) :
// dessiné ici, aux couleurs du thème, avec des exemples inventés ; jamais une capture.
export type MockKind = "alerts" | "offers" | "apply" | "follow" | "orp" | "trainings";

defineProps<{ kind: MockKind }>();

const TITLES: Record<MockKind, string> = {
  alerts: "Candidatures › Alertes",
  offers: "Candidatures › Offres",
  apply: "Préparer ma candidature",
  follow: "Candidatures › Suivi",
  orp: "Justificatifs ORP · octobre",
  trainings: "Bilan › Formations",
};
</script>

<template>
  <div
    class="dmock"
    aria-hidden="true"
  >
    <div class="dmock-bar">
      <span /><span /><span />
      <strong>{{ TITLES[kind] }}</strong>
    </div>

    <div
      v-if="kind === 'alerts'"
      class="dmock-body"
    >
      <div
        v-for="row in [['jobup.ch', 'Infirmier·ère · Vaud'], ['Indeed', 'Soins · Genève'], ['jobup.ch', 'Infirmier·ère · Fribourg']]"
        :key="row[1]"
        class="dmock-row"
      >
        <span class="dmock-site">{{ row[0] }}</span>
        <span class="dmock-grow">{{ row[1] }}</span>
        <span class="dmock-toggle" />
      </div>
      <span class="dmock-button">+ Nouvelle alerte</span>
    </div>

    <div
      v-else-if="kind === 'offers'"
      class="dmock-body"
    >
      <div
        v-for="offer in [[92, 'Infirmier·ère 80–100 %', 'Lausanne'], [84, 'Infirmier·ère de nuit', 'Morges'], [61, 'Aide-soignant·e', 'Vevey']]"
        :key="offer[1]"
        class="dmock-row"
      >
        <!-- La note comme dans l'application : un cercle qui se remplit (docs/73), plus une pastille. -->
        <ScoreRing :score="Number(offer[0])" />
        <span class="dmock-grow"><strong>{{ offer[1] }}</strong><small>{{ offer[2] }}</small></span>
      </div>
    </div>

    <div
      v-else-if="kind === 'apply'"
      class="dmock-body"
    >
      <p class="dmock-letter">
        Madame, Monsieur,
      </p>
      <span class="dmock-line" />
      <span class="dmock-line" />
      <span class="dmock-line short" />
      <span class="dmock-line" />
      <div class="dmock-row plain">
        <span class="dmock-tag with-icon"><AppIcon name="done" />CV adapté</span>
        <span class="dmock-button">Copier la lettre</span>
      </div>
    </div>

    <div
      v-else-if="kind === 'follow'"
      class="dmock-body"
    >
      <div class="dmock-calendar">
        <span
          v-for="day in 21"
          :key="day"
          :class="{ sent: [3, 5, 9, 12, 16].includes(day), today: day === 18 }"
        />
      </div>
      <div class="dmock-row">
        <span class="dmock-dot" />
        <span class="dmock-grow">Relance prévue jeudi</span>
      </div>
    </div>

    <div
      v-else-if="kind === 'orp'"
      class="dmock-body"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="dmock-row"
      >
        <span class="dmock-check"><AppIcon name="done" /></span>
        <span class="dmock-line" />
      </div>
      <div class="dmock-row plain">
        <strong>10 / 10 recherches</strong>
        <span class="dmock-button">Remettre</span>
      </div>
    </div>

    <div
      v-else
      class="dmock-body"
    >
      <div
        v-for="item in [['Formation', 'Soins palliatifs : nouvelle session'], ['Certificat', 'Gestion de projet, en ligne']]"
        :key="item[1]"
        class="dmock-row"
      >
        <span class="dmock-thumb" />
        <span class="dmock-grow"><small class="dmock-kicker">{{ item[0] }}</small><strong>{{ item[1] }}</strong></span>
      </div>
    </div>
  </div>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.discover-scene.flip .discover-stage .dmock { left: auto; right: 0; transform: rotate(2deg); }
.dmock-toggle::after { content: ""; position: absolute; right: 0.15rem; top: 0.15rem; width: 0.75rem; height: 0.75rem; border-radius: var(--radius-pill); background: #fff; }
.dmock-thumb { width: 3rem; height: 2.2rem; border-radius: var(--radius-sm); background: var(--accent-soft); flex: none; }
@media (max-width: 820px) {
.discover-stage .dmock { width: 92%; }
}
</style>
