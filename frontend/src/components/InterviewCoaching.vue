<script setup lang="ts">
import type { InterviewInsights } from "../api/client";

// Pistes de l'IA (docs/23 §3), affichées telles quelles.
defineProps<{ coaching: NonNullable<InterviewInsights["coaching"]> }>();
const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
</script>

<template>
  <div
    class="coaching"
    data-test="coaching"
  >
    <p class="hint">
      Pistes de l'IA du {{ dateFormat.format(new Date(coaching.created_at)) }}, d'après tes retours et ton profil.
    </p>
    <ul v-if="coaching.pistes.length">
      <li
        v-for="item in coaching.pistes"
        :key="item"
      >
        {{ item }}
      </li>
    </ul>
    <template v-if="coaching.answers.length">
      <h4>Réponses proposées</h4>
      <dl>
        <template
          v-for="item in coaching.answers"
          :key="item.question"
        >
          <dt>{{ item.question }}</dt>
          <dd>{{ item.answer }}</dd>
        </template>
      </dl>
    </template>
    <template v-if="coaching.questions_to_ask.length">
      <h4>Questions à poser</h4>
      <ul>
        <li
          v-for="item in coaching.questions_to_ask"
          :key="item"
        >
          {{ item }}
        </li>
      </ul>
    </template>
  </div>
</template>
