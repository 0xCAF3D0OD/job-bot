<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application, ApplicationStatus, Interview, OrpRow } from "../api/client";
import { followUpDue, interviewUpcoming, needsFeedback, noAnswerDue } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { applicationStatusLabel } from "../format";
import { contactName, toFollowUp } from "../contactLabels";
import ContactsPanel from "./ContactsPanel.vue";
import FollowUpPanel from "./FollowUpPanel.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import SidePanel from "./SidePanel.vue";
import { KINDS, NEXT_STEPS } from "../interviewLabels";
import CopyLabel from "./CopyLabel.vue";
import JobRoomDeclared from "./JobRoomDeclared.vue";

// Panneau d'une candidature (docs/46 §3) : Statut, Entretiens, Pour l'ORP, Documents, Contacts.
const props = defineProps<{ application: Application; orpRow?: OrpRow | null }>();

const emit = defineEmits<{
  status: [application: Application, status: ApplicationStatus];
  edit: [application: Application];
  remove: [application: Application];
  interview: [application: Application, interview: Interview | null];
  prepare: [application: Application];
  practice: [application: Application];
  changed: [];
}>();

// Lien vers la plateforme dans l'événement d'agenda (docs/40 §1).
const origin = globalThis.location?.origin ?? "";
const upcoming = computed(() => interviewUpcoming(props.application));
const feedback = computed(() => needsFeedback(props.application));
const latest = computed<Interview | null>(() => props.application.interviews?.at(-1) ?? null);
const hasInterviews = computed(() => props.application.status === "entretien" || !!props.application.interview_at || !!latest.value);
const interviewDate = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long", hour: "numeric", minute: "2-digit" });
const summary = computed(() => {
  const i = latest.value;
  if (!i) return "";
  const parts = [(i.kind && KINDS[i.kind]) || "Entretien", `ressenti ${i.rating}/5`];
  if (i.next_step && i.next_step !== "rien") {
    const when = i.next_step_at ? ` avant le ${new Date(`${i.next_step_at}T12:00:00`).toLocaleDateString("fr-CH")}` : "";
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
      href: `/api/applications/${a.id}/interview.ics?origin=${encodeURIComponent(origin)}`,
      download: true,
    });
  }
  // S'entraîner avec l'IA (docs/75), seulement si l'IA est configurée.
  if (assistant.available.value) {
    items.push({ label: "M'entraîner", test: "interview-practice", run: () => emit("practice", a) });
  }
  const last = latest.value;
  if (last) {
    items.push({ label: "Voir le retour", test: "interview-open", run: () => emit("interview", a, last) });
    if (!feedback.value) {
      items.push({ label: "Ajouter un autre entretien", test: "interview-add", run: () => emit("interview", a, null) });
    }
  }
  return items;
});
const followUpOpen = ref(false);
function onFollowedUp(): void {
  followUpOpen.value = false;
  emit("changed");
}
const contactsDue = computed(() => (props.application.contacts ?? []).filter((c) => toFollowUp(c)));
const hasDocuments = computed(
  () =>
    !!props.application.letter_draft_id ||
    !!props.application.cv_draft_id ||
    !!props.application.application_url?.startsWith("http"),
);
// Télétravail complet hors de Suisse (docs/26 §6) : rappel pour l'ORP, pas un avis officiel.
const remoteAbroad = computed(
  () => props.application.remote_full && !/suisse|switzerland|schweiz/i.test(props.application.remote_region ?? ""),
);

const copied = ref("");
async function copy(value: string, key: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    copied.value = key;
    setTimeout(() => {
      if (copied.value === key) copied.value = "";
    }, 1500);
  } catch {
    copied.value = "";
  }
}

// « ⋯ » (docs/50 §1) : Modifier, Demander à l'assistant, Supprimer.
const assistant = useAssistant();
function askAssistant(): void {
  const a = props.application;
  assistant.askAbout({ applicationId: a.id, label: `candidature ${a.job_title} chez ${a.company}` });
}
const menuItems = computed<MoreMenuItem[]>(() => [
  { label: "Modifier", test: "panel-edit", run: () => emit("edit", props.application) },
  ...(assistant.available.value ? [{ label: "Demander à l'assistant", test: "panel-ask", run: askAssistant }] : []),
  { label: "Supprimer", test: "panel-remove", danger: true, run: () => emit("remove", props.application) },
]);

const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric" });
const onStatus = (event: Event): void =>
  emit("status", props.application, (event.target as HTMLSelectElement).value as ApplicationStatus);
</script>

<template>
  <div
    class="application-panel"
    data-test="application-panel"
  >
    <div class="application-panel-head">
      <p class="muted">
        {{ application.job_title }} · envoyée le {{ shortDate.format(new Date(application.sent_at)) }}
        <span
          v-if="application.assigned_by_orp"
          class="badge"
        >ORP</span>
        <span
          v-if="application.spontaneous"
          class="badge spontaneous-badge"
        >Spontanée</span>
      </p>
      <MoreMenu
        :items="menuItems"
        label="Actions sur la candidature"
        test-id="panel-more"
      />
    </div>

    <section
      class="panel-section"
      data-test="section-status"
    >
      <h3>Statut</h3>
      <label class="card-status">
        <span class="visually-hidden">Statut</span>
        <select
          :value="application.status"
          :class="['status-select', application.status]"
          data-test="panel-status"
          @change="onStatus"
        >
          <option
            v-for="(text, value) in applicationStatusLabel"
            :key="value"
            :value="value"
          >
            {{ text }}
          </option>
        </select>
      </label>
      <p
        v-if="followUpDue(application)"
        class="follow-up-line"
        data-test="panel-follow-up"
      >
        Sans réponse depuis 10 jours.
        <button
          type="button"
          class="link"
          data-test="panel-follow-up-open"
          @click="followUpOpen = true"
        >
          Relancer
        </button>
      </p>
      <p
        v-else-if="noAnswerDue(application)"
        class="follow-up-line"
        data-test="panel-no-answer"
      >
        Pas de réponse depuis la relance.
        <button
          type="button"
          class="link"
          @click="emit('status', application, 'sans_reponse')"
        >
          Passer en Sans réponse
        </button>
      </p>
    </section>
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

    <section
      v-if="hasInterviews"
      class="panel-section"
      data-test="section-interviews"
    >
      <div class="panel-section-head">
        <h3>Entretiens</h3>
        <MoreMenu
          v-if="interviewItems.length"
          class="section-more"
          :items="interviewItems"
          label="Actions sur les entretiens"
          test-id="interviews-more"
        />
      </div>
      <p
        v-if="upcoming"
        class="panel-line"
      >
        Prévu {{ interviewDate.format(new Date(application.interview_at!)) }}
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
          @click="emit('prepare', application)"
        >
          Préparer l'entretien
        </button>
        <button
          v-else
          type="button"
          class="link"
          data-test="interview-feedback"
          @click="emit('interview', application, null)"
        >
          Faire le point sur l'entretien
        </button>
      </p>
    </section>

    <section
      v-if="orpRow || remoteAbroad"
      class="panel-section"
      data-test="section-orp"
    >
      <h3>Pour l'ORP</h3>
      <p
        v-if="orpRow?.missing.length"
        class="notice card-missing"
        data-test="card-missing"
      >
        Il manque : {{ orpRow.missing.join(", ") }}.
        <button
          type="button"
          class="link"
          data-test="card-complete"
          @click="emit('edit', application)"
        >
          Compléter
        </button>
      </p>
      <p
        v-if="remoteAbroad"
        class="remote-orp"
        data-test="remote-orp"
      >
        100 % télétravail{{ application.remote_region ? ` · ${application.remote_region}` : "" }} : si l'employeur est à
        l'étranger, vérifie contrat et assurances sociales avec ton conseiller ORP.
      </p>
      <JobRoomDeclared
        v-if="orpRow"
        :application-id="application.id"
        :declared-at="orpRow.declared_at"
        @changed="emit('changed')"
      />
      <dl
        v-if="orpRow"
        class="card-job-room"
        data-test="card-job-room-fields"
      >
        <template
          v-for="item in orpRow.job_room"
          :key="item.label"
        >
          <dt>{{ item.label }}</dt>
          <dd>
            <span
              v-if="item.choice"
              class="job-room-choice"
            >{{ item.value ? `à cocher : ${item.value}` : "—" }}</span>
            <span v-else>{{ item.value || "—" }}</span>
            <button
              v-if="item.value && !item.choice"
              type="button"
              class="link"
              data-test="card-copy"
              @click="copy(item.value, item.label)"
            >
              <CopyLabel :done="copied === item.label" />
            </button>
          </dd>
        </template>
      </dl>
    </section>

    <section
      v-if="hasDocuments"
      class="panel-section"
      data-test="section-documents"
    >
      <h3>Documents</h3>
      <p class="panel-section-links">
        <a
          v-if="application.letter_draft_id"
          class="link"
          :href="`/api/letters/${application.letter_draft_id}/docx`"
          download
        >Lettre</a>
        <a
          v-if="application.cv_draft_id"
          class="link"
          :href="`/api/cvs/${application.cv_draft_id}/docx`"
          download
        >CV</a>
        <a
          v-if="application.application_url?.startsWith('http')"
          class="link"
          :href="application.application_url"
          target="_blank"
          rel="noopener noreferrer"
        >Lien de candidature</a>
      </p>
    </section>

    <section
      class="panel-section"
      data-test="section-contacts"
    >
      <h3>Contacts</h3>
      <p
        v-if="contactsDue.length"
        class="contact-due-line"
        data-test="card-contact-due"
      >
        Sans réponse depuis 7 jours : relancer {{ contactsDue.map(contactName).join(", ") }} ?
      </p>
      <ContactsPanel
        :key="application.id"
        :application-id="application.id"
        @changed="emit('changed')"
      />
    </section>
  </div>
</template>
