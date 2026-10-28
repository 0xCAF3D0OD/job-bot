<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import FaceState from "../components/FaceState.vue";
import Illustration from "../components/Illustration.vue";
import CopyLabel from "../components/CopyLabel.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import IconButton from "../components/IconButton.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import { usePageReady } from "../composables/usePageTransition";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import OrpOutcomeForm from "../components/OrpOutcomeForm.vue";
import HoverNote from "../components/HoverNote.vue";
import { meetingDate } from "../dates";
import { formatMonth, plural } from "../format";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// Le rendez-vous ORP (docs/83) : la feuille pour le conseiller, tirée de tes données, sans IA.
// Rien n'est envoyé à l'ORP : tu la télécharges, l'imprimes ou la lis toi-même.
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const page = ref<Page | null>(null);
usePageReady("orp-meeting", () => !!page.value);
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
// Ce qui reste à faire seulement (docs/131 §B.9) : le fait n'aide plus à décider.
function monthTitle(month: string): string {
  const name = formatMonth(month);
  return name.charAt(0).toUpperCase() + name.slice(1);
}
const pendingObligations = computed(() => (prep.value?.obligations ?? []).filter((o) => !o.done));
// Aucune candidature encore (docs/128 §3) : la feuille et le mois attendent.
const noApplications = computed(() => prep.value?.has_applications === false);
const started = computed(() => !!meeting.value && new Date(meeting.value.starts_at) <= new Date());

// Une obligation dont l'échéance est passée (décision du 25/10) : elle rejoint la conclusion.
function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}
// Sans candidature encore, pas d'alerte : les preuves d'un mois vide ne sont pas en retard.
const lateObligations = computed(() =>
  noApplications.value ? [] : pendingObligations.value.filter((o) => !!o.due && o.due < todayIso()),
);
function lateLine(text: string): string {
  const line = text.replace(" : ", ", ");
  return ` En retard : ${line.charAt(0).toLowerCase()}${line.slice(1)}`;
}
// La conclusion en haut (règles §3.2, 1.6.23) : la date, l'heure en accent, le lieu ; puis ce qui
// est en retard, en orange (ce qui demande d'agir, §4).
type Part = { text: string; strong?: boolean; late?: boolean };
const conclusion = computed<Part[]>(() => {
  const parts: Part[] = [];
  const m = meeting.value;
  if (m && !editing.value) {
    parts.push(
      { text: started.value ? "Rendez-vous du " : "Prochain rendez-vous " },
      // « à » et l'heure ne se séparent pas (espace insécable, 1.6.30).
      { text: meetingDate(m.starts_at).replace(" à ", " à\u00a0"), strong: true },
      { text: `${m.place ? `, ${m.place}` : ""}.` },
    );
  }
  for (const o of lateObligations.value) parts.push({ text: parts.length ? lateLine(o.text) : lateLine(o.text).trimStart(), late: true });
  return parts;
});
// « Préparer », à droite de la conclusion : descend à la préparation.
const prepareTitle = ref<HTMLElement | null>(null);
function goPrepare(): void {
  const reduce = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  prepareTitle.value?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
}
// Le résumé de chaque ligne du mois (règles §3.4).
const monthValue = computed(() => {
  const last = prep.value?.months?.at(-1);
  if (!last) return "";
  return last.target ? `${last.count} candidatures sur ${last.target}` : plural(last.count, "candidature", "candidatures");
});
const dutiesValue = computed(() => {
  const late = lateObligations.value.length;
  const rest = pendingObligations.value.length - late;
  const parts = [late ? `${late} en retard` : "", rest ? plural(rest, "échéance", "échéances") : ""].filter(Boolean);
  return parts.join(", ");
});

// Un rendez-vous (dates.ts) : « jeudi 29 octobre à 9 h 30 ».
function dayText(iso: string): string {
  return meetingDate(iso);
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

const meetingItems = computed<MoreMenuItem[]>(() => [
  { label: "Modifier", test: "meeting-edit", run: startEditing, icon: "pencil" },
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
      <!-- La conclusion d'abord (règles §3.2, décision du 25/10) : date, heure et lieu ; « Préparer »
           en lien et le « ⋯ » du rendez-vous à droite (dessous sur téléphone). -->
      <div
        v-if="conclusion.length"
        class="orp-conclusion"
      >
        <p
          class="offers-sentence"
          data-test="meeting-when"
        >
          <component
            :is="part.strong ? 'strong' : 'span'"
            v-for="(part, index) in conclusion"
            :key="index"
            :class="{ 'orp-late': part.late }"
          >
            {{ part.text }}
          </component>
        </p>
        <div class="orp-conclusion-actions">
          <button
            v-if="prep && !noApplications"
            type="button"
            class="link"
            data-test="go-prepare"
            @click="goPrepare"
          >
            Préparer
          </button>
          <MoreMenu
            v-if="meeting && !editing"
            :items="meetingItems"
            label="Actions sur le rendez-vous"
            test-id="meeting-more"
          />
        </div>
      </div>
      <!-- Préparer (docs/130 §B, docs/133 §4) : ce qu'on modifie, chaque carte sur toute la
           largeur pour que le texte respire : les questions, la feuille. -->
      <!-- Sans candidature, seul le formulaire du rendez-vous reste : pas de titre (1.6.24, comme Figma). -->
      <h2
        v-if="prep && !noApplications"
        ref="prepareTitle"
        class="section-title orp-section"
      >
        Préparer
      </h2>
      <div class="orp-meeting-sheet">
        <div
          v-if="!meeting || editing || started"
          class="form-card"
          data-test="meeting"
        >
          <!-- Aucun rendez-vous prévu (planche « Illustrations ») : l'illustration au-dessus du formulaire ; pas
               avec l'écran « Pas encore de candidature », une seule par écran. -->
          <Illustration
            v-if="!meeting && !editing && !noApplications"
            name="rendez-vous-vide"
            class="spot"
            sizes="(max-width: 820px) 260px, 424px"
          />
          <div class="orp-meeting-when">
            <h2>{{ meeting && started && !editing ? "Ce qui a été convenu" : meeting || editing ? "Le prochain rendez-vous" : "Aucun rendez-vous ORP prévu" }}</h2>
          </div>
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
              <!-- La seule action principale de l'écran (règles §3.3). -->
              <button
                type="submit"
                class="primary"
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
        <template v-if="prep && !noApplications">
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
              <IconButton
                type="submit"
                icon="plus"
                label="Ajouter la question"
                data-test="question-add"
              />
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
            class="form-card orp-sheet-wide"
            data-test="sheet-download"
          >
            <h2>La feuille</h2>
            <p class="setting-desc">
              Rien n'est envoyé à l'ORP : tu la télécharges, ou tu l'envoies toi-même.
            </p>
            <label class="orp-sheet-name">
              Ton nom sur la feuille (facultatif)
              <input
                v-model="name"
                type="text"
                maxlength="120"
                autocomplete="name"
              >
            </label>
            <!-- Une colonne (décision du 25/10) : la seule action principale, puis l'IA en contour. -->
            <div class="form-actions orp-sheet-actions">
              <a
                class="button-link primary-link"
                :href="sheetLink"
                download
                data-test="sheet-pdf"
              ><span class="with-icon"><AppIcon name="download" />Télécharger la feuille (PDF)</span></a>
              <button
                v-if="meeting"
                type="button"
                class="secondary"
                :disabled="writing"
                data-test="sheet-write"
                @click="writeSheet"
              >
                <HoverNote :text="aiNote('Environ 0,02 CHF.')">
                  <span class="with-icon"><AppIcon name="ai" />{{ writing ? "Rédaction…" : meeting.sheet_text ? "Rédiger à nouveau" : "Rédiger avec l'IA" }}</span>
                </HoverNote>
              </button>
              <button
                v-if="meeting?.sheet_text"
                type="button"
                class="link"
                @click="copySheet"
              >
                <CopyLabel :done="copied" />
              </button>
            </div>
            <!-- Le même contenu en message, rédigé par l'IA (docs/130 §B). -->
            <div
              v-if="meeting"
              class="orp-sheet-message"
              data-test="sheet-ai"
            >
              <p
                v-if="meeting.sheet_text"
                class="orp-sheet-text"
                data-test="sheet-text"
              >
                {{ meeting.sheet_text }}
              </p>
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
            </div>
          </section>
        </template>
      </div>
      <!-- Aucune candidature encore (docs/128 §3) : la feuille se remplira avec elles. -->
      <FaceState
        v-if="noApplications"
        title="Pas encore de candidature"
        data-test="sheet-none-yet"
      >
        <p>Ta feuille ORP se remplit avec tes candidatures.</p>
        <div class="face-state-actions">
          <!-- Un lien (décision du 25/10) : « Enregistrer » reste la seule action principale. -->
          <RouterLink
            to="/candidatures/offres"
            class="link"
            data-test="see-offers"
          >
            Voir les offres
          </RouterLink>
        </div>
      </FaceState>
      <!-- Le mois (règles §3.4, décision du 25/10) : une ligne repliable par partie, avec son résumé ;
           « Le mois en bref » ouvert ; une partie vide ne s'affiche pas (docs/131 §B.8). -->
      <template v-if="(prep && !noApplications) || page.past.length">
        <h2 class="section-title orp-section">
          Le mois
        </h2>
        <div
          class="orp-month-rows"
          data-test="sheet-facts"
        >
          <template v-if="prep && !noApplications">
            <DisclosureRow
              title="Le mois en bref"
              :value="monthValue"
              start-open
              data-test="sheet-summary"
            >
              <!-- Une ligne de chiffres par mois (docs/131 §A.5) ; le texte complet va à la feuille. -->
              <ul
                v-if="prep.months?.length"
                class="orp-month-lines"
              >
                <li
                  v-for="month in prep.months"
                  :key="month.month"
                >
                  <strong>{{ monthTitle(month.month) }}</strong> · {{ plural(month.count, "candidature", "candidatures") }}{{ month.target ? ` sur ${month.target}` : "" }} · {{ plural(month.answered, "réponse", "réponses") }} · {{ plural(month.interviews, "entretien", "entretiens") }}
                </li>
              </ul>
              <template v-else>
                <p
                  v-for="line in prep.summaries"
                  :key="line"
                >
                  {{ line }}
                </p>
              </template>
            </DisclosureRow>
            <DisclosureRow
              v-if="prep.blockers.length || prep.works"
              title="Ce qui bloque"
              :value="plural(prep.blockers.length + (prep.works ? 1 : 0), 'piste', 'pistes')"
              data-test="sheet-blockers"
            >
              <ul v-if="prep.blockers.length">
                <li
                  v-for="line in prep.blockers"
                  :key="line"
                >
                  {{ line }}
                </li>
              </ul>
              <p
                v-if="prep.works"
                class="orp-meeting-works"
              >
                Ce qui marche : {{ prep.works }}
              </p>
            </DisclosureRow>
            <DisclosureRow
              v-if="prep.missing.length"
              title="Compétences demandées qui manquent"
              :value="plural(prep.missing.length, 'compétence', 'compétences')"
              data-test="sheet-missing"
            >
              <ul v-if="prep.missing.length">
                <li
                  v-for="item in prep.missing"
                  :key="item.skill"
                >
                  <strong>{{ item.skill }}</strong> : demandé dans {{ item.count }} des
                  {{ plural(prep.offers, "offre bien notée", "offres bien notées") }} des 3 derniers mois.
                  <RouterLink
                    v-if="item.training_title"
                    to="/bilan/formations"
                  >
                    {{ item.training_title }}
                  </RouterLink>
                </li>
              </ul>
            </DisclosureRow>
            <DisclosureRow
              v-if="pendingObligations.length"
              title="Obligations et échéances"
              :value="dutiesValue"
              data-test="sheet-obligations"
            >
              <ul class="orp-meeting-duties">
                <li
                  v-for="item in pendingObligations"
                  :key="item.text"
                >
                  {{ item.text }}
                </li>
              </ul>
            </DisclosureRow>
          </template>
          <!-- Le carnet, replié (docs/130 §B) : « Modifier » sur la ligne de chaque rendez-vous. -->
          <DisclosureRow
            v-if="page.past.length"
            class="orp-log"
            title="Le carnet"
            :value="plural(page.past.length, 'rendez-vous', 'rendez-vous')"
            data-test="meeting-log"
          >
            <ul>
              <li
                v-for="item in page.past"
                :key="item.id"
              >
                <div class="orp-log-head">
                  <h3>{{ dayText(item.starts_at) }}<span v-if="item.place"> · {{ item.place }}</span></h3>
                  <button
                    v-if="item.outcome_at && noting !== item.id"
                    type="button"
                    class="link"
                    :data-test="`log-outcome-${item.id}`"
                    @click="noting = item.id"
                  >
                    Modifier
                  </button>
                </div>
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
                    v-if="!item.outcome_at"
                    type="button"
                    class="secondary small"
                    :data-test="`log-outcome-${item.id}`"
                    @click="noting = item.id"
                  >
                    Noter ce qui a été convenu
                  </button>
                </template>
              </li>
            </ul>
          </DisclosureRow>
        </div>
      </template>
    </template>
  </section>
</template>
