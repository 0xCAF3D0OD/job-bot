<script setup lang="ts">
import { PROVIDER_LABEL, type Provider, startHref } from "../oauthText";

// Se connecter avec un compte existant (docs/65, complément du 2026-11-05 ; maquette Connexion) : un bouton par
// fournisseur configuré sur le serveur, dans l'ordre Apple, Google, Microsoft, aux couleurs officielles (Apple
// noir en clair et blanc en sombre, Google blanc avec le G en couleur). Chaque bouton est un lien : la page part chez
// le fournisseur, puis revient connectée. Puis le séparateur « ou avec ton identifiant ».
const props = withDefaults(defineProps<{ providers: Provider[]; suite?: string }>(), { suite: undefined });
const href = (provider: Provider) => startHref(provider, { suite: props.suite });
</script>

<template>
  <div
    class="social-signin"
    data-test="social-signin"
  >
    <div class="social-buttons">
      <a
        v-for="provider in providers"
        :key="provider"
        :href="href(provider)"
        :class="['social-button', `social-${provider}`]"
        :data-test="`social-${provider}`"
      >
        <svg
          v-if="provider === 'google'"
          viewBox="0 0 48 48"
          aria-hidden="true"
        >
          <path
            fill="#FFC107"
            d="M43.6 20.1H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 8 3l5.7-5.7C34 6.1 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.6-.4-3.9z"
          />
          <path
            fill="#FF3D00"
            d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 8 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"
          />
          <path
            fill="#4CAF50"
            d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2c-2 1.5-4.5 2.4-7.2 2.4-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"
          />
          <path
            fill="#1976D2"
            d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.6-.4-3.9z"
          />
        </svg>
        <svg
          v-else-if="provider === 'apple'"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            fill="currentColor"
            d="M16.37 1.43c0 1.14-.5 2.27-1.18 3.08-.74.9-1.99 1.57-2.99 1.57-.12 0-.23-.02-.3-.03-.01-.06-.04-.22-.04-.39 0-1.15.57-2.27 1.2-2.98.81-.94 2.15-1.64 3.25-1.68.03.13.06.28.06.43zm4.56 15.71c-.03.07-.46 1.58-1.52 3.12-.94 1.34-1.94 2.71-3.43 2.71-1.52 0-1.9-.88-3.63-.88-1.7 0-2.3.91-3.67.91-1.38 0-2.33-1.26-3.43-2.8-1.29-1.82-2.32-4.63-2.32-7.28 0-4.28 2.8-6.55 5.55-6.55 1.45 0 2.67.95 3.6.95.86 0 2.22-1.01 3.9-1.01.61 0 2.89.06 4.37 2.19-.13.09-2.38 1.37-2.38 4.19 0 3.26 2.85 4.42 2.96 4.45z"
          />
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            fill="#F25022"
            d="M2 2h9.5v9.5H2z"
          />
          <path
            fill="#7FBA00"
            d="M12.5 2H22v9.5h-9.5z"
          />
          <path
            fill="#00A4EF"
            d="M2 12.5h9.5V22H2z"
          />
          <path
            fill="#FFB900"
            d="M12.5 12.5H22V22h-9.5z"
          />
        </svg>
        <span>Continuer avec {{ PROVIDER_LABEL[provider] }}</span>
      </a>
    </div>
    <p
      class="social-divider"
      role="separator"
    >
      <span>ou avec ton identifiant</span>
    </p>
  </div>
</template>

<style>
/* Maquette Connexion : 52 px, pilule, 16 px gras ; couleurs officielles des fournisseurs (valeurs de la maquette). */
.social-signin { display: flex; flex-direction: column; }
.social-buttons { display: flex; flex-direction: column; gap: var(--space-3); }
.social-button { display: flex; align-items: center; justify-content: center; gap: var(--space-3); box-sizing: border-box; width: 100%; height: var(--btn-secondary); border-radius: var(--radius-pill); border: 1.5px solid; font-size: var(--font-body); font-weight: var(--weight-bold); text-decoration: none; }
.social-button svg { flex: none; width: 20px; height: 20px; }
.social-apple { background: #000000; border-color: #000000; color: #FFFFFF; }
.social-google { background: #FFFFFF; border-color: #747775; color: #1F1F1F; }
.social-microsoft { background: var(--surface); border-color: #CFCBC1; color: var(--text); }
.social-button:hover, .social-button:visited { text-decoration: none; }
.social-apple:hover, .social-apple:visited { color: #FFFFFF; }
.social-google:hover, .social-google:visited { color: #1F1F1F; }
.social-microsoft:hover, .social-microsoft:visited { color: var(--text); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .social-apple { background: #FFFFFF; border-color: #FFFFFF; color: #000000; }
  :root:not([data-theme="light"]) .social-google { border-color: #FFFFFF; }
  :root:not([data-theme="light"]) .social-microsoft { border-color: #4A443C; }
}
:root[data-theme="dark"] .social-apple { background: #FFFFFF; border-color: #FFFFFF; color: #000000; }
:root[data-theme="dark"] .social-google { border-color: #FFFFFF; }
:root[data-theme="dark"] .social-microsoft { border-color: #4A443C; }
.social-divider { display: flex; align-items: center; gap: var(--space-3); margin: var(--space-5) 0 var(--space-3); color: var(--text-tertiary); font-size: var(--font-small); }
.social-divider::before, .social-divider::after { content: ""; flex: 1; height: 1px; background: var(--line); }
</style>
