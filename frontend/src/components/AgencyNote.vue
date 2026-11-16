<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// La ligne « Agence de placement » de la fiche (section 35 du 16.11, planches OffreAgence et
// CandidaturesOrdinateurAgence) : sous l'entreprise, après un trait, le rond de 32 px aux deux flèches, le titre en gras
// et ce qu'il faut faire. Le lien « Ce n'est pas une agence » attend l'enregistrement de la correction (détection).
defineProps<{ company: string | null }>();
</script>

<template>
  <p
    class="agency-note"
    data-test="agency-note"
  >
    <span class="agency-dot"><AppIcon name="agency" /></span>
    <span><b>Agence de placement</b>{{ company ?? "L’agence" }} recrute pour un client dont le nom n’est pas donné. Demande-le avant d’envoyer : tu évites de postuler deux fois au même poste.</span>
  </p>
</template>

<style>
.agency-note { --agency-gap: 10px; --agency-top: 14px; display: flex; align-items: flex-start; gap: var(--agency-gap); margin: var(--agency-top) 0 0; padding-top: var(--agency-top); border-top: 1px solid var(--line); font-size: var(--font-small); line-height: 1.25rem; color: var(--text-lead); }
.agency-note b { display: block; font-size: var(--font-label); color: var(--text); }
.agency-dot { flex: none; display: flex; align-items: center; justify-content: center; width: var(--space-8); height: var(--space-8); border-radius: 50%; background: var(--agency-bg); color: var(--agency-text); }
.agency-dot > .icon { width: 18px; height: 18px; stroke-width: 2.2; }
</style>
