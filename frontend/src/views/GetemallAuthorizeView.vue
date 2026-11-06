<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import BrandMark from "../components/BrandMark.vue";

// « Relier Get'emAll à ton compte ? » (docs/140, maquette AutoriserGetemall) : ouverte par
// Get'emAll avec l'adresse de retour, l'état et le défi PKCE. Le serveur compare l'adresse à sa
// liste, pour « Autoriser » comme pour « Refuser » : la page ne redirige jamais d'elle-même.
// La case ORP est décochée au départ et ne vaut qu'au clic sur « Autoriser » (I-4).
const route = useRoute();
const router = useRouter();

function param(name: string): string {
  const value = route.query[name];
  return typeof value === "string" ? value : "";
}

const request = {
  redirect_uri: param("redirect_uri"),
  state: param("state"),
  code_challenge: param("code_challenge"),
  method: param("code_challenge_method"),
};
const complete = Boolean(request.redirect_uri && request.state && request.code_challenge) && request.method === "S256";

const READS = [
  { label: "Tes premiers pas", hint: "Combien sont faits sur 5, et le suivant" },
  { label: "Tes candidatures", hint: "Poste, entreprise, statut, date d'entretien" },
  { label: "Le texte d'une offre", hint: "Quand tu t'entraînes pour elle, sans les contacts" },
] as const;

const orp = ref(false);
const status = ref<"loading" | "ready" | "leaving" | "blocked">("loading");
const message = ref("");

// « Tu reviendras ensuite sur getthemall.ch » : le site de l'adresse de retour ; l'app, sinon.
const back = computed(() => {
  try {
    const url = new URL(request.redirect_uri);
    if (url.protocol === "https:" && url.hostname) return `sur ${url.hostname}`;
  } catch {
    // Adresse illisible : le serveur la refusera de toute façon.
  }
  return "dans Get'emAll";
});

const BLOCKED: Record<number, string> = {
  400: "Ce lien ne vient pas de Get'emAll. Reviens dans l'app et réessaie.",
  403: "Get'emAll est réservé aux testeurs invités pour l'instant.",
  404: "La connexion avec Get'emAll n'est pas ouverte sur jobA1.",
};

function block(code: number | undefined): void {
  status.value = "blocked";
  message.value = (code && BLOCKED[code]) || "Ça n'a pas marché. Reviens dans Get'emAll et réessaie.";
}

onMounted(async () => {
  if (!complete) {
    block(400);
    return;
  }
  const { data } = await api.GET("/api/partenaires/getemall");
  if (!data) block(undefined);
  else if (!data.available) block(404);
  else if (!data.tester) block(403);
  else status.value = "ready";
});

async function allow(): Promise<void> {
  status.value = "leaving";
  const { data, response } = await api.POST("/api/partenaires/getemall/autorisation", {
    body: {
      redirect_uri: request.redirect_uri,
      state: request.state,
      code_challenge: request.code_challenge,
      code_challenge_method: "S256",
      orp: orp.value,
    },
  });
  if (data) window.location.assign(data.redirect_to);
  else block(response.status);
}

async function refuse(): Promise<void> {
  status.value = "leaving";
  const { data } = complete
    ? await api.POST("/api/partenaires/getemall/refus", {
        body: { redirect_uri: request.redirect_uri, state: request.state },
      })
    : { data: undefined };
  if (data) window.location.assign(data.redirect_to);
  else await router.replace({ path: "/aujourdhui" });
}
</script>

<template>
  <div class="partner-page">
    <main class="partner-main">
      <div
        class="partner-tiles"
        aria-hidden="true"
      >
        <span class="partner-tile">
          <BrandMark :size="36" />
        </span>
        <AppIcon
          name="swap"
          class="partner-swap"
        />
        <span class="partner-tile partner-tile-getemall">
          <AppIcon name="chat" />
        </span>
      </div>
      <header class="partner-head">
        <h1>Relier Get'emAll à ton compte&nbsp;?</h1>
        <p>Get'emAll t'entraîne aux entretiens. Avec ton accord, il lit ton suivi pour t'entraîner sur tes vraies candidatures.</p>
      </header>
      <p
        v-if="status === 'blocked'"
        class="partner-blocked"
        role="alert"
        data-test="partner-blocked"
      >
        <AppIcon name="alert-circle" />
        {{ message }}
      </p>
      <section
        aria-labelledby="partner-reads"
        class="partner-section"
      >
        <h2 id="partner-reads">
          Get'emAll pourra lire
        </h2>
        <ul class="partner-list">
          <li
            v-for="item in READS"
            :key="item.label"
            class="partner-row"
          >
            <span class="partner-dot partner-dot-yes"><AppIcon name="tick" /></span>
            <span class="partner-text">
              <span class="partner-label">{{ item.label }}</span>
              <span class="partner-hint">{{ item.hint }}</span>
            </span>
          </li>
          <li class="partner-orp">
            <label
              for="partner-orp"
              class="partner-row"
              :class="{ 'is-checked': orp }"
            >
              <input
                id="partner-orp"
                v-model="orp"
                type="checkbox"
                data-test="partner-orp"
              >
              <span class="partner-text">
                <span class="partner-label">Aussi mes recherches ORP du mois</span>
                <span class="partner-hint">Facultatif. Seulement le nombre fait et l'objectif, jamais le détail ni tes preuves.</span>
              </span>
            </label>
          </li>
        </ul>
      </section>
      <section
        aria-labelledby="partner-never"
        class="partner-section"
      >
        <h2 id="partner-never">
          Get'emAll ne lira jamais
        </h2>
        <div class="partner-never">
          <span class="partner-dot"><AppIcon name="ban" /></span>
          <p>Ton nom, tes coordonnées, ton numéro AVS, ton CV, tes lettres et tes documents, les contacts des offres, tes preuves ORP, ni l'identifiant de ton compte jobA1.</p>
        </div>
      </section>
      <p class="partner-note">
        Lecture seule : Get'emAll ne peut rien changer dans jobA1. Tu peux retirer l'accès à tout moment dans
        <strong>Réglages › Connexions</strong>.
        <RouterLink :to="{ name: 'privacy', hash: '#getemall' }">
          Détails dans Données personnelles
        </RouterLink>
      </p>
    </main>
    <footer class="partner-foot">
      <button
        type="button"
        class="partner-allow"
        :disabled="status !== 'ready'"
        data-test="partner-allow"
        @click="allow"
      >
        {{ status === "leaving" ? "Retour vers Get'emAll…" : "Autoriser" }}
      </button>
      <button
        type="button"
        class="partner-refuse"
        :disabled="status === 'leaving'"
        data-test="partner-refuse"
        @click="refuse"
      >
        Refuser
      </button>
      <p class="partner-back">
        Tu reviendras ensuite {{ back }}
      </p>
    </footer>
  </div>
</template>

<style>
/* Maquette AutoriserGetemall (390 px) : mesures du HTML de la maquette, couleurs des jetons. Les tailles hors
   échelle sont rangées sur la plus proche (titre 24 → --font-section, 15 → --font-body, 13 → --font-small,
   tuiles 20 → --radius-card, espacements 14, 18 et 22 → --space-4 et --space-5). */
.partner-page { display: flex; flex-direction: column; min-height: 100dvh; background: var(--bg); color: var(--text); }
.partner-main { flex: 1; display: flex; flex-direction: column; gap: var(--space-4); width: 100%; max-width: 560px; box-sizing: border-box; margin: 0 auto; padding: calc(var(--space-6) + var(--space-1)) var(--space-4) var(--space-5); }
.partner-tiles { display: flex; align-items: center; justify-content: center; gap: var(--space-3); padding-top: var(--space-2); }
.partner-tile { display: flex; align-items: center; justify-content: center; width: 60px; height: 60px; box-sizing: border-box; border-radius: var(--radius-card); background: var(--surface); border: 1px solid var(--line); }
.partner-tile-getemall { background: var(--peach-soft); color: var(--primary-text); }
.partner-tile-getemall .icon { width: 30px; height: 30px; stroke-width: var(--icon-stroke); }
.partner-swap { width: 28px; height: 28px; color: var(--text-secondary); stroke-width: var(--icon-stroke); }
.partner-head { display: flex; flex-direction: column; gap: var(--space-2); padding: 0 var(--space-2); text-align: center; }
.partner-head h1 { margin: 0; font-size: var(--font-section); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.3px; }
.partner-head p, .partner-never p { margin: 0; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
.partner-blocked { display: flex; gap: var(--space-2); align-items: flex-start; margin: 0; color: var(--danger); font-size: var(--font-small); line-height: var(--leading-normal); font-weight: var(--weight-semibold); }
.partner-blocked .icon { flex: none; width: 18px; height: 18px; margin-top: 1px; }
.partner-section { display: flex; flex-direction: column; gap: var(--space-2); }
.partner-section h2 { margin: 0 var(--space-1); font-size: var(--label-caps); font-weight: var(--weight-bold); letter-spacing: var(--letter-label); text-transform: uppercase; color: var(--text-secondary); }
.partner-list { margin: 0; padding: 0; list-style: none; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); overflow: hidden; }
.partner-row { display: flex; align-items: center; gap: var(--space-3); min-height: 60px; box-sizing: border-box; padding: var(--space-3) var(--space-4); }
.partner-list > li + li { border-top: 1px solid var(--line-soft); }
.partner-orp .partner-row { align-items: flex-start; cursor: pointer; }
.partner-orp .partner-row.is-checked { background: var(--primary-soft); }
.partner-orp input { flex: none; width: 24px; height: 24px; margin: 1px 0 0; accent-color: var(--primary); cursor: pointer; }
.partner-dot { flex: none; display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: var(--radius-pill); background: var(--neutral-soft); color: var(--text-secondary); }
.partner-dot .icon { width: 16px; height: 16px; stroke-width: 2.4px; }
.partner-dot-yes { background: var(--success-soft); color: var(--success); }
.partner-text { display: flex; flex-direction: column; gap: 1px; }
.partner-label { font-size: var(--font-body); font-weight: var(--weight-semibold); }
.partner-hint { font-size: var(--font-small); line-height: var(--leading-tight); color: var(--text-secondary); }
.partner-never { display: flex; gap: var(--space-3); padding: var(--space-4); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); }
.partner-note { margin: 0 var(--space-1); font-size: var(--font-small); line-height: var(--leading-normal); color: var(--text-tertiary); }
.partner-note strong { font-weight: var(--weight-bold); color: var(--text); }
.partner-note a { color: var(--primary-text); font-weight: var(--weight-semibold); }
.partner-foot { position: sticky; bottom: 0; display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-3) var(--space-4) var(--space-5); background: var(--bg); border-top: 1px solid var(--line); }
.partner-foot > * { width: 100%; max-width: 528px; margin-left: auto; margin-right: auto; }
.partner-allow, .partner-refuse { justify-content: center; border: 0; border-radius: var(--radius-pill); font: inherit; font-weight: var(--weight-bold); cursor: pointer; }
.partner-allow { height: var(--btn-primary); background: var(--primary); color: var(--on-primary); font-size: var(--font-title); }
.partner-allow:disabled { opacity: 0.6; cursor: default; }
.partner-refuse { height: var(--btn-tertiary); background: transparent; color: var(--primary-text); font-size: var(--font-body); }
.partner-back { margin-top: 0; margin-bottom: 0; text-align: center; font-size: var(--font-small); line-height: var(--leading-tight); color: var(--text-secondary); }
</style>
