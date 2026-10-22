
<script setup lang="ts">
import { ref } from "vue";

import type { Offer } from "../api/client";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import ScoreWord from "./ScoreWord.vue";

// « Pour cette offre » (docs/47 §2) : la note, les points forts et les manques, à côté de la
// lettre et du CV, pour écrire en ayant l'offre sous les yeux.
const props = defineProps<{ offer: Offer }>();
const open = ref(false);
const strengths = () => props.offer.strengths ?? [];
const gaps = () => props.offer.gaps ?? [];
</script>

<template>
  <div
    v-if="offer.summary_role"
    class="side-card offer-brief"
    data-test="offer-brief"
  >
    <h2>Pour cette offre</h2>
    <p class="offer-brief-head">
      <ScoreWord
        v-if="offer.score !== null && offer.score !== undefined"
        :score="offer.score"
      />
      <span class="muted">
        {{ [strengths().length ? plural(strengths().length, "point fort", "points forts") : "", gaps().length ? plural(gaps().length, "manque", "manques") : ""].filter(Boolean).join(" · ") }}
      </span>
    </p>
    <div
      v-if="strengths().length || gaps().length"
      :class="['offer-brief-points', { folded: !open }]"
      data-test="offer-brief-points"
    >
      <ul>
        <li
          v-for="point in strengths()"
          :key="point.text"
          class="ok"
        >
          {{ point.text }}
        </li>
        <li
          v-for="point in gaps()"
          :key="point.text"
          class="gap"
        >
          {{ point.text }}
        </li>
      </ul>
    </div>
    <button
      v-if="!open && strengths().length + gaps().length > 3"
      type="button"
      class="link offer-brief-more"
      data-test="offer-brief-more"
      @click="open = true"
    >
      <span class="with-icon">Tout voir<AppIcon name="chevron-down" /></span>
    </button>
  </div>
</template>
