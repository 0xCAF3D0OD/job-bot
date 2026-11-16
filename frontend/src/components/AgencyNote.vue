<script setup lang="ts">
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";

// La ligne « Agence de placement » de la fiche (section 35 du 16.11, planches OffreAgence et
// CandidaturesOrdinateurAgence) : sous l'entreprise, après un trait, le rond de 32 px aux deux flèches, le titre en gras
// et ce qu'il faut faire ; « Ce n'est pas une agence » à droite sur ordinateur, dessous sur téléphone.
// Marge, trait et écart de 12 px au lieu de 14 et 10 sur la planche : la grille de 4 (audit-grille). Agence connue par
// son nom : « Agence de placement » ; annonce « pour notre client » seulement : « Probablement une agence de
// placement ». Une candidature envoyée ces 90 derniers jours à un poste proche est dite dans la même ligne.
defineProps<{
  kind: "known" | "probable";
  company: string | null;
  duplicate?: { title: string; company: string; sent_at: string } | null;
  busy?: boolean;
}>();
defineEmits<{ correct: [] }>();
</script>

<template>
  <div
    class="agency-note"
    data-test="agency-note"
  >
    <span
      class="agency-dot"
      aria-hidden="true"
    ><AppIcon name="agency" /></span>
    <p>
      <b>{{ kind === "known" ? "Agence de placement" : "Probablement une agence de placement" }}</b>{{ company ?? "L’agence" }} recrute pour un client dont le nom n’est pas donné. Demande-le avant d’envoyer : tu évites de postuler deux fois au même poste.<span
        v-if="duplicate"
        data-test="agency-duplicate"
      > Tu as déjà postulé {{ dateInSentence(duplicate.sent_at) }} à un poste proche : {{ duplicate.title }} chez {{ duplicate.company }}.</span>
    </p>
    <button
      type="button"
      class="link agency-fix"
      :disabled="busy"
      data-test="not-agency"
      @click="$emit('correct')"
    >
      Ce n’est pas une agence
    </button>
  </div>
</template>

<style>
.agency-note { display: grid; grid-template-columns: auto 1fr auto; align-items: start; gap: 0 var(--space-3); margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--line); font-size: var(--font-small); line-height: var(--leading-normal); color: var(--text-lead); }
.agency-note p { margin: 0; }
.agency-note b { display: block; font-size: var(--font-label); color: var(--text); }
.agency-dot { display: flex; align-items: center; justify-content: center; width: var(--space-8); height: var(--space-8); border-radius: 50%; background: var(--agency-bg); color: var(--agency-text); }
.agency-dot > .icon { width: 18px; height: 18px; stroke-width: 2.2; }
.agency-note .agency-fix { min-height: var(--space-8); font-size: var(--font-small); font-weight: var(--weight-bold); white-space: nowrap; }
@media (max-width: 820px) {
  .agency-note .agency-fix { grid-column: 2; justify-self: start; min-height: 44px; font-size: var(--font-label); }
}
</style>
