<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import type { Application, Interview } from "../api/client";
import { interviewUpcoming, needsFeedback } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { usePhone } from "../composables/usePhone";
import { dateInSentence, meetingDate } from "../dates";
import { feelingText, KINDS, NEXT_STEPS } from "../interviewLabels";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// Les entretiens d'une candidature (docs/74) : le prochain, le résumé du dernier et une seule action visible ; le reste
// dans « ⋯ ». Partagé par le panneau d'une candidature et le détail d'Envoyées (§8).
const props = defineProps<{ application: Application }>();
const emit = defineEmits<{ interview: [application: Application, interview: Interview | null]; prepare: []; practice: [] }>();

const origin = globalThis.location?.origin ?? "";
const assistant = useAssistant();
const router = useRouter();
const { phone: wide } = usePhone("(min-width: 1024px)");
const { phone } = usePhone();
// Ordinateur (§72p, Kevin 19.11) : « Ajouter un autre entretien » toujours là ; il ouvre le panneau de Rendez-vous.
const desktop = computed(() => wide.value && !phone.value);
const upcoming = computed(() => interviewUpcoming(props.application));
const feedback = computed(() => needsFeedback(props.application));
const latest = computed<Interview | null>(() => props.application.interviews?.at(-1) ?? null);
const summary = computed(() => {
  const i = latest.value;
  if (!i) return "";
  const parts = [(i.kind && KINDS[i.kind]) || "Entretien", `ressenti ${feelingText(i)}`];
  if (i.next_step && i.next_step !== "rien") {
    const when = i.next_step_at ? ` avant ${dateInSentence(`${i.next_step_at}T12:00:00`)}` : "";
    parts.push(`suite : ${(NEXT_STEPS[i.next_step] ?? "").toLowerCase()}${when}`);
  }
  return parts.join(" · ");
});
const canFeedback = computed(
  () => !upcoming.value && (feedback.value || (props.application.status === "entretien" && !latest.value)),
);
const interviewItems = computed<MoreMenuItem[]>(() => {
  const a = props.application;
  const items: MoreMenuItem[] = [];
  if (upcoming.value) {
    items.push({
      label: "Ajouter à mon agenda",
      test: "interview-calendar",
      icon: "calendar",
      href: `/api/applications/${a.id}/interview.ics?origin=${encodeURIComponent(origin)}`,
      download: true,
    });
  }
  // S'entraîner avec l'IA (docs/75), seulement si l'IA est configurée.
  if (assistant.available.value) {
    items.push({ label: "M’entraîner", test: "interview-practice", icon: "ai", run: () => emit("practice") });
  }
  const last = latest.value;
  if (last) {
    items.push({ label: "Voir le retour", test: "interview-open", icon: "eye", run: () => emit("interview", a, last) });
  }
  if (desktop.value) {
    const to = `/candidatures/rendez-vous-orp?rdv=ajouter-${a.id}`;
    items.push({ label: "Ajouter un autre entretien", test: "interview-add", icon: "plus", run: () => void router.push(to) });
  } else if (last && !feedback.value) {
    items.push({ label: "Ajouter un autre entretien", test: "interview-add", icon: "plus", run: () => emit("interview", a, null) });
  }
  return items;
});
</script>

<template>
  <section
    class="panel-section"
    data-test="section-interviews"
  >
    <div class="panel-section-head">
      <h3>Entretiens</h3>
      <MoreMenu
        v-if="interviewItems.length"
        class="section-more"
        :items="interviewItems"
        label="Plus d’actions sur les entretiens"
        test-id="interviews-more"
      />
    </div>
    <p
      v-if="upcoming"
      class="panel-line"
    >
      Prévu {{ meetingDate(application.interview_at!) }}
    </p>
    <p
      v-if="summary"
      class="interview-summary"
      data-test="interview-summary"
    >
      {{ summary }}
    </p>
    <!-- Une seule action visible, la plus utile maintenant ; le reste dans « ⋯ » (docs/74). -->
    <p
      v-if="upcoming || canFeedback"
      class="panel-section-links"
    >
      <button
        v-if="upcoming"
        type="button"
        class="link"
        data-test="interview-prepare"
        @click="emit('prepare')"
      >
        Préparer l’entretien
      </button>
      <button
        v-else
        type="button"
        class="link"
        data-test="interview-feedback"
        @click="emit('interview', application, null)"
      >
        Faire le point sur l’entretien
      </button>
    </p>
  </section>
</template>
