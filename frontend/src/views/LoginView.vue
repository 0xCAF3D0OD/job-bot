<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import AuthIllustration from "../components/AuthIllustration.vue";
import BrandMark from "../components/BrandMark.vue";
import HoverNote from "../components/HoverNote.vue";
import SocialSignIn from "../components/SocialSignIn.vue";
import { useAuth } from "../composables/useAuth";
import { knownProviders, oauthMessage, type Provider } from "../oauthText";

// Page de connexion (maquettes Connexion, Sombre · Connexion et Connexion, ordinateur ; 2026-11-05) : le logo,
// l'illustration (bandeau de 150 px sur téléphone, moitié gauche sur ordinateur), « Content de te revoir. », les
// boutons Apple, Google et Microsoft des fournisseurs configurés sur le serveur (docs/65, complément du
// 2026-11-05), puis l'identifiant et le mot de passe. Les erreurs vont sous le champ concerné.
const route = useRoute();
const router = useRouter();
const { me, load, login } = useAuth();
const username = ref("");
const password = ref("");
const shown = ref(false);
const busy = ref(false);
// L'erreur de chaque champ ; celle du serveur (identifiant ou mot de passe faux) va sous le mot de passe et marque
// les deux champs.
const userError = ref("");
const passwordError = ref("");
const bothInvalid = ref(false);
// Les demandes de compte ouvertes (docs/102) : le lien « Créer un compte » ; sinon, l'invitation.
const signupOpen = ref(false);
const providers = ref<Provider[]>([]);

// Le retour d'un fournisseur : refus (?erreur=), ou demande de compte envoyée (?info=demande).
const oauthError = computed(() =>
  typeof route.query.erreur === "string" ? oauthMessage(route.query.erreur, route.query.fournisseur) : "",
);
const oauthInfo = computed(() => (route.query.info === "demande" ? oauthMessage("demande", route.query.fournisseur) : ""));

function next(): string {
  const wanted = typeof route.query.suite === "string" ? route.query.suite : "";
  // Seulement une page de la plateforme (pas d'adresse externe).
  return wanted.startsWith("/") && !wanted.startsWith("//") ? wanted : "/aujourdhui";
}
const suite = computed(() => (typeof route.query.suite === "string" && next() === route.query.suite ? route.query.suite : undefined));

async function submit(): Promise<void> {
  if (busy.value) return;
  const name = username.value.trim();
  userError.value = name ? "" : "Écris ton identifiant.";
  passwordError.value = password.value ? "" : "Écris ton mot de passe.";
  bothInvalid.value = false;
  if (!name || !password.value) return;
  busy.value = true;
  try {
    const problem = await login(name, password.value);
    password.value = "";
    if (problem) {
      passwordError.value = problem.charAt(0).toUpperCase() + problem.slice(1) + ".";
      bothInvalid.value = true;
      return;
    }
    // Un compte dont l'accueil n'est pas fini le reprend là où il s'était arrêté (docs/66 §4).
    const welcome = me.value?.welcome;
    await router.replace(welcome === "pending" || welcome === "postponed" ? "/bienvenue" : next());
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  void load();
  const [signup, offered] = await Promise.all([api.GET("/api/auth/signup"), api.GET("/api/auth/providers")]);
  signupOpen.value = signup.data?.open === true;
  providers.value = knownProviders(offered.data?.providers);
});
</script>

<template>
  <section
    class="login-page"
    data-test="login-page"
  >
    <div
      class="login-art"
      aria-hidden="true"
    >
      <AuthIllustration large />
      <p class="login-pitch">
        Tes alertes triées, tes candidatures préparées, tes preuves ORP prêtes.
      </p>
    </div>
    <div class="login-panel">
      <header class="login-brand">
        <BrandMark :size="30" />
        <span>jobA1</span>
      </header>
      <AuthIllustration class="login-art-phone" />
      <main class="login-main">
        <h1 class="login-title">
          Content de <span class="login-hand">te revoir.</span>
        </h1>
        <p class="login-sub">
          Tes offres, tes candidatures et tes preuves ORP, au même endroit.
        </p>
        <div
          v-if="me?.setup_needed"
          class="auth-setup"
          data-test="setup-needed"
        >
          <p>
            Aucun compte n'existe encore.
            <HoverNote text="12 caractères au moins. Le mot de passe n'est jamais enregistré en clair.">
              Crée-le une fois
            </HoverNote>, dans un terminal, depuis le dossier du projet :
          </p>
          <pre class="command"><code>cd backend && uv run jobbot set-password</code></pre>
        </div>
        <template v-else>
          <p
            v-if="oauthError"
            class="login-alert"
            role="alert"
            data-test="oauth-error"
          >
            <AppIcon name="alert-circle" />
            <span>{{ oauthError }}</span>
          </p>
          <p
            v-else-if="oauthInfo"
            class="login-info"
            role="status"
            data-test="oauth-info"
          >
            {{ oauthInfo }}
          </p>
          <SocialSignIn
            v-if="providers.length"
            :providers="providers"
            :suite="suite"
          />
          <form
            class="signin-form"
            data-test="login-form"
            novalidate
            @submit.prevent="submit"
          >
            <div class="login-field">
              <label for="login-username">Identifiant</label>
              <input
                id="login-username"
                v-model="username"
                type="text"
                autocomplete="username"
                autocapitalize="none"
                spellcheck="false"
                :aria-invalid="userError || bothInvalid ? 'true' : 'false'"
                :aria-describedby="userError ? 'login-username-error' : undefined"
                data-test="username"
              >
              <p
                v-if="userError"
                id="login-username-error"
                class="login-field-error"
                data-test="username-error"
              >
                <AppIcon name="alert-circle" />
                <span>{{ userError }}</span>
              </p>
            </div>
            <div class="login-field">
              <label for="login-password">Mot de passe</label>
              <span class="login-password">
                <input
                  id="login-password"
                  v-model="password"
                  :type="shown ? 'text' : 'password'"
                  autocomplete="current-password"
                  :aria-invalid="passwordError ? 'true' : 'false'"
                  :aria-describedby="passwordError ? 'login-password-error' : undefined"
                  data-test="password"
                >
                <button
                  type="button"
                  class="login-reveal"
                  aria-label="Afficher le mot de passe"
                  :aria-pressed="shown ? 'true' : 'false'"
                  data-test="password-toggle"
                  @click="shown = !shown"
                >
                  <AppIcon :name="shown ? 'eye-off' : 'eye'" />
                </button>
              </span>
              <p
                v-if="passwordError"
                id="login-password-error"
                class="login-field-error"
                role="alert"
                data-test="login-error"
              >
                <AppIcon name="alert-circle" />
                <span>{{ passwordError }}</span>
              </p>
            </div>
            <button
              type="submit"
              class="primary login-submit"
              :disabled="busy"
              data-test="login-submit"
            >
              {{ busy ? "Connexion…" : "Se connecter" }}
            </button>
          </form>
          <!-- Deux lignes : l'inscription, puis les données personnelles (docs/102). -->
          <p class="login-foot">
            <template v-if="signupOpen">
              Pas encore de compte ? <RouterLink
                to="/inscription"
                data-test="signup-link"
              >
                Créer un compte
              </RouterLink>
            </template>
            <template v-else>
              Pas encore de compte ? L'accès se fait sur invitation.
            </template>
          </p>
          <p class="login-foot login-foot-small">
            <RouterLink to="/tes-donnees">
              Données personnelles
            </RouterLink>
          </p>
        </template>
      </main>
    </div>
  </section>
</template>

<style>
/* Maquette Connexion (390 px) : valeurs exactes du HTML de la maquette, couleurs des jetons. */
.login-page { display: flex; min-height: 100dvh; background: var(--bg); color: var(--text); }
.login-art { display: none; }
.login-panel { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.login-brand { flex: none; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-5) var(--space-5) 0; font-size: var(--font-title); font-weight: var(--weight-bold); }
.login-main { display: flex; flex-direction: column; padding: var(--space-3) var(--space-5) var(--space-6); }
.login-title { margin: 0; font-size: var(--title-login); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -0.5px; }
.login-hand { font-family: "Caveat Brush", cursive; font-weight: var(--weight-regular); font-size: 1.45em; letter-spacing: 0; color: var(--primary-graphic); }
.login-sub { display: none; }
.login-main .social-signin { margin-top: var(--space-5); }
.login-alert, .login-field-error { display: flex; gap: var(--space-2); align-items: flex-start; margin: 0; color: var(--danger); font-size: var(--font-small); line-height: var(--leading-normal); font-weight: var(--weight-semibold); }
.login-alert { margin-top: var(--space-5); }
.login-alert .icon, .login-field-error .icon { flex: none; width: 18px; height: 18px; margin-top: 1px; }
.login-info { margin: var(--space-5) 0 0; font-size: var(--font-small); line-height: var(--leading-normal); font-weight: var(--weight-semibold); color: var(--text); }
.signin-form { display: flex; flex-direction: column; gap: var(--space-3); margin: 0; padding: 0; }
.login-main > .signin-form:first-child, .login-main .login-alert + .signin-form, .login-main .login-info + .signin-form { margin-top: var(--space-5); }
.login-field { display: flex; flex-direction: column; gap: var(--space-2); }
.login-field label { font-size: var(--font-body); font-weight: var(--weight-semibold); color: var(--text); }
.login-field input { width: 100%; box-sizing: border-box; height: var(--btn-secondary); padding: 0 var(--space-4); border-radius: var(--radius-card); border: 1.5px solid var(--field-border); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body); }
.login-field input[aria-invalid="true"] { border-color: var(--danger); }
.login-password { position: relative; display: block; }
.login-password input { padding-right: calc(var(--target-min) + var(--space-5)); }
.login-reveal { position: absolute; right: 4px; top: 4px; display: flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); padding: 0; border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--text-tertiary); cursor: pointer; }
.login-reveal .icon { width: 22px; height: 22px; }
.login-submit { margin-top: var(--space-1); width: 100%; height: var(--btn-primary); justify-content: center; border-radius: var(--radius-pill); font-size: var(--font-title); font-weight: var(--weight-bold); }
.login-foot { margin: var(--space-5) 0 0; text-align: center; font-size: var(--font-body); color: var(--text-tertiary); }
.login-foot a { color: var(--primary-text); font-weight: var(--weight-bold); }
.login-foot-small { margin-top: var(--space-2); font-size: var(--font-small); }
.login-foot-small a { color: var(--text-tertiary); font-weight: var(--weight-regular); }
.login-main .auth-setup { margin-top: var(--space-5); }

/* Maquette Connexion, ordinateur (1440 px) : l'illustration à gauche sur la carte, la connexion à droite (600 px). */
@media (min-width: 821px) {
  .login-art { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: calc(var(--space-6) + var(--space-1)); min-width: 0; padding: 0 var(--space-6); background: var(--surface); border-right: 1px solid var(--line); }
  .login-art-phone { display: none; }
  .login-pitch { margin: 0; max-width: 460px; text-align: center; font-size: var(--font-section); line-height: var(--leading-tight); font-weight: var(--weight-bold); }
  .login-panel { flex: none; width: 600px; max-width: 50%; padding: var(--space-8) 0; }
  .login-brand { padding: 0 calc(var(--space-8) * 2); font-size: var(--font-section); }
  .login-brand .brand-logo { width: 32px; height: 32px; }
  .login-main { flex: 1; justify-content: center; padding: 0 calc(var(--space-12) * 2); }
  .login-title { font-size: var(--title-login-wide); }
  .login-sub { display: block; margin: var(--space-2) 0 0; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-tertiary); }
  .login-main .social-signin { margin-top: var(--space-6); }
}
@media (min-width: 821px) and (max-width: 1200px) {
  .login-brand { padding: 0 calc(var(--space-5) * 2); }
  .login-main { padding: 0 var(--space-12); }
}
</style>
