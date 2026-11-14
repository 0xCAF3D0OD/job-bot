<script setup lang="ts">
import { ref } from "vue";

import AppIcon from "./AppIcon.vue";
import CopyButton from "./CopyButton.vue";

// Les trois étapes pour créer l'alerte d'un site (planche AlertesOrdinateurSite, paquet du 13 novembre) : le rappel
// de la recherche, puis « Ouvre <site> avec ta recherche », « Mets cette adresse comme destinataire » (l'adresse et
// son bouton Copier de 44 px) et « Enregistre l'alerte ». Partagées par le panneau « Alerte <site> » des Alertes et
// par l'étape « Alerte » des premiers pas (corrections du 13.11 au soir, §1 : OnboardingC étape 3,
// OnboardingOrdinateurAlerte). Ouvrir le site copie l'adresse d'avance (docs/121 §B.2) : il ne reste qu'à la coller.
const props = withDefaults(
  defineProps<{
    siteName: string;
    searchLabel: string;
    links: { key: string; url: string; label: string }[];
    mailbox?: string | null;
    // Le texte sous « Mets cette adresse… » et le titre de la 3e étape : plus courts sur téléphone (OnboardingC).
    addressHelp?: string;
    saveTitle?: string;
  }>(),
  {
    mailbox: null,
    addressHelp: "Elle est déjà copiée quand tu ouvres le site : colle-la dans le champ e-mail de l’alerte.",
    saveTitle: "",
  },
);

const copied = ref(false);
function copyOnOpen(): void {
  const address = props.mailbox;
  if (!address) return;
  void navigator.clipboard
    ?.writeText(address)
    .then(() => (copied.value = true))
    .catch(() => undefined);
}
</script>

<template>
  <p
    class="alert-site-search"
    data-test="alert-site-search"
  >
    Recherche : <b>{{ searchLabel }}</b>
  </p>
  <ol class="alert-site-steps">
    <li>
      <span
        class="alert-site-num"
        aria-hidden="true"
      >1</span>
      <div>
        <b class="alert-site-step-title">Ouvre {{ siteName }} avec ta recherche</b>
        <div class="alert-site-links">
          <a
            v-for="link in links"
            :key="link.key"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
            class="alert-site-open"
            :data-test="link.key.startsWith('remote') ? 'wizard-open-remote' : 'wizard-open'"
            @click="copyOnOpen"
          >{{ link.label }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </div>
      </div>
    </li>
    <li v-if="mailbox">
      <span
        class="alert-site-num"
        aria-hidden="true"
      >2</span>
      <div>
        <b class="alert-site-step-title">Mets cette adresse comme destinataire</b>
        <p class="alert-site-help">
          {{ addressHelp }}
        </p>
        <div class="alert-site-address">
          <span data-test="wizard-address">{{ mailbox }}</span>
          <CopyButton
            :value="mailbox"
            label="Copier l’adresse"
            test-id="alert-site-copy"
            :announce="false"
            @copied="copied = true"
          />
        </div>
        <p
          class="alert-site-copied"
          role="status"
          data-test="alert-site-copied"
        >
          {{ copied ? "Adresse copiée" : "" }}
        </p>
      </div>
    </li>
    <li>
      <span
        class="alert-site-num"
        aria-hidden="true"
      >{{ mailbox ? 3 : 2 }}</span>
      <div>
        <b class="alert-site-step-title">{{ saveTitle || `Enregistre l’alerte sur ${siteName}, puis reviens ici` }}</b>
        <p class="alert-site-help">
          La première alerte arrive souvent dès le lendemain.
        </p>
      </div>
    </li>
  </ol>
</template>

<style>
/* Valeurs du HTML de la planche AlertesOrdinateurSite, couleurs en jetons. */
.alert-site-search { --as-22: 22px; margin: 0 0 var(--space-4); font-size: var(--font-label); line-height: var(--as-22); color: var(--text-lead); }
.alert-site-steps { --as-22: 22px; --as-step-top: 5px; margin: 0; padding: 0; list-style: none; }
.alert-site-steps > li { display: flex; gap: var(--space-4); padding: var(--space-5) 0; border-top: 1px solid var(--line); }
.alert-site-steps > li > div { flex: 1; min-width: 0; }
.alert-site-num { flex: none; width: 32px; height: 32px; border-radius: var(--radius-pill); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-heavy); display: flex; align-items: center; justify-content: center; }
.alert-site-step-title { display: block; font-size: var(--font-body); line-height: var(--as-22); padding-top: var(--as-step-top); }
.alert-site-help { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.alert-site-links { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-3); }
.alert-site-open { display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--target-min); padding: 0 var(--space-5); border: 1.5px solid var(--primary-graphic); border-radius: var(--radius-pill); background: transparent; color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; }
.alert-site-open:hover { background: var(--primary-soft); color: var(--primary-text); }
.alert-site-address { display: flex; align-items: center; gap: var(--space-2); height: 48px; margin-top: var(--space-3); padding: 0 1px 0 var(--space-5); box-sizing: border-box; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-pill); }
.alert-site-address > span { flex: 1; min-width: 0; font-size: var(--font-label); font-weight: var(--weight-semibold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* 44 × 44 px dans le champ de 48 px (décision de Kevin du 13.11 ; la planche dit 40). */
.alert-site-address .copy-button { flex: none; width: var(--target-min); height: var(--target-min); border: 0; background: var(--primary-soft); color: var(--primary-text); }
.alert-site-copied { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--success); }
.alert-site-copied:empty { margin: 0; }
</style>
