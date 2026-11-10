<script setup lang="ts">
import type { components } from "../api/schema";
import TroupeScene from "./TroupeScene.vue";
import OrpMeetingForm from "./OrpMeetingForm.vue";

// Aucun rendez-vous ORP prévu (maquette RendezVousPreparer, §15 du 9 novembre) : le « 1 » seul, 72 px de haut, posé
// en bas de l'en-tête, à côté du titre ; le formulaire compact ; les entretiens s'ajoutent depuis leur candidature.
type Page = components["schemas"]["MeetingPage"];
const emit = defineEmits<{ saved: [page: Page] }>();
</script>

<template>
  <section
    class="rdv-empty"
    aria-labelledby="rdv-empty-title"
    data-test="meeting-empty"
  >
    <div class="rdv-empty-head">
      <TroupeScene
        scene="un"
        :height="72"
        class="rdv-empty-person"
        data-test="meeting-person"
      />
      <div>
        <h2 id="rdv-empty-title">
          Aucun rendez-vous à venir
        </h2>
        <p>Ajoute ton prochain rendez-vous ORP : jobA1 prépare ta feuille la veille.</p>
      </div>
    </div>
    <OrpMeetingForm @saved="emit('saved', $event)" />
    <p class="rdv-empty-note">
      Un entretien d’embauche ? Ajoute-le depuis la candidature concernée, dans Envoyées.
    </p>
  </section>
</template>

<style>
/* Maquette : le « 1 » de 72 px de haut, le titre en 20 très gras, la phrase en 15 ; écart 14 entre les blocs, posé sur
   la grille de 4 : 16 (prompt du 10 novembre, PR 16, audit-grille.js). */
.rdv-empty { --empty-15: 15px; --empty-20: 20px; --empty-lh-title: 1.25; --empty-lh-text: 1.4; --empty-lh-note: 1.43; display: flex; flex-direction: column; gap: var(--space-4); }
.rdv-empty-head { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-1) var(--space-1) 0; }
.rdv-empty-head h2 { margin: 0; font-size: var(--empty-20); font-weight: var(--weight-heavy); line-height: var(--empty-lh-title); }
.rdv-empty-head p { margin: var(--space-1) 0 0; font-size: var(--empty-15); line-height: var(--empty-lh-text); color: var(--text-tertiary); }
.rdv-empty-person { align-self: flex-end; }
.rdv-empty-note { margin: 0 var(--space-1); font-size: var(--font-small); line-height: var(--empty-lh-note); color: var(--text-secondary); }
</style>
