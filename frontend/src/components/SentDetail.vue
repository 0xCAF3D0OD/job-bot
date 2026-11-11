<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api, type Application, type ApplicationStatus, type ContactsPage, type Interview, type OrpRow } from "../api/client";
import { followUpDue, noAnswerDue } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { applicationStatusLabel, colorIndex, companyPlace, initials } from "../format";
import { sentHistory, sentSteps, sentWords } from "../sentDetail";
import AppIcon from "./AppIcon.vue";
import ApplicationInterviews from "./ApplicationInterviews.vue";
import NewMeetingSheet from "./NewMeetingSheet.vue";
import ApplicationOrp from "./ApplicationOrp.vue";
import ContactQuickForm from "./ContactQuickForm.vue";
import ContactsPanel from "./ContactsPanel.vue";
import FollowUpCard from "./FollowUpCard.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import BottomSheet from "./BottomSheet.vue";
import SentRows, { type SentRow } from "./SentRows.vue";
import SidePanel from "./SidePanel.vue";

// Le détail d'une candidature envoyée sur ordinateur (MODIFICATIONS du 9 novembre, §8.1 ; maquette
// CandidaturesOrdinateurB, onglet Envoyées) : des cartes blanches séparées sur le crème, 8 px entre elles. En tête,
// le statut en mots et le Suivi en 5 étapes ; à gauche la relance conseillée puis l'Historique ; à droite (280 px)
// « Ce que tu as envoyé » et « Trouver un contact ».
const props = defineProps<{ application: Application; orpRow?: OrpRow | null; phone?: boolean }>();
const emit = defineEmits<{
  status: [application: Application, status: ApplicationStatus];
  edit: [application: Application];
  remove: [application: Application];
  interview: [application: Application, interview: Interview | null];
  prepare: [application: Application];
  practice: [application: Application];
  changed: [];
  close: [];
}>();

const company = computed(() => props.application.company || props.application.job_title);
const words = computed(() => sentWords(props.application, props.orpRow));
const steps = computed(() => sentSteps(props.application, props.orpRow));
const history = computed(() => sentHistory(props.application, props.orpRow));
const followUp = computed(() => followUpDue(props.application));
const hasInterviews = computed(
  () => props.application.status === "entretien" || !!props.application.interview_at || !!props.application.interviews?.length,
);
// « Pour l'ORP » reste une carte tant qu'il y a quelque chose à faire : déclarer, compléter, ou le rappel télétravail.
const remoteAbroad = computed(
  () => props.application.remote_full && !/suisse|switzerland|schweiz/i.test(props.application.remote_region ?? ""),
);
const orpTodo = computed(() => !!props.orpRow && (!props.orpRow.declared_at || props.orpRow.missing.length > 0));

// Les recherches de contacts (docs/31) : la même source que l'ancien bloc « Trouver quelqu'un ».
const contacts = ref<ContactsPage | null>(null);
async function loadContacts(): Promise<void> {
  contacts.value = null;
  try {
    const { data } = await api.GET("/api/applications/{application_id}/contacts", {
      params: { path: { application_id: props.application.id } },
    });
    contacts.value = data && Array.isArray(data.searches) ? data : null;
  } catch {
    contacts.value = null;
  }
}
watch(() => props.application.id, () => void loadContacts(), { immediate: true });
const linkedinUrl = computed(() => contacts.value?.searches.find((s) => s.kind === "recruiting")?.url ?? null);
const findRows = computed<SentRow[]>(() => {
  const page = contacts.value;
  if (!page) return [];
  const rows = page.searches.map((s) => {
    const role = /\(([^)]*)\)$/.exec(s.label)?.[1];
    const label = s.label.replace(/\s*\([^)]*\)$/, "");
    const sub = s.kind === "recruiting" ? `${page.company} sur LinkedIn` : s.kind === "team" ? (role ?? page.company) : `Sur LinkedIn, chez ${page.company}`;
    return { label, sub, href: s.url, download: false, test: `find-${s.kind}` };
  });
  if (page.website) rows.push({ label: "Site de l’employeur", sub: hostname(page.website), href: page.website, download: false, test: "find-website" });
  return rows;
});

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
const sentRows = computed(() => {
  const a = props.application;
  const rows: SentRow[] = [];
  if (a.letter_draft_id) rows.push({ label: "Lettre", sub: "PDF", href: `/api/letters/${a.letter_draft_id}/pdf`, download: true, test: "sent-letter" });
  if (a.cv_draft_id) rows.push({ label: "CV adapté", sub: "PDF", href: `/api/cvs/${a.cv_draft_id}/pdf`, download: true, test: "sent-cv" });
  if (a.application_url?.startsWith("http")) {
    rows.push({ label: "L’annonce", sub: `Sur ${hostname(a.application_url)}`, href: a.application_url, download: false, test: "sent-offer" });
  }
  return rows;
});

// « … » : Changer le statut, Modifier, Demander à l'assistant, Supprimer.
const assistant = useAssistant();
const statusOpen = ref(false);
const contactsOpen = ref(false);
// « J'ai contacté quelqu'un » (PR 28) : sur ordinateur la carte se déplie sous l'historique, sur téléphone le
// formulaire s'ouvre dans une fenêtre du bas. Enregistré, le contact entre dans l'historique (la fiche se recharge).
const contactedOpen = ref(false);
function contactSaved(): void {
  contactedOpen.value = false;
  emit("changed");
}
watch(
  () => props.application.id,
  () => {
    contactedOpen.value = false;
  },
);
const docsOpen = ref(false);
const findOpen = ref(false);
// Les deux lignes de 72 px du téléphone (§8.3) : « Lettre, CV adapté et l’annonce », « 3 pistes chez Sword Services ».
const sentSummary = computed(() => {
  const names = sentRows.value.map((r, i) => (i === 0 ? r.label : r.label.replace(/^L’a/, "l’a")));
  return names.length > 1 ? `${names.slice(0, -1).join(", ")} et ${names.at(-1)}` : (names[0] ?? "");
});
const findSummary = computed(() => {
  const n = findRows.value.length;
  return `${n} ${n > 1 ? "pistes" : "piste"} chez ${props.application.company}`;
});
const meetingOpen = ref(false);
function meetingAdded(): void {
  meetingOpen.value = false;
  emit("changed");
}
const menuItems = computed<MoreMenuItem[]>(() => {
  const a = props.application;
  return [
    { label: "Changer le statut", test: "panel-status-open", icon: "pencil", run: () => (statusOpen.value = true) },
    // PR 41 : le même panneau « Nouveau rendez-vous » que l'onglet Rendez-vous, la candidature déjà choisie.
    ...(a.status === "refus" || a.status === "engagement"
      ? []
      : [{ label: "J’ai un entretien", test: "panel-interview-new", icon: "calendar" as const, run: () => (meetingOpen.value = true) }]),
    { label: "Modifier", test: "panel-edit", icon: "pencil", run: () => emit("edit", a) },
    ...(assistant.available.value
      ? [{
          label: "Demander à l’assistant",
          test: "panel-ask",
          icon: "ai" as const,
          run: () => assistant.askAbout({ applicationId: a.id, label: `candidature ${a.job_title} chez ${a.company}` }),
        }]
      : []),
    { label: "Supprimer", test: "panel-remove", icon: "trash", danger: true, separator: true, run: () => emit("remove", a) },
  ];
});
function onStatus(value: ApplicationStatus): void {
  statusOpen.value = false;
  emit("status", props.application, value);
}
</script>

<template>
  <div
    :class="['sent-detail-cards', { 'sent-detail-phone': phone }]"
    data-test="application-panel"
  >
    <!-- Téléphone (§8.3, EnvoyeeDetail) : l'écran poussé a sa barre « ‹ Envoyées » et « … », sans barre d'onglets. -->
    <header
      v-if="phone"
      class="sent-screen-top"
    >
      <button
        type="button"
        class="sent-screen-back"
        data-test="sent-back"
        @click="emit('close')"
      >
        <AppIcon name="chevron-left" />Envoyées
      </button>
      <MoreMenu
        :items="menuItems"
        label="Plus d’options"
        test-id="panel-more"
      />
    </header>
    <div class="sent-card sent-head">
      <div class="sent-head-top">
        <span
          v-if="!phone"
          :class="['list-card-logo', 'sent-head-logo', `c${colorIndex(company)}`]"
          aria-hidden="true"
        >{{ initials(company) }}</span>
        <div class="sent-head-title">
          <component
            :is="phone ? 'h1' : 'h2'"
            data-test="panel-title"
          >
            {{ application.job_title }}
          </component>
          <p>{{ companyPlace(application.company, application.location) }}</p>
        </div>
        <MoreMenu
          v-if="!phone"
          :items="menuItems"
          label="Plus d’actions"
          test-id="panel-more"
        />
      </div>
      <p
        class="sent-words"
        data-test="sent-words"
      >
        <span
          v-for="word in words"
          :key="word.test"
          :class="word.tone"
          :data-test="word.test"
        ><AppIcon
          v-if="word.check"
          name="done"
        />{{ word.text }}</span>
      </p>
      <!-- Pas de graphique de suivi sur téléphone (§8.3) : les mots disent où on en est. -->
      <ol
        v-if="!phone"
        class="sent-steps"
        aria-label="Suivi de la candidature"
        data-test="sent-steps"
      >
        <li
          v-for="(step, i) in steps"
          :key="step.label"
          :class="step.state"
          :aria-current="step.state === 'current' ? 'step' : undefined"
        >
          <span
            v-if="i < steps.length - 1"
            :class="['sent-step-line', { on: steps[i + 1]!.state !== 'todo' }]"
            aria-hidden="true"
          />
          <span
            class="sent-step-dot"
            aria-hidden="true"
          ><AppIcon
            v-if="step.state === 'done'"
            name="done"
          /></span>
          <span class="sent-step-label">{{ step.label }}</span>
          <span class="sent-step-sub">{{ step.sub }}</span>
        </li>
      </ol>
    </div>

    <div class="sent-grid">
      <div class="sent-main">
        <FollowUpCard
          v-if="followUp"
          :application="application"
          compact
          :linkedin-url="linkedinUrl"
          @edit="emit('edit', application)"
          @done="emit('changed')"
        />
        <div
          v-else-if="noAnswerDue(application)"
          class="sent-card sent-plain"
          data-test="panel-no-answer"
        >
          <p>Pas de réponse depuis la relance.</p>
          <button
            type="button"
            class="link"
            @click="emit('status', application, 'sans_reponse')"
          >
            Passer en Sans réponse
          </button>
        </div>
        <ApplicationInterviews
          v-if="hasInterviews"
          class="sent-card"
          :application="application"
          @interview="(app, i) => emit('interview', app, i)"
          @prepare="emit('prepare', application)"
          @practice="emit('practice', application)"
        />
        <ApplicationOrp
          v-if="orpTodo || remoteAbroad"
          class="sent-card"
          :application="application"
          :orp-row="orpRow ?? null"
          @edit="emit('edit', application)"
          @changed="emit('changed')"
        />
        <section
          v-if="phone && (sentRows.length || findRows.length)"
          class="sent-card sent-links"
          aria-label="Documents et contacts"
        >
          <button
            v-if="sentRows.length"
            type="button"
            data-test="sent-docs-open"
            @click="docsOpen = true"
          >
            <span class="sent-row-text"><b>Ce que tu as envoyé</b><span>{{ sentSummary }}</span></span>
            <AppIcon name="chevron" />
          </button>
          <button
            v-if="findRows.length"
            type="button"
            data-test="sent-find-open"
            @click="findOpen = true"
          >
            <span class="sent-row-text"><b>Trouver un contact</b><span>{{ findSummary }}</span></span>
            <AppIcon name="chevron" />
          </button>
        </section>
        <section
          class="sent-history"
          aria-labelledby="sent-history-title"
          data-test="sent-history"
        >
          <p
            id="sent-history-title"
            class="sent-cap"
          >
            Historique
          </p>
          <ul>
            <li
              v-for="(event, i) in history"
              :key="i"
            >
              <span class="sent-history-date">{{ event.date }}</span>
              <span class="sent-history-text">{{ event.title }}<span
                v-if="event.detail"
                class="sent-history-detail"
              >{{ event.detail }}</span></span>
            </li>
          </ul>
          <button
            v-if="phone"
            type="button"
            class="link sent-contacted"
            aria-haspopup="dialog"
            data-test="contacted-open"
            @click="contactedOpen = true"
          >
            <span class="with-icon">J’ai contacté quelqu’un<AppIcon name="chevron" /></span>
          </button>
          <template v-else>
            <button
              type="button"
              class="sent-contacted-fold"
              :aria-expanded="contactedOpen"
              aria-controls="sent-contacted-zone"
              data-test="contacted-open"
              @click="contactedOpen = !contactedOpen"
            >
              J’ai contacté quelqu’un<AppIcon :name="contactedOpen ? 'chevron-up' : 'chevron-down'" />
            </button>
            <div
              v-show="contactedOpen"
              id="sent-contacted-zone"
              data-test="contacted-zone"
            >
              <ContactQuickForm
                v-if="contactedOpen"
                :key="`quick-${application.id}`"
                :application-id="application.id"
                @saved="contactSaved"
                @cancel="contactedOpen = false"
              />
            </div>
          </template>
          <button
            v-if="application.contacts?.length"
            type="button"
            class="link sent-contacts-all"
            data-test="contacts-open"
            @click="contactsOpen = true"
          >
            Voir les prises de contact
          </button>
        </section>
      </div>
      <aside
        v-if="!phone"
        class="sent-side"
        aria-label="Documents et contacts"
      >
        <SentRows
          v-if="sentRows.length"
          title="Ce que tu as envoyé"
          :rows="sentRows"
          data-test="section-documents"
        />
        <SentRows
          v-if="findRows.length"
          title="Trouver un contact"
          :rows="findRows"
          data-test="section-contacts"
        />
      </aside>
    </div>

    <!-- Sur téléphone, des feuilles du bas (BottomSheet) ; sur ordinateur, des panneaux à droite. -->
    <template v-if="phone">
      <BottomSheet
        :open="docsOpen"
        title="Ce que tu as envoyé"
        @close="docsOpen = false"
      >
        <SentRows
          :rows="sentRows"
          data-test="sent-docs-sheet"
        />
      </BottomSheet>
      <BottomSheet
        :open="findOpen"
        title="Trouver un contact"
        @close="findOpen = false"
      >
        <p class="sent-sheet-help">
          Une personne de l’équipe répond souvent plus vite que l’adresse générale.
        </p>
        <SentRows
          :rows="findRows"
          data-test="sent-find-sheet"
        />
      </BottomSheet>
    </template>
    <component
      :is="phone ? BottomSheet : SidePanel"
      :open="statusOpen"
      title="Statut"
      @close="statusOpen = false"
    >
      <fieldset
        class="sent-status-choices"
        data-test="panel-status"
      >
        <legend class="visually-hidden">
          Statut de la candidature
        </legend>
        <label
          v-for="(text, value) in applicationStatusLabel"
          :key="value"
        >
          <input
            type="radio"
            name="sent-status"
            :value="value"
            :checked="application.status === value"
            @change="onStatus(value)"
          >
          {{ text }}
        </label>
      </fieldset>
    </component>
    <BottomSheet
      v-if="phone"
      :open="contactedOpen"
      title="J’ai contacté quelqu’un"
      data-test="contacted-sheet"
      @close="contactedOpen = false"
    >
      <ContactQuickForm
        v-if="contactedOpen"
        :key="`quick-${application.id}`"
        sheet
        :application-id="application.id"
        @saved="contactSaved"
      />
    </BottomSheet>
    <component
      :is="phone ? BottomSheet : SidePanel"
      :open="contactsOpen"
      title="Prises de contact"
      @close="contactsOpen = false"
    >
      <ContactsPanel
        v-if="contactsOpen"
        :key="`log-${application.id}`"
        part="follow"
        :application-id="application.id"
        @changed="emit('changed')"
      />
    </component>
    <NewMeetingSheet
      :open="meetingOpen"
      :applications="[application]"
      :application-id="application.id"
      @close="meetingOpen = false"
      @interview="meetingAdded"
    />
  </div>
</template>

<style>
/* Valeurs de CandidaturesOrdinateurB (onglet Envoyées, §8.1), ramenées sur la grille de 4 quand elles en sortent (écarts
   de 18 → 12 et 24 dans l’en-tête, 6 → 4, libellé et date du Suivi collés) : cartes blanches à trait 1,5 px --card-line, rayon 18,
   8 px entre elles ; en-tête 22,5 de marge, logo 56, titre 24/30 800, « entreprise · ville » 15 ; mots 15/20 700
   décalés de 72 ; Suivi : cercles de 28 à trait 2, libellés 14/18 700 à gauche, dates 13/16, traits de 2 à 8 px des
   cercles ; colonne droite de 280, lignes de 56 ; Historique sur le crème, 20 px plus bas. */
.sent-detail-cards { --sent-8: 8px; --sent-18-5: 18.5px; --sent-22-5: 22.5px; --sent-26-5: 26.5px; --sent-56: 56px; --sent-72: 72px; --sent-19: 19px; --sent-30: 30px; --sent-28: 28px; --sent-14: 14px; --sent-13: 13px; --sent-16: 16px; --sent-18: 18px; --sent-2: 2px; --sent-280: 280px; --sent-64: 64px; --sent-6: 6px; display: flex; flex-direction: column; gap: var(--sent-8); }
.sent-card { padding: var(--sent-18-5); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.sent-head { display: flex; flex-direction: column; padding: var(--sent-22-5) var(--sent-22-5) var(--sent-26-5); }
.sent-head-top { display: flex; align-items: flex-start; gap: var(--space-4); }
.sent-head-top .sent-head-logo { width: var(--sent-56); height: var(--sent-56); font-size: var(--sent-19); }
.sent-head-title { flex: 1; min-width: 0; }
.sent-head-title h2 { margin: 0; font-size: var(--space-6); line-height: var(--sent-30); font-weight: var(--weight-heavy); }
.sent-head-title p { margin: var(--space-1) 0 0; font-size: var(--font-label); color: var(--text-secondary); }
.sent-words { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-4); margin: var(--space-3) 0 0; padding-left: var(--sent-72); font-size: var(--font-label); line-height: var(--space-5); font-weight: var(--weight-bold); }
.sent-words > span { display: inline-flex; align-items: center; gap: var(--space-1); }
.sent-words .icon { width: var(--sent-16); height: var(--sent-16); stroke-width: 2.6; }
.sent-words .peach { color: var(--peach-text); }
.sent-words .green { color: var(--success); }
.sent-words .grey { color: var(--text-tertiary); }
.sent-words .muted { color: var(--text-secondary); }
.sent-steps { position: relative; display: flex; margin: var(--space-6) 0 0; padding: 0 0 0 var(--sent-72); list-style: none; }
.sent-steps > li { position: relative; flex: 1; display: flex; flex-direction: column; align-items: flex-start; min-width: 0; }
.sent-steps > li:last-child { flex: 0 0 auto; }
.sent-step-line { position: absolute; left: calc(var(--sent-28) + var(--sent-8)); right: var(--sent-8); top: calc(var(--sent-28) / 2 - 1px); height: var(--sent-2); background: var(--card-line); }
.sent-step-line.on { background: var(--success); }
.sent-step-dot { display: flex; align-items: center; justify-content: center; width: var(--sent-28); height: var(--sent-28); border: var(--sent-2) solid var(--card-line); border-radius: 50%; background: var(--surface); color: var(--success); }
.sent-step-dot .icon { width: var(--sent-16); height: var(--sent-16); stroke-width: 2.6; }
.sent-steps .done .sent-step-dot { border-color: var(--success); }
.sent-steps .current .sent-step-dot { border-color: var(--primary-graphic); background: var(--primary-soft); }
.sent-steps .current .sent-step-dot::after { content: ""; width: 10px; height: 10px; border-radius: 50%; background: var(--primary-graphic); }
.sent-step-label { margin-top: var(--sent-8); font-size: var(--sent-14); line-height: var(--sent-18); font-weight: var(--weight-bold); color: var(--text); }
.sent-steps .current .sent-step-label { color: var(--primary-text); }
.sent-steps .todo .sent-step-label { color: var(--text-secondary); }
.sent-step-sub { font-size: var(--sent-13); line-height: var(--sent-16); color: var(--text-secondary); }
.sent-grid { display: grid; grid-template-columns: minmax(0, 1fr) var(--sent-280); column-gap: var(--sent-8); align-items: start; }
.sent-main { display: flex; flex-direction: column; gap: var(--sent-8); min-width: 0; }
.sent-main > .sent-card > h3, .sent-main .panel-section-head h3 { margin: 0 0 var(--space-3); font-size: var(--font-body); }
.sent-plain p { margin: 0; color: var(--peach-text); font-size: var(--font-label); }
.sent-plain .link { min-height: var(--target-min); font-weight: var(--weight-bold); }
.sent-side { display: flex; flex-direction: column; gap: var(--sent-8); }
.sent-rows { padding-bottom: 0; }
.sent-rows-bare { padding-top: 0; }
.sent-rows-bare a:first-of-type { border-top: 0; }
.sent-rows h3 { margin: 0 0 var(--space-3); font-size: var(--font-body); line-height: var(--space-6); }
.sent-rows a { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-56); margin: 0 calc(-1 * var(--sent-18-5)); padding: var(--sent-8) var(--sent-18-5); border-top: 1px solid var(--line-soft); color: var(--text); text-decoration: none; }
/* Lignes-liens d'une carte (PR 33 point 5) : ni rayon ni bordure propre, pas de soulignement ; un filet de 1 px entre
   les lignes, la dernière suit le rayon de la carte. */
.sent-rows { overflow: hidden; }
.sent-rows a { border-radius: 0; }
.sent-rows a:hover { background: var(--primary-soft); }
.sent-rows a > .icon { flex: none; color: var(--primary-text); }
.sent-row-text { flex: 1; min-width: 0; }
.sent-row-text b { display: block; font-size: var(--font-label); line-height: var(--space-5); }
.sent-row-text span { display: block; font-size: var(--sent-13); line-height: var(--space-5); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sent-history { margin-top: calc(var(--space-5) - var(--sent-8)); }
.sent-cap { margin: 0 0 var(--space-1); font-size: var(--sent-13); line-height: var(--sent-16); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.sent-history ul { margin: 0; padding: 0; list-style: none; }
.sent-history li { display: flex; gap: var(--space-4); padding: var(--space-3) 0; border-top: 1px solid var(--line-soft); }
.sent-history-date { flex: none; width: var(--sent-64); font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--text-secondary); }
.sent-history-text { flex: 1; min-width: 0; overflow-wrap: anywhere; font-size: var(--font-label); line-height: var(--space-5); }
.sent-history-detail { display: block; margin-top: var(--sent-2); font-size: var(--font-small); color: var(--text-secondary); }
/* Ordinateur (PR 28) : le bouton teinté de 44 px avec son chevron, 8 px sous l'historique. */
.sent-contacted-fold { display: inline-flex; align-items: center; gap: var(--sent-fold-gap, 6px); height: var(--target-min); min-height: var(--target-min); margin-top: var(--space-2); padding: 0 var(--sent-fold-r, 14px) 0 var(--sent-fold-l, 18px); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.sent-contacted-fold .icon { width: 20px; height: 20px; }
.sent-contacts-all { display: flex; align-items: center; min-height: var(--target-min); font-size: var(--font-small); font-weight: var(--weight-bold); }
.sent-contacted { min-height: var(--target-min); margin-top: var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); }
.sent-status-choices { display: flex; flex-direction: column; margin: 0; padding: 0; border: 0; }
.sent-status-choices label { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-56); border-top: 1px solid var(--line-soft); font-size: var(--font-label); font-weight: var(--weight-semibold); }
/* Écran moyen (1024 à 1279 px) : la colonne de droite passe sous la colonne principale, pour garder des lignes lisibles. */
@media (max-width: 1279px) {
  .sent-grid { grid-template-columns: minmax(0, 1fr); row-gap: var(--sent-8); }
}
/* Téléphone (EnvoyeeDetail, §8.3) : barre de 56 « ‹ Envoyées » et « … », marges de 20, 12 px entre les cartes, titre
   22/28 800, mots à 20 px du titre ; carte de deux lignes de 72 à chevron gris ; Historique 8 px plus bas. */
.sent-detail-phone { --sent-72-row: 72px; --sent-22: 22px; --sent-28-line: 28px; gap: var(--space-3); padding: 0 var(--space-5) var(--space-8); }
.sent-screen-top { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; justify-content: space-between; height: var(--sent-56); margin: 0 calc(-1 * var(--space-3)); padding: 0 var(--space-2) 0 0; background: var(--bg); }
.sent-screen-back { display: inline-flex; align-items: center; gap: 0; min-height: var(--target-min); padding: 0 var(--space-3) 0 var(--space-1); border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold); }
.sent-detail-phone .sent-head { padding: var(--sent-18-5) var(--sent-18-5) var(--sent-22-5); }
.sent-detail-phone .sent-head-title h1 { margin: 0; font-size: var(--sent-22); line-height: var(--sent-28-line); font-weight: var(--weight-heavy); }
.sent-detail-phone .sent-head-title p { margin: 0; line-height: var(--space-5); }
.sent-detail-phone .sent-words { margin-top: var(--space-5); padding-left: 0; }
.sent-detail-phone .sent-grid { grid-template-columns: minmax(0, 1fr); }
.sent-detail-phone .sent-main { gap: var(--space-3); }
.sent-links { display: flex; flex-direction: column; padding: 0; overflow: hidden; }
.sent-links button { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-72-row); padding: var(--space-3) var(--sent-18-5); border: 0; background: none; color: var(--text); font: inherit; text-align: left; }
.sent-links button + button { border-top: 1px solid var(--line-soft); }
.sent-links .sent-row-text b { font-size: var(--font-body); line-height: var(--space-6); }
.sent-links .sent-row-text span { margin-top: var(--space-1); font-size: var(--font-small); }
.sent-links button > .icon { flex: none; color: var(--text-secondary); }
.sent-detail-phone .sent-history { margin-top: var(--space-2); }
.sent-sheet-help { margin: 0 0 var(--space-4); font-size: var(--font-label); line-height: var(--sent-22); color: var(--text-secondary); }
</style>
