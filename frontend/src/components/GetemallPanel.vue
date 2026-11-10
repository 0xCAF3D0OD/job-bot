<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { dateWithTime } from "../dates";
import AppIcon from "./AppIcon.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Réglages › Connexions, Get'emAll (docs/140, maquettes ReglagesConnexions et ReglagesRetirer) : l'app reliée,
// sa dernière lecture, « Partager mes recherches ORP » (enregistré tout de suite, sans nouvelle autorisation) et
// « Retirer l'accès » après confirmation. La confirmation est en bleu : retirer se refait en un clic (I-4).
type LinkState = components["schemas"]["GetemallLinkState"];

const state = ref<LinkState | null>(null);
const saved = ref(false);
const error = ref("");
const confirming = ref(false);
const dialog = ref<HTMLDialogElement | null>(null);
let returnTo: HTMLElement | null = null;

async function load(): Promise<void> {
  const { data } = await api.GET("/api/partenaires/getemall");
  state.value = data ?? null;
}

async function share(orp: boolean): Promise<void> {
  saved.value = false;
  error.value = "";
  const { data } = await api.PATCH("/api/partenaires/getemall", { body: { orp } });
  if (data) {
    state.value = data;
    saved.value = true;
  } else {
    error.value = "Pas enregistré. Réessaie.";
  }
}

async function open(): Promise<void> {
  confirming.value = true;
  returnTo = document.activeElement as HTMLElement | null;
  await nextTick();
  const el = dialog.value;
  if (el && typeof el.showModal === "function") el.showModal();
  else el?.setAttribute("open", "");
}

function close(): void {
  const el = dialog.value;
  if (el && typeof el.close === "function" && el.open) el.close();
  confirming.value = false;
  returnTo?.focus?.();
}

async function revoke(): Promise<void> {
  const { response } = await api.DELETE("/api/partenaires/getemall");
  close();
  if (!response.ok) {
    error.value = "L’accès n’a pas pu être retiré. Réessaie.";
    return;
  }
  await load();
}

onMounted(load);
</script>

<template>
  <template v-if="state?.available">
    <SettingCard
      v-if="state.linked"
      data-test="getemall-panel"
    >
      <div class="partner-app">
        <span
          class="partner-app-tile"
          aria-hidden="true"
        ><AppIcon name="chat" /></span>
        <span class="setting-row-text">
          <span class="setting-row-title">Get’emAll</span>
          <span class="setting-row-description">Entraînement aux entretiens, lecture seule</span>
          <span
            class="setting-row-description"
            data-test="getemall-last-read"
          >
            {{ state.last_used_at ? `Dernière lecture : ${dateWithTime(state.last_used_at)}` : "Pas encore lu" }}
          </span>
        </span>
      </div>
      <SettingRow
        v-slot="c"
        title="Partager mes recherches ORP"
        description="Le nombre fait et l’objectif du mois"
        :saved="saved"
        :error="error"
      >
        <input
          type="checkbox"
          role="switch"
          :checked="state.orp"
          :aria-labelledby="c.labelledby"
          :aria-describedby="c.describedby"
          data-test="getemall-orp"
          @change="share(!state.orp)"
        >
      </SettingRow>
      <div class="partner-app-remove">
        <button
          type="button"
          class="partner-app-remove-button"
          data-test="getemall-remove"
          @click="open"
        >
          Retirer l’accès
        </button>
      </div>
    </SettingCard>
    <p
      v-else
      class="partner-app-empty"
      role="status"
      data-test="getemall-empty"
    >
      Aucune application reliée. Celles que tu autorises apparaissent ici.
    </p>
    <dialog
      v-if="confirming"
      ref="dialog"
      class="partner-confirm"
      role="alertdialog"
      aria-labelledby="getemall-remove-title"
      aria-describedby="getemall-remove-text"
      data-test="getemall-confirm"
      @cancel.prevent="close"
    >
      <h2 id="getemall-remove-title">
        Retirer l’accès de Get’emAll&nbsp;?
      </h2>
      <p id="getemall-remove-text">
        Get’emAll ne pourra plus lire ton suivi. Ton entraînement reste dans Get’emAll : tu peux l’effacer depuis
        l’app. Tu pourras relier ton compte de nouveau plus tard.
      </p>
      <div class="partner-confirm-actions">
        <button
          type="button"
          class="partner-confirm-keep"
          data-test="getemall-keep"
          @click="close"
        >
          Garder l’accès
        </button>
        <button
          type="button"
          class="partner-confirm-remove"
          data-test="getemall-confirm-remove"
          @click="revoke"
        >
          Retirer l’accès
        </button>
      </div>
    </dialog>
  </template>
</template>

<style>
/* Maquettes ReglagesConnexions et ReglagesRetirer (390 px) : mesures du HTML, couleurs des jetons. Rayons hors
   échelle rangés sur la plus proche (D7) : tuile 14 et bouton 16 → --radius-card, fenêtre 26 → --radius-block. */
.partner-app { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-5) var(--space-6); }
.partner-app-tile { flex: none; display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; box-sizing: border-box; border-radius: var(--radius-card); background: var(--peach-soft); border: 1px solid var(--line); color: var(--primary-text); }
.partner-app-tile .icon { width: 24px; height: 24px; stroke-width: var(--icon-stroke); }
.partner-app + .setting-row, .setting-row + .partner-app-remove { border-top: 1px solid var(--divider); }
.partner-app-remove { padding: var(--space-3) var(--space-6) var(--space-5); }
.partner-app-remove-button { width: 100%; min-height: var(--btn-tertiary); justify-content: center; border: 1.5px solid var(--line); border-radius: var(--radius-card); background: var(--surface); color: var(--primary-text); font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold); cursor: pointer; }
.partner-app-empty { margin: 0; padding: var(--space-4); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.partner-confirm { width: calc(100% - 2 * var(--space-6)); max-width: 420px; box-sizing: border-box; padding: var(--space-6) var(--space-5) var(--space-5); border: 0; border-radius: var(--radius-block); background: var(--surface); color: var(--text); box-shadow: 0 20px 50px rgba(27, 31, 42, 0.25); }
.partner-confirm[open] { display: flex; flex-direction: column; gap: var(--space-3); }
.partner-confirm::backdrop { background: rgba(27, 31, 42, 0.45); }
.partner-confirm h2 { margin: 0; font-size: var(--font-section); line-height: var(--leading-tight); font-weight: var(--weight-bold); }
.partner-confirm p { margin: 0; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.partner-confirm-actions { display: flex; flex-direction: column; gap: var(--space-2); margin-top: var(--space-1); }
.partner-confirm-actions button { height: var(--btn-secondary); justify-content: center; border: 0; border-radius: var(--radius-pill); font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold); cursor: pointer; }
.partner-confirm-keep { background: var(--text); color: var(--surface); }
.partner-confirm-remove { background: transparent; color: var(--primary-text); }
@media (max-width: 820px) {
  .partner-app { padding: var(--space-4); }
  .partner-app-remove { padding: var(--space-2) var(--space-4) var(--space-4); }
}
</style>
