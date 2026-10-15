<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application, ApplicationStatus, Interview, OrpRow } from "../api/client";
import { nextStep } from "../applicationState";
import { applicationStatusLabel } from "../format";
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
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

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
  <article
    class="application-card"
    data-test="application-card"
  >
    <button
      type="button"
      class="application-card-main"
      data-test="card-open"
      @click="emit('open', application)"
    >
      <strong class="application-card-company">
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
      <span class="muted">{{ application.job_title }} · {{ shortDate.format(new Date(application.sent_at)) }}</span>
      <span
        class="app-status"
        data-test="card-status"
      >
        <span :class="['dot', application.status]" />{{ applicationStatusLabel[application.status] }}
      </span>
    </button>
    <p
      :class="['application-card-foot', step.key]"
      data-test="card-step"
    >
      <span>{{ step.text }}</span>
      <button
        type="button"
        class="link"
        :data-test="`card-step-${step.key}`"
        @click="run"
      >
        {{ step.action }} ›
      </button>
    </p>
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
