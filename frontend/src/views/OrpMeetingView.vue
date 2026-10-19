<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import CopyLabel from "../components/CopyLabel.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import MoreMenu from "../components/MoreMenu.vue";
import OrpOutcomeForm from "../components/OrpOutcomeForm.vue";
import HoverNote from "../components/HoverNote.vue";
import { plural } from "../format";

// Le rendez-vous ORP (docs/83) : la feuille pour le conseiller, tirée de tes données, sans IA.
// Rien n'est envoyé à l'ORP : tu la télécharges, l'imprimes ou la lis toi-même.
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const page = ref<Page | null>(null);
const failed = ref(false);
const editing = ref(false);
const when = ref("");
const place = ref("");
const advisor = ref("");
const custom = ref("");
const name = ref("");
const message = ref("");
// Le rendez-vous dont on note ce qui a été convenu (0.67.2).
const noting = ref<number | null>(null);
const writing = ref(false);
const writeMessage = ref("");
const copied = ref(false);

const meeting = computed(() => page.value?.meeting ?? null);
const prep = computed(() => page.value?.preparation ?? null);
const dateFormat = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" });
const timeFormat = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit" });
const meetingText = computed(() => {
  if (!meeting.value) return "";
  const at = new Date(meeting.value.starts_at);
  const where = meeting.value.place ? `, ${meeting.value.place}` : "";
  const who = meeting.value.advisor ? ` avec ${meeting.value.advisor}` : "";
  return `Le ${dateFormat.format(at)} à ${timeFormat.format(at)}${where}${who}.`;
});
const started = computed(() => !!meeting.value && new Date(meeting.value.starts_at) <= new Date());

function dayText(iso: string): string {
  const at = new Date(iso);
  return `${dateFormat.format(at)} à ${timeFormat.format(at)}`;
}

// Ce qui a été convenu, en lignes courtes : pour le prochain rendez-vous et le carnet.
function agreed(item: Meeting): { label: string; text: string }[] {
  const lines: { label: string; text: string }[] = [];
  if (item.agreed_target) lines.push({ label: "Objectif", text: `${item.agreed_target} candidatures par mois` });
  if (item.measures.length) lines.push({ label: "Mesures", text: item.measures.map((m) => m.text).join(", ") });
  if (item.assignments) lines.push({ label: "Assignations", text: item.assignments });
  if (item.next_starts_at) lines.push({ label: "Rendez-vous suivant", text: dayText(item.next_starts_at) });
  if (item.note) lines.push({ label: "Note", text: item.note });
  return lines;
}

function outcomeSaved(data: Page): void {
  page.value = data;
  noting.value = null;
}

async function writeSheet(): Promise<void> {
  writing.value = true;
  writeMessage.value = "";
  copied.value = false;
  try {
    const { data, error } = await api.POST("/api/orp-meeting/redaction");
    if (data) page.value = data;
    else writeMessage.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible de rédiger pour l'instant.";
  } finally {
    writing.value = false;
  }
}

async function copySheet(): Promise<void> {
  if (!meeting.value?.sheet_text) return;
  try {
    await navigator.clipboard.writeText(meeting.value.sheet_text);
    copied.value = true;
  } catch {
    copied.value = false;
  }
}

const sheetLink = computed(() => {
  const who = name.value.trim();
  return `/api/orp-meeting/feuille.pdf${who ? `?name=${encodeURIComponent(who)}` : ""}`;
});

// <input type="datetime-local"> : l'heure de l'ordinateur, sans fuseau.
function localInput(iso: string): string {
  const at = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${at.getFullYear()}-${pad(at.getMonth() + 1)}-${pad(at.getDate())}T${pad(at.getHours())}:${pad(at.getMinutes())}`;
}

function startEditing(): void {
  when.value = meeting.value ? localInput(meeting.value.starts_at) : "";
  place.value = meeting.value?.place ?? "";
  advisor.value = meeting.value?.advisor ?? "";
  editing.value = true;
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/orp-meeting");
  if (data) page.value = data;
  else failed.value = true;
}

async function saveMeeting(): Promise<void> {
  if (!when.value) return;
  const { data } = await api.PUT("/api/orp-meeting", {
    body: { starts_at: new Date(when.value).toISOString(), place: place.value, advisor: advisor.value },
  });
  if (data) {
    page.value = data;
    editing.value = false;
  }
}

async function removeMeeting(): Promise<void> {
  const { data } = await api.DELETE("/api/orp-meeting");
  if (data) page.value = data;
}

async function saveQuestions(questions: Question[]): Promise<void> {
  const { data, error } = await api.PUT("/api/orp-meeting/questions", { body: { questions } });
  if (data) {
    page.value = data;
    message.value = "";
  } else {
    message.value = (error as { detail?: string } | undefined)?.detail ?? "Impossible d'enregistrer pour l'instant.";
  }
}

function toggle(question: Question, checked: boolean): void {
  if (!prep.value) return;
  void saveQuestions(prep.value.questions.map((q) => (q.key === question.key ? { ...q, checked } : q)));
}

function addQuestion(): void {
  const text = custom.value.trim();
  if (!text || !prep.value) return;
  void saveQuestions([...prep.value.questions, { key: `custom:${Date.now()}`, text, checked: true }]);
  custom.value = "";
}

const meetingItems = computed(() => [
  { label: "Modifier", test: "meeting-edit", run: startEditing },
  { label: "Supprimer", test: "meeting-delete", run: () => void removeMeeting(), danger: true },
]);

onMounted(() => void load());
</script>

<template>
  <section class="jobs-body orp-meeting">
    <p
      v-if="failed"
      class="notice error"
    >
      Impossible de préparer le rendez-vous pour l'instant.
    </p>
    <LoadingBlocks v-else-if="!page" />
    <template v-else>
      <p class="muted orp-meeting-intro">
        Une feuille pour ton conseiller. Rien n'est envoyé à l'ORP.
      </p>

      <div
        class="form-card"
        data-test="meeting"
      >
        <div class="orp-meeting-when">
          <h2>Le prochain rendez-vous</h2>
          <MoreMenu
            v-if="meeting && !editing"
            :items="meetingItems"
            label="Actions sur le rendez-vous"
            test-id="meeting-more"
          />
        </div>
        <p
          v-if="meeting && !editing"
          data-test="meeting-when"
        >
          {{ meetingText }}
        </p>
        <template v-if="meeting && started && !editing">
          <OrpOutcomeForm
            v-if="noting === meeting.id"
            :meeting="meeting"
            :target="page.target"
            :trainings="page.trainings"
            @saved="outcomeSaved"
            @cancel="noting = null"
          />
          <template v-else>
            <dl
              v-if="meeting.outcome_at"
              class="orp-agreed"
              data-test="meeting-agreed"
            >
              <template
                v-for="line in agreed(meeting)"
                :key="line.label"
              >
                <dt>{{ line.label }}</dt>
                <dd>{{ line.text }}</dd>
              </template>
            </dl>
            <div class="form-actions">
              <button
                type="button"
                :class="{ secondary: !!meeting.outcome_at }"
                data-test="meeting-outcome"
                @click="noting = meeting.id"
              >
                {{ meeting.outcome_at ? "Modifier ce qui a été convenu" : "Noter ce qui a été convenu" }}
              </button>
            </div>
          </template>
        </template>
        <form
          v-else-if="editing || !meeting"
          class="orp-meeting-form"
          data-test="meeting-form"
          @submit.prevent="saveMeeting"
        >
          <label>
            Date et heure
            <input
              v-model="when"
              type="datetime-local"
              required
              data-test="meeting-at"
            >
          </label>
          <label>
            Lieu (facultatif)
            <input
              v-model="place"
              type="text"
              maxlength="200"
              placeholder="ORP de Lausanne, ou visio"
            >
          </label>
          <label>
            Conseiller (facultatif)
            <input
              v-model="advisor"
              type="text"
              maxlength="120"
            >
          </label>
          <div class="form-actions">
            <button
              type="submit"
              data-test="meeting-save"
            >
              Enregistrer
            </button>
            <button
              v-if="editing"
              type="button"
              class="secondary"
              @click="editing = false"
            >
              Annuler
            </button>
          </div>
        </form>
      </div>

      <div
        v-if="prep"
        class="orp-meeting-sheet"
      >
        <section
          class="form-card"
          data-test="sheet-summary"
        >
          <h2>Mois en bref</h2>
          <p
            v-for="line in prep.summaries"
            :key="line"
          >
            {{ line }}
          </p>
        </section>

        <section
          class="form-card"
          data-test="sheet-blockers"
        >
          <h2>Ce qui bloque</h2>
          <ul v-if="prep.blockers.length">
            <li
              v-for="line in prep.blockers"
              :key="line"
            >
              {{ line }}
            </li>
          </ul>
          <p
            v-else
            class="muted"
          >
            Rien de net pour l'instant : pas assez de candidatures sans réponse pour conclure.
          </p>
          <p
            v-if="prep.works"
            class="orp-meeting-works"
          >
            Ce qui marche : {{ prep.works }}
          </p>
        </section>

        <section
          class="form-card"
          data-test="sheet-missing"
        >
          <h2>Ce qui revient dans les offres et te manque</h2>
          <ul v-if="prep.missing.length">
            <li
              v-for="item in prep.missing"
              :key="item.skill"
            >
              <strong>{{ item.skill }}</strong> : demandé dans {{ item.count }} des
              {{ plural(prep.offers, "offre bien notée", "offres bien notées") }} des 3 derniers mois.
              <RouterLink
                v-if="item.training_title"
                to="/formations"
              >
                {{ item.training_title }}
              </RouterLink>
            </li>
          </ul>
          <p
            v-else
            class="muted"
          >
            Rien qui revienne assez souvent (au moins 3 offres bien notées) pour en faire un argument.
          </p>
        </section>

        <section
          class="form-card"
          data-test="sheet-questions"
        >
          <h2>Questions au conseiller</h2>
          <p
            v-if="!meeting"
            class="hint"
          >
            Indique d'abord la date du rendez-vous : tes questions lui seront rattachées.
          </p>
          <ul class="orp-meeting-questions">
            <li
              v-for="question in prep.questions"
              :key="question.key"
            >
              <label>
                <input
                  type="checkbox"
                  :checked="question.checked"
                  :disabled="!meeting"
                  :data-test="`question-${question.key}`"
                  @change="toggle(question, ($event.target as HTMLInputElement).checked)"
                >
                {{ question.text }}
              </label>
            </li>
          </ul>
          <form
            v-if="meeting"
            class="inline-field"
            @submit.prevent="addQuestion"
          >
            <input
              v-model="custom"
              type="text"
              maxlength="300"
              placeholder="Une autre question"
              aria-label="Une autre question"
              data-test="question-new"
            >
            <button
              type="submit"
              class="secondary"
            >
              Ajouter
            </button>
          </form>
          <p
            v-if="message"
            role="status"
            class="notice error"
          >
            {{ message }}
          </p>
          <p class="hint">
            Sur tes droits, c'est ton conseiller qui répond.
          </p>
        </section>

        <section
          class="form-card"
          data-test="sheet-obligations"
        >
          <h2>Obligations et échéances</h2>
          <ul class="orp-meeting-duties">
            <li
              v-for="item in prep.obligations"
              :key="item.text"
              :class="{ done: item.done }"
            >
              {{ item.done ? "Fait : " : "" }}{{ item.text }}
            </li>
          </ul>
        </section>

        <section
          class="form-card"
          data-test="sheet-download"
        >
          <h2>La feuille</h2>
          <label>
            Ton nom sur la feuille (facultatif)
            <input
              v-model="name"
              type="text"
              maxlength="120"
              autocomplete="name"
            >
          </label>
          <div class="form-actions">
            <a
              class="button-link"
              :href="sheetLink"
              download
              data-test="sheet-pdf"
            >Télécharger la feuille (PDF)</a>
          </div>
        </section>

        <section
          v-if="meeting"
          class="form-card"
          data-test="sheet-ai"
        >
          <h2>Le message pour ton conseiller</h2>
          <p
            v-if="meeting.sheet_text"
            class="orp-sheet-text"
            data-test="sheet-text"
          >
            {{ meeting.sheet_text }}
          </p>
          <p
            v-else
            class="muted"
          >
            L'IA rédige la feuille en un message suivi, à envoyer avant le rendez-vous.
          </p>
          <div class="form-actions">
            <button
              type="button"
              :class="{ secondary: !!meeting.sheet_text }"
              :disabled="writing"
              data-test="sheet-write"
              @click="writeSheet"
            >
              <HoverNote text="Environ 0,02 CHF.">
                {{ writing ? "Rédaction…" : meeting.sheet_text ? "Rédiger à nouveau" : "Rédiger avec l'IA" }}
              </HoverNote>
            </button>
            <button
              v-if="meeting.sheet_text"
              type="button"
              class="link"
              @click="copySheet"
            >
              <CopyLabel :done="copied" />
            </button>
          </div>
          <p
            v-if="writeMessage"
            role="status"
            class="notice error"
          >
            {{ writeMessage }}
          </p>
          <p class="hint">
            Ni ton nom, ni le lieu, ni ton conseiller ne partent à l'IA.
          </p>
        </section>
      </div>

      <section
        v-if="page.past.length"
        class="form-card orp-log"
        data-test="meeting-log"
      >
        <h2>Le carnet</h2>
        <ul>
          <li
            v-for="item in page.past"
            :key="item.id"
          >
            <h3>{{ dayText(item.starts_at) }}<span v-if="item.place"> · {{ item.place }}</span></h3>
            <OrpOutcomeForm
              v-if="noting === item.id"
              :meeting="item"
              :target="page.target"
              :trainings="page.trainings"
              @saved="outcomeSaved"
              @cancel="noting = null"
            />
            <template v-else>
              <dl
                v-if="item.outcome_at"
                class="orp-agreed"
              >
                <template v-if="item.asked.length">
                  <dt>Questions</dt>
                  <dd>{{ item.asked.join(" · ") }}</dd>
                </template>
                <template
                  v-for="line in agreed(item)"
                  :key="line.label"
                >
                  <dt>{{ line.label }}</dt>
                  <dd>{{ line.text }}</dd>
                </template>
              </dl>
              <button
                type="button"
                :class="item.outcome_at ? 'link' : 'secondary small'"
                :data-test="`log-outcome-${item.id}`"
                @click="noting = item.id"
              >
                {{ item.outcome_at ? "Modifier" : "Noter ce qui a été convenu" }}
              </button>
            </template>
          </li>
        </ul>
      </section>
    </template>
  </section>
</template>
