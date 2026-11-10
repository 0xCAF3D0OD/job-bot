<script setup lang="ts">
import { onMounted, ref } from "vue";

import AppIcon from "./AppIcon.vue";
import BrandMark from "./BrandMark.vue";
import ProfileCompletionForm, { type Level } from "./ProfileCompletionForm.vue";

// « Complétons ton profil » (prompt du 10 novembre, PR 17 ; maquettes OnboardingProfil et OnboardingOrdinateurProfil,
// clair et sombre) : l'étape 1 sur 3 des premiers pas quand le CV n'a pas pu être lu, ou quand il n'y en a pas.
// Téléphone : retour, barre en 3 segments, « 1 sur 3 », barre du bas fixe (« Continuer » pleine largeur, « Plus tard »).
// Ordinateur : la grille commune des premiers pas, l'encadré « À quoi ça sert » à droite.
const props = defineProps<{
  desk: boolean;
  cvName: string;
  // La raison en clair (« C’est une image scannée : le texte n’est pas lisible. ») ; vide sans fichier.
  cvReason: string;
  documentId: number | null;
  roles: string[];
}>();
const emit = defineEmits<{ back: []; later: []; done: [levels: Record<string, Level>]; file: [file: File] }>();

const form = ref<InstanceType<typeof ProfileCompletionForm> | null>(null);
const title = ref<HTMLElement | null>(null);

onMounted(() => {
  window.scrollTo({ top: 0 });
  title.value?.focus({ preventScroll: true });
});

async function onFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (file) emit("file", file);
}

async function next(): Promise<void> {
  if (!form.value || form.value.saving) return;
  if (await form.value.save()) emit("done", { ...form.value.levels });
}
const LEAD =
  "jobA1 n’a pas pu lire ton CV. Ces informations suffisent pour noter les offres et écrire tes lettres sans rien inventer. Seul ton nom est obligatoire.";
const LEAD_NO_CV =
  "Ces informations suffisent pour noter les offres et écrire tes lettres sans rien inventer. Seul ton nom est obligatoire.";
</script>

<template>
  <section
    :class="['wps', desk ? 'wdk' : 'wps-phone']"
    data-test="welcome-profile"
  >
    <header
      v-if="desk"
      class="wdk-top"
    >
      <span class="welcome-brand"><BrandMark :size="28" />jobA1</span>
      <span class="wdk-step">Étape 1 sur 3</span>
      <span
        class="wdk-bars"
        aria-hidden="true"
      ><span class="on current" /><span /><span /></span>
    </header>
    <header
      v-else
      class="wps-top"
    >
      <button
        type="button"
        class="wps-back"
        aria-label="Retour"
        data-test="welcome-profile-back"
        @click="emit('back')"
      >
        <AppIcon name="arrow-left" />
      </button>
      <span
        class="wps-bars"
        aria-hidden="true"
      ><span class="on" /><span /><span /></span>
      <span class="wps-count">1 sur 3</span>
    </header>

    <div :class="desk ? 'wdk-grid' : 'wps-body'">
      <div :class="desk ? 'wdk-col' : 'wps-col'">
        <p :class="desk ? 'wdk-cap' : 'wps-cap'">
          Ton parcours
        </p>
        <h1
          ref="title"
          tabindex="-1"
          :class="desk ? 'wdk-title' : 'wps-title'"
        >
          Complétons ton profil
        </h1>
        <p :class="desk ? 'wdk-lead wps-lead' : 'wps-lead'">
          {{ props.cvName ? LEAD : LEAD_NO_CV }}
        </p>
        <div
          v-if="props.cvName"
          class="wps-file"
          data-test="welcome-profile-file"
        >
          <AppIcon
            name="file-alert"
            class="wps-file-icon"
          />
          <span class="wps-file-text">
            <b>{{ props.cvName }}</b>
            <span>{{ props.cvReason }}</span>
          </span>
          <label class="wps-file-link">
            Essayer un autre fichier
            <input
              type="file"
              accept=".pdf,.docx"
              class="visually-hidden"
              data-test="welcome-profile-other"
              @change="onFile"
            >
          </label>
        </div>

        <ProfileCompletionForm
          ref="form"
          class="wps-form"
          :desk="desk"
          :roles="roles"
          :document-id="documentId"
        />

        <div
          v-if="desk"
          class="wdk-foot"
        >
          <button
            type="button"
            class="secondary wdk-back"
            data-test="welcome-profile-back"
            @click="emit('back')"
          >
            Retour
          </button>
          <span class="wps-foot-end">
            <button
              type="button"
              class="wdk-link"
              data-test="welcome-profile-later"
              @click="emit('later')"
            >
              Plus tard
            </button>
            <button
              type="button"
              class="primary wdk-cta"
              :aria-disabled="form?.saving ? 'true' : undefined"
              data-test="welcome-profile-continue"
              @click="next"
            >
              Continuer
            </button>
          </span>
        </div>
      </div>
      <aside
        v-if="desk"
        class="wps-aside"
      >
        <div class="wps-why">
          <b class="wps-why-title">À quoi ça sert</b>
          <p><b>Expériences</b>&#8239;: jobA1 compare tes tâches aux offres et écrit ta lettre avec tes vrais exemples.</p>
          <p><b>Langues</b>&#8239;: beaucoup d’offres en Suisse en demandent une. Tu verras «&#8239;Langue à vérifier&#8239;» tant qu’elle n’est pas renseignée.</p>
          <p><b>Coordonnées</b>&#8239;: elles remplissent l’en-tête de tes lettres.</p>
          <p class="wps-why-note">
            Tu peux tout changer plus tard dans Profil.
          </p>
        </div>
      </aside>
    </div>

    <footer
      v-if="!desk"
      class="wps-bar"
    >
      <button
        type="button"
        class="primary wps-continue"
        :aria-disabled="form?.saving ? 'true' : undefined"
        data-test="welcome-profile-continue"
        @click="next"
      >
        Continuer
      </button>
      <button
        type="button"
        class="wps-later"
        data-test="welcome-profile-later"
        @click="emit('later')"
      >
        Plus tard
      </button>
    </footer>
  </section>
</template>

<style>
/* Valeurs des maquettes du 10 novembre, ramenées sur la grille de 4 là où elles tombent entre deux (6 → 8, 14 → 16). */
.wps { --wps-56: 56px; --wps-48: 48px; --wps-seg: 6px; --wps-30: 30px; --wps-36: 36px; --wps-24: 24px; --wps-22: 22px;
  --wps-20: 20px; --wps-52: 52px; --wps-pad: 14.5px; --wps-desk-pad: 18.5px; --wps-why-top: 168px; --wps-15: 15px; --wps-17: 17px;
  --wps-bar-room: 196px; background: var(--bg); color: var(--text); }
.wps-phone { min-height: 100dvh; }
.wps-top { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; gap: var(--space-3); height: var(--wps-56); padding: 0 var(--space-2) 0 var(--space-1); background: var(--bg); }
.wps-back { display: grid; place-items: center; width: var(--wps-48); height: var(--wps-48); min-height: var(--wps-48); padding: 0; border: 0; border-radius: var(--radius-pill); background: none; color: var(--text); }
.wps-back .icon { width: var(--wps-24); height: var(--wps-24); stroke-width: var(--icon-stroke); }
.wps-bars { flex: 1; display: flex; gap: var(--space-2); }
.wps-bars span { flex: 1; height: var(--wps-seg); border-radius: var(--radius-pill); background: var(--line-strong); }
.wps-bars span.on { background: var(--primary-graphic); }
.wps-count { padding-right: var(--space-3); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); }
.wps-body { padding: var(--space-3) var(--space-5) var(--wps-bar-room); }
.wps-cap { margin: 0; font-size: var(--font-caption); line-height: var(--wps-20); font-weight: var(--weight-bold); letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); }
.wps-title { margin: var(--space-3) 0 0; font-size: var(--wps-30); line-height: var(--wps-36); font-weight: var(--weight-heavy); letter-spacing: -0.4px; }
.wps-title:focus { outline: none; }
.wps-lead { margin: var(--space-3) 0 0; font-size: var(--font-body); line-height: var(--wps-24); color: var(--text-lead); }
.wdk-lead.wps-lead { font-size: var(--wdk-18); line-height: var(--wdk-28); }
.wps-file { display: flex; flex-wrap: wrap; align-items: flex-start; gap: var(--space-4); margin-top: var(--space-6); padding: var(--wps-pad); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.wdk .wps-file { align-items: center; padding: var(--wps-desk-pad); }
.wps-file-icon { flex: none; width: var(--wps-24); height: var(--wps-24); color: var(--file-error); stroke-width: 2; }
.wps-file-text { flex: 1; min-width: 180px; }
.wps-file-text b { display: block; font-size: var(--font-body); line-height: var(--wps-22); overflow-wrap: anywhere; }
.wps-file-text span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--wps-20); color: var(--text-secondary); }
.wps-file-link { flex: none; display: inline-flex; align-items: center; min-height: var(--target-min); margin-left: calc(var(--wps-24) + var(--space-4)); color: var(--primary-text); font-size: var(--wps-15); font-weight: var(--weight-bold); cursor: pointer; }
.wdk .wps-file-link { margin-left: 0; }
.wps-file-link:focus-within { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--radius-sm); }
.wps-form { margin-top: var(--pc-sec-gap, 36px); }
.wps-bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 3; display: flex; flex-direction: column; align-items: center; gap: var(--space-1); padding: var(--space-3) var(--space-5) var(--space-6); background: var(--bg); border-top: 1px solid var(--line); }
.wps-continue { display: flex; align-items: center; justify-content: center; width: 100%; height: var(--wps-52); min-height: var(--wps-52); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.wps-later { min-height: var(--target-min); padding: 0 var(--space-2); border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--wps-15); font-weight: var(--weight-bold); }
.wps-foot-end { display: flex; align-items: center; gap: var(--space-6); }
.wps-aside { padding-top: var(--wps-why-top); }
.wps-why { display: flex; flex-direction: column; gap: var(--space-4); padding: var(--wps-desk-pad); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.wps-why-title { font-size: var(--wps-17); line-height: var(--wps-22); }
.wps-why p { margin: 0; font-size: var(--wps-15); line-height: var(--wps-22); color: var(--text-lead); }
.wps-why .wps-why-note { font-size: var(--font-small); line-height: var(--wps-20); color: var(--text-secondary); }
</style>
