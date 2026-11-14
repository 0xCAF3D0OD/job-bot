<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { api, type Application } from "../api/client";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// La relance conseillée d'une candidature envoyée (MODIFICATIONS du 9 novembre, §8.1) : le message déjà écrit
// (docs/38 : IA ou modèle simple ; rien n'est envoyé par jobA1), le destinataire et le canal avec « Changer », puis
// « Ouvrir l’e-mail » ou « Copier et ouvrir LinkedIn ». Quand la personne revient sur jobA1, la candidature passe à
// « Relancée ».
const props = defineProps<{ application: Application; linkedinUrl?: string | null; compact?: boolean }>();
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
const sheetOpen = ref(false);

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
  <!-- Ordinateur (maquette du 14 novembre, §8 Envoyées point 3 ; planche CandidaturesOrdinateurStatut) : en-tête
       « Relance conseillée » et sa pastille, ligne « À » avec « Changer », ligne « Message », pied à deux pilules de
       52 px (le libellé suit le canal : « Relancer par e-mail » ou « Copier et ouvrir LinkedIn »), puis « Après l’envoi ». -->
  <section
    v-if="!compact"
    class="sent-card follow-card fc-card"
    aria-labelledby="follow-card-title"
    data-test="follow-card"
  >
    <header class="fc-head">
      <h3
        id="follow-card-title"
        class="follow-card-title"
      >
        {{ failed ? "Le message n’a pas pu être écrit" : "Relance conseillée" }}
      </h3>
      <span
        v-if="draft && !failed"
        class="fc-pill"
      >Message prêt</span>
    </header>
    <div
      class="fc-row fc-to"
      data-test="follow-to"
    >
      <span class="fc-row-text"><span class="fc-label">À</span><b>{{ recipient }} · {{ channel === "email" ? "E-mail" : "LinkedIn" }}</b></span>
      <MoreMenu
        class="follow-card-change"
        :items="changeItems"
        :inline="false"
        trigger="Changer"
        label="Changer le destinataire ou le canal"
        test-id="follow-change"
      />
    </div>
    <div
      v-if="loading || draft"
      class="fc-row fc-message"
    >
      <span class="fc-label">Message</span>
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
      <p
        v-else-if="draft"
        class="follow-card-quote"
        data-test="follow-quote"
      >
        {{ draft.text }}
      </p>
    </div>
    <div class="fc-actions">
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
        ><span class="with-icon">Relancer par e-mail<AppIcon name="mail" /></span></a>
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
          class="secondary"
          :disabled="!draft"
          :aria-pressed="editing"
          data-test="follow-edit"
          @click="editing = !editing"
        >
          {{ editing ? "Terminé" : "Modifier le message" }}
        </button>
      </template>
    </div>
    <p
      v-if="saveError"
      class="notice error fc-error"
      role="alert"
    >
      {{ saveError }}
    </p>
    <p class="fc-after">
      <span class="fc-after-pill">Après l’envoi</span>
      Quand tu reviens, le statut passe à « Relancé » et la prochaine relance est proposée dans 10 jours.
    </p>
  </section>
  <section
    v-else
    class="sent-card follow-card follow-card-compact"
    aria-labelledby="follow-card-title"
    data-test="follow-card"
  >
    <!-- Téléphone (§8.3, EnvoyeeDetail et EnvoyeeDetailRelance) : carte compacte et « Voir et envoyer », qui ouvre la
            feuille Relance (destinataire, message entier, note, pied fixe). -->
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
    >Court et poli, à envoyer {{ channel === "email" ? "par e-mail" : "sur LinkedIn" }} à {{ application.company }}.</span>
    <button
      v-if="failed"
      type="button"
      class="primary follow-card-wide"
      data-test="follow-retry"
      @click="write"
    >
      Réessayer
    </button>
    <button
      v-else
      type="button"
      class="primary follow-card-wide"
      :disabled="loading"
      data-test="follow-sheet-open"
      @click="sheetOpen = true"
    >
      {{ loading ? "J’écris ton message…" : "Voir et envoyer" }}
    </button>
    <BottomSheet
      :open="sheetOpen"
      title="Relance"
      @close="sheetOpen = false"
    >
      <div
        class="follow-sheet"
        data-test="follow-sheet"
      >
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
        <label
          v-if="draft && editing"
          class="follow-card-edit"
        >
          <span class="visually-hidden">Message de relance</span>
          <textarea
            v-model="draft.text"
            rows="10"
            data-test="follow-text"
            @input="keep"
          />
        </label>
        <div
          v-else-if="draft"
          class="follow-sheet-message"
          data-test="follow-quote"
        >
          {{ draft.text }}
        </div>
        <p class="follow-card-note">
          Quand tu reviens, le statut passe à « Relancé » et la prochaine relance est proposée dans 10 jours.
        </p>
        <p
          v-if="saveError"
          class="notice error"
          role="alert"
        >
          {{ saveError }}
        </p>
      </div>
      <template #actions>
        <div class="follow-sheet-actions">
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
            {{ editing ? "Terminé" : "Modifier le message" }}
          </button>
        </div>
      </template>
    </BottomSheet>
  </section>
</template>

<style>
/* Valeurs de CandidaturesOrdinateurB (onglet Envoyées) : libellé 13/16 700 capitales #8A4A16, titre 18/24 à 8 px du libellé, aide 14/20 à 4 px
   grise, citation 15/22 à trait gauche de 3 px, ligne « À : » 14/20, bouton plein de 48 px, « Modifier » en lien. */
.follow-card { --follow-17: 17px; --follow-18: 18px; --follow-18-5: 18.5px; --follow-13: 13px; --follow-16: 16px; --follow-22: 22px; --follow-3: 3px; }
.follow-card-cap { margin: 0 0 var(--space-2); font-size: var(--follow-13); line-height: var(--follow-16); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--peach-text); }
.follow-card-title { display: block; font-size: var(--follow-18); line-height: var(--space-6); }
.follow-card-help { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.follow-card-quote { margin: var(--space-4) 0 0; padding: 0 0 0 var(--space-4); border-left: var(--follow-3) solid var(--card-line); font-size: var(--font-label); line-height: var(--follow-22); color: var(--text-secondary); white-space: pre-line; }
/* Un extrait de 4 lignes, coupé par « … » : « Modifier » montre le message en entier (prompt récapitulatif du
   11 novembre, PR 32). La lettre complète ne s'affiche pas dans la carte. */
.follow-card-quote { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 4; line-clamp: 4; overflow: hidden; }
.follow-card-wait { font-style: italic; }
.follow-card-edit textarea { width: 100%; margin-top: var(--space-4); font: inherit; font-size: var(--font-label); line-height: var(--follow-22); }
.follow-card-to { display: flex; flex-wrap: wrap; align-items: center; gap: 0 var(--space-1); margin: var(--space-4) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.follow-card-to b { color: var(--text); }
.follow-card-change .more-trigger { min-height: var(--space-6); padding: 0; border: 0; background: none; color: var(--primary-text); font-size: inherit; font-weight: var(--weight-bold); }
.follow-card-actions { display: flex; align-items: center; gap: var(--space-5); margin-top: var(--space-4); }
.follow-card-actions :is(.primary, .primary-link) { min-height: var(--space-12); padding: 0 var(--space-5); border-radius: var(--radius-pill); }
.follow-card-actions .link { min-height: var(--target-min); font-size: var(--font-label); font-weight: var(--weight-bold); }
.follow-card-note { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
/* Ordinateur, maquette du 14 novembre (§8, §9 ; planche CandidaturesOrdinateurStatut) : en-tête de 20 px de marge,
   titre 18/700, pastille verte ; lignes à étiquette 13 grise au-dessus de la valeur 15/700, 12 px en haut et en bas,
   64 px au moins, filet de 1 px ; pilules de 52 px, 12 px entre elles ; « Après l’envoi » en pastille grise. */
.sent-card.fc-card { --fc-x: 20px; --fc-r: 6px; --fc-52: 52px; --fc-64: 64px; padding: 0; overflow: hidden; }
.fc-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: var(--space-4) var(--fc-x); border-bottom: 1px solid var(--line); }
.fc-head .follow-card-title { margin: 0; font-size: var(--follow-18); line-height: var(--space-6); font-weight: var(--weight-bold); }
.fc-pill, .fc-after-pill { flex: none; padding: var(--space-1) var(--space-2); border-radius: var(--fc-r); font-size: var(--follow-13); line-height: var(--follow-16); font-weight: var(--weight-bold); }
.fc-pill { background: var(--success-soft); color: var(--success); }
.fc-row { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; min-height: var(--fc-64); padding: var(--space-3) var(--fc-x); border-bottom: 1px solid var(--line); }
.fc-row-text { flex: 1; min-width: 0; }
.fc-label { display: block; font-size: var(--follow-13); line-height: var(--space-5); color: var(--text-secondary); }
.fc-row b { display: block; font-size: var(--font-label); line-height: var(--space-5); }
.fc-message { flex-direction: column; align-items: stretch; gap: var(--space-1); }
.fc-card .follow-card-quote { margin: 0; padding: 0; border: 0; font-size: var(--font-label); line-height: var(--follow-22); color: var(--text); }
.fc-card .follow-card-edit textarea { margin-top: 0; }
.fc-card .follow-card-change .more-trigger { min-height: var(--target-min); font-size: var(--font-label); }
.fc-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); padding: var(--space-4) var(--fc-x); border-bottom: 1px solid var(--line); }
.fc-actions :is(.primary, .primary-link, .secondary) { min-height: var(--fc-52); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.fc-actions .secondary { border: 1.5px solid var(--line-strong); background: var(--surface); color: var(--text); }
.fc-error { margin: var(--space-3) var(--fc-x) 0; }
.fc-after { display: flex; align-items: center; gap: var(--space-3); margin: 0; padding: var(--space-3) var(--fc-x); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.fc-after-pill { background: color-mix(in srgb, var(--text) 7%, var(--surface)); color: var(--text); }
/* Téléphone (EnvoyeeDetail, EnvoyeeDetailRelance) : titre 17/24, phrase 15/22, bouton plein pleine largeur de 48 à
   20 px ; dans la feuille, « À : » 15/22, message dans une carte blanche 16/24, pied à deux boutons empilés. */
.follow-card-compact .follow-card-cap { margin-bottom: var(--space-2); }
.follow-card-compact .follow-card-title { font-size: var(--follow-17); line-height: var(--space-6); }
.follow-card-compact .follow-card-help { margin-top: var(--space-1); font-size: var(--font-label); line-height: var(--follow-22); }
.follow-card-wide { justify-content: center; width: 100%; min-height: var(--space-12); margin-top: var(--space-5); border-radius: var(--radius-pill); }
.follow-sheet, .follow-sheet-actions { --follow-18-5: 18.5px; --follow-22: 22px; --follow-52: 52px; }
.follow-sheet { display: flex; flex-direction: column; gap: var(--space-4); }
.follow-sheet .follow-card-change .more-trigger { min-height: var(--target-min); }
.follow-sheet .follow-card-to { margin: 0; font-size: var(--font-label); line-height: var(--follow-22); }
.follow-sheet-message { padding: var(--follow-18-5); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); font-size: var(--font-body); line-height: var(--space-6); white-space: pre-line; }
.follow-sheet .follow-card-note { margin: 0; }
.follow-sheet-actions { display: flex; flex-direction: column; align-items: stretch; gap: var(--space-1); width: 100%; }
.follow-sheet-actions :is(.primary, .primary-link) { justify-content: center; min-height: var(--follow-52); border-radius: var(--radius-pill); }
.follow-sheet-actions .link { justify-content: center; text-align: center; min-height: var(--space-12); font-size: var(--font-body); font-weight: var(--weight-bold); }
</style>
