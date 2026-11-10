<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { api, type Chunk, type ChunkProposal, type DocumentOut } from "../api/client";
import { dateInSentence } from "../dates";
import { plural } from "../format";
import { foundCount, foundDetail, useCvReading, type CvNotice } from "../composables/useCvReading";
import ChunkProposals from "./ChunkProposals.vue";
import ProfileCompletionPanel from "./ProfileCompletionPanel.vue";

// Le bloc d'état de la carte « Mon CV » (maquettes ProfilOrdinateurCV et ProfilTel du 10 novembre au soir, PR 21 et
// 24) : sous un filet, dans la même carte, un seul bouton plein par état. La zone est en role="status" et
// aria-live="polite" et reste en place : chaque changement d'état est annoncé, même quand le bloc apparaît.
// « Choisir les éléments » ouvre la liste existante des éléments proposés ; « Remplir à la main », l'étape
// « Complétons ton profil » (PR 17) ; « Déposer un autre fichier » laisse la page ouvrir son sélecteur de fichier.
const props = defineProps<{ doc: DocumentOut; notice?: CvNotice | null }>();
const emit = defineEmits<{ replace: []; changed: [] }>();

const reading = useCvReading();
const state = computed(() => reading.stateOf(props.doc));
// Le message après un dépôt (PR 24) passe avant l'état, jusqu'à « Fermer », « Plus tard » ou « Relire ».
const shown = computed(() => props.notice ?? (state.value === "fait" ? null : state.value));
const busy = ref(false);
const failed = ref("");

async function read(): Promise<void> {
  if (busy.value) return;
  busy.value = true;
  failed.value = "";
  if (!(await reading.read(props.doc.id))) failed.value = "La lecture n’a pas pu partir : vérifie ta connexion et réessaie.";
  busy.value = false;
}

// La barre avance sur les 30 secondes annoncées, sans jamais finir seule : la fin vient du serveur.
const elapsed = ref(0);
let tick: ReturnType<typeof setInterval> | undefined;
watch(
  () => shown.value === "cours",
  (running) => {
    clearInterval(tick);
    elapsed.value = 0;
    if (running) tick = setInterval(() => (elapsed.value += 1), 1000);
  },
  { immediate: true },
);
onBeforeUnmount(() => clearInterval(tick));
const progress = computed(() => Math.min(90, Math.round(10 + (elapsed.value / 30) * 80)));

// « Choisir les éléments » : la liste trouvée, cochée par défaut sauf les doublons.
const choosing = ref<{ items: ChunkProposal[]; existing: Chunk[] } | null>(null);
async function choose(): Promise<void> {
  const [items, existing] = await Promise.all([
    reading.proposals(props.doc.id),
    api.GET("/api/profile-chunks").then((r) => r.data ?? []),
  ]);
  choosing.value = { items, existing };
}
async function saved(): Promise<void> {
  choosing.value = null;
  await reading.chosen(props.doc.id);
  emit("changed");
}

const completing = ref(false);
function manual(event: Event): void {
  event.preventDefault();
  completing.value = true;
}
function later(event: Event): void {
  event.preventDefault();
  reading.closeNotice();
}

const readOn = computed(() => (props.doc.read_at ? dateInSentence(props.doc.read_at) : ""));
</script>

<template>
  <div
    class="cv-state-live"
    role="status"
    aria-live="polite"
    data-test="cv-state-live"
  >
    <div
      v-if="shown"
      class="cv-state"
      :class="`cv-state-${shown}`"
      :data-test="`cv-state-${shown}`"
    >
      <!-- L'icône de 24 (22 pour la lecture en cours) : exclamation orange, coche verte, information bleue. -->
      <svg
        v-if="shown === 'cours'"
        class="cv-state-icon cv-state-spinner"
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        stroke-width="2.8"
        stroke-linecap="round"
        aria-hidden="true"
      ><circle
        cx="12"
        cy="12"
        r="9"
        class="cv-state-track"
      /><path
        d="M12 3a9 9 0 0 1 9 9"
        class="cv-state-arc"
      /></svg>
      <svg
        v-else-if="shown === 'lu' || shown === 'deja'"
        class="cv-state-icon"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      ><circle
        cx="12"
        cy="12"
        r="9"
      /><path d="m8 12.5 3 3 5-6" /></svg>
      <svg
        v-else-if="shown === 'nouveau'"
        class="cv-state-icon"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      ><circle
        cx="12"
        cy="12"
        r="9"
      /><path d="M12 11v5.5M12 7.5h.01" /></svg>
      <svg
        v-else
        class="cv-state-icon"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      ><circle
        cx="12"
        cy="12"
        r="9"
      /><path d="M12 7.5v5.5M12 16.5h.01" /></svg>

      <div class="cv-state-body">
        <template v-if="shown === 'relire'">
          <p class="cv-state-title">
            Ton CV n’a pas encore été lu
          </p>
          <p class="cv-state-text">
            jobA1 n’en a rien repris. Sans tes expériences ni tes compétences, les offres ne peuvent pas être notées.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-primary"
              data-test="cv-read"
              @click="read"
            >
              Relire mon CV
            </button>
            <span class="cv-state-hint">Environ 30 secondes</span>
          </div>
        </template>

        <template v-else-if="shown === 'cours'">
          <p class="cv-state-title">
            Lecture de ton CV…
          </p>
          <p class="cv-state-text">
            Environ 30 secondes. Tu peux quitter cette page&#8239;: on te prévient quand c’est prêt.
          </p>
          <div class="cv-state-actions">
            <div
              class="cv-state-progress"
              role="progressbar"
              aria-label="Lecture du CV"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-valuenow="progress"
            >
              <span :style="{ width: `${progress}%` }" />
            </div>
          </div>
        </template>

        <template v-else-if="shown === 'lu'">
          <p class="cv-state-title">
            {{ plural(foundCount(doc), "élément trouvé", "éléments trouvés") }}
          </p>
          <p class="cv-state-text">
            {{ foundDetail(doc) }}. Choisis ceux à garder.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-primary"
              data-test="cv-choose"
              @click="choose"
            >
              Choisir les éléments
            </button>
          </div>
        </template>

        <template v-else-if="shown === 'indispo'">
          <p class="cv-state-title">
            La lecture est indisponible pour le moment
          </p>
          <p class="cv-state-text">
            Ce n’est pas ton fichier. Réessaie dans quelques minutes.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-outline"
              data-test="cv-retry"
              @click="read"
            >
              Réessayer
            </button>
          </div>
        </template>

        <template v-else-if="shown === 'illisible'">
          <p class="cv-state-title">
            Le texte de ce CV n’est pas lisible
          </p>
          <p class="cv-state-text">
            C’est sans doute une image scannée. Dépose un PDF exporté depuis Word, ou remplis ton profil à la main.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-tonal"
              data-test="cv-other-file"
              @click="emit('replace')"
            >
              Déposer un autre fichier
            </button>
            <a
              href="#"
              class="cv-state-link"
              data-test="cv-manual"
              @click="manual"
            >Remplir à la main</a>
          </div>
        </template>

        <template v-else-if="shown === 'jamais'">
          <p class="cv-state-title">
            Ce CV était déjà déposé, mais il n’a jamais été lu
          </p>
          <p class="cv-state-text">
            Relis-le pour reprendre tes expériences et faire noter tes offres.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-primary"
              data-test="cv-read"
              @click="read"
            >
              Relire mon CV
            </button>
          </div>
        </template>

        <template v-else-if="shown === 'deja'">
          <p class="cv-state-title">
            Ce CV est déjà dans ton profil
          </p>
          <p class="cv-state-text">
            C’est le même fichier{{ readOn ? `, déjà lu ${readOn}` : ", déjà lu" }}. Rien n’a changé.
          </p>
        </template>

        <template v-else-if="shown === 'nouveau'">
          <p class="cv-state-title">
            Nouveau CV déposé
          </p>
          <p class="cv-state-text">
            Relis-le pour mettre à jour ton profil. Tu choisiras ce que tu gardes.
          </p>
          <div class="cv-state-actions">
            <button
              type="button"
              class="cv-state-button cv-state-primary"
              data-test="cv-read"
              @click="read"
            >
              Relire mon CV
            </button>
            <a
              href="#"
              class="cv-state-link"
              data-test="cv-later"
              @click="later"
            >Plus tard</a>
          </div>
        </template>

        <p
          v-if="failed"
          class="cv-state-failed"
        >
          {{ failed }}
        </p>
      </div>
      <button
        v-if="notice"
        type="button"
        class="cv-state-close"
        aria-label="Fermer le message"
        data-test="cv-close"
        @click="reading.closeNotice()"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.2"
          stroke-linecap="round"
          aria-hidden="true"
        ><path d="M6 6l12 12M18 6 6 18" /></svg>
      </button>
    </div>
  </div>
  <ChunkProposals
    v-if="choosing"
    :document-id="doc.id"
    :document-name="doc.filename"
    :proposals="choosing.items"
    :existing="choosing.existing"
    @close="choosing = null"
    @saved="saved"
  />
  <ProfileCompletionPanel
    :open="completing"
    title="Complétons ton profil"
    @close="completing = false"
    @saved="completing = false; emit('changed')"
  />
</template>

<style>
/* Le bloc d'état (maquettes ProfilOrdinateurCV et ProfilTel) : filet de 1 px en haut, 16 de marge verticale et la marge
   horizontale de la carte (18,5 sur ordinateur, 16 sur téléphone, --cv-pad-x), icône de 24 à 12 du texte ; titre 16/22
   gras, texte 14/20 en --text-tertiary ; actions à 12 dessous, 16 d'écart, boutons de 44 en pilule. */
.cv-state { display: flex; gap: var(--space-3); padding: var(--space-4) var(--cv-pad-x, 1.15625em); border-top: 1px solid var(--line); background: var(--surface); }
.cv-state-relire, .cv-state-indispo, .cv-state-illisible, .cv-state-jamais { background: var(--peach-wash); }
.cv-state-lu, .cv-state-deja { background: var(--success-wash); }
.cv-state-nouveau { background: var(--primary-soft); }
.cv-state-icon { flex: none; color: var(--peach-text); }
.cv-state-lu .cv-state-icon, .cv-state-deja .cv-state-icon { color: var(--success); }
.cv-state-nouveau .cv-state-icon { color: var(--primary-text); }
.cv-state-track { stroke: var(--line); }
.cv-state-arc { stroke: var(--primary); }
.cv-state-spinner { animation: cv-state-turn 1s linear infinite; }
@keyframes cv-state-turn { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .cv-state-spinner { animation: none; } }
.cv-state-body { flex: 1; min-width: 0; }
.cv-state-title { margin: 0; font-size: var(--font-body); line-height: 1.375em; font-weight: var(--weight-bold); color: var(--text); }
.cv-state-text { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-tertiary); }
.cv-state-actions { margin-top: var(--space-3); display: flex; align-items: center; gap: var(--space-4); flex-wrap: wrap; }
.cv-state-button { height: 2.75rem; padding: 0 var(--space-5); border-radius: var(--radius-pill); font-family: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); white-space: nowrap; cursor: pointer; }
.cv-state-primary { border: 0; background: var(--primary); color: var(--on-primary, #fff); }
.cv-state-outline { border: 1.5px solid var(--primary); background: var(--surface); color: var(--primary-text); font-weight: var(--weight-semibold); padding: 0 1.2333em; }
.cv-state-tonal { border: 0; background: var(--primary-soft); color: var(--primary-text); }
.cv-state-link { display: inline-flex; align-items: center; min-height: 2.75rem; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.cv-state-link:hover { text-decoration: underline; }
.cv-state-hint { font-size: var(--font-small); color: var(--text-secondary); }
.cv-state-progress { flex: 1; height: 0.375rem; border-radius: var(--radius-pill); background: var(--line); overflow: hidden; }
.cv-state-progress span { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--primary); transition: width 1s linear; }
.cv-state-failed { margin: var(--space-2) 0 0; font-size: var(--font-small); color: var(--peach-text); }
.cv-state-close { flex: none; width: 2.75rem; height: 2.75rem; margin: -0.625rem -0.625rem 0 0; padding: 0; border: 0; background: none; color: var(--text-secondary); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
</style>
