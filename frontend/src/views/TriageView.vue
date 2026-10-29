<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import DailyPick from "../components/DailyPick.vue";
import FaceState from "../components/FaceState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PageHero from "../components/PageHero.vue";
import StepProgress from "../components/StepProgress.vue";
import { markTriageDone, useDailyDose } from "../composables/useDailyDose";

// L'écran de tri (planche « Tri et panneau de commande ») : un deuxième niveau, ouvert par
// « Commencer le tri » (Aujourd'hui, Offres). Une colonne : la progression « 1 sur 5 » en haut, une
// offre à la fois, « Écarter » et « Garder » de même largeur (dans le panneau sur téléphone),
// « Annuler » pendant 6 secondes. On revient par « ← Aujourd'hui ».
const router = useRouter();
const { dose, restDay, loaded, load } = useDailyDose();
const pick = ref<InstanceType<typeof DailyPick> | null>(null);

// La place dans la pile : « 1 sur 5 » ; plus rien une fois le tri fini.
const position = computed(() => pick.value?.position ?? 1);
const total = computed(() => pick.value?.total ?? dose.value.length);

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
  <PageHero
    title="Offres du jour"
    class="triage-head"
  >
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
        <div class="triage-pile">
          <StepProgress
            v-if="position"
            :current="position"
            :total="total"
          />
          <DailyPick
            ref="pick"
            :offers="dose"
            @show-preparing="showPreparing"
          />
        </div>
      </template>
    </div>
  </section>
</template>
