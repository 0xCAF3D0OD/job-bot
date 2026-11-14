<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { api, type Application } from "../api/client";
import { daysSince } from "../dates";
import { plural } from "../format";
import BusyButton from "./BusyButton.vue";
import CopyButton from "./CopyButton.vue";
import FormField from "./FormField.vue";

// Relancer une candidature (docs/38), refait d'après la planche RelanceOrdinateurV2 du 13 novembre et la décision
// de Kevin du 14.11 :
// - le message s'écrit à la première ouverture, puis il est gardé avec la candidature ; rouvrir ne refait pas
//   d'appel à l'IA, « Réécrire » en demande un nouveau ;
// - objet et message restent visibles en lecture ; « Modifier le message » les rend modifiables, et la version de
//   la personne est gardée ; rien ne part sans avoir été lu ;
// - « Relancer par e-mail » : bouton principal (la messagerie s'ouvre, rien n'est envoyé par jobA1), l'illustration
//   dans le bandeau ; « Marquer comme relancée » : lien sous le bouton ;
// - si l'écriture échoue : la carte « Réessayer » de la lettre.
// Gardés de main, absents de la planche : « Copier la relance » (seul moyen sans e-mail du contact) et la mention
// « Modèle simple, sans IA (raison) ».
const props = defineProps<{ application: Application }>();
const emit = defineEmits<{ done: [] }>();

const subject = ref("");
const text = ref("");
const reason = ref<string | null>(null);
const writing = ref(false);
const failed = ref(false);
const editing = ref(false);
const editSubject = ref("");
const editText = ref("");
const saving = ref(false);
const marking = ref(false);
const error = ref("");

const ready = computed(() => !!text.value && !failed.value);
const sentLine = computed(() => {
  const days = daysSince(`${props.application.sent_at}T12:00:00`);
  const since = days <= 0 ? "Envoyée aujourd’hui" : days === 1 ? "Envoyée hier" : `Envoyée il y a ${plural(days, "jour", "jours")}`;
  return `${since} · sans réponse`;
});
const paragraphs = computed(() => text.value.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean));

// Ouvre la messagerie avec destinataire, objet et texte (rien n'est envoyé d'office).
const mailto = computed(() => {
  const to = props.application.contact_email;
  if (!to || !ready.value) return null;
  const query = new URLSearchParams({ subject: subject.value, body: text.value }).toString().replace(/\+/g, "%20");
  return `mailto:${encodeURIComponent(to)}?${query}`;
});

async function write(rewrite = false): Promise<void> {
  writing.value = true;
  failed.value = false;
  error.value = "";
  editing.value = false;
  try {
    const { data } = await api.POST("/api/applications/{application_id}/follow-up/draft", {
      params: { path: { application_id: props.application.id }, query: rewrite ? { rewrite: true } : {} },
    });
    if (!data || data.failed) {
      failed.value = true;
      return;
    }
    subject.value = data.subject;
    text.value = data.text;
    reason.value = data.ai ? null : data.reason;
  } catch {
    failed.value = true;
  } finally {
    writing.value = false;
  }
}

function startEdit(): void {
  editSubject.value = subject.value;
  editText.value = text.value;
  editing.value = true;
}

async function saveEdit(): Promise<void> {
  if (!editText.value.trim()) return;
  saving.value = true;
  error.value = "";
  try {
    const { data } = await api.PUT("/api/applications/{application_id}/follow-up/draft", {
      params: { path: { application_id: props.application.id } },
      body: { subject: editSubject.value, text: editText.value },
    });
    if (!data) {
      error.value = "Enregistrement impossible : réessaie.";
      return;
    }
    subject.value = data.subject;
    text.value = data.text;
    editing.value = false;
  } finally {
    saving.value = false;
  }
}

async function markDone(): Promise<void> {
  marking.value = true;
  error.value = "";
  try {
    const { data } = await api.POST("/api/applications/{application_id}/follow-up", {
      params: { path: { application_id: props.application.id } },
    });
    if (!data) {
      error.value = "Enregistrement impossible.";
      return;
    }
    emit("done");
  } finally {
    marking.value = false;
  }
}

onMounted(() => void write());
watch(
  () => props.application.id,
  () => {
    subject.value = "";
    text.value = "";
    void write();
  },
);
</script>

<template>
  <div
    class="fu"
    data-test="follow-up"
  >
    <div class="fu-head">
      <b class="fu-title">{{ application.job_title }}</b>
      <span class="fu-sent">{{ sentLine }}</span>
    </div>

    <div class="fu-band">
      <div class="fu-band-text">
        <span class="fu-band-hand">c’est le moment de relancer</span>
        <span
          v-if="!failed"
          class="fu-band-line"
        >{{ writing ? "J’écris ton message…" : "Le message est prêt, à ton nom." }}</span>
      </div>
      <img
        class="fu-band-image"
        src="/illustrations/relance-260.webp"
        alt=""
        width="130"
        height="85"
      >
    </div>

    <div
      v-if="writing"
      class="fu-letter fu-letter-wait"
      role="status"
      data-test="follow-up-writing"
    >
      <span
        class="fu-spin"
        aria-hidden="true"
      />
      J’écris ta relance… quelques secondes
    </div>

    <div
      v-else-if="failed"
      class="fu-failed"
      role="alert"
      data-test="follow-up-failed"
    >
      <p class="fu-failed-title">
        Le message n’a pas pu être écrit
      </p>
      <p class="fu-failed-text">
        L’écriture a été interrompue. Rien n’a été envoyé.
      </p>
      <BusyButton
        class="primary"
        :busy="writing"
        busy-label="Écriture…"
        data-test="follow-up-retry"
        @click="write(true)"
      >
        Réessayer
      </BusyButton>
    </div>

    <form
      v-else-if="editing"
      class="fu-edit"
      data-test="follow-up-edit"
      @submit.prevent="saveEdit"
    >
      <FormField
        v-slot="f"
        label="Objet"
      >
        <input
          :id="f.id"
          v-model="editSubject"
          :aria-describedby="f.describedby"
          maxlength="300"
          data-test="follow-up-subject"
        >
      </FormField>
      <FormField
        v-slot="f"
        label="Message"
      >
        <textarea
          :id="f.id"
          v-model="editText"
          :aria-describedby="f.describedby"
          rows="10"
          maxlength="5000"
          data-test="follow-up-text"
        />
      </FormField>
    </form>

    <template v-else-if="ready">
      <article
        class="fu-letter"
        data-test="follow-up-message"
      >
        <p
          class="fu-subject"
          data-test="follow-up-subject-read"
        >
          <span>Objet</span> {{ subject }}
        </p>
        <p
          v-for="(p, i) in paragraphs"
          :key="i"
        >
          {{ p }}
        </p>
      </article>
      <p class="fu-under">
        <span
          v-if="reason"
          data-test="follow-up-template"
        >Modèle simple, sans IA ({{ reason }}).</span>
        <button
          type="button"
          class="link"
          data-test="follow-up-rewrite"
          @click="write(true)"
        >
          Réécrire
        </button>
      </p>
    </template>

    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>

    <div class="fu-foot">
      <template v-if="editing">
        <div class="fu-main-wrap">
          <BusyButton
            class="primary"
            :busy="saving"
            busy-label="Enregistrement…"
            :disabled="!editText.trim()"
            data-test="follow-up-save"
            @click="saveEdit"
          >
            Enregistrer le message
          </BusyButton>
        </div>
        <button
          type="button"
          class="link fu-link"
          data-test="follow-up-cancel-edit"
          @click="editing = false"
        >
          Annuler
        </button>
      </template>
      <template v-else>
        <a
          v-if="mailto"
          class="button-link primary-link fu-main"
          :href="mailto"
          data-test="follow-up-mail"
        >Relancer par e-mail</a>
        <div
          v-else-if="ready"
          class="fu-main-copy"
        >
          <CopyButton
            :value="`${subject}\n\n${text}`"
            label="Copier la relance"
            text="la relance"
            test-id="follow-up-copy"
          />
        </div>
        <div class="fu-links">
          <button
            v-if="ready"
            type="button"
            class="link fu-link"
            data-test="follow-up-modify"
            @click="startEdit"
          >
            Modifier le message
          </button>
          <span
            v-if="ready && mailto"
            class="fu-copy"
          >
            <CopyButton
              :value="`${subject}\n\n${text}`"
              label="Copier"
              text="la relance"
              test-id="follow-up-copy"
            />
          </span>
          <button
            type="button"
            class="link fu-link"
            :disabled="marking"
            data-test="follow-up-done"
            @click="markDone"
          >
            Marquer comme relancée
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Valeurs du HTML de RelanceOrdinateurV2 (13.11), ramenées à la grille de 4 : poste 22/28 en gras, ligne d'envoi
   de 15 px ; bandeau pêche (rayon 20, padding 16/16/16/20), « c'est le moment de relancer » manuscrit 24 px, bleu,
   penché de 2° ; illustration de 84 px de haut ; message sur papier blanc (rayon 3, filet bleu de 6 px à gauche,
   ombre, padding 20, 16/24) ; pied collé en bas, filet au-dessus, bouton de 52 px puis liens de 48 px. */
.fu { --fu-22: 22px; --fu-28: 28px; --fu-20: 20px; --fu-24: 24px; --fu-84: 84px; --fu-52: 52px; --fu-48: 48px; --fu-6: 6px; --fu-3: 3px;
  display: flex; flex-direction: column; min-height: 100%; gap: 0; color: var(--text); }
.fu-head { display: grid; gap: var(--space-1); padding-bottom: var(--space-4); }
.fu-title { font-size: var(--fu-22); line-height: var(--fu-28); font-weight: var(--weight-heavy); }
.fu-sent { font-size: var(--font-label); color: var(--text-secondary); }
.fu-band { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--fu-24); padding: var(--space-4) var(--space-4) var(--space-4) var(--fu-20); border-radius: var(--fu-20); background: var(--peach-soft); }
.fu-band-text { flex: 1; min-width: 0; }
.fu-band-hand { display: inline-block; font-family: var(--font-hand); font-size: var(--fu-24); line-height: var(--leading-none); color: var(--primary-text); transform: rotate(-2deg); }
.fu-band-line { display: block; margin-top: var(--space-3); font-size: var(--font-label); line-height: var(--fu-22); color: var(--text-lead); }
.fu-band-image { flex: none; width: auto; height: var(--fu-84); }
.fu-letter { padding: var(--fu-20); border-left: var(--fu-6) solid var(--primary-graphic); border-radius: var(--fu-3); background: var(--surface); color: var(--text); box-shadow: 0 1px 2px rgb(27 31 42 / 10%), 0 10px 24px rgb(27 31 42 / 8%); font-size: var(--font-body); line-height: var(--fu-24); }
.fu-letter p { margin: 0 0 var(--space-3); white-space: pre-line; }
.fu-letter p:last-child { margin-bottom: 0; }
.fu-subject { font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.fu-subject > span { font-weight: var(--weight-bold); color: var(--text); }
.fu-letter-wait { display: flex; align-items: center; gap: var(--space-3); color: var(--text-secondary); }
.fu-spin { --fu-18: 18px; flex: none; width: var(--fu-18); height: var(--fu-18); box-sizing: border-box; border: 2.5px solid var(--card-line); border-top-color: var(--primary-graphic); border-radius: var(--radius-pill); animation: fu-spin 1s linear infinite; }
@keyframes fu-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .fu-spin { animation: none; } }
.fu-under { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--space-2); margin: var(--space-3) 0 0; font-size: var(--font-small); color: var(--text-secondary); }
.fu-under .link { margin-left: auto; min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); }
.fu-failed { display: flex; flex-direction: column; align-items: center; gap: var(--space-3); padding: var(--fu-28) var(--fu-24); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); background: var(--surface); box-shadow: var(--shadow-menu); text-align: center; }
.fu-failed-title { margin: 0; font-size: var(--font-title); line-height: var(--fu-24); font-weight: var(--weight-bold); }
.fu-failed-text { margin: 0; font-size: var(--font-label); line-height: var(--fu-22); color: var(--text-secondary); }
.fu-failed .primary { min-height: var(--fu-48); margin-top: var(--space-2); padding: 0 var(--fu-24); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.fu-edit { display: grid; gap: var(--space-4); }
.fu-foot { position: sticky; bottom: 0; display: grid; margin: auto calc(-1 * var(--fu-20)) 0; padding: var(--space-3) var(--fu-20) var(--fu-28); border-top: 1px solid var(--surface-muted); background: var(--bg); }
.fu-foot > .fu-main, .fu-foot > :deep(.fu-main) { display: flex; align-items: center; justify-content: center; width: 100%; min-height: var(--fu-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none; }
.fu-foot > .fu-link { justify-self: center; }
.fu-main-wrap :deep(button) { width: 100%; min-height: var(--fu-52); border-radius: var(--radius-pill); font-size: var(--font-body); }
.fu-links { display: flex; flex-wrap: wrap; justify-content: center; gap: 0 var(--space-4); margin-top: var(--space-1); }
.fu-link { min-height: var(--fu-48); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); }
.fu-copy { display: inline-flex; }
.fu-copy :deep(.copy-text) { min-width: 0; min-height: var(--fu-48); padding: 0; background: none; font-size: var(--font-label); }
.fu-main-copy :deep(.copy-text) { display: flex; align-items: center; justify-content: center; width: 100%; min-height: var(--fu-52); font-size: var(--font-body); }
.fu-main-copy :deep(.copy-text:not(.copy-done)) { background: var(--action); color: var(--on-action); }
.fu-head, .fu-band, .fu-letter, .fu-under, .fu-failed, .fu-edit { flex: none; }
</style>
