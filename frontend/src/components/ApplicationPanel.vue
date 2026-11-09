<script setup lang="ts">
import { computed, ref } from "vue";

import { api, type Application, type ApplicationStatus, type Interview, type OrpRow } from "../api/client";
import { noAnswerText, followUpDue, noAnswerDue } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { dateInList, dateInSentence } from "../dates";
import { applicationStatusLabel } from "../format";
import { contactName, toFollowUp } from "../contactLabels";
import AppIcon from "./AppIcon.vue";
import DateField from "./DateField.vue";
import ContactsPanel from "./ContactsPanel.vue";
import FollowUpPanel from "./FollowUpPanel.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import SidePanel from "./SidePanel.vue";
import StatusPill from "./StatusPill.vue";
import ApplicationInterviews from "./ApplicationInterviews.vue";
import ApplicationOrp from "./ApplicationOrp.vue";

// Panneau d'une candidature (docs/46 §3) : Statut, Entretiens, Pour l'ORP, Documents, Contacts.
// Sur ordinateur, le détail d'Envoyées est SentDetail (§8 du 9 novembre) ; ce panneau sert au téléphone et aux
// écrans moyens.
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

// La relance (revue de l'étape 7c, reprise de l'ancienne étape « Suivre ») : le jour choisi, sinon 10 jours
// après l'envoi ; « Changer » propose un jour entre 5 et 30 jours après l'envoi. Une fois répondue ou relancée,
// plus de relance prévue.
const REMIND_AFTER_DAYS = 10;
const MIN_DAYS = 5;
const MAX_DAYS = 30;
function isoDay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function shift(day: string, days: number): string {
  const d = new Date(`${day}T12:00:00`);
  d.setDate(d.getDate() + days);
  return isoDay(d);
}
const followUpOn = ref<string | null>(null);
const remindOn = computed(() => followUpOn.value ?? props.application.follow_up_on ?? shift(props.application.sent_at, REMIND_AFTER_DAYS));
// Le jour venu ou passé, toujours en attente : « Relance à faire » à la place de la date.
const remindDue = computed(() => remindOn.value <= isoDay(new Date()));
const remindEditing = ref(false);
const remindDraft = ref("");
const remindError = ref("");
function startRemind(): void {
  remindError.value = "";
  remindDraft.value = remindOn.value;
  remindEditing.value = true;
}
async function saveRemind(): Promise<void> {
  remindError.value = "";
  const { data } = await api.PATCH("/api/applications/{application_id}/follow-up-date", {
    params: { path: { application_id: props.application.id } },
    body: { follow_up_on: remindDraft.value || null },
  });
  if (!data) {
    remindError.value = `Choisis un jour entre ${MIN_DAYS} et ${MAX_DAYS} jours après l'envoi.`;
    return;
  }
  followUpOn.value = data.follow_up_on ?? shift(data.sent_at, REMIND_AFTER_DAYS);
  remindEditing.value = false;
  emit("changed");
}

const latest = computed<Interview | null>(() => props.application.interviews?.at(-1) ?? null);
const hasInterviews = computed(() => props.application.status === "entretien" || !!props.application.interview_at || !!latest.value);
const documentItems = computed<MoreMenuItem[]>(() => {
  const a = props.application;
  const items: MoreMenuItem[] = [];
  if (a.cv_draft_id) items.push({ label: "CV (Word)", test: "panel-cv", icon: "download", href: `/api/cvs/${a.cv_draft_id}/docx`, download: true });
  if (a.application_url?.startsWith("http")) {
    items.push({ label: "Ouvrir l'annonce", test: "panel-link", icon: "external", href: a.application_url });
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

// « ⋯ » (docs/50 §1) : Modifier, Demander à l'assistant, Supprimer.
const assistant = useAssistant();
function askAssistant(): void {
  const a = props.application;
  assistant.askAbout({ applicationId: a.id, label: `candidature ${a.job_title} chez ${a.company}` });
}
const menuItems = computed<MoreMenuItem[]>(() => [
  { label: "Modifier", test: "panel-edit", icon: "pencil", run: () => emit("edit", props.application) },
  ...(assistant.available.value ? [{ label: "Demander à l'assistant", test: "panel-ask", icon: "ai" as const, run: askAssistant }] : []),
  { label: "Supprimer", test: "panel-remove", icon: "trash", run: () => emit("remove", props.application) },
]);

const onStatus = (event: Event): void =>
  emit("status", props.application, (event.target as HTMLSelectElement).value as ApplicationStatus);
</script>

<template>
  <div
    class="application-panel"
    data-test="application-panel"
  >
    <div class="application-panel-head">
      <p class="muted meta-line">
        <span>{{ application.job_title }}</span>
        <span><AppIcon name="send" /><span class="visually-hidden">envoyée le </span>{{ dateInList(`${application.sent_at}T12:00:00`) }}</span>
        <!-- Des étiquettes sans état, au bout de la ligne : sans point, neutres (règle §4). -->
        <StatusPill
          v-if="application.assigned_by_orp"
          :dot="false"
        >
          ORP
        </StatusPill>
        <StatusPill
          v-if="application.spontaneous"
          :dot="false"
          data-test="panel-spontaneous"
        >
          Spontanée
        </StatusPill>
      </p>
      <MoreMenu
        :items="menuItems"
        label="Plus d'actions sur la candidature"
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
          :class="['status-select', 'field-compact', application.status]"
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
        {{ noAnswerText(application) }}.
        <button
          type="button"
          class="link"
          data-test="panel-follow-up-open"
          @click="followUpOpen = true"
        >
          <span class="with-icon"><AppIcon name="reply" />Relancer</span>
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
      <p
        v-if="application.status !== 'en_attente'"
        class="panel-line muted"
        data-test="panel-remind"
      >
        Plus de relance prévue
      </p>
      <form
        v-else-if="remindEditing"
        class="panel-line remind-edit"
        data-test="panel-remind"
        @submit.prevent="saveRemind"
      >
        <DateField
          :model-value="remindDraft"
          label="Relance le"
          :min="shift(application.sent_at, MIN_DAYS)"
          :max="shift(application.sent_at, MAX_DAYS)"
          :invalid="!!remindError"
          data-test="remind-date"
          @update:model-value="remindDraft = $event ?? ''"
        />
        <button
          type="submit"
          class="primary small"
          data-test="remind-save"
        >
          Enregistrer
        </button>
        <button
          type="button"
          class="link"
          @click="remindEditing = false"
        >
          Annuler
        </button>
        <span
          v-if="remindError"
          id="remind-error"
          class="field-error"
          role="alert"
        >{{ remindError }}</span>
      </form>
      <p
        v-else
        class="panel-line"
        data-test="panel-remind"
      >
        {{ remindDue ? "Relance à faire" : `Relance : ${dateInSentence(`${remindOn}T12:00:00`)}` }} ·
        <button
          type="button"
          class="link"
          data-test="remind-change"
          @click="startRemind"
        >
          Changer<span class="visually-hidden"> le jour de la relance</span>
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

    <ApplicationInterviews
      v-if="hasInterviews"
      :application="application"
      @interview="(app, i) => emit('interview', app, i)"
      @prepare="emit('prepare', application)"
      @practice="emit('practice', application)"
    />
    <ApplicationOrp
      v-if="orpRow || remoteAbroad"
      :application="application"
      :orp-row="orpRow ?? null"
      @edit="emit('edit', application)"
      @changed="emit('changed')"
    />
    <section
      v-if="hasDocuments"
      class="panel-section"
      data-test="section-documents"
    >
      <div class="panel-section-head">
        <h3>Documents</h3>
        <MoreMenu
          v-if="documentItems.length"
          class="section-more"
          :items="documentItems"
          :inline="!application.letter_draft_id"
          label="Plus d'actions sur les documents"
          test-id="documents-more"
        />
      </div>
      <!-- La lettre visible ; le CV et l'annonce dans « ⋯ », mêmes libellés que le tableau
           du Suivi (docs/76 §3). -->
      <p
        v-if="application.letter_draft_id"
        class="panel-section-links"
      >
        <a
          class="link"
          :href="`/api/letters/${application.letter_draft_id}/docx`"
          download
          data-test="panel-letter"
        ><span class="with-icon"><AppIcon name="download" />Lettre (Word)</span></a>
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
        part="all"
        :application-id="application.id"
        @changed="emit('changed')"
      />
    </section>
  </div>
</template>

<style>
/* Lot 18 (§2.2, niveau « texte ») : le lien vers la fiche « Pour l'ORP », sur téléphone. */
.orp-fiche-link { display: inline-flex; align-items: center; min-height: var(--target-min); padding: 0; border: 0; background: none; color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; }
.orp-fiche-link:hover { text-decoration: underline; }
</style>
