<script setup lang="ts">
import type { Scene } from "../troupe";
import AppIcon from "./AppIcon.vue";
import TroupeScene from "./TroupeScene.vue";

// La colonne de droite sans élément ouvert (§36 du 16 novembre, planches CandidaturesOrdinateurAucuneOuverte,
// EnvoyeesOrdinateurAucuneOuverte, RendezVousOrdinateurAucunOuvert) : centrées, la scène de 340 px, le titre 24/800,
// puis une pastille bleue avec une flèche vers la liste. Pas de bouton : l'action est dans la liste, que les
// personnages montrent du doigt. Ordinateur seulement (la colonne n'existe pas sur téléphone).
defineProps<{ scene: Scene; title: string; hint: string }>();
</script>

<template>
  <div
    class="choose-detail"
    data-test="choose-detail"
  >
    <TroupeScene
      :scene="scene"
      :width="340"
      :desktop-width="340"
    />
    <h2 class="choose-title">
      {{ title }}
    </h2>
    <p class="choose-hint">
      <AppIcon name="arrow-left" />{{ hint }}
    </p>
  </div>
</template>

<style>
/* Valeurs des planches : bloc centré, 24 px sur les côtés et 48 dessous ; titre à 24 px de la scène ; pastille à 12 px,
   6/12, 14/20 600, flèche de 16 px (trait 2,2) à 6 px du texte. Sombre : fond #232B45, texte #C9D3FF. */
.choose-detail { --choose-title: 1.5rem; --choose-title-lh: 1.875rem; --choose-pill-y: 6px; --choose-pill-gap: 6px; --choose-pill-text: var(--primary-text);
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 var(--space-6) var(--space-12); text-align: center; }
:root[data-theme="dark"] .choose-detail { --choose-pill-text: #C9D3FF; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .choose-detail { --choose-pill-text: #C9D3FF; } }
.choose-detail .choose-title { margin: var(--space-6) 0 0; font-size: var(--choose-title); line-height: var(--choose-title-lh); font-weight: var(--weight-heavy); color: var(--text); }
.choose-detail .choose-hint { display: inline-flex; align-items: center; gap: var(--choose-pill-gap); margin: var(--space-3) 0 0; padding: var(--choose-pill-y) var(--space-3); border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--choose-pill-text); font-size: var(--font-small); line-height: 1.25rem; font-weight: var(--weight-semibold); }
.choose-hint .icon { stroke-width: 2.2; }
</style>
