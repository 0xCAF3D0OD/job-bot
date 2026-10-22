<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application, ApplicationStatus, Interview, OrpRow } from "../api/client";
import { nextStep } from "../applicationState";
import { applicationStatusLabel, colorIndex } from "../format";
import FollowUpPanel from "./FollowUpPanel.vue";
import SidePanel from "./SidePanel.vue";

// Carte d'une candidature (docs/46 §2) : qui, quoi, le statut, et une seule prochaine étape.
// Le reste (statut, entretiens, ORP, documents, contacts) est dans le panneau.
const props = defineProps<{ application: Application; orpRow?: OrpRow | null }>();
const emit = defineEmits<{
  open: [application: Application];
  status: [application: Application, status: ApplicationStatus];
  edit: [application: Application];
  interview: [application: Application, interview: Interview | null];
  prepare: [application: Application];
  changed: [];
}>();

const step = computed(() => nextStep(props.application, props.orpRow));
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

// Relance (docs/38) : son panneau s'ouvre depuis la carte.
const followUpOpen = ref(false);
function onFollowedUp(): void {
  followUpOpen.value = false;
  emit("changed");
}

function run(): void {
  const a = props.application;
  switch (step.value.key) {
    case "prepare":
      emit("prepare", a);
      break;
    case "feedback":
      emit("interview", a, null);
      break;
    case "follow-up":
      followUpOpen.value = true;
      break;
    case "no-answer":
      emit("status", a, "sans_reponse");
      break;
    case "complete":
      emit("edit", a);
      break;
    default:
      emit("open", a);
  }
}
</script>

<template>
  <!-- Une ligne, la même forme qu'Aujourd'hui (docs/130 §A) : l'initiale, l'entreprise, le poste
       et la date, ce qui se passe ; l'action à droite. Le statut est dans la phrase. -->
  <article
    class="application-row"
    data-test="application-card"
  >
    <span
      class="logo"
      :class="`c${colorIndex(application.company)}`"
      aria-hidden="true"
    >{{ application.company.trim().charAt(0).toUpperCase() }}</span>
    <button
      type="button"
      class="application-row-main"
      data-test="card-open"
      :title="`${application.company} · ${application.job_title}`"
      @click="emit('open', application)"
    >
      <strong>
        {{ application.company }}
        <span
          v-if="application.assigned_by_orp"
          class="badge"
        >ORP</span>
        <span
          v-if="application.spontaneous"
          class="badge spontaneous-badge"
          data-test="card-spontaneous"
        >Spontanée</span>
      </strong>
      <span class="today-row-line">{{ application.job_title }} · envoyée le {{ shortDate.format(new Date(application.sent_at)) }}</span>
      <span
        :class="['today-row-line', 'application-row-step', step.key]"
        data-test="card-step"
      >
        <span
          :class="{ 'visually-hidden': step.text }"
          data-test="card-status"
        >{{ applicationStatusLabel[application.status] }}</span>{{ step.text }}
      </span>
    </button>
    <button
      type="button"
      class="link application-row-action"
      :data-test="`card-step-${step.key}`"
      @click="run"
    >
      {{ step.action }}
    </button>
    <SidePanel
      v-if="followUpOpen"
      open
      :title="`Relancer ${application.company}`"
      @close="followUpOpen = false"
    >
      <FollowUpPanel
        :application="application"
        @done="onFollowedUp"
      />
    </SidePanel>
  </article>
</template>
