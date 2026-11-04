<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type OrpMonth, type Today } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import LiquidCircle from "../components/LiquidCircle.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import OrpSheet from "../components/OrpSheet.vue";
import RhythmCard from "../components/RhythmCard.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { plural } from "../format";
import { isNetworkError } from "../network";

// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04). De haut en bas :
// l'objectif du mois (le cercle liquide), l'export, les trois dernières recherches, le lien vers tout
// le mois, puis la carte Rythme (téléphone, A5). Sans objectif saisi, une carte invite à l'indiquer
// au lieu d'un « 0 sur 0 ». « Recherches » est le mot du formulaire de l'ORP (B5).
const orp = ref<OrpMonth | null>(null);
const rhythm = ref<Today["rhythm"] | null>(null);
const error = ref(false);
const offline = ref(false);
const { phone } = usePhone();
usePageReady("bilan-orp", () => !!orp.value || error.value);

const LAST = 3;
const SHORT_MONTH = new Intl.DateTimeFormat("fr-CH", { month: "short" });
const LONG_DAY = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

// « 31 octobre » : la fin du mois suivi.
const deadline = computed(() => {
  if (!orp.value) return "";
  const [year, month] = orp.value.month.split("-").map(Number);
  return LONG_DAY.format(new Date(year!, month!, 0));
});
const left = computed(() => (orp.value?.target ? orp.value.target - orp.value.count : 0));
const title = computed(() => (left.value > 0 ? `${plural(left.value, "recherche", "recherches")} à faire` : "Objectif du mois atteint"));

// Les lignes du formulaire ont leur date en « 28.10.2026 » : les plus récentes d'abord.
const last = computed(() =>
  (orp.value?.rows ?? [])
    .map((row) => {
      const [day, month, year] = row.date.split(".").map(Number);
      const date = new Date(year!, month! - 1, day!);
      return { ...row, day, month: SHORT_MONTH.format(date), time: date.getTime() };
    })
    .sort((a, b) => b.time - a.time)
    .slice(0, LAST),
);
const how = (method: string) => method.charAt(0).toUpperCase() + method.slice(1);

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
        <section
          v-if="orp.target"
          class="orp-goal"
          data-test="orp-goal"
        >
          <LiquidCircle
            :count="orp.count"
            :target="orp.target"
            :size="112"
          />
          <div>
            <h2>{{ title }}</h2>
            <p>Objectif fixé avec l'ORP. Échéance le {{ deadline }}.</p>
          </div>
        </section>
        <section
          v-else
          class="orp-goal"
          data-test="orp-goal-missing"
        >
          <div>
            <h2>Indique ton objectif ORP</h2>
            <p>Le nombre de recherches que l'ORP te demande chaque mois. Le cercle se remplit à chaque candidature.</p>
            <RouterLink
              :to="{ path: '/reglages', query: { rubrique: 'recherche' } }"
              class="button-link"
            >
              Indiquer mon objectif
            </RouterLink>
          </div>
        </section>

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
          <ul
            v-if="last.length"
            data-test="orp-last"
          >
            <li
              v-for="row in last"
              :key="row.application_id"
            >
              <span class="orp-day"><strong>{{ row.day }}</strong>{{ row.month }}</span>
              <span class="orp-what"><strong>{{ row.company }}</strong>{{ row.job_title }} · {{ how(row.method) }}</span>
              <span
                v-if="row.missing.length"
                class="status-pill expired"
              ><AppIcon name="alert" />À joindre</span>
              <span
                v-else
                class="status-pill applied"
              ><AppIcon name="check" />Preuve</span>
            </li>
          </ul>
          <p
            v-else
            class="orp-none"
          >
            Aucune recherche ce mois-ci.
          </p>
        </section>

        <RouterLink
          :to="{ path: '/candidatures/suivi', query: { mois: orp.month } }"
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
