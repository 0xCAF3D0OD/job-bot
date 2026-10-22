<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Offer } from "../api/client";
import { offerUndo } from "../composables/useUndo";
import AppIcon from "./AppIcon.vue";
import CompanyLogo from "./CompanyLogo.vue";
import FaceMark from "./FaceMark.vue";
import ScoreWord from "./ScoreWord.vue";

// Les offres du jour, une à la fois (docs/124 §D) : « Garder » (l'offre passe en « À préparer »)
// ou « Écarter » (« Ignorée »), puis la suivante ; « Annuler » pendant 6 secondes (docs/108).
// La phrase « pourquoi » dit déjà ce qui manque : « Il te manque » seulement sans elle.
// Sur téléphone, balayer à droite ou à gauche fait la même chose, en plus des boutons. Toucher
// le titre ouvre la fiche.
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
const direction = ref<Choice>("keep");

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

// Le balayage, au doigt seulement : 80 px suffisent ; la carte suit le doigt.
const drag = ref(0);
let start: number | null = null;
function down(event: PointerEvent): void {
  if (event.pointerType !== "touch") return;
  start = event.clientX;
}
function move(event: PointerEvent): void {
  if (start !== null) drag.value = event.clientX - start;
}
function up(): void {
  if (start === null) return;
  const dx = drag.value;
  start = null;
  drag.value = 0;
  if (dx > 80) decide("keep");
  else if (dx < -80) decide("dismiss");
}

const summary = computed(() =>
  [
    kept.value ? `${kept.value} ${kept.value === 1 ? "gardée" : "gardées"}` : "",
    dismissed.value ? `${dismissed.value} ${dismissed.value === 1 ? "écartée" : "écartées"}` : "",
  ]
    .filter(Boolean)
    .join(", "),
);
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
      <article
        v-if="current"
        :key="current.id"
        class="pick-card"
        :style="drag ? { transform: `translateX(${drag}px) rotate(${drag / 40}deg)` } : undefined"
        data-test="pick-card"
        @pointerdown="down"
        @pointermove="move"
        @pointerup="up"
        @pointercancel="up"
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
            <span class="muted meta-line">
              <span><AppIcon name="building" /><span class="visually-hidden">Entreprise : </span>{{ current.company || "Entreprise non indiquée" }}</span>
              <span v-if="current.location"><AppIcon name="pin" /><span class="visually-hidden">Lieu : </span>{{ current.location }}</span>
            </span>
          </div>
          <span
            class="pick-count muted"
            data-test="pick-count"
          >{{ index + 1 }} sur {{ queue.length }}</span>
        </header>
        <div class="pick-score">
          <ScoreWord :score="current.score ?? null" />
          <p
            v-if="current.why"
            class="pick-why"
          >
            {{ current.why }}
          </p>
        </div>
        <p
          v-if="gaps.length && !current.why"
          class="pick-gaps muted"
        >
          Il te manque : {{ gaps.join(", ") }}
        </p>
        <div class="pick-actions">
          <button
            type="button"
            class="secondary"
            data-test="pick-dismiss"
            @click="decide('dismiss')"
          >
            <span class="with-icon"><AppIcon name="x-circle" />Écarter</span>
          </button>
          <button
            type="button"
            class="primary"
            data-test="pick-keep"
            @click="decide('keep')"
          >
            <span class="with-icon"><AppIcon name="done" />Garder</span>
          </button>
        </div>
      </article>
      <div
        v-else
        class="pick-done"
        data-test="pick-done"
      >
        <p class="pick-done-line">
          <FaceMark mood="ravi" />
          <span><strong>Tri du jour terminé.</strong>{{ summary ? ` ${summary}.` : "" }}</span>
        </p>
        <button
          v-if="kept"
          type="button"
          class="link"
          data-test="pick-preparing"
          @click="emit('showPreparing')"
        >
          Voir les offres à préparer
        </button>
      </div>
    </Transition>
  </div>
</template>
