<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import { useArrowKeys } from "../composables/useArrowKeys";
import { useNarrow } from "../composables/usePhone";
import { offerUndo } from "../composables/useUndo";
import { plural, rateText, remoteText } from "../format";
import { whyLine } from "../whyLine";
import ActionBar from "./ActionBar.vue";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import FaceState from "./FaceState.vue";
import KeyHints from "./KeyHints.vue";
import ScoreWord from "./ScoreWord.vue";

// Les offres du jour, une à la fois (planche « Tri et panneau de commande ») : la carte comme la
// fiche (note et pourquoi sur une ligne, 2 ou 3 étiquettes, « Voir l'annonce »), puis « Écarter » et
// « Garder » de même largeur, dans le panneau de commande sur téléphone. ← écarte, → garde ;
// « Annuler » pendant 6 secondes. Pas de balayage (décision de Kevin). Toucher le titre ouvre la fiche.
const props = defineProps<{ offers: Offer[] }>();
const emit = defineEmits<{ changed: []; showPreparing: [] }>();

type Choice = "keep" | "dismiss";
const index = ref(0);
const kept = ref(0);
const dismissed = ref(0);
// La liste du jour ne change pas pendant le tri (un rechargement d'Aujourd'hui ne la refait pas).
const queue = ref<Offer[]>([...props.offers]);
watch(
  () => props.offers.map((o) => o.id).join(","),
  () => {
    if (index.value === 0) queue.value = [...props.offers];
  },
);
const current = computed(() => queue.value[index.value] ?? null);
const gaps = computed(() =>
  (current.value?.keywords_asks ?? []).filter((a) => a.covered === false).map((a) => a.text).slice(0, 2),
);
// Les étiquettes de la fiche : taux, contrat, télétravail ; trois au plus.
const tags = computed(() => {
  const o = current.value;
  if (!o) return [];
  return [rateText(o.rate_min, o.rate_max).replace("–", " à "), o.employment_type ?? "", remoteText(o)?.replace(" j", " jours") ?? ""]
    .filter(Boolean)
    .slice(0, 3);
});
const adUrl = computed(() => current.value?.links[0]?.url ?? null);
const direction = ref<Choice>("keep");
// Sous 600 px, on lit en haut et on agit en bas : la note, son pourquoi et l'annonce passent dans le
// panneau, la carte ne garde que ce qu'on lit (planche, B1).
const { phone: narrow } = useNarrow();

function decide(choice: Choice): void {
  const offer = current.value;
  if (!offer) return;
  direction.value = choice;
  index.value += 1;
  if (choice === "keep") kept.value += 1;
  else dismissed.value += 1;
  void offerUndo({
    message: choice === "keep" ? `Gardée : ${offer.title}.` : `Écartée : ${offer.title}.`,
    commit: async (keepalive) => {
      const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
        params: { path: { offer_id: offer.id } },
        body: { status: choice === "keep" ? "preparing" : "ignored" },
        keepalive,
      });
      if (response.ok) emit("changed");
      return response.ok;
    },
    restore: () => {
      index.value = Math.max(0, index.value - 1);
      if (choice === "keep") kept.value -= 1;
      else dismissed.value -= 1;
    },
  });
}
useArrowKeys({ left: () => decide("dismiss"), right: () => decide("keep") });

// La place dans la pile, pour la progression de l'écran (« 1 sur 5 ») ; rien une fois le tri fini.
const position = computed(() => (current.value ? index.value + 1 : 0));
const total = computed(() => queue.value.length);
const remaining = computed(() => Math.max(0, queue.value.length - index.value));
defineExpose({ position, total, remaining });

const summary = computed(() =>
  [
    kept.value ? `${kept.value} ${kept.value === 1 ? "gardée" : "gardées"}` : "",
    dismissed.value ? `${dismissed.value} ${dismissed.value === 1 ? "écartée" : "écartées"}` : "",
  ]
    .filter(Boolean)
    .join(", "),
);
const prepareLabel = computed(() => `Préparer ${kept.value === 1 ? "l'offre gardée" : `les ${plural(kept.value, "offre gardée", "offres gardées")}`}`);
</script>

<template>
  <div
    class="daily-pick"
    data-test="daily-pick"
  >
    <Transition
      :name="`pick-${direction}`"
      mode="out-in"
    >
      <div
        v-if="current"
        :key="current.id"
        class="pick-step"
      >
        <article
          class="pick-card"
          data-test="pick-card"
        >
          <header class="pick-head">
            <CompanyLogo :offer="current" />
            <div class="pick-title">
              <RouterLink
                :to="{ path: '/candidatures/offres', query: { offre: current.id } }"
                data-test="pick-open"
              >
                <strong>{{ current.title }}</strong>
              </RouterLink>
              <span class="muted">{{ [current.company || "Entreprise non indiquée", current.location].filter(Boolean).join(" · ") }}</span>
            </div>
          </header>
          <template v-if="!narrow">
            <div
              class="pick-score"
              data-test="pick-score"
            >
              <ScoreWord :score="current.score ?? null" />
              <p
                v-if="current.why"
                class="pick-why"
              >
                {{ whyLine(current.why) }}
              </p>
              <p
                v-else-if="gaps.length"
                class="pick-why muted"
              >
                Il te manque : {{ gaps.join(", ") }}
              </p>
            </div>
          </template>
          <ul
            v-if="tags.length"
            class="pick-tags"
            data-test="pick-tags"
          >
            <li
              v-for="tag in tags"
              :key="tag"
            >
              {{ tag }}
            </li>
          </ul>
          <template v-if="!narrow">
            <a
              v-if="adUrl"
              :href="adUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="pick-ad"
              data-test="pick-ad"
            ><span class="with-icon">Voir l'annonce<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
          </template>
        </article>
        <ActionBar>
          <template v-if="narrow">
            <div
              class="pick-score"
              data-test="pick-score"
            >
              <ScoreWord :score="current.score ?? null" />
              <p
                v-if="current.why"
                class="pick-why"
              >
                {{ whyLine(current.why) }}
              </p>
              <p
                v-else-if="gaps.length"
                class="pick-why muted"
              >
                Il te manque : {{ gaps.join(", ") }}
              </p>
            </div>
            <a
              v-if="adUrl"
              :href="adUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="pick-ad"
              data-test="pick-ad"
            ><span class="with-icon">Voir l'annonce<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
          </template>
          <div class="action-bar-row">
            <button
              type="button"
              class="secondary"
              aria-keyshortcuts="ArrowLeft"
              data-test="pick-dismiss"
              @click="decide('dismiss')"
            >
              <span class="with-icon"><AppIcon name="x-circle" />Écarter</span>
            </button>
            <button
              type="button"
              class="primary"
              aria-keyshortcuts="ArrowRight"
              data-test="pick-keep"
              @click="decide('keep')"
            >
              <span class="with-icon"><AppIcon name="done" />Garder</span>
            </button>
          </div>
        </ActionBar>
        <KeyHints
          v-if="!narrow"
          left="Écarter"
          right="Garder"
        />
      </div>
      <FaceState
        v-else
        title="Tri du jour terminé"
        illustration="reussite"
        class="pick-done"
        data-test="pick-done"
      >
        <p v-if="summary">
          {{ summary }}.
        </p>
        <div class="face-state-actions">
          <button
            v-if="kept"
            type="button"
            class="secondary"
            data-test="pick-preparing"
            @click="emit('showPreparing')"
          >
            {{ prepareLabel }}
          </button>
          <RouterLink
            v-else
            :to="{ name: 'today' }"
            class="button-link"
            data-test="pick-today"
          >
            Revenir à Aujourd'hui
          </RouterLink>
        </div>
      </FaceState>
    </Transition>
  </div>
</template>
