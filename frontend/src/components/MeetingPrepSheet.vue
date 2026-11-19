<script setup lang="ts">
import { computed, nextTick, reactive, ref, useId } from "vue";

import type { components } from "../api/schema";
import { offerUndo } from "../composables/useUndo";
import { checkedCount, dateText, timeAndPlace } from "../rendezVous";
import type { SaveState } from "../sheetIdentity";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CalendarDate from "./CalendarDate.vue";
import FieldSaveStatus from "./FieldSaveStatus.vue";
import MoreMenu from "./MoreMenu.vue";
import UndoToast from "./UndoToast.vue";

// La feuille « Préparer le rendez-vous » (MODIFICATIONS du 8 novembre au soir, §10.7 ; maquettes RendezVousPreparer
// et RendezVousPreparerSombre), ouverte depuis la carte « À venir » du rendez-vous ORP : le rappel (calendrier,
// « Rendez-vous ORP », date · lieu) ; « Où tu en es », le libellé au-dessus de la valeur ; « Tes questions au
// conseiller · n cochées », cases de 24 px sur des lignes de 44 px au moins ; puis « Imprimer ou télécharger en PDF ».
// §46 du 17.11 (décision de Kevin du 17.11) : une page entière sur fond beige, pas une feuille ; la flèche « Retour » à
// gauche du titre à la place de la croix. Retour, Échap et le retour du téléphone la ferment (BottomSheet).
type Question = components["schemas"]["QuestionIO"];

const props = defineProps<{
  open: boolean;
  at: string;
  place: string | null | undefined;
  lines: { label: string; text: string }[];
  questions: Question[];
  checked: number;
  pdf: string;
  // Sous « Ton nom sur la feuille » : le nom et l'office enregistrés ; sous « Voir la feuille » : « 6 recherches,
  // 2 questions ». Vides : la ligne n'a que son titre.
  nameLine?: string;
  sheetLine?: string;
  // Enregistre la liste entière des questions ; `false` si le serveur ne l'a pas prise.
  save?: (questions: Question[]) => Promise<boolean>;
}>();
const emit = defineEmits<{ close: []; toggle: [question: Question, checked: boolean]; name: []; sheet: [] }>();

const whereId = useId();
const askId = useId();
const sheetId = useId();

// « + Ajouter une question » (Kevin, 18.11, réponse à la planche PreparerRendezVous) : un toucher ajoute en bas de la
// carte une ligne avec un champ, le focus dedans ; Entrée ou sortie du champ l'enregistre, non cochée ; vide, la ligne
// disparaît ; Échap annule. Une question à toi se modifie en touchant son texte, se supprime par « ⋯ › Supprimer »
// avec le bandeau « Annuler ». Chaque enregistrement dit « Enregistrement… », puis « Enregistré » (comme FeuilleNom) ;
// s'il échoue, « Pas enregistré · Réessayer » et le texte reste dans le champ. Les questions proposées par jobA1 se
// cochent seulement : leur texte vient de tes données.
const NEW = "new";
const editing = ref<string | null>(null);
const draft = ref("");
const added = ref<Question | null>(null);
const hidden = reactive(new Set<string>());
const states = reactive<Record<string, SaveState>>({});
const field = ref<HTMLTextAreaElement | null>(null);
let cancelled = false;
const isOwn = (q: Question): boolean => q.key.startsWith("custom:");
const shown = computed(() => {
  const list = props.questions.filter((q) => !hidden.has(q.key) && !q.removed);
  const extra = added.value;
  return extra && !list.some((q) => q.key === extra.key) ? [...list, extra] : list;
});

// Une seule saisie à la fois : le champ ouvert, dans la liste ou dans la ligne nouvelle.
function setField(el: unknown): void {
  if (el instanceof HTMLTextAreaElement) field.value = el;
}
async function focusField(): Promise<void> {
  await nextTick();
  field.value?.focus();
}
function startAdd(): void {
  editing.value = NEW;
  draft.value = "";
  void focusField();
}
function startEdit(question: Question): void {
  editing.value = question.key;
  draft.value = question.text;
  void focusField();
}
function cancel(): void {
  // Le champ retiré peut perdre le focus (« blur ») ou non selon le navigateur : le drapeau ne vit qu'un instant.
  cancelled = true;
  editing.value = null;
  added.value = null;
  void nextTick(() => {
    cancelled = false;
  });
}
async function send(key: string, questions: Question[]): Promise<boolean> {
  if (!props.save) return false;
  states[key] = "saving";
  const ok = await props.save(questions);
  states[key] = ok ? "saved" : "failed";
  return ok;
}
// La sortie du champ (Entrée y mène aussi) : enregistre, sauf après Échap.
async function leave(): Promise<void> {
  if (cancelled) {
    cancelled = false;
    return;
  }
  const key = editing.value;
  if (!key) return;
  const text = draft.value.trim();
  const isNew = key === NEW || key === added.value?.key;
  const current = props.questions.find((q) => q.key === key);
  if (!text) {
    // Vide : la ligne disparaît (une question déjà enregistrée part comme avec « Supprimer »).
    editing.value = null;
    if (current) remove(current);
    else added.value = null;
    return;
  }
  if (!isNew && current && current.text === text) {
    editing.value = null;
    return;
  }
  editing.value = null;
  if (isNew) {
    const question = { key: key === NEW ? `custom:${Date.now()}` : key, text, checked: false };
    added.value = question;
    const ok = await send(question.key, [...props.questions.filter((q) => q.key !== question.key), question]);
    if (ok) added.value = null;
    else {
      editing.value = question.key;
      draft.value = text;
    }
    return;
  }
  const ok = await send(key, props.questions.map((q) => (q.key === key ? { ...q, text } : q)));
  if (!ok) {
    editing.value = key;
    draft.value = text;
  }
}
// « Réessayer » : renvoie ce qui est dans le champ.
function retry(): void {
  void leave();
}
function remove(question: Question): void {
  delete states[question.key];
  if (editing.value === question.key) editing.value = null;
  // Jamais enregistrée (l'enregistrement a échoué) : rien à annuler côté serveur, la ligne part.
  if (!props.questions.some((q) => q.key === question.key)) {
    added.value = null;
    return;
  }
  hidden.add(question.key);
  void offerUndo({
    message: "Question supprimée",
    commit: async () => {
      const ok = props.save ? await props.save(props.questions.filter((q) => q.key !== question.key)) : false;
      if (ok) hidden.delete(question.key);
      return ok;
    },
    restore: () => {
      hidden.delete(question.key);
    },
  });
}
// « ⋯ › Retirer » une question proposée par jobA1 (Kevin, 18.11, option A) : le serveur la garde comme retirée
// et ne la propose plus pour ce rendez-vous ; « Annuler » pendant 6 s, comme tous les bandeaux (Kevin, 19.11).
function retire(question: Question): void {
  hidden.add(question.key);
  void offerUndo({
    message: "Question retirée",
    commit: async () => {
      const list = props.questions.map((q) => (q.key === question.key ? { ...q, checked: false, removed: true } : q));
      const ok = props.save ? await props.save(list) : false;
      if (ok) hidden.delete(question.key);
      return ok;
    },
    restore: () => {
      hidden.delete(question.key);
    },
  });
}
// « Annuler » sous le champ : touché, il ne doit pas d'abord enregistrer en faisant perdre le focus au champ.
function holdCancel(): void {
  cancelled = true;
}
function onKey(event: KeyboardEvent): void {
  if (event.key === "Enter") {
    event.preventDefault();
    (event.target as HTMLTextAreaElement).blur();
  } else if (event.key === "Escape") {
    // Échap annule le champ, pas la page.
    event.preventDefault();
    event.stopPropagation();
    cancel();
  }
}

function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Préparer le rendez-vous"
    full
    back
    class="rdv-prep-page prep-page"
    data-test="rdv-prep-sheet"
    @close="emit('close')"
  >
    <div class="prep-card prep-date">
      <CalendarDate
        v-bind="cal(at)"
        tone="orp"
      />
      <div>
        <b class="prep-date-title">Rendez-vous ORP</b>
        <span class="prep-sub">{{ dateText(at) }}, {{ timeAndPlace(at, place) }}</span>
      </div>
    </div>
    <section
      v-if="lines.length"
      :aria-labelledby="whereId"
      data-test="rdv-prep-lines"
    >
      <h3
        :id="whereId"
        class="prep-title"
      >
        Où tu en es
      </h3>
      <ul class="prep-card prep-rows">
        <li
          v-for="line in lines"
          :key="line.label"
          class="prep-line"
        >
          <div class="prep-key">
            {{ line.label }}
          </div>
          <div class="prep-value">
            {{ line.text }}
          </div>
        </li>
      </ul>
    </section>
    <section
      :aria-labelledby="askId"
      data-test="rdv-prep-questions"
    >
      <h3
        :id="askId"
        class="prep-title"
      >
        Tes questions au conseiller · {{ checkedCount(checked) }}
      </h3>
      <ul class="prep-card prep-rows">
        <li
          v-for="question in shown"
          :key="question.key"
        >
          <div
            v-if="editing === question.key"
            class="prep-check prep-edit"
          >
            <span
              class="prep-box"
              :class="{ on: question.checked }"
              aria-hidden="true"
            />
            <div class="prep-edit-body">
              <textarea
                :ref="setField"
                v-model="draft"
                class="prep-field"
                rows="2"
                maxlength="300"
                placeholder="Ta question"
                aria-label="Ta question"
                data-test="rdv-question-field"
                @keydown="onKey"
                @blur="leave"
              />
              <div class="prep-actions">
                <FieldSaveStatus
                  v-if="states[question.key] && states[question.key] !== 'idle'"
                  class="prep-actions-status"
                  :state="states[question.key]!"
                  @retry="retry"
                />
                <button
                  type="button"
                  class="prep-cancel"
                  data-test="rdv-question-cancel"
                  @pointerdown="holdCancel"
                  @mousedown.prevent
                  @click="cancel"
                >
                  Annuler
                </button>
                <button
                  type="button"
                  class="primary prep-submit"
                  data-test="rdv-question-submit"
                  @mousedown.prevent
                  @click="leave"
                >
                  {{ question.key === added?.key ? "Ajouter" : "Enregistrer" }}
                </button>
              </div>
            </div>
          </div>
          <div
            v-else
            class="prep-q"
          >
            <label class="prep-check">
              <input
                type="checkbox"
                :checked="question.checked"
                :data-test="`rdv-question-${question.key}`"
                @change="emit('toggle', question, ($event.target as HTMLInputElement).checked)"
              >
              <span>{{ question.text }}</span>
            </label>
            <MoreMenu
              v-if="!isOwn(question)"
              class="prep-more"
              :items="[{ label: 'Retirer', test: `rdv-question-retire-${question.key}`, run: () => retire(question) }]"
              :inline="false"
              label="Actions sur la question"
              :test-id="`rdv-question-more-${question.key}`"
            />
            <MoreMenu
              v-else
              class="prep-more"
              :items="[
                { label: 'Modifier', test: `rdv-question-edit-${question.key}`, run: () => startEdit(question), icon: 'pencil' },
                { label: 'Supprimer', test: `rdv-question-delete-${question.key}`, run: () => remove(question), danger: true, icon: 'trash' },
              ]"
              label="Actions sur la question"
              :test-id="`rdv-question-more-${question.key}`"
            />
          </div>
          <FieldSaveStatus
            v-if="editing !== question.key && states[question.key] && states[question.key] !== 'idle'"
            class="prep-status"
            :state="states[question.key]!"
            reserve
            @retry="retry"
          />
        </li>
        <li v-if="editing === NEW">
          <div class="prep-check prep-edit">
            <span
              class="prep-box"
              aria-hidden="true"
            />
            <div class="prep-edit-body">
              <textarea
                :ref="setField"
                v-model="draft"
                class="prep-field"
                rows="2"
                maxlength="300"
                placeholder="Ta question"
                aria-label="Nouvelle question"
                data-test="rdv-question-field"
                @keydown="onKey"
                @blur="leave"
              />
              <div class="prep-actions">
                <button
                  type="button"
                  class="prep-cancel"
                  data-test="rdv-question-cancel"
                  @pointerdown="holdCancel"
                  @mousedown.prevent
                  @click="cancel"
                >
                  Annuler
                </button>
                <button
                  type="button"
                  class="primary prep-submit"
                  data-test="rdv-question-submit"
                  @mousedown.prevent
                  @click="leave"
                >
                  Ajouter
                </button>
              </div>
            </div>
          </div>
        </li>
        <li v-else-if="!editing">
          <button
            type="button"
            class="prep-add"
            data-test="rdv-question-add"
            @click="startAdd"
          >
            + Ajouter une question
          </button>
        </li>
      </ul>
    </section>
    <section :aria-labelledby="sheetId">
      <h3
        :id="sheetId"
        class="prep-title"
      >
        La feuille
      </h3>
      <ul class="prep-card prep-rows">
        <li>
          <button
            type="button"
            class="prep-link"
            data-test="rdv-name"
            @click="emit('name')"
          >
            <span><b>Ton nom sur la feuille</b><span
              v-if="nameLine"
              class="prep-sub"
              data-test="rdv-name-line"
            >{{ nameLine }}</span></span><AppIcon name="chevron" />
          </button>
        </li>
        <li>
          <button
            type="button"
            class="prep-link"
            data-test="rdv-view-sheet"
            @click="emit('sheet')"
          >
            <span><b>Voir la feuille</b><span
              v-if="sheetLine"
              class="prep-sub"
            >{{ sheetLine }}</span></span><AppIcon name="chevron" />
          </button>
        </li>
        <li>
          <a
            class="prep-link"
            :href="pdf"
            download
            data-test="rdv-pdf"
          ><span><b>Imprimer ou télécharger en PDF</b></span><AppIcon name="chevron" /></a>
        </li>
      </ul>
    </section>
    <!-- Le bandeau « Annuler » dans la page : celui de l'application resterait derrière elle. -->
    <UndoToast bar />
  </BottomSheet>
</template>

<style scoped>
/* Planche PreparerRendezVous (§71, 18.11) : sur le fond beige, des cartes blanches (trait 1 px, rayon 20 px, 12 px
   entre elles) ; titres de groupe en phrase, 18 px, graisse 800, 24 px au-dessus et 12 px dessous (22 et 10 sur la planche : grille de 4), 4 px plus à
   l'intérieur que les cartes ; lignes séparées d'un trait doux ; libellé 13 px gris au-dessus d'une valeur de 16 px. */
.prep-page { --pp-radius: 20px; --pp-row-h: 56px; --pp-check: 24px; --pp-check-radius: 6px; --pp-chevron: 18px; --pp-lh-sub: 19px; --pp-lh-key: 18px; --pp-lh: 22px; --pp-field-h: 52px; }
.prep-page :deep(.sheet-body) { grid-template-columns: minmax(0, 1fr); gap: 0; padding-inline: var(--space-4); }
.prep-card { margin: 0 0 var(--space-3); padding: 0; list-style: none; border: 1px solid var(--line); border-radius: var(--pp-radius); background: var(--surface); }
.prep-rows > li + li { border-top: 1px solid var(--line-soft); }
.prep-date { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); }
.prep-date-title { display: block; font-size: var(--font-title); font-weight: var(--weight-bold); line-height: var(--space-6); }
.prep-sub { display: block; margin-top: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-regular); line-height: var(--pp-lh-sub); color: var(--text-secondary); }
.prep-title { margin: var(--space-6) var(--space-1) var(--space-3); font-size: var(--font-title); line-height: var(--space-6); font-weight: var(--weight-heavy); }
.prep-line { padding: var(--space-3) var(--space-4); }
.prep-key { font-size: var(--label-caps); line-height: var(--pp-lh-key); color: var(--text-secondary); }
.prep-value { margin-top: var(--space-1); font-size: var(--font-body); line-height: var(--pp-lh); overflow-wrap: anywhere; }
.prep-check { display: flex; align-items: flex-start; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-3) var(--space-4); font-size: var(--font-body); line-height: var(--pp-lh); cursor: pointer; }
.prep-check input[type="checkbox"] { flex: none; appearance: none; width: var(--pp-check); height: var(--pp-check); margin: 0; border-radius: var(--pp-check-radius); box-shadow: inset 0 0 0 2px var(--field-border); background: var(--surface) center / 16px no-repeat; cursor: pointer; }
.prep-check input[type="checkbox"]:checked { box-shadow: none; background-color: var(--primary-graphic); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 12 5 5 9-10'/%3E%3C/svg%3E"); }
.prep-link { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); box-sizing: border-box; width: 100%; min-height: var(--pp-row-h); padding: var(--space-2) var(--space-4); border: 0; background: none; color: var(--text); font: inherit; text-align: left; text-decoration: none; cursor: pointer; }
.prep-link b { display: block; font-size: var(--font-body); font-weight: var(--weight-semibold); line-height: var(--pp-lh); }
.prep-q { display: flex; align-items: flex-start; }
.prep-q > .prep-check { flex: 1; min-width: 0; }
.prep-more { flex: none; margin: var(--space-1) var(--space-1) 0 calc(var(--space-3) * -1); }
.prep-edit { cursor: auto; }
.prep-edit > .prep-box { margin-top: var(--space-3); }
.prep-edit-body { flex: 1; min-width: 0; }
.prep-field { display: block; box-sizing: border-box; width: 100%; min-height: var(--pp-field-h); padding: var(--space-3); border: 2px solid var(--primary-graphic); border-radius: var(--space-3); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body); line-height: var(--pp-lh); resize: none; outline: 0; }
.prep-actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: var(--space-2); margin-top: var(--space-3); }
.prep-actions-status { flex: 1 0 100%; min-width: 0; }
.prep-cancel, .prep-submit { flex: none; min-height: var(--target-min); padding: 0 var(--space-4); border-radius: var(--target-min); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); cursor: pointer; }
.prep-cancel { border: 0; background: none; color: var(--text); }
.prep-submit { padding-inline: var(--space-5); border: 0; }
.prep-box { flex: none; box-sizing: border-box; width: var(--pp-check); height: var(--pp-check); border-radius: var(--pp-check-radius); box-shadow: inset 0 0 0 2px var(--field-border); }
.prep-box.on { box-shadow: none; background: var(--primary-graphic); }
.prep-status { margin: 0 var(--space-4) var(--space-3); }
.prep-add { display: flex; align-items: center; width: 100%; min-height: var(--pp-row-h); padding: 0 var(--space-4); border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); text-align: left; cursor: pointer; }
/* Le bandeau « Annuler » en bas de la page, au-dessus de tout (la page couvre l'écran). */
.prep-page :deep(.tri-toast) { position: fixed; left: var(--space-4); right: var(--space-4); bottom: calc(var(--space-4) + env(safe-area-inset-bottom)); z-index: 2; display: flex; align-items: center; justify-content: space-between; min-height: var(--pp-row-h); padding: 0 var(--space-2) 0 var(--space-4); border-radius: var(--space-4); background: var(--snackbar-bg); color: var(--snackbar-text); font-size: var(--font-label); overflow: hidden; }
.prep-page :deep(.tri-toast button) { min-height: var(--target-min); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font: inherit; font-weight: var(--weight-bold); cursor: pointer; }
.prep-link > .icon { flex: none; width: var(--pp-chevron); height: var(--pp-chevron); color: var(--text-secondary); }
</style>
