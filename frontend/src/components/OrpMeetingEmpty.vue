<script setup lang="ts">
// Aucun rendez-vous à venir sur téléphone (prompt du 10 novembre au soir, PR 28 ; maquette RendezVous, états `vide` et
// `addSheet`) : une carte d'une ligne, « Aucun rendez-vous à venir · jobA1 prépare ta feuille la veille. », et le bouton
// teinté « Ajouter ». Il ouvre la fenêtre « Nouveau rendez-vous » de la page (PR 41 : une entreprise ou l'ORP). Plus de
// personnage ici (décision de Kevin du 11 novembre).
const emit = defineEmits<{ add: [] }>();
</script>

<template>
  <section
    class="rdv-empty"
    aria-labelledby="rdv-empty-title"
    data-test="meeting-empty"
  >
    <div class="rdv-empty-card">
      <div class="rdv-empty-text">
        <h2 id="rdv-empty-title">
          Aucun rendez-vous à venir
        </h2>
        <p>jobA1 prépare ta feuille la veille.</p>
      </div>
      <button
        type="button"
        class="rdv-empty-add"
        aria-haspopup="dialog"
        data-test="meeting-add"
        @click="emit('add')"
      >
        Ajouter
      </button>
    </div>
    <p class="rdv-empty-note">
      Un entretien d’embauche ? Ajoute-le depuis la candidature concernée, dans Envoyées.
    </p>
  </section>
</template>

<style>
/* Maquette : la carte blanche, trait de 1,5 px, rayon 18, 16 / 18,5 dedans ; le titre 17/22 gras, la phrase 14/20 à
   2 px (posée sur la grille : 4) ; « Ajouter » teinté de 44 px ; 16 px avant la note (14 dans la maquette). */
.rdv-empty { --empty-17: 17px; --empty-pad-x: 18.5px; --empty-add-pad: 18px; --empty-lh-title: 22px; --empty-lh-text: 20px; display: flex; flex-direction: column; gap: var(--space-4); }
.rdv-empty-card { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4) var(--empty-pad-x); background: var(--surface); border: var(--action-line) solid var(--card-line); border-radius: var(--radius-card); }
.rdv-empty-text { flex: 1; min-width: 0; }
.rdv-empty-text h2 { margin: 0; font-size: var(--empty-17); line-height: var(--empty-lh-title); font-weight: var(--weight-bold); }
.rdv-empty-text p { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--empty-lh-text); color: var(--text-secondary); }
.rdv-empty-add { flex: none; height: var(--target-min); min-height: var(--target-min); padding: 0 var(--empty-add-pad); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.rdv-empty-note { margin: 0 var(--space-1); font-size: var(--font-small); line-height: var(--empty-lh-text); color: var(--text-secondary); }
</style>
