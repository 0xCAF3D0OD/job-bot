<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from "vue";

import { api, type Application, type ApplicationStatus, type ContactsPage, type Interview, type OrpRow } from "../api/client";
import { followUpDue, noAnswerDue } from "../applicationState";
import { useAssistant } from "../composables/useAssistant";
import { applicationStatusLabel, companyPlace } from "../format";
import { orpTodo as orpTodoOf, phoneSteps as stepsOnPhone, sentHistory, sentSteps, sentWords } from "../sentDetail";
import AppIcon from "./AppIcon.vue";
import ApplicationInterviews from "./ApplicationInterviews.vue";
import NewMeetingSheet from "./NewMeetingSheet.vue";
import ContactQuickForm from "./ContactQuickForm.vue";
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

const words = computed(() => sentWords(props.application, props.orpRow));
const steps = computed(() => sentSteps(props.application, props.orpRow));
const history = computed(() => sentHistory(props.application, props.orpRow));
const followUp = computed(() => followUpDue(props.application));
const hasInterviews = computed(
  () => props.application.status === "entretien" || !!props.application.interview_at || !!props.application.interviews?.length,
);
// Plus de carte « Pour l'ORP » (Kevin, 18.11, points 9 et 10) : l'état ORP est sur la ligne d'état de l'en-tête, et le
// rappel télétravail à l'étranger garde sa petite carte.
const remoteAbroad = computed(
  () => props.application.remote_full && !/suisse|switzerland|schweiz/i.test(props.application.remote_region ?? ""),
);
const orpTodo = computed(() => orpTodoOf(props.orpRow));
// « À déclarer à l’ORP › » et « À compléter pour l’ORP › » ouvrent la fiche ORP de la candidature, au mois de sa date
// (« 02.11.2026 » donne 2026-11), qui dit aussi ce qui manque. La frise de 4 étapes ; le trait vert va jusqu’à l’étape en cours.
const ficheTo = computed(() => {
  const [, m, y] = (props.orpRow?.date ?? "").split(".");
  return { path: `/bilan/orp/candidature/${props.application.id}`, query: m && y ? { mois: `${y}-${m}` } : {} };
});
const phoneSteps = computed(() => stepsOnPhone(props.application));
const phoneReach = computed(() => {
  const current = phoneSteps.value.findIndex((s) => s.state === "current");
  return current >= 0 ? current : phoneSteps.value.map((s) => s.state).lastIndexOf("done");
});

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
// Ordinateur (§8 point 4) : la ligne « Historique » dit le nombre d’étapes et la dernière ; elle déplie la liste,
// « J’ai contacté quelqu’un » et les prises de contact, dans la même carte.
const historyOpen = ref(false);
const historySummary = computed(() => {
  const n = history.value.length;
  const last = history.value[0];
  if (!last) return "";
  return `${n} ${n > 1 ? "étapes" : "étape"} · dernière le ${last.date}, ${last.title.charAt(0).toLowerCase()}${last.title.slice(1)}`;
});
watch(
  () => props.application.id,
  () => {
    historyOpen.value = false;
  },
);
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
// Les contacts (et leurs choix « Écrire à », « Canal ») chargés à l’ouverture, pas avec Suivi (règle du poids, audit
// du 17.11) : le panneau attend déjà sa liste du serveur avant de s’afficher.
const ContactsPanel = defineAsyncComponent(() => import("./ContactsPanel.vue"));
</script>

<template>
  <div
    :class="['sent-detail-cards', { 'sent-detail-phone': phone }]"
    data-test="application-panel"
  >
    <!-- Téléphone (EnvoyeeDetail du 14 novembre, §6) : l’écran poussé a sa barre, flèche de retour puis « Candidature »,
         et « … », sans barre d’onglets ; la flèche de 24 px dans un bouton de 48, couleur du texte. -->
    <header
      v-if="phone"
      class="sent-screen-top"
    >
      <div class="sent-screen-title">
        <button
          type="button"
          class="sent-screen-back"
          aria-label="Retour aux envoyées"
          data-test="sent-back"
          @click="emit('close')"
        >
          <AppIcon name="arrow-left" />
        </button>
        <span>Candidature</span>
      </div>
      <MoreMenu
        :items="menuItems"
        label="Plus d’options"
        test-id="panel-more"
      />
    </header>
    <!-- Ordinateur (maquette du 14 novembre, §8 Envoyées) : une colonne de cartes empilées, 16 px entre elles. 1. titre ;
         2. le suivi en 5 colonnes égales ; 3. la relance conseillée (ou l’état et les cartes Entretien et ORP) ;
         4. Documents et contacts en deux colonnes, puis la ligne « Historique ». -->
    <template v-if="!phone">
      <header
        class="sd-title"
        data-test="sent-title-card"
      >
        <div class="sent-head-top">
          <div class="sent-head-title">
            <h2 data-test="panel-title">
              {{ application.job_title }}
            </h2>
            <p>{{ companyPlace(application.company, application.location) }}</p>
          </div>
          <MoreMenu
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
          <RouterLink
            v-if="orpTodo"
            :to="ficheTo"
            :class="['sent-orp-todo', orpTodo.tone]"
            :data-test="orpTodo.test"
          >
            {{ orpTodo.text }}<AppIcon name="chevron" />
          </RouterLink>
        </p>
      </header>
      <div class="sent-card sd-steps-card">
        <ol
          class="sent-steps sd-steps"
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
      <FollowUpCard
        v-if="followUp"
        :application="application"
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
      <p
        v-if="remoteAbroad"
        class="sent-card sd-remote"
        data-test="remote-orp"
      >
        Employeur à l’étranger ? Vérifie le contrat et les assurances avec ton conseiller.
      </p>
      <section
        class="sent-card sd-docs"
        aria-label="Documents et contacts"
        data-test="sent-docs-card"
      >
        <div
          v-if="sentRows.length || findRows.length"
          class="sd-docs-cols"
        >
          <SentRows
            v-if="sentRows.length"
            title="Ce que tu as envoyé"
            :rows="sentRows"
            flat
            data-test="section-documents"
          />
          <SentRows
            v-if="findRows.length"
            title="Trouver un contact"
            :rows="findRows"
            flat
            data-test="section-contacts"
          />
        </div>
        <button
          type="button"
          class="sd-history-row"
          :aria-expanded="historyOpen"
          aria-controls="sent-history-zone"
          data-test="sent-history-open"
          @click="historyOpen = !historyOpen"
        >
          <span class="sent-row-text"><b>Historique</b><span>{{ historySummary }}</span></span>
          <AppIcon name="chevron" />
        </button>
        <section
          v-show="historyOpen"
          id="sent-history-zone"
          class="sent-history sd-history"
          aria-label="Historique"
          data-test="sent-history"
        >
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
      </section>
    </template>
    <!-- Téléphone, refait d’après la planche EnvoyeeDetail (+Sombre) du 18.11 : 1. la carte du haut (poste, entreprise,
         la ligne d’état avec l’état ORP, la frise Envoyée, Réponse, Entretien, Décision, §40) ; 2. la relance
         conseillée ou l’entretien ; 3. une carte « Ce que tu as envoyé / Trouver un contact », lignes séparées d’un
         trait de 1 px ; 4. « Historique » replié, puis « J’ai contacté quelqu’un ». Plus de carte « Pour l’ORP ». -->
    <template v-else>
      <section
        class="sdt-head"
        aria-labelledby="sdt-title"
        data-test="sent-title-card"
      >
        <div class="sent-head-title">
          <h1
            id="sdt-title"
            data-test="panel-title"
          >
            {{ application.job_title }}
          </h1>
          <p>{{ companyPlace(application.company, application.location) }}</p>
        </div>
        <p
          class="sdt-words"
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
          <RouterLink
            v-if="orpTodo"
            :to="ficheTo"
            :class="['sent-orp-todo', orpTodo.tone]"
            :data-test="orpTodo.test"
          >
            {{ orpTodo.text }}<AppIcon name="chevron" />
          </RouterLink>
        </p>
        <ol
          class="sdt-steps"
          aria-label="Étapes de la candidature"
          data-test="sent-steps"
        >
          <span
            class="sdt-track"
            aria-hidden="true"
          />
          <span
            class="sdt-track on"
            :style="{ width: `${25 * phoneReach}%` }"
            aria-hidden="true"
          />
          <li
            v-for="step in phoneSteps"
            :key="step.label"
            :class="step.state"
            :aria-current="step.state === 'current' ? 'step' : undefined"
          >
            <span
              class="sdt-dot"
              aria-hidden="true"
            ><AppIcon
              v-if="step.state === 'done'"
              name="done"
            /></span>
            <span class="sdt-step-label">{{ step.label }}<span class="visually-hidden">{{ step.state === "done" ? " (faite)" : step.state === "current" ? " (en cours)" : "" }}</span></span>
          </li>
        </ol>
      </section>
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
      <!-- Pas sur la planche : le rappel télétravail à l’étranger (docs/26 §6), gardé seul en attendant la décision de Kevin. -->
      <p
        v-if="remoteAbroad"
        class="sent-card sdt-remote"
        data-test="remote-orp"
      >
        Employeur à l’étranger ? Vérifie le contrat et les assurances avec ton conseiller.
      </p>
      <section
        v-if="sentRows.length || findRows.length"
        class="sdt-links"
        aria-label="Documents et contacts"
      >
        <button
          v-if="sentRows.length"
          type="button"
          data-test="sent-docs-open"
          @click="docsOpen = true"
        >
          <span class="sdt-link-text"><b>Ce que tu as envoyé</b><span>{{ sentSummary }}</span></span>
          <AppIcon name="chevron" />
        </button>
        <button
          v-if="findRows.length"
          type="button"
          data-test="sent-find-open"
          @click="findOpen = true"
        >
          <span class="sdt-link-text"><b>Trouver un contact</b><span>{{ findSummary }}</span></span>
          <AppIcon name="chevron" />
        </button>
      </section>
      <section
        class="sdt-history"
        aria-label="Historique"
      >
        <button
          type="button"
          class="sdt-history-row"
          :aria-expanded="historyOpen"
          aria-controls="sdt-history-list"
          data-test="sent-history-open"
          @click="historyOpen = !historyOpen"
        >
          <span class="sdt-link-text"><b>Historique</b><span>{{ historySummary }}</span></span>
          <AppIcon name="chevron-down" />
        </button>
        <ul
          v-show="historyOpen"
          id="sdt-history-list"
          data-test="sent-history"
        >
          <li
            v-for="(event, i) in history"
            :key="i"
          >
            <span class="sdt-history-date">{{ event.date }}</span>
            <span class="sdt-history-text">{{ event.title }}<span
              v-if="event.detail"
              class="sdt-history-detail"
            >{{ event.detail }}</span></span>
          </li>
        </ul>
        <button
          type="button"
          class="link sdt-contacted"
          aria-haspopup="dialog"
          data-test="contacted-open"
          @click="contactedOpen = true"
        >
          J’ai contacté quelqu’un<AppIcon name="chevron" />
        </button>
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
    </template>
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
.sent-detail-cards { --sent-8: 8px; --sent-18-5: 18.5px; --sent-22-5: 22.5px; --sent-56: 56px; --sent-72: 72px; --sent-19: 19px; --sent-30: 30px; --sent-28: 28px; --sent-14: 14px; --sent-13: 13px; --sent-16: 16px; --sent-18: 18px; --sent-2: 2px; --sent-64: 64px; display: flex; flex-direction: column; gap: var(--sent-8); }
.sent-card { padding: var(--sent-18-5); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.sent-head-top { display: flex; align-items: flex-start; gap: var(--space-4); }
.sent-head-title { flex: 1; min-width: 0; }
.sent-head-title h2 { margin: 0; font-size: var(--space-6); line-height: var(--sent-30); font-weight: var(--weight-heavy); }
.sent-head-title p { margin: var(--space-1) 0 0; font-size: var(--font-label); line-height: normal; color: var(--text-secondary); }
.sent-words { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-4); margin: calc(-1 * var(--space-1)) 0 0; font-size: var(--font-label); line-height: var(--space-5); font-weight: var(--weight-bold); }
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
.sent-detail-phone > .sent-card > h3, .sent-detail-phone .panel-section-head h3 { margin: 0 0 var(--space-3); font-size: var(--font-body); }
.sent-plain p { margin: 0; color: var(--peach-text); font-size: var(--font-label); }
.sent-plain .link { min-height: var(--target-min); font-weight: var(--weight-bold); }
.sent-rows h3 { margin: 0 0 var(--space-3); font-size: var(--font-body); line-height: var(--space-6); }
.sent-rows a { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-56); margin: 0 calc(-1 * var(--sent-18-5)); padding: var(--sent-8) var(--sent-18-5); border-top: 1px solid var(--line-soft); border-radius: 0; color: var(--text); text-decoration: none; }
/* Lignes-liens d'une carte (PR 33 point 5) : ni rayon ni bordure propre, pas de soulignement ; un filet de 1 px entre
   les lignes, la dernière suit le rayon de la carte. */
.sent-rows { padding-bottom: 0; overflow: hidden; }
.sent-rows a:hover { background: var(--primary-soft); }
.sent-rows a > .icon { flex: none; color: var(--primary-text); }
/* Dans une feuille (§45 du 17.11) : plus de carte, des lignes simples de 64 px ; un trait #E5E2D9 au-dessus de chaque ligne et sous la dernière. */
.sent-rows-bare { border-bottom: 1px solid var(--line); }
.sent-rows-bare a { min-height: var(--sent-64); margin: 0; padding: var(--space-3) var(--space-1); border-top-color: var(--line); }
.sent-row-text { flex: 1; min-width: 0; }
.sent-row-text b { display: block; font-size: var(--font-label); line-height: var(--space-5); }
.sent-row-text span { display: block; font-size: var(--sent-13); line-height: var(--space-5); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sent-history { margin-top: calc(var(--space-5) - var(--sent-8)); }
.sent-history ul { margin: 0; padding: 0; list-style: none; }
.sent-history li { display: flex; gap: var(--space-4); padding: var(--space-3) 0; border-top: 1px solid var(--line-soft); }
.sent-history-date { flex: none; width: var(--sent-64); font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--text-secondary); }
.sent-history-text { flex: 1; min-width: 0; overflow-wrap: anywhere; font-size: var(--font-label); line-height: var(--space-5); }
.sent-history-detail { display: block; margin-top: var(--sent-2); font-size: var(--font-small); color: var(--text-secondary); }
/* Ordinateur (PR 28) : le bouton teinté de 44 px avec son chevron, 8 px sous l'historique. */
.sent-contacted-fold { display: inline-flex; align-items: center; gap: var(--space-2); height: var(--target-min); min-height: var(--target-min); margin-top: var(--space-2); padding: 0 var(--space-3) 0 var(--space-4); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); }
.sent-contacted-fold .icon { width: 20px; height: 20px; }
.sent-contacts-all { display: flex; align-items: center; min-height: var(--target-min); font-size: var(--font-small); font-weight: var(--weight-bold); }
.sent-status-choices { display: flex; flex-direction: column; margin: 0; padding: 0; border: 0; }
.sent-status-choices label { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sent-56); border-top: 1px solid var(--line-soft); font-size: var(--font-label); font-weight: var(--weight-semibold); }
/* Ordinateur, maquette du 14 novembre (§8 Envoyées, §9) : 16 px entre les cartes ; le suivi seul dans sa carte, 5 colonnes
   égales, cercle et libellés centrés ; Documents et contacts en deux colonnes séparées d’un filet de 1 px, lignes de
   64 px au moins (12 px en haut et en bas), puis la ligne « Historique » à chevron. */
.sent-detail-cards:not(.sent-detail-phone) { gap: var(--space-4); }
/* §18 du 15 novembre : la tête en carte, 24 px sous le haut de la zone, marges 22 / 28 / 22 / 24 sur la planche, 22,5 en haut et en bas ici (la règle de grille compte 1,5 px de trait), rayon 24. */
.sd-title {
  --sent-pad-y: 22.5px; display: flex; flex-direction: column; gap: var(--space-4); margin-top: var(--space-6); padding: var(--sent-pad-y) var(--sent-28) var(--sent-pad-y) var(--space-6);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--space-6);
}
.sd-steps-card { padding: var(--space-5) var(--space-6); border-width: 1px; border-color: var(--line); border-radius: var(--space-6); }
.sd-steps { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); margin: 0; padding: 0; }
.sd-steps > li, .sd-steps > li:last-child { flex: none; align-items: center; text-align: center; }
.sd-steps .sent-step-line { left: calc(50% + var(--sent-28) / 2 + var(--sent-8)); right: calc(-50% + var(--sent-28) / 2 + var(--sent-8)); }
.sd-docs { padding: var(--sent-18-5) 0 0; overflow: hidden; }
.sd-docs-cols { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border-bottom: 1px solid var(--line); }
.sd-docs-cols > .sent-rows + .sent-rows { border-left: 1px solid var(--line); }
.sd-docs .sent-rows h3 { --sd-22: 22px; margin: 0; padding: 0 var(--space-6) var(--space-3); font-size: var(--font-body); line-height: var(--sd-22); }
.sd-docs .sent-rows a { box-sizing: border-box; min-height: var(--sent-64); margin: 0; padding: var(--space-3) var(--space-6); border-top-color: var(--line); }
.sd-history-row { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; width: 100%; min-height: var(--sent-64); padding: var(--space-3) var(--space-6); border: 0; border-radius: 0; background: none; color: var(--text); font: inherit; text-align: left; }
.sd-history-row:hover { background: var(--primary-soft); }
/* Le chevron tourne d'un quart à l'ouverture (décision de Kevin du 15.11) ; --t-fast passe à 0 si l'appareil demande moins d'animations. */
.sd-history-row > .icon { flex: none; color: var(--primary-text); transition: rotate var(--t-fast); }
.sd-history-row[aria-expanded="true"] > .icon { rotate: 90deg; }
.sd-history { margin: 0; padding: 0 var(--space-6) var(--space-4); }
/* Téléphone (EnvoyeeDetail, §8.3 ; retour du 14 novembre, §6) : barre de 56 « ← Candidature » et « … », marges de 20, 12 px entre les cartes, titre
   22/28 800, mots à 20 px du titre ; carte de deux lignes de 72 à chevron gris ; Historique 8 px plus bas. */
.sent-detail-phone { --sent-72-row: 72px; --sent-22: 22px; --sent-28-line: 28px; gap: var(--space-3); padding: 0 var(--space-5) var(--space-8); }
.sent-screen-top { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; justify-content: space-between; height: var(--sent-56); margin: 0 calc(-1 * var(--space-3)); padding: 0 var(--space-2) 0 0; background: var(--bg); }
.sent-screen-title { --sent-48: 48px; --sent-17: 17px; display: flex; align-items: center; gap: var(--space-1); font-size: var(--sent-17); font-weight: var(--weight-bold); }
.sent-screen-back { display: inline-flex; align-items: center; justify-content: center; width: var(--sent-48); height: var(--sent-48); min-height: var(--sent-48); padding: 0; border: 0; border-radius: 50%; background: none; color: var(--text); }
.sent-screen-back .icon { width: 24px; height: 24px; }
/* Téléphone, planche EnvoyeeDetail (HTML) : 12 px entre les cartes. Carte du haut : marges 18,5 / 18,5 / 22,5, trait
   1,5 --card-line, rayon 18, 20 px entre ses blocs ; titre 22/28 800, entreprise 15/20 à 2 px ; ligne d’état 15/20 gras,
   16 px entre les mots ; frise : trait 1 px au-dessus, 16 px, ronds de 24 (fait : vert plein et coche ; en cours :
   anneau orange de 3 ; à venir : anneau gris de 2), libellés 12/16. */
/* 4 px sous la barre (planche : marge haute de 4) au lieu des 12 entre les cartes. */
.sent-screen-top + .sdt-head { margin-top: calc(var(--space-1) - var(--space-3)); }
.sdt-head { display: flex; flex-direction: column; gap: var(--space-5); padding: var(--sent-18-5) var(--sent-18-5) var(--sent-22-5); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.sdt-head h1 { margin: 0; font-size: var(--sent-22); line-height: var(--sent-28-line); font-weight: var(--weight-heavy); letter-spacing: -0.2px; }
.sdt-head .sent-head-title p { margin: 0; font-size: var(--font-label); line-height: var(--space-5); color: var(--text-secondary); }
.sdt-words { display: flex; flex-wrap: wrap; align-items: center; column-gap: var(--space-4); row-gap: var(--space-1); margin: 0; font-size: var(--font-label); line-height: var(--space-5); font-weight: var(--weight-bold); }
.sdt-words > span { display: inline-flex; align-items: center; gap: var(--sent-8); }
.sdt-words .icon { width: var(--sent-16); height: var(--sent-16); stroke-width: 2.6; }
.sdt-words .peach { color: var(--peach-text); }
.sdt-words .green { color: var(--success); }
.sdt-words .grey { color: var(--text-tertiary); }
.sdt-words .muted { color: var(--text-secondary); }
/* La ligne d'état ORP qui reste à faire (Kevin, 18.11) : bleu « À déclarer », orange « À compléter » (#B4631F
   de la maquette, sombre #F2B98E : --icon-peach, le même orange que l'Accueil) ; une cible de 44 px de haut sans agrandir la ligne de 20 px. */
.sent-orp-todo { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); margin: calc((var(--space-5) - var(--target-min)) / 2) 0; text-decoration: none; }
.sent-orp-todo.blue { color: var(--primary-text); }
.sent-orp-todo.orange { color: var(--icon-peach); }
.sent-orp-todo .icon { width: var(--sent-16); height: var(--sent-16); }
.sd-remote { margin: 0; font-size: var(--font-label); line-height: var(--space-5); color: var(--text-secondary); }
.sdt-steps { --sdt-24: 24px; position: relative; display: flex; margin: 0; padding: var(--space-4) 0 0; border-top: 1px solid var(--line); list-style: none; }
.sdt-track { position: absolute; left: 12.5%; right: 12.5%; top: calc(var(--space-4) + var(--sdt-24) / 2 - 1px); height: var(--sent-2); background: var(--card-line); }
.sdt-track.on { right: auto; background: var(--success); }
.sdt-steps > li { position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; align-items: center; gap: var(--space-1); min-width: 0; }
.sdt-dot { display: flex; align-items: center; justify-content: center; box-sizing: border-box; width: var(--sdt-24); height: var(--sdt-24); border: var(--sent-2) solid var(--card-line); border-radius: 50%; background: var(--surface); }
.sdt-steps .done .sdt-dot { border: 0; background: var(--success); color: var(--surface); }
.sdt-steps .current .sdt-dot { border: 3px solid var(--peach-text); }
.sdt-dot .icon { width: var(--sent-14); height: var(--sent-14); stroke-width: 3; }
.sdt-step-label { font-size: var(--font-caption); line-height: var(--sent-16); font-weight: var(--weight-medium); color: var(--text-secondary); }
.sdt-steps .done .sdt-step-label { font-weight: var(--weight-bold); color: var(--text); }
.sdt-steps .current .sdt-step-label { font-weight: var(--weight-bold); color: var(--peach-text); }
.sdt-remote { margin: 0; font-size: var(--font-label); line-height: var(--space-5); color: var(--text-secondary); }
/* Une carte, deux lignes de 72 à chevron gris, séparées d’un trait de 1 px --line-soft ; aucune carte dans la carte. */
.sdt-links { display: flex; flex-direction: column; overflow: hidden; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.sdt-links button { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; min-height: var(--sent-72-row); margin: 0; padding: var(--space-3) var(--sent-18-5); border: 0; border-radius: 0; background: none; color: var(--text); font: inherit; text-align: left; }
.sdt-links button + button { border-top: 1px solid var(--line-soft); }
.sdt-links button > .icon, .sdt-history-row > .icon { flex: none; width: 24px; height: 24px; color: var(--text-secondary); }
.sdt-link-text { flex: 1; min-width: 0; }
.sdt-link-text b { display: block; font-size: var(--font-body); line-height: var(--sent-22); }
.sdt-link-text span { display: block; margin-top: var(--space-1); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
/* Historique : sur le crème, 8 px plus bas ; ligne de 56 entre deux traits de 1 px, résumé 13/18, chevron qui se
   retourne ; puis les étapes (date 56 px 14/20 gras, texte 15/20, détail 13/18). */
.sdt-history { margin-top: var(--sent-8); }
.sdt-history-row { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; width: 100%; min-height: var(--sent-56); margin: 0; padding: var(--space-2) 0; border: 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); border-radius: 0; background: none; color: var(--text); font: inherit; text-align: left; }
.sdt-history-row .sdt-link-text span { white-space: normal; font-size: var(--sent-13); line-height: var(--sent-18); }
.sdt-history-row > .icon { transition: rotate var(--t-fast); }
.sdt-history-row[aria-expanded="true"] > .icon { rotate: 180deg; }
.sdt-history ul { margin: 0; padding: 0; list-style: none; }
.sdt-history li { display: flex; gap: var(--space-4); padding: var(--space-3) 0; }
.sdt-history li + li { border-top: 1px solid var(--line); }
.sdt-history-date { flex: none; width: var(--sent-56); font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--text-secondary); }
.sdt-history-text { flex: 1; min-width: 0; overflow-wrap: anywhere; font-size: var(--font-label); line-height: var(--space-5); }
.sdt-history-detail { display: block; font-size: var(--sent-13); line-height: var(--sent-18); color: var(--text-secondary); }
.sdt-contacted { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); margin-top: var(--space-1); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); }
.sdt-contacted .icon { width: 20px; height: 20px; }
.sent-sheet-help { margin: 0 0 var(--space-4); font-size: var(--font-label); line-height: var(--sent-22); color: var(--text-secondary); }
</style>
