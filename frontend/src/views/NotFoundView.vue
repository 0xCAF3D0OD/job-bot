<script setup lang="ts">
import sign from "../assets/accessoires/accessoire-panneau.webp";
import BrandMark from "../components/BrandMark.vue";
import TroupeScene from "../components/TroupeScene.vue";

// Page introuvable (docs/59 §5 ; maquette PageIntrouvable du 2026-11-05) : une adresse qui ne mène nulle
// part le dit, au lieu de renvoyer sans un mot vers l'accueil. Le logo et « jobA1 » en haut, sans barre ;
// les 4 personnages du logo (scène « introuvable », §15 du 9 novembre, 340 px) devant le panneau, les nuages et le
// sol ; « Retour à l'accueil » en bas, pleine largeur.
// Ordinateur dès 1 024 px (maquette du 8 novembre, PageIntrouvableOrdinateur) : l'en-tête complet quand on est
// connecté (App.vue), la scène seule à 392 px, le titre de 34 et « Retour à l'accueil » en bouton plein dessous.
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
        <TroupeScene
          scene="introuvable"
          full
          class="lost-person"
          data-test="not-found-person"
        />
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
/* Valeurs de la maquette PageIntrouvable (390 px), ramenées aux échelles ; la scène à 340 px. */
.lost-page { min-height: 100dvh; display: flex; flex-direction: column; background: var(--bg); color: var(--text); }
.lost-brand { flex: none; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-5) var(--space-5) 0; font-size: var(--font-section); font-weight: var(--weight-bold); }
.lost-main { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); padding: 0 var(--space-6); text-align: center; }
.lost-scene { position: relative; flex: none; width: 340px; max-width: 100%; height: 320px; }
.lost-scene svg { position: absolute; display: block; fill: var(--primary-soft); }
.lost-cloud { left: 14px; top: 20px; width: 130px; height: 65px; }
.lost-cloud-small { top: auto; left: 4px; bottom: 16px; width: 84px; height: 46px; }
.lost-sign { position: absolute; right: 10px; bottom: 10px; width: auto; height: 136px; }
.lost-person { position: absolute; left: 50%; bottom: 12px; transform: translateX(-50%); }
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
}
/* Ordinateur (maquette PageIntrouvableOrdinateur) : la scène seule, 392 px ; le titre de 34/42 en
   800, la phrase de 18/28, le bouton plein de 44 dessous. */
@media (min-width: 1024px) {
  .lost-page { --lost-34: 34px; --lost-42: 42px; --lost-18: 18px; --lost-28: 28px; min-height: calc(100dvh - 12rem); flex: 1; justify-content: center; }
  :root:has(.topbar) .lost-brand { display: none; }
  .lost-brand { padding: var(--space-5) max(var(--space-6), calc((100vw - var(--header-max)) / 2 + var(--space-6))) 0; }
  .lost-main { flex: 0 0 auto; align-self: center; max-width: 880px; gap: 0; padding: var(--space-6) 0 0; }
  .lost-scene { width: auto; height: auto; }
  .lost-scene :is(svg, .lost-sign, .lost-ground) { display: none; }
  .lost-person { position: static; transform: none; }
  .lost-title { margin: var(--space-6) 0 0; font-size: var(--lost-34); line-height: var(--lost-42); font-weight: var(--weight-heavy); letter-spacing: normal; }
  .lost-line { max-width: 560px; margin: var(--space-3) 0 0; font-size: var(--lost-18); line-height: var(--lost-28); color: var(--text-secondary); }
  .lost-actions { padding: var(--lost-28) 0 var(--space-12); }
  .lost-home { width: auto; max-width: none; min-height: var(--target-min); padding: 0 var(--space-5); border: 0; background: var(--primary); color: var(--on-primary); font-size: var(--font-label); }
  .lost-home:hover { background: color-mix(in srgb, var(--primary) 88%, var(--text)); color: var(--on-primary); }
}
</style>
