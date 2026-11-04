<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type OrpMonth, type Today } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import OrpGoalCard from "../components/OrpGoalCard.vue";
import OrpSearchRows from "../components/OrpSearchRows.vue";
import OrpSheet from "../components/OrpSheet.vue";
import RhythmCard from "../components/RhythmCard.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { isNetworkError } from "../network";

// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04). De haut en bas :
// l'objectif du mois (le cercle liquide), l'export, les trois dernières recherches, le lien vers le
// Suivi ORP du mois, puis la carte Rythme (téléphone, A5).
const orp = ref<OrpMonth | null>(null);
const rhythm = ref<Today["rhythm"] | null>(null);
const error = ref(false);
const offline = ref(false);
const { phone } = usePhone();
usePageReady("bilan-orp", () => !!orp.value || error.value);

const LAST = 3;
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);

async function load(): Promise<void> {
  error.value = false;
  offline.value = false;
  if (phone.value) {
    void api
      .GET("/api/today")
      .then(({ data }) => (rhythm.value = data?.rhythm ?? null))
      .catch(() => undefined);
  }
  try {
    const { data } = await api.GET("/api/orp");
    if (!data) throw new Error();
    orp.value = data;
  } catch (cause) {
    error.value = true;
    offline.value = isNetworkError(cause);
  }
}
onMounted(() => void load());
</script>

<template>
  <section class="band">
    <div class="container bilan-orp">
      <NetworkError
        v-if="error && offline"
        @retry="load()"
      />
      <p
        v-else-if="error"
        class="notice error"
        role="alert"
      >
        Le suivi ORP n'a pas pu être chargé.
      </p>
      <LoadingBlocks
        v-else-if="!orp"
        :heights="['10rem', '3.5rem', '14rem']"
      />
      <template v-else>
        <OrpGoalCard :data="orp" />
        <button
          type="button"
          class="secondary orp-export"
          data-test="orp-export"
          @click="sheet?.printPdf()"
        >
          <AppIcon name="download" />Exporter le formulaire (PDF)
        </button>
        <OrpSheet
          ref="sheet"
          :data="orp"
          @reload="load"
        />

        <section
          class="orp-last"
          aria-labelledby="orp-last-title"
        >
          <h2 id="orp-last-title">
            <span>Dernières recherches</span>
            <span>{{ orp.count }} ce mois</span>
          </h2>
          <OrpSearchRows
            :rows="orp.rows"
            :limit="LAST"
          />
        </section>

        <RouterLink
          :to="{ path: '/bilan/orp', query: { mois: orp.month } }"
          class="orp-all"
          data-test="orp-all"
        >
          Voir tout le mois et les preuves
        </RouterLink>

        <RhythmCard
          v-if="phone && rhythm"
          :week="rhythm"
        />
      </template>
    </div>
  </section>
</template>
