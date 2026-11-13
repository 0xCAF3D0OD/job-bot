<script setup lang="ts">
import type { IconName } from "../icons";
import type { Scene } from "../troupe";
import AppIcon from "./AppIcon.vue";
import BrandMark from "./BrandMark.vue";
import TroupeScene from "./TroupeScene.vue";

// Un moment en écran plein (maquette CandidatureEnvoyee du 6.11, docs/141 §3) : la marque en haut sur
// téléphone, la scène des 4 personnages du logo (§15 du 9 novembre ; 340 px, 471 sur ordinateur), le titre et ses
// lignes au centre (annoncés, role="status"), les actions en bas.
// Sert à « Candidature envoyée. », « Entretien décroché », à la réponse négative et à l'au revoir.
// Les actions viennent de la vue (`#actions`) : `sent-screen-primary` pour le bouton plein, `sent-screen-next`
// pour le lien dessous.
// `hand` : la fin du titre, manuscrite sur ordinateur (maquette du 8 novembre, CandidatureEnvoyeeOrdinateur) ;
// les actions se rangent côte à côte sous le texte.
// `icon` à la place de `scene` : une icône sobre, pour une réponse négative (§15 : jamais les personnages sur un
// refus).
// `image` : une illustration propre à l'écran, à la place de la scène (« C’est trié ! », lot du 11 novembre au soir) ;
// `handPhone` : la fin manuscrite aussi sur téléphone (maquette FinDuTri).
withDefaults(defineProps<{ scene?: Scene; icon?: IconName; image?: string; title: string; hand?: string; handPhone?: boolean; line?: string }>(), {
  scene: undefined,
  icon: undefined,
  image: undefined,
  hand: "",
  handPhone: false,
  line: "",
});
</script>

<template>
  <section class="sent-screen">
    <header class="sent-screen-brand">
      <BrandMark :size="30" />
      <span>jobA1</span>
    </header>
    <div
      class="sent-screen-body"
      role="status"
    >
      <TroupeScene
        v-if="scene"
        :scene="scene"
        full
      />
      <img
        v-else-if="image"
        class="sent-screen-image"
        :src="image"
        alt=""
      >
      <span
        v-else-if="icon"
        class="sent-screen-icon"
        aria-hidden="true"
        data-test="moment-icon"
      ><AppIcon :name="icon" /></span>
      <h1 class="sent-screen-title">
        {{ title }}<template v-if="hand">
          {{ " " }}<span :class="['sent-screen-hand', { 'sent-screen-hand-phone': handPhone }]">{{ hand }}</span>
        </template>
      </h1>
      <p v-if="line">
        {{ line }}
      </p>
      <slot />
    </div>
    <div class="sent-screen-actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
/* Valeurs de la maquette CandidatureEnvoyee (390 px), ramenées aux échelles. */
.sent-screen { display: flex; flex-direction: column; min-height: 100dvh; max-width: 30rem; margin-inline: auto; box-sizing: border-box; color: var(--text); }
.sent-screen-brand { flex: none; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-5) var(--space-5) 0; font-size: var(--font-section); font-weight: var(--weight-bold); }
.sent-screen-body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); padding: 0 var(--space-6); text-align: center; }
.sent-screen-icon { --moment-icon: 6rem; --moment-glyph: 2.5rem; display: grid; place-items: center; width: var(--moment-icon); height: var(--moment-icon); border-radius: 50%; background: var(--surface-muted); color: var(--text-secondary); }
.sent-screen-icon :deep(svg) { width: var(--moment-glyph); height: var(--moment-glyph); }
.sent-screen-image { --moment-image: 290px; display: block; flex: none; width: min(100%, var(--moment-image)); height: auto; }
.sent-screen-hand-phone { font-family: var(--font-hand); font-weight: var(--weight-regular); font-size: 1.45em; line-height: 0; color: var(--primary-graphic); }
.sent-screen-title { margin: var(--space-2) 0 0; font-size: var(--font-figure); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.3px; }
.sent-screen-body :slotted(p) { margin: 0; max-width: 310px; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.sent-screen-body :slotted(p strong) { color: var(--text); }
.sent-screen-body :slotted(.sent-screen-small) { margin-top: var(--space-1); font-size: var(--font-small); }
.sent-screen-actions { flex: none; display: grid; gap: var(--space-2); padding: var(--space-4) var(--space-5) var(--space-8); }
.sent-screen-actions :slotted(.sent-screen-primary) { justify-content: center; width: 100%; min-height: var(--btn-primary); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.sent-screen-actions :slotted(.sent-screen-next) { display: flex; font-size: var(--font-body); align-items: center; justify-content: center; min-height: var(--btn-tertiary); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.sent-screen-actions :slotted(.sent-screen-cancel) { justify-self: center; min-height: var(--target-min); color: var(--text-secondary); font-weight: var(--weight-regular); }
@media (min-width: 821px) { .sent-screen { min-height: 0; padding-block: var(--space-8); } .sent-screen-brand { display: none; } }
/* Ordinateur (maquette du 8 novembre, CandidatureEnvoyeeOrdinateur) : 880 px, la scène de 471, le titre de 34/42
   en 800 et sa fin manuscrite, la phrase de 18/28 ; les deux boutons de 44 côte à côte, le contour puis le plein. */
@media (min-width: 1024px) {
  .sent-screen { --sent-34: 34px; --sent-42: 42px; --sent-18: 18px; --sent-28: 28px; --sent-10: 10px; max-width: 880px; padding-top: var(--space-6); }
  .sent-screen-body { flex: 0 0 auto; gap: 0; padding: 0; }
  .sent-screen-image { --moment-image: 440px; }
  .sent-screen-title { margin: var(--space-6) 0 0; font-size: var(--sent-34); line-height: var(--sent-42); font-weight: var(--weight-heavy); letter-spacing: normal; }
  .sent-screen-hand { font-family: var(--font-hand); font-weight: var(--weight-regular); font-size: 1.45em; line-height: 0; color: var(--primary-graphic); }
  .sent-screen-body :slotted(p) { max-width: 560px; margin: var(--space-3) 0 0; font-size: var(--sent-18); line-height: var(--sent-28); color: var(--text-secondary); }
  .sent-screen-body :slotted(.sent-screen-small) { margin-top: 0; font-size: var(--sent-18); }
  .sent-screen-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: var(--sent-10); padding: var(--sent-28) 0 var(--space-12); }
  .sent-screen-actions :slotted(.sent-screen-primary) { order: 1; width: auto; min-height: var(--target-min); padding: 0 var(--space-4); border: 1.5px solid var(--field-border); background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-semibold); }
  .sent-screen-actions :slotted(.goal-reached-home) { order: 2; min-height: var(--target-min); padding: 0 var(--space-5); border-radius: var(--radius-pill); background: var(--primary); color: var(--on-primary); font-size: var(--font-label); }
  .sent-screen-actions :slotted(.sent-screen-cancel) { order: 3; flex-basis: 100%; }
}
</style>
