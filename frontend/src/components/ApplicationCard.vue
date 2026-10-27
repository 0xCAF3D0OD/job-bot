<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application, ApplicationStatus, Interview, OrpRow } from "../api/client";
import { nextStep } from "../applicationState";
import { applicationStatusLabel } from "../format";
import FollowUpPanel from "./FollowUpPanel.vue";
import OfferLine from "./OfferLine.vue";
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
// L'état sous le titre (planche « Ligne d'offre ») : en orange s'il faut agir, en gris sinon.
const URGENT = ["feedback", "follow-up", "no-answer", "complete"];
const state = computed(() => step.value.text || `Envoyée le ${shortDate.format(new Date(props.application.sent_at))}`);
const urgent = computed(() => URGENT.includes(step.value.key));

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
  <!-- La Ligne d'offre compacte (planche « Ligne d'offre ») : l'initiale, le poste, « entreprise · lieu »,
       l'état sous le titre, l'action à droite ; toute la ligne ouvre le panneau. -->
  <OfferLine
    :title="application.job_title"
    :company="application.company"
    :location="application.location ?? null"
    :state="state"
    :urgent="urgent"
    :action="step.key === 'manage' ? null : step.action"
    :action-test="`card-step-${step.key}`"
    class="application-line"
    data-test="application-card"
    @select="emit('open', application)"
    @action="run"
  >
    <template #badges>
      <span
        v-if="application.assigned_by_orp"
        class="badge"
      >ORP</span>
      <span
        v-if="application.spontaneous"
        class="badge spontaneous-badge"
        data-test="card-spontaneous"
      >Spontanée</span>
      <span
        class="visually-hidden"
        data-test="card-status"
      >{{ applicationStatusLabel[application.status] }}</span>
    </template>
  </OfferLine>
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
</template>
