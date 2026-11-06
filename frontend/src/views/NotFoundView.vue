<script setup lang="ts">
import sign from "../assets/accessoires/accessoire-panneau.webp";
import lost from "../assets/personnage/perso-06-perplexe-400.webp";
import lost2x from "../assets/personnage/perso-06-perplexe-800.webp";
import BrandMark from "../components/BrandMark.vue";

// Page introuvable (docs/59 §5 ; maquette PageIntrouvable du 2026-11-05) : une adresse qui ne mène nulle
// part le dit, au lieu de renvoyer sans un mot vers l'accueil. Le logo et « jobA1 » en haut, sans barre ;
// le personnage perplexe du kit (400 px, 800 px pour les écrans 2×, 200 px de haut au plus sur téléphone)
// devant le panneau, les nuages et le sol ; « Retour à l'accueil » en bas, pleine largeur.
</script>

<template>
  <div class="lost-page">
    <header class="lost-brand">
      <BrandMark :size="30" />
      <span>jobA1</span>
    </header>
    <div class="lost-main">
      <div
        class="lost-scene"
        aria-hidden="true"
        data-test="not-found-scene"
      >
        <svg
          class="lost-cloud"
          viewBox="0 0 200 100"
        ><path d="M30 100 a30 30 0 0 1 10-58 a46 46 0 0 1 88-6 a34 34 0 0 1 48 34 a24 24 0 0 1 -6 30 Z" /></svg>
        <svg
          class="lost-cloud lost-cloud-small"
          viewBox="0 0 100 55"
        ><path d="M0 55 a22 22 0 0 1 22-30 a28 28 0 0 1 52 0 a22 22 0 0 1 26 30 Z" /></svg>
        <img
          class="lost-sign"
          :src="sign"
          alt=""
          width="295"
          height="337"
          decoding="async"
        >
        <img
          class="lost-person"
          :src="lost"
          :srcset="`${lost} 1x, ${lost2x} 2x`"
          alt=""
          width="146"
          height="400"
          decoding="async"
          data-test="not-found-person"
        >
        <span class="lost-ground" />
      </div>
      <h1 class="lost-title">
        Cette page s’est perdue
      </h1>
      <p class="lost-line">
        Le lien est peut-être ancien. Tout le reste est à sa place.
      </p>
    </div>
    <div class="lost-actions">
      <RouterLink
        to="/aujourdhui"
        class="lost-home"
        data-test="not-found-home"
      >
        Retour à l’accueil
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* Valeurs de la maquette PageIntrouvable (390 px), ramenées aux échelles ; le personnage à 200 px (règle du kit). */
.lost-page { min-height: 100dvh; display: flex; flex-direction: column; background: var(--bg); color: var(--text); }
.lost-brand { flex: none; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-5) var(--space-5) 0; font-size: var(--font-section); font-weight: var(--weight-bold); }
.lost-main { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); padding: 0 var(--space-6); text-align: center; }
.lost-scene { position: relative; flex: none; width: 340px; max-width: 100%; height: 240px; }
.lost-scene svg { position: absolute; display: block; fill: var(--primary-soft); }
.lost-cloud { left: 14px; top: 0; width: 130px; height: 65px; }
.lost-cloud-small { top: auto; left: 4px; bottom: 16px; width: 84px; height: 46px; }
.lost-sign { position: absolute; right: 24px; bottom: 10px; width: auto; height: 110px; }
.lost-person { position: absolute; left: 50%; bottom: 12px; width: auto; height: 200px; max-width: none; transform: translateX(-50%); }
.lost-ground { position: absolute; left: 5px; right: 5px; bottom: 2px; height: 16px; border-radius: var(--radius-sm); background: var(--surface-muted); }
.lost-title { margin: var(--space-2) 0 0; font-size: var(--font-figure); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.3px; }
.lost-line { margin: 0; max-width: 310px; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.lost-actions { flex: none; display: flex; justify-content: center; padding: var(--space-4) var(--space-5) var(--space-8); }
.lost-home {
  display: flex; align-items: center; justify-content: center; width: 100%; max-width: 26rem; min-height: var(--btn-secondary);
  border: 1.5px solid var(--primary-graphic); border-radius: var(--radius-pill); color: var(--primary-text);
  font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none;
}
.lost-home:hover { background: var(--primary-soft); color: var(--primary-text); }
@media (min-width: 821px) {
  .lost-scene { height: 340px; }
  .lost-person { height: 290px; }
  .lost-sign { height: 136px; }
}
</style>
