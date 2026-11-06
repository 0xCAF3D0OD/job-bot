<script setup lang="ts">
import type { Pose } from "../personnage";
import BrandMark from "./BrandMark.vue";
import Illustration from "./Illustration.vue";

// Un moment en écran plein (maquette CandidatureEnvoyee du 6.11, docs/141 §3) : la marque en haut sur
// téléphone, le personnage, le titre et ses lignes au centre (annoncés, role="status"), les actions en bas.
// Sert à « Candidature envoyée. », « Entretien décroché », à la réponse négative et à l'au revoir.
// Les actions viennent de la vue (`#actions`) : `sent-screen-primary` pour le bouton plein, `sent-screen-next`
// pour le lien dessous.
withDefaults(defineProps<{ pose: Pose; title: string; line?: string; height?: number }>(), { line: "", height: 280 });
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
      <Illustration
        :pose="pose"
        :height="height"
        full
      />
      <h1 class="sent-screen-title">
        {{ title }}
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
.sent-screen-title { margin: var(--space-2) 0 0; font-size: var(--font-figure); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.3px; }
.sent-screen-body :slotted(p) { margin: 0; max-width: 310px; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.sent-screen-body :slotted(p strong) { color: var(--text); }
.sent-screen-body :slotted(.sent-screen-small) { margin-top: var(--space-1); font-size: var(--font-small); }
.sent-screen-actions { flex: none; display: grid; gap: var(--space-2); padding: var(--space-4) var(--space-5) var(--space-8); }
.sent-screen-actions :slotted(.sent-screen-primary) { justify-content: center; width: 100%; min-height: var(--btn-primary); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.sent-screen-actions :slotted(.sent-screen-next) { display: flex; font-size: var(--font-body); align-items: center; justify-content: center; min-height: var(--btn-tertiary); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.sent-screen-actions :slotted(.sent-screen-cancel) { justify-self: center; min-height: var(--target-min); color: var(--text-secondary); font-weight: var(--weight-regular); }
@media (min-width: 821px) { .sent-screen { min-height: 0; padding-block: var(--space-8); } .sent-screen-brand { display: none; } }
</style>
