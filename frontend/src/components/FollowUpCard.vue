<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api, type Application } from "../api/client";
import AppIcon from "./AppIcon.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// La relance conseillée d'une candidature envoyée (MODIFICATIONS du 9 novembre, §8.1) : le message déjà écrit
// (docs/38 : IA ou modèle simple ; rien n'est envoyé par jobA1), le destinataire et le canal avec « Changer », puis
// « Ouvrir l’e-mail » ou « Copier et ouvrir LinkedIn ». Quand la personne revient sur jobA1, la candidature passe à
// « Relancée ».
const props = defineProps<{ application: Application; linkedinUrl?: string | null }>();
const emit = defineEmits<{ edit: []; done: [] }>();

type Draft = { subject: string; text: string };
// Une rédaction par candidature et par session : rouvrir le détail ne relance pas l'IA.
const drafts = draftCache();

const draft = ref<Draft | null>(drafts.get(props.application.id) ?? null);
const loading = ref(false);
const failed = ref(false);
const editing = ref(false);
const sentOut = ref(false);
const saveError = ref("");

const canMail = computed(() => !!props.application.contact_email);
const channel = ref<"email" | "linkedin">(canMail.value ? "email" : "linkedin");
const recipient = computed(() => {
  const a = props.application;
  if (channel.value === "email") return a.contact_name || a.contact_email || a.company;
  return a.contact_name || `Recrutement, ${a.company}`;
});
const changeItems = computed<MoreMenuItem[]>(() => [
  ...(canMail.value && channel.value !== "email"
    ? [{ label: "Par e-mail", test: "follow-channel-email", icon: "mail" as const, run: () => (channel.value = "email") }]
    : []),
  ...(channel.value !== "linkedin"
    ? [{ label: "Sur LinkedIn", test: "follow-channel-linkedin", icon: "external" as const, run: () => (channel.value = "linkedin") }]
    : []),
  { label: "Modifier le contact", test: "follow-contact-edit", icon: "pencil", run: () => emit("edit") },
]);
const mailto = computed(() => {
  const to = props.application.contact_email;
  if (!to || !draft.value) return null;
  const query = new URLSearchParams({ subject: draft.value.subject, body: draft.value.text }).toString().replace(/\+/g, "%20");
  return `mailto:${encodeURIComponent(to)}?${query}`;
});

async function write(): Promise<void> {
  loading.value = true;
  failed.value = false;
  try {
    const { data } = await api.POST("/api/applications/{application_id}/follow-up/draft", {
      params: { path: { application_id: props.application.id } },
    });
    if (!data) {
      failed.value = true;
      return;
    }
    draft.value = { subject: data.subject, text: data.text };
    drafts.set(props.application.id, draft.value);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

function keep(): void {
  if (draft.value) drafts.set(props.application.id, { ...draft.value });
}

async function copyAndOpen(): Promise<void> {
  if (!draft.value) return;
  try {
    await navigator.clipboard.writeText(draft.value.text);
  } catch {
    // Copie refusée par le navigateur : LinkedIn s'ouvre quand même, le message reste affiché ici.
  }
  if (props.linkedinUrl) window.open(props.linkedinUrl, "_blank", "noopener,noreferrer");
  sentOut.value = true;
}

// Le retour sur l'onglet après l'envoi : la candidature passe à « Relancée » (docs/38).
async function markDone(): Promise<void> {
  if (!sentOut.value || document.visibilityState !== "visible") return;
  sentOut.value = false;
  saveError.value = "";
  const { data } = await api.POST("/api/applications/{application_id}/follow-up", {
    params: { path: { application_id: props.application.id } },
  });
  if (!data) {
    saveError.value = "La relance n’a pas pu être enregistrée.";
    return;
  }
  drafts.delete(props.application.id);
  emit("done");
}

onMounted(() => {
  if (!draft.value) void write();
  document.addEventListener("visibilitychange", markDone);
  window.addEventListener("focus", markDone);
});
onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", markDone);
  window.removeEventListener("focus", markDone);
});
watch(
  () => props.application.id,
  (id) => {
    draft.value = drafts.get(id) ?? null;
    editing.value = false;
    sentOut.value = false;
    channel.value = canMail.value ? "email" : "linkedin";
    if (!draft.value) void write();
  },
);
</script>

<script lang="ts">
const cache = new Map<number, { subject: string; text: string }>();
function draftCache(): Map<number, { subject: string; text: string }> {
  return cache;
}
</script>

<template>
  <section
    class="follow-card-wrap"
    aria-labelledby="follow-card-title"
    data-test="follow-card"
  >
    <div class="sent-card follow-card">
      <p
        id="follow-card-title"
        class="follow-card-cap"
      >
        Relance conseillée
      </p>
      <b class="follow-card-title">{{ failed ? "Le message n’a pas pu être écrit" : "Ton message est prêt" }}</b>
      <span
        v-if="!failed"
        class="follow-card-help"
      >Court et poli, à envoyer au même endroit que ta candidature.</span>
      <p
        v-if="loading"
        class="follow-card-quote follow-card-wait"
        role="status"
        data-test="follow-writing"
      >
        J’écris ton message…
      </p>
      <label
        v-else-if="draft && editing"
        class="follow-card-edit"
      >
        <span class="visually-hidden">Message de relance</span>
        <textarea
          v-model="draft.text"
          rows="6"
          data-test="follow-text"
          @input="keep"
        />
      </label>
      <blockquote
        v-else-if="draft"
        class="follow-card-quote"
        data-test="follow-quote"
      >
        {{ draft.text }}
      </blockquote>
      <p
        class="follow-card-to"
        data-test="follow-to"
      >
        À : <b>{{ recipient }}</b> · {{ channel === "email" ? "E-mail" : "LinkedIn" }} ·
        <MoreMenu
          class="follow-card-change"
          :items="changeItems"
          :inline="false"
          trigger="Changer"
          label="Changer le destinataire ou le canal"
          test-id="follow-change"
        />
      </p>
      <div class="follow-card-actions">
        <button
          v-if="failed"
          type="button"
          class="primary"
          data-test="follow-retry"
          @click="write"
        >
          Réessayer
        </button>
        <template v-else>
          <a
            v-if="channel === 'email'"
            :class="['button-link', 'primary-link', { disabled: !mailto }]"
            :href="mailto ?? undefined"
            :aria-disabled="!mailto"
            data-test="follow-open"
            @click="sentOut = !!mailto"
          ><span class="with-icon">Ouvrir l’e-mail<AppIcon name="mail" /></span></a>
          <button
            v-else
            type="button"
            class="primary"
            :disabled="!draft"
            data-test="follow-open"
            @click="copyAndOpen"
          >
            <span class="with-icon">Copier et ouvrir LinkedIn<AppIcon name="external" /></span><span class="visually-hidden"> (nouvel onglet)</span>
          </button>
          <button
            type="button"
            class="link"
            :disabled="!draft"
            :aria-pressed="editing"
            data-test="follow-edit"
            @click="editing = !editing"
          >
            {{ editing ? "Terminé" : "Modifier" }}
          </button>
        </template>
      </div>
      <p
        v-if="saveError"
        class="notice error"
        role="alert"
      >
        {{ saveError }}
      </p>
    </div>
    <p class="follow-card-note">
      Quand tu reviens, le statut passe à « Relancé » et la prochaine relance est proposée dans 10 jours.
    </p>
  </section>
</template>

<style>
/* Valeurs de CandidaturesOrdinateurB (onglet Envoyées) : libellé 13/16 700 capitales #8A4A16, titre 16/22, aide 14/20
   grise, citation 15/22 à trait gauche de 3 px, ligne « À : » 14/20, bouton plein de 48 px, « Modifier » en lien. */
.follow-card { --follow-13: 13px; --follow-16: 16px; --follow-22: 22px; --follow-3: 3px; --follow-2: 2px; }
.follow-card-cap { margin: 0 0 var(--space-1); font-size: var(--follow-13); line-height: var(--follow-16); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--peach-text); }
.follow-card-title { display: block; font-size: var(--font-body); line-height: var(--follow-22); }
.follow-card-help { display: block; margin-top: var(--follow-2); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.follow-card-quote { margin: var(--space-4) 0 0; padding: var(--follow-2) 0 var(--follow-2) var(--space-4); border-left: var(--follow-3) solid var(--card-line); font-size: var(--font-label); line-height: var(--follow-22); color: var(--text-secondary); white-space: pre-line; }
.follow-card-wait { font-style: italic; }
.follow-card-edit textarea { width: 100%; margin-top: var(--space-4); font: inherit; font-size: var(--font-label); line-height: var(--follow-22); }
.follow-card-to { display: flex; flex-wrap: wrap; align-items: center; gap: 0 var(--space-1); margin: var(--space-4) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.follow-card-to b { color: var(--text); }
.follow-card-change .more-trigger { min-height: var(--space-6); padding: 0; border: 0; background: none; color: var(--primary-text); font-size: inherit; font-weight: var(--weight-bold); }
.follow-card-actions { display: flex; align-items: center; gap: var(--space-5); margin-top: var(--space-4); }
.follow-card-actions :is(.primary, .primary-link) { min-height: var(--space-12); padding: 0 var(--space-5); border-radius: var(--radius-pill); }
.follow-card-actions .link { min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); }
.follow-card-note { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
</style>
