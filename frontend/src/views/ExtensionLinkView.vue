<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { browserName } from "../browserName";

// « Relier ce navigateur » (docs/71 §4) : ouverte par l'extension, qui lit le jeton dans cet
// onglet puis l'efface de la page. Le jeton n'est jamais dans l'adresse. Sans extension pour le
// lire, il est révoqué au bout de 2 minutes.
const UNREAD_MS = 120_000;

const router = useRouter();
const name = browserName();
const state = ref<"idle" | "waiting" | "linked" | "timeout" | "error">("idle");
const token = ref<string | null>(null);
const output = ref<HTMLOutputElement | null>(null);
let tokenId: number | null = null;
let observer: MutationObserver | null = null;
let timer: ReturnType<typeof setTimeout> | undefined;

function stop(): void {
  observer?.disconnect();
  observer = null;
  clearTimeout(timer);
}

async function link(): Promise<void> {
  const { data } = await api.POST("/api/extension-tokens", { body: { name, link: true } });
  if (!data) {
    state.value = "error";
    return;
  }
  tokenId = data.id;
  token.value = data.token;
  state.value = "waiting";
  await nextTick();
  // L'extension efface le jeton de la page une fois lu.
  observer = new MutationObserver(() => {
    if (output.value && !output.value.dataset.token) {
      stop();
      token.value = null;
      state.value = "linked";
    }
  });
  if (output.value) observer.observe(output.value, { attributes: true });
  timer = setTimeout(() => void expire(), UNREAD_MS);
  // Le changement d'adresse prévient l'extension que le jeton est là.
  await router.replace({ query: { etat: "pret" } });
}

async function expire(): Promise<void> {
  stop();
  token.value = null;
  state.value = "timeout";
  if (tokenId !== null) {
    await api.DELETE("/api/extension-tokens/{token_id}", { params: { path: { token_id: tokenId } } });
  }
}

onBeforeUnmount(stop);
</script>

<template>
  <section class="band">
    <div class="container extension-link">
      <h1>Relier ce navigateur</h1>
      <template v-if="state === 'linked'">
        <p
          class="extension-link-done"
          data-test="link-done"
        >
          C'est relié. Tu peux fermer cet onglet : l'icône jobA1 de ton navigateur est prête.
        </p>
      </template>
      <template v-else>
        <p>L'extension jobA1 de ce navigateur ({{ name }}) pourra :</p>
        <ul>
          <li>remplir les formulaires de candidature et la saisie Job-Room avec tes données ;</li>
          <li>enregistrer « J'ai envoyé » et « C'est déclaré » dans ton Suivi ;</li>
          <li>proposer, à ta demande, une réponse aux questions libres d'un formulaire.</li>
        </ul>
        <p class="muted">
          Elle n'agit que quand tu cliques. Tu peux la délier dans Réglages › Outils.
        </p>
        <p
          v-if="state === 'waiting'"
          class="muted"
          data-test="link-waiting"
        >
          En attente de l'extension…
        </p>
        <p
          v-else-if="state === 'timeout'"
          class="notice"
          data-test="link-timeout"
        >
          L'extension n'a pas répondu : ouvre-la et clique sur « Relier ».
        </p>
        <p
          v-else-if="state === 'error'"
          class="notice"
        >
          Le lien n'a pas pu être créé. Réessaie.
        </p>
        <div class="form-actions">
          <button
            type="button"
            class="primary"
            :disabled="state === 'waiting'"
            data-test="link-browser"
            @click="link"
          >
            Relier ce navigateur
          </button>
          <RouterLink
            to="/reglages"
            class="link"
          >
            Annuler
          </RouterLink>
        </div>
      </template>
      <!-- Lu puis effacé par l'extension ; jamais affiché. -->
      <output
        id="jobbot-extension-token"
        ref="output"
        hidden
        :data-token="token ?? undefined"
      />
    </div>
  </section>
</template>
