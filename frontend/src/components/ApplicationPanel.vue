<script setup lang="ts">
import { computed, ref, type FunctionalComponent } from "vue";

import { api, type Application, type ApplicationStatus, type Interview, type OrpRow } from "../api/client";
import { noAnswerText, followUpDue, interviewUpcoming, needsFeedback, noAnswerDue } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { usePhone } from "../composables/usePhone";
import { dateInList, dateInSentence, meetingDate } from "../dates";
import { applicationStatusLabel, colorIndex, initials } from "../format";
import { contactName, toFollowUp } from "../contactLabels";
import AppIcon from "./AppIcon.vue";
import DateField from "./DateField.vue";
import ContactsPanel from "./ContactsPanel.vue";
import FollowUpPanel from "./FollowUpPanel.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import SidePanel from "./SidePanel.vue";
import StatusPill from "./StatusPill.vue";
import { KINDS, NEXT_STEPS } from "../interviewLabels";
import CopyButton from "./CopyButton.vue";
import JobRoomDeclared from "./JobRoomDeclared.vue";
import DetailTwoColumns from "./DetailTwoColumns.vue";

// Panneau d'une candidature (docs/46 §3) : Statut, Entretiens, Pour l'ORP, Documents, Contacts.
// `columns` (MODIFICATIONS du 8 novembre au soir, lot 12) : le détail d'Envoyées sur ordinateur, en deux colonnes ;
// Documents et « Trouver quelqu'un » passent dans la colonne d'appui. Sans `columns` (téléphone), l'ordre reste.
const props = defineProps<{ application: Application; orpRow?: OrpRow | null; columns?: boolean }>();

// Sans colonnes, les deux parties se suivent simplement : Statut… puis Documents et Contacts.
const Flat: FunctionalComponent = (_props, { slots }) => [slots.main?.(), slots.aside?.()];
const layout = computed(() => (props.columns ? DetailTwoColumns : Flat));
const layoutProps = computed(() => (props.columns ? { asideLabel: "Documents et contacts" } : {}));
const company = computed(() => props.application.company || props.application.job_title);
const { phone } = usePhone();
// La fiche « Pour l'ORP » du mois de la candidature (« 02.11.2026 » donne 2026-11).
const ficheTo = computed(() => {
  const [, m, y] = (props.orpRow?.date ?? "").split(".");
  return { path: `/bilan/orp/candidature/${props.application.id}`, query: m && y ? { mois: `${y}-${m}` } : {} };
});
// Les étiquettes sous le titre (maquette CandidaturesOrdinateurB, onglet Envoyées).
const headChips = computed(() => {
  const chips: { text: string; tone: "peach" | "green" | ""; test: string }[] = [];
  if (followUpDue(props.application)) chips.push({ text: noAnswerText(props.application), tone: "peach", test: "head-no-answer" });
  if (props.orpRow?.declared_at) chips.push({ text: "Déclarée à l’ORP", tone: "green", test: "head-declared" });
  if (props.application.assigned_by_orp) chips.push({ text: "ORP", tone: "", test: "head-orp" });
  if (props.application.spontaneous) chips.push({ text: "Spontanée", tone: "", test: "panel-spontaneous" });
  return chips;
});

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

// Lien vers la plateforme dans l'événement d'agenda (docs/40 §1).
const origin = globalThis.location?.origin ?? "";
const upcoming = computed(() => interviewUpcoming(props.application));
const feedback = computed(() => needsFeedback(props.application));
const latest = computed<Interview | null>(() => props.application.interviews?.at(-1) ?? null);
const hasInterviews = computed(() => props.application.status === "entretien" || !!props.application.interview_at || !!latest.value);
const summary = computed(() => {
  const i = latest.value;
  if (!i) return "";
  const parts = [(i.kind && KINDS[i.kind]) || "Entretien", `ressenti ${i.rating}/5`];
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
    items.push({ label: "M'entraîner", test: "interview-practice", icon: "ai", run: () => emit("practice", a) });
  }
  const last = latest.value;
  if (last) {
    items.push({ label: "Voir le retour", test: "interview-open", icon: "eye", run: () => emit("interview", a, last) });
    if (!feedback.value) {
      items.push({ label: "Ajouter un autre entretien", test: "interview-add", icon: "plus", run: () => emit("interview", a, null) });
    }
  }
  return items;
});
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
    :class="['application-panel', { 'application-panel-columns': columns }]"
    data-test="application-panel"
  >
    <template v-if="columns">
      <div class="application-panel-head application-panel-head-wide">
        <span
          :class="['list-card-logo', 'application-panel-logo', `c${colorIndex(company)}`]"
          aria-hidden="true"
        >{{ initials(company) }}</span>
        <div class="application-panel-title">
          <h2 data-test="panel-title">
            {{ application.job_title }}
          </h2>
          <p>{{ [application.company, application.location].filter(Boolean).join(" · ") }}</p>
        </div>
        <MoreMenu
          :items="menuItems"
          label="Plus d'actions sur la candidature"
          test-id="panel-more"
        />
      </div>
      <p
        v-if="headChips.length"
        class="application-panel-chips"
      >
        <span
          v-for="chip in headChips"
          :key="chip.test"
          :class="chip.tone"
          :data-test="chip.test"
        >{{ chip.text }}</span>
      </p>
    </template>
    <div
      v-else
      class="application-panel-head"
    >
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

    <component
      :is="layout"
      v-bind="layoutProps"
    >
      <template #main>
        <section
          :class="['panel-section', { 'detail-section': columns }]"
          data-test="section-status"
        >
          <h3>Statut</h3>
          <label class="card-status">
            <span class="visually-hidden">Statut</span>
            <select
              :value="application.status"
              :class="columns ? 'detail-status-select' : ['status-select', 'field-compact', application.status]"
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
              <span
                v-if="columns"
                class="with-icon"
              >Relancer<AppIcon name="chevron" /></span>
              <span
                v-else
                class="with-icon"
              ><AppIcon name="reply" />Relancer</span>
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

        <section
          v-if="hasInterviews"
          :class="['panel-section', { 'detail-section': columns }]"
          data-test="section-interviews"
        >
          <div class="panel-section-head">
            <h3>Entretiens</h3>
            <MoreMenu
              v-if="interviewItems.length"
              class="section-more"
              :items="interviewItems"
              label="Plus d'actions sur les entretiens"
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
          :class="['panel-section', { 'detail-section': columns }]"
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
            Employeur à l'étranger ? Vérifie le contrat et les assurances avec ton conseiller.
          </p>
          <!-- Téléphone (lot 18, §10.3) : les champs à recopier sont dans la fiche « Pour l'ORP ». -->
          <RouterLink
            v-if="orpRow && phone"
            :to="ficheTo"
            class="orp-fiche-link"
            data-test="orp-fiche-link"
          >
            Pour l’ORP ›
          </RouterLink>
          <JobRoomDeclared
            v-if="orpRow && (!phone || orpRow.declared_at)"
            :application-id="application.id"
            :declared-at="orpRow.declared_at"
            @changed="emit('changed')"
          />
          <dl
            v-if="orpRow && !phone"
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
                <CopyButton
                  v-if="item.value && !item.choice"
                  :value="item.value"
                  :label="`Copier : ${item.label}`"
                  test-id="card-copy"
                />
              </dd>
            </template>
          </dl>
        </section>

        <ContactsPanel
          v-if="columns"
          :key="`follow-${application.id}`"
          part="follow"
          :application-id="application.id"
          @changed="emit('changed')"
        />
      </template>
      <template #aside>
        <section
          v-if="hasDocuments && columns"
          class="panel-section detail-section"
          data-test="section-documents"
        >
          <h3>Documents</h3>
          <ul class="detail-links">
            <li v-if="application.letter_draft_id">
              <a
                class="detail-link strong"
                :href="`/api/letters/${application.letter_draft_id}/docx`"
                download
                data-test="panel-letter"
              ><AppIcon name="download" />Lettre (Word)</a>
            </li>
            <li v-if="application.cv_draft_id">
              <a
                class="detail-link strong"
                :href="`/api/cvs/${application.cv_draft_id}/docx`"
                download
                data-test="panel-cv"
              ><AppIcon name="download" />CV (Word)</a>
            </li>
            <li v-if="application.application_url?.startsWith('http')">
              <a
                class="detail-link"
                :href="application.application_url"
                target="_blank"
                rel="noopener noreferrer"
                data-test="panel-link"
              >Ouvrir l'annonce<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
            </li>
          </ul>
        </section>
        <section
          v-else-if="hasDocuments"
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
          :class="['panel-section', { 'detail-section': columns }]"
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
            :part="columns ? 'find' : 'all'"
            :application-id="application.id"
            @changed="emit('changed')"
          />
        </section>
      </template>
    </component>
  </div>
</template>

<style>
/* Détail d'Envoyées sur ordinateur (maquette CandidaturesOrdinateurB, onglet Envoyées) : logo de 56, titre de 24 en
   800, « entreprise · lieu » en 15, étiquettes de 12 ; Statut en liste de 200 de large ; liens d'appui de 44. */
.application-panel-columns { --panel-56: 56px; --panel-19: 19px; --panel-30: 30px; --panel-200: 200px; --panel-18: 18px; --panel-24: 24px; --panel-2: 2px; --panel-14: 14px; gap: var(--panel-18); }
.application-panel-head-wide { align-items: flex-start; gap: var(--space-4); }
.application-panel-head-wide .application-panel-logo { width: var(--panel-56); height: var(--panel-56); font-size: var(--panel-19); }
.application-panel-title { flex: 1; min-width: 0; }
.application-panel-title h2 { margin: 0; font-size: var(--panel-24); line-height: var(--panel-30); font-weight: var(--weight-heavy); color: var(--text); }
.application-panel-title p { margin: var(--space-1) 0 0; font-size: var(--font-label); color: var(--text-secondary); }
.application-panel-chips { display: flex; flex-wrap: wrap; gap: var(--space-1); margin: 0; }
.application-panel-chips > span { padding: var(--panel-2) var(--space-2); border-radius: var(--radius-sm); background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-tertiary); font-size: var(--font-caption); font-weight: var(--weight-semibold); white-space: nowrap; }
.application-panel-chips > .peach { background: var(--peach-soft); color: var(--peach-text); }
.application-panel-chips > .green { background: var(--success-soft); color: var(--success); }
.application-panel-columns .panel-section.detail-section { display: block; margin: 0; padding: var(--cols-pad-top) 0 var(--cols-pad-bottom); border-top: 1px solid var(--line-soft); }
.application-panel-columns :is(.detail-columns-main, .detail-columns-aside) > .panel-section.detail-section:first-child { border-top: 0; }
.application-panel-columns .detail-columns-aside > .panel-section.detail-section:last-child { padding-bottom: var(--space-2); }
.application-panel-columns .panel-section.detail-section > h3 { margin: 0 0 var(--space-4); font-size: var(--font-title); line-height: var(--cols-title); font-weight: var(--weight-bold); }
.application-panel-columns .detail-status-select { width: var(--panel-200); }
.application-panel-columns .follow-up-line, .application-panel-columns .panel-line { font-size: var(--font-label); line-height: var(--leading-normal); }
.application-panel-columns .follow-up-line { margin: var(--space-5) 0 0; color: var(--peach-text); }
.application-panel-columns .follow-up-line .link, .application-panel-columns .panel-line .link { font-weight: var(--weight-bold); }
.application-panel-columns .follow-up-line .icon { width: var(--panel-14); height: var(--panel-14); }
.application-panel-columns .follow-up-line + .panel-line { margin-top: var(--space-2); }
.application-panel-columns .panel-line { margin-top: var(--space-5); }
/* Tous les boutons du détail sont ronds : plus de bouton rectangulaire à 8 px. */
.application-panel-columns button:is(.primary, .secondary) { border-radius: var(--radius-pill); }
/* Niveaux d'action D30 dans le détail en deux colonnes (§2.7) : plein pour l'action principale, contour bleu sinon. */
.application-panel-columns button.primary:not(:disabled) { background: var(--action); border-color: var(--action); color: var(--on-action); }
.application-panel-columns button.secondary { background: var(--surface); border: var(--action-line) solid var(--primary-graphic); color: var(--primary-text); }
/* Lot 18 (§2.2, niveau « texte ») : le lien vers la fiche « Pour l'ORP », sur téléphone. */
.orp-fiche-link { display: inline-flex; align-items: center; min-height: var(--target-min); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; }
.orp-fiche-link:hover { text-decoration: underline; }
</style>
