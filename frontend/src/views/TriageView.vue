<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import DailyPick from "../components/DailyPick.vue";
import FaceState from "../components/FaceState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PageHero from "../components/PageHero.vue";
import { markTriageDone, useDailyDose } from "../composables/useDailyDose";
import { plural } from "../format";

// L'écran de tri (1.6.50, revue 1.6.46, planche « Tri des offres du jour ») : un deuxième niveau,
// ouvert par « Commencer le tri » (Aujourd'hui, Offres). Une offre à la fois, en pile au centre ;
// « Écarter » et « Garder » côte à côte, « Annuler » pendant 6 secondes ; au doigt, balayer à droite
// garde, à gauche écarte. Pas de barre d'onglets : on revient par « ← Aujourd'hui ».
const router = useRouter();
const { dose, restDay, loaded, load } = useDailyDose();
const pick = ref<InstanceType<typeof DailyPick> | null>(null);

// Ce qu'il reste à trier, pour la phrase du haut : il diminue à chaque offre gardée ou écartée.
const remaining = computed(() => pick.value?.remaining ?? dose.value.length);
const position = computed(() => pick.value?.position ?? "");
const sentence = computed(() => (remaining.value ? `${plural(remaining.value, "offre", "offres")}` : ""));

// La pile vidée : Aujourd'hui passe à « Tri terminé · À demain » (1.6.51).
watch(
  () => !!pick.value && pick.value.remaining === 0,
  (done) => {
    if (done) markTriageDone();
  },
);

function showPreparing(): void {
  void router.push({ path: "/candidatures/offres", query: { statut: "in_progress" } });
}

onMounted(load);
</script>

<template>
  <PageHero title="Offres du jour">
    <template #back>
      <RouterLink
        :to="{ name: 'today' }"
        class="back-link"
        data-test="triage-back"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Aujourd'hui</span>
      </RouterLink>
    </template>
  </PageHero>
  <section class="band">
    <div class="container triage-page">
      <LoadingBlocks
        v-if="!loaded"
        :heights="['2.5rem', '14rem']"
      />
      <FaceState
        v-else-if="restDay || !dose.length"
        :title="restDay ? 'Jour de repos' : 'Rien à trier'"
        data-test="triage-empty"
      >
        <p>{{ restDay ? "Pas de tri aujourd'hui." : "Les nouvelles offres arrivent chaque matin." }}</p>
        <div class="face-state-actions">
          <RouterLink
            :to="{ name: 'today' }"
            class="button-link"
          >
            Revenir à Aujourd'hui
          </RouterLink>
        </div>
      </FaceState>
      <template v-else>
        <p
          v-if="sentence"
          class="offers-sentence"
          data-test="triage-sentence"
        >
          <strong>{{ sentence }}</strong> à trier.
        </p>
        <div class="triage-pile">
          <p
            v-if="position"
            class="triage-position muted"
            data-test="triage-position"
          >
            {{ position }}
          </p>
          <DailyPick
            ref="pick"
            :offers="dose"
            @show-preparing="showPreparing"
          />
          <RouterLink
            v-if="!remaining"
            :to="{ name: 'today' }"
            class="button-link primary-link triage-done"
            data-test="triage-done"
          >
            Revenir à Aujourd'hui
          </RouterLink>
        </div>
      </template>
    </div>
  </section>
</template>
