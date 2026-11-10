<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Chunk, type DocumentOut } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import AvatarPicker from "./AvatarPicker.vue";
import CriteriaForm from "./CriteriaForm.vue";
import CvStateBlock from "./CvStateBlock.vue";
import ProfileEditSheet from "./ProfileEditSheet.vue";
import ProfileGauge from "./ProfileGauge.vue";
import ProfileImage from "./ProfileImage.vue";
import QueryLink from "./QueryLink.vue";
import { cvSubtitle, useCvReading } from "../composables/useCvReading";
import { useProfileImage } from "../composables/useProfileImage";
import { useProfiles } from "../composables/useProfiles";
import { useNarrow } from "../composables/usePhone";
import { plural } from "../format";

// Profil en page unique, sur ordinateur (maquette ProfilOrdinateur ; PR 9b) et sur téléphone (maquette ProfilTel ;
// prompt du 10 novembre, PR 20, décision B) : l'en-tête (image à pastille crayon, nom, poste · lieu, « Modifier »), Mon CV, Compétences trouvées, Ce que je
// cherche, puis « Mon parcours » en lignes qui ouvrent chacune leur page (?onglet=…). La pastille crayon ouvre
// « Ton image » : plus de bouton « Changer d'image ». « Modifier » ne change que le nom, le poste et le lieu.
type Identity = components["schemas"]["Identity"];

const image = useProfileImage();
const { phone: narrow } = useNarrow();
const profiles = useProfiles();
// Les documents viennent de la lecture du CV (PR 21) : la carte suit la lecture même quand elle finit ailleurs.
const reading = useCvReading();
const documents = computed<DocumentOut[]>(() => reading.documents.value ?? []);
const chunks = ref<Chunk[]>([]);
const identity = ref<Identity | null>(null);
const picking = ref(false);
const editing = ref(false);
const uploading = ref(false);
const message = ref("");

async function loadDocuments(): Promise<void> {
  await reading.load();
}
async function loadAll(): Promise<void> {
  const [chunkList, who] = await Promise.all([
    api.GET("/api/profile-chunks"),
    api.GET("/api/identity"),
    loadDocuments(),
    profiles.list.value ? Promise.resolve() : profiles.load(),
  ]);
  chunks.value = chunkList.data ?? [];
  identity.value = who.data ?? null;
}
onMounted(() => {
  void image.load();
  void loadAll().catch(() => undefined);
});

// « Junior DevOps · Renens » : le poste du profil de recherche, puis la localité.
const subline = computed(() => [profiles.current.value?.occupation?.trim(), image.city.value].filter(Boolean).join(" · "));

// Mon CV : le dernier document déposé qui n'est pas un certificat de travail (il n'existe pas de type « CV »).
const cv = computed(() =>
  [...documents.value].filter((d) => d.kind !== "certificate").sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at))[0] ?? null,
);
// La ligne sous le nom du fichier (maquette ProfilOrdinateurCV) : orange quand il reste à lire, vert quand la lecture a
// trouvé des éléments, grise sinon.
const cvLine = computed(() => (cv.value ? cvSubtitle(cv.value, null) : null));

// « Remplacer » du bloc d'état (« Lecture impossible ») ouvre le même choix de fichier que le bouton de la carte.
const fileInputs: HTMLInputElement[] = [];
function keepInput(el: unknown): void {
  if (el instanceof HTMLInputElement && !fileInputs.includes(el)) fileInputs.push(el);
}
function pickFile(): void {
  fileInputs.find((input) => input.isConnected)?.click();
}

// « Remplacer » dépose le nouveau CV ; l'ancien reste dans « Documents et certificats », rien n'est effacé.
async function onFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || uploading.value) return;
  uploading.value = true;
  message.value = "";
  try {
    const { data, error, response } = await api.POST("/api/documents", {
      body: { file: "" },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    if (data) {
      await loadDocuments();
      message.value = data.text_status === "ok" ? "CV déposé." : "CV déposé, mais son texte n’est pas lisible (PDF scanné ?).";
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Refusé : ${detail}.` : `Refusé (HTTP ${response.status}).`;
    }
  } catch {
    message.value = "API injoignable : réessaie dans un moment.";
  } finally {
    uploading.value = false;
  }
}

// Compétences trouvées : les blocs « Compétence » actifs, ceux que la note des offres lit.
const skills = computed(() => chunks.value.filter((c) => c.kind === "competence" && c.active));

// Mon parcours : une ligne par partie, avec son résumé.
const count = (kind: string) => chunks.value.filter((c) => c.kind === kind).length;
const parcours = computed(() => {
  const certificates = documents.value.filter((d) => d.kind === "certificate").length;
  const others = documents.value.length - certificates;
  const docs = [others ? plural(others, "document", "documents") : "", certificates ? plural(certificates, "certificat", "certificats") : ""]
    .filter(Boolean)
    .join(" · ");
  const who = identity.value;
  const phone = who?.phone?.trim();
  const contact = [who?.city?.trim(), phone ? `${phone.slice(0, 3)}…` : ""].filter(Boolean).join(" · ");
  return [
    { key: "formations", label: "Formations", line: count("formation") ? plural(count("formation"), "formation", "formations") : "Aucune pour l’instant" },
    { key: "experiences", label: "Expériences", line: count("experience") ? plural(count("experience"), "expérience", "expériences") : "Aucune pour l’instant" },
    { key: "documents", label: "Documents et certificats", line: docs || "Aucun pour l’instant" },
    { key: "coordonnees", label: "Coordonnées", line: contact || "À compléter" },
  ];
});

async function onSaved(): Promise<void> {
  await Promise.all([image.load(true), loadAll()]);
}
</script>

<template>
  <div
    class="profile-desktop"
    data-test="profile-desktop"
  >
    <header
      class="jobs-head profile-head"
      data-test="profile-head"
    >
      <div class="profile-head-main">
        <button
          type="button"
          class="profile-head-image"
          aria-label="Changer d’image"
          data-test="profile-image-edit"
          @click="picking = true"
        >
          <ProfileImage
            :choice="image.choice.value"
            :initials="image.initials.value"
            :size="narrow ? 64 : 72"
          />
          <span
            class="profile-head-pencil"
            aria-hidden="true"
          ><AppIcon name="pencil" /></span>
        </button>
        <div class="profile-head-text">
          <!-- Sur téléphone, le titre de la page est « Mon profil » (barre du haut) : le nom n'est pas un second h1. -->
          <component
            :is="narrow ? 'p' : 'h1'"
            class="profile-head-name"
          >
            {{ image.name.value || "Profil" }}
          </component>
          <p
            v-if="subline"
            class="profile-head-subline"
            data-test="profile-subline"
          >
            {{ subline }}
          </p>
        </div>
        <div class="profile-head-actions">
          <button
            type="button"
            class="secondary action-2"
            aria-haspopup="dialog"
            data-test="profile-edit"
            @click="editing = true"
          >
            Modifier
          </button>
        </div>
      </div>
    </header>
    <AvatarPicker
      :open="picking"
      @close="picking = false"
    />
    <ProfileEditSheet
      :open="editing"
      @close="editing = false"
      @saved="onSaved"
    />

    <div class="profile-desktop-body">
      <!-- La jauge du profil (docs/121 §C.4) : ce qui manque encore, en premier. -->
      <ProfileGauge />

      <section
        class="profile-section"
        aria-labelledby="profile-cv-title"
        data-test="profile-cv"
      >
        <div class="profile-section-head">
          <h2 id="profile-cv-title">
            Mon CV
          </h2>
        </div>
        <div
          class="profile-card profile-cv-card"
          data-test="cv-card"
        >
          <div class="profile-cv">
            <AppIcon
              name="file"
              class="profile-cv-icon"
            />
            <div class="profile-cv-text">
              <strong data-test="profile-cv-name">{{ cv ? cv.filename : "Aucun CV déposé" }}</strong>
              <span
                v-if="cvLine"
                :class="`profile-cv-line profile-cv-line-${cvLine.tone}`"
                data-test="profile-cv-line"
              >{{ cvLine.text }}</span>
              <span v-else>PDF, DOCX, TXT ou MD · 10 Mo au plus</span>
            </div>
            <template v-if="!narrow">
              <a
                v-if="cv"
                class="button secondary action-2"
                :href="`/api/documents/${cv.id}/file`"
                target="_blank"
                rel="noopener"
                data-test="profile-cv-open"
              >Voir<span class="visually-hidden">{{ ` ${cv.filename} (nouvel onglet)` }}</span></a>
              <label
                class="button secondary action-2 profile-cv-upload"
                :aria-busy="uploading ? 'true' : undefined"
                data-test="profile-cv-replace"
              >
                <input
                  :ref="keepInput"
                  type="file"
                  class="visually-hidden"
                  accept=".pdf,.docx,.txt,.md"
                  data-test="profile-cv-input"
                  @change="onFile"
                >
                {{ uploading ? "Envoi…" : cv ? "Remplacer" : "Déposer mon CV" }}
              </label>
            </template>
          </div>
          <!-- Sous un filet, le bloc d'état de la lecture du CV (PR 21, maquettes ProfilTel et ProfilOrdinateurCV). -->
          <CvStateBlock
            v-if="cv"
            :doc="cv"
            @replace="pickFile"
            @changed="loadAll"
          />
          <!-- Téléphone (ProfilTel) : « Voir | Remplacer » en bas de la carte, séparés par un filet. -->
          <div
            v-if="narrow"
            class="profile-cv-split"
          >
            <a
              v-if="cv"
              :href="`/api/documents/${cv.id}/file`"
              target="_blank"
              rel="noopener"
              data-test="profile-cv-open"
            >Voir<span class="visually-hidden">{{ ` ${cv.filename} (nouvel onglet)` }}</span></a>
            <label
              class="profile-cv-upload"
              :aria-busy="uploading ? 'true' : undefined"
              data-test="profile-cv-replace"
            >
              <input
                :ref="keepInput"
                type="file"
                class="visually-hidden"
                accept=".pdf,.docx,.txt,.md"
                data-test="profile-cv-input"
                @change="onFile"
              >
              {{ uploading ? "Envoi…" : cv ? "Remplacer" : "Déposer mon CV" }}
            </label>
          </div>
        </div>
        <p
          v-if="message"
          class="muted"
          role="status"
        >
          {{ message }}
        </p>
      </section>

      <section
        class="profile-section"
        aria-labelledby="profile-skills-title"
        data-test="profile-skills"
      >
        <div class="profile-section-head">
          <h2 id="profile-skills-title">
            Compétences trouvées
          </h2>
          <span>Utilisées pour noter les offres</span>
        </div>
        <div
          v-if="!skills.length"
          class="profile-card profile-skills-empty"
          data-test="profile-skills-empty"
        >
          <template v-if="narrow">
            Rien pour l’instant. Relis ton CV ou ajoute-les à la main.<br>
            <QueryLink
              :to="{ query: { onglet: 'competences', nouveau: '1' } }"
              class="profile-skills-add-link"
              data-test="profile-skill-add"
            >
              Ajouter une compétence
            </QueryLink>
          </template>
          <template v-else>
            Rien pour l’instant. Relis ton CV ou <QueryLink
              :to="{ query: { onglet: 'competences', nouveau: '1' } }"
              data-test="profile-skill-add"
              text="ajoute-les à la main"
            />.
          </template>
        </div>
        <div
          v-else
          class="profile-card profile-skills"
        >
          <QueryLink
            v-for="skill in skills"
            :key="skill.id"
            class="profile-skill"
            :to="{ query: { onglet: 'competences', bloc: skill.id } }"
            :data-test="`profile-skill-${skill.id}`"
          >
            {{ skill.title }}
          </QueryLink>
          <QueryLink
            class="profile-skill-add"
            :to="{ query: { onglet: 'competences', nouveau: '1' } }"
            data-test="profile-skill-add"
          >
            + Ajouter
          </QueryLink>
        </div>
      </section>

      <div class="profile-section">
        <CriteriaForm heading="Ce que je cherche" />
      </div>

      <section
        class="profile-section"
        aria-labelledby="profile-parcours-title"
        data-test="profile-parcours"
      >
        <div class="profile-section-head">
          <h2 id="profile-parcours-title">
            Mon parcours
          </h2>
        </div>
        <ul class="criteria-rows">
          <li
            v-for="row in parcours"
            :key="row.key"
          >
            <QueryLink
              class="criteria-row"
              :to="{ query: { onglet: row.key } }"
              :data-test="`profile-parcours-${row.key}`"
            >
              <span class="criteria-row-text">
                <span class="criteria-row-label">{{ row.label }}</span>
                <span class="criteria-row-value">{{ row.line }}</span>
              </span>
              <span
                class="arrow-circle small"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </QueryLink>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style>
/* Les valeurs de ProfilOrdinateur, sur la grille de 4 (§2.9) : titres de 18 px, cartes à bordure de 1,5 px (12,5 / 18,5 px
   de marge, trait compris), puces de compétence 14 px sur fond gris clair (--surface-muted, #F1EFE9 n’est pas un jeton). */
.profile-desktop { --pd-18: 18px; --pd-pad-y: 14.5px; --pd-pad-x: 18.5px; --pd-chip-y: 4px; --pd-chip-h: 32px; max-width: 880px; margin: 0 auto; }
.profile-desktop-body { display: flex; flex-direction: column; gap: var(--space-6); padding-top: var(--space-4); max-width: 880px; padding-right: var(--space-6); padding-bottom: var(--space-8); padding-left: var(--space-6); margin: 0 auto; box-sizing: content-box; }
.profile-section { display: flex; flex-direction: column; gap: var(--space-2); }
.profile-section .section-title { margin: 0 var(--space-1); font-size: var(--pd-18); }
.profile-section-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-4); margin: 0 var(--space-1); }
.profile-section-head h2 { margin: 0; font-size: var(--pd-18); font-weight: var(--weight-bold); }
.profile-section-head span { font-size: var(--font-small); color: var(--text-secondary); }
.profile-card { background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.profile-cv-card { overflow: hidden; }
.profile-cv { display: flex; align-items: center; gap: var(--space-4); padding: var(--pd-pad-y) var(--pd-pad-x); }
.profile-cv-icon { flex: none; width: 28px; height: 28px; color: var(--primary-graphic); }
.profile-cv-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.profile-cv-text strong { font-size: var(--font-label); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-cv-text span { font-size: var(--font-small); color: var(--text-secondary); }
.profile-cv-text .profile-cv-line-todo { color: var(--peach-text); font-weight: var(--weight-semibold); }
.profile-cv-text .profile-cv-line-ok { color: var(--success); font-weight: var(--weight-semibold); }
.profile-cv-card { --cv-pad-x: var(--pd-pad-x); }
.profile-cv .button { display: inline-flex; align-items: center; min-height: 44px; padding: 0 var(--space-5); box-sizing: border-box; border: 1.5px solid var(--primary); border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-semibold); text-decoration: none; white-space: nowrap; cursor: pointer; }
.profile-cv .button:hover { background: var(--primary-soft); }
.profile-cv-upload:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.profile-skills-empty { padding: var(--pd-pad-y) var(--pd-pad-x); font-size: var(--font-small); color: var(--text-secondary); }
.profile-skills-empty a { color: var(--primary-text); font-weight: var(--weight-bold); }
.profile-skills { display: flex; flex-wrap: wrap; gap: var(--space-2); padding: var(--pd-pad-y) var(--pd-pad-x); }
.profile-skill, .profile-skill-add { display: inline-flex; align-items: center; min-height: var(--pd-chip-h); padding: var(--pd-chip-y) var(--space-3); box-sizing: border-box; border-radius: var(--radius-pill); font-size: var(--font-small); font-weight: var(--weight-semibold); text-decoration: none; }
.profile-skill { background: var(--surface-muted); color: var(--text-secondary); }
.profile-skill:hover { color: var(--text); }
.profile-skill-add { border: 1.5px dashed var(--field-border); color: var(--primary-text); }
.profile-section .criteria-row { text-decoration: none; }
.profile-desktop .narrow-block, .profile-section .narrow-block { max-width: none; }

/* Téléphone (maquette ProfilTel, prompt du 10 novembre, PR 20) : la barre « Mon profil » de 56 px avec le retour de
   48 px ; l'en-tête en ligne (image de 64, nom de 20, « Modifier » en lien) ; les titres de section en sur-titre de
   13 px en capitales ; sections à 20 px des bords, 12 px au-dessus et au-dessous, sans trait. La carte du CV : nom du
   fichier tronqué sur une ligne, « Voir | Remplacer » en bas, séparés par un filet (--line). */
.profile-topbar { --pt-22: 22px; display: flex; align-items: center; gap: var(--space-1); min-height: 56px; padding: 0 var(--space-2) 0 var(--space-1); }
.profile-topbar h1 { margin: 0; font-size: var(--pt-22); font-weight: var(--weight-heavy); }
.profile-topbar-back { display: grid; place-items: center; width: 48px; height: 48px; color: var(--text); }
.profile-topbar-back .icon { width: 24px; height: 24px; }
.jobs-head.profile-subhead.profile-topbar { flex-direction: row; align-items: center; max-width: none; margin: 0; padding: 0 var(--space-2) 0 var(--space-1); }
.profile-subhead.profile-topbar h1 { font-size: var(--pt-22); letter-spacing: 0; }
.profile-cv-split { display: flex; border-top: 1px solid var(--line); }
.profile-cv-split > :is(a, label) { flex: 1; display: inline-flex; align-items: center; justify-content: center; min-height: 44px; color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; cursor: pointer; }
.profile-cv-split > * + * { border-left: 1px solid var(--line); }
.profile-cv-split label:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: -2px; }
@media (max-width: 599px) {
  .profile-desktop { --pd-pad-y: 14.5px; --pd-pad-x: 16px; --pd-13: 13px; --pd-15: 15px; --pd-18-lh: 18px; --pd-20: 20px; --pd-22-lh: 22px; --pd-26: 26px; }
  .profile-desktop .jobs-head.profile-head { padding: var(--space-3) var(--space-5) var(--space-2); }
  .profile-desktop .profile-head-main { gap: var(--space-4); padding: var(--space-1) var(--space-1) var(--space-2); }
  .profile-desktop .profile-head-text .profile-head-name { margin: 0; overflow-wrap: anywhere; font-size: var(--pd-20); line-height: var(--pd-26); font-weight: var(--weight-bold); letter-spacing: 0; }
  .profile-desktop .profile-head-text .profile-head-subline { margin: 0; font-size: var(--pd-15); color: var(--text-secondary); }
  .profile-desktop .profile-head-actions button { min-height: 44px; padding: 0; border: 0; background: none; color: var(--primary-text); font-size: var(--pd-15); font-weight: var(--weight-bold); }
  .profile-desktop-body { gap: 0; padding: 0 var(--space-5) var(--space-8); box-sizing: border-box; }
  .profile-desktop-body > .profile-section { padding: var(--space-3) 0; }
  .profile-section-head h2, .profile-section .section-title { margin: 0; font-size: var(--pd-13); line-height: var(--pd-18-lh); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
  .profile-section-head { margin: 0; }
  .profile-section-head span { display: none; }
  .profile-cv-card { border-radius: var(--radius-card); }
  .profile-skills-empty { padding: var(--space-4); font-size: var(--pd-15); line-height: var(--pd-22-lh); }
  /* Les puces sont des liens : 44 px de cible au toucher (la maquette les dessine à 30 px, sans lien). */
  .profile-skill, .profile-skill-add { min-height: var(--target-min); }
  .profile-skills-add-link { display: inline-flex; align-items: center; min-height: 44px; text-decoration: none; }
}
</style>
