<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Chunk, type DocumentOut } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "./AppIcon.vue";
import AvatarPicker from "./AvatarPicker.vue";
import CriteriaForm from "./CriteriaForm.vue";
import ProfileEditSheet from "./ProfileEditSheet.vue";
import ProfileGauge from "./ProfileGauge.vue";
import ProfileImage from "./ProfileImage.vue";
import { useProfileImage } from "../composables/useProfileImage";
import { useProfiles } from "../composables/useProfiles";
import { dateInSentence } from "../dates";
import { plural } from "../format";

// Profil sur ordinateur, en page unique (maquette ProfilOrdinateur ; PR 9b, décision de Kevin du 10 novembre) :
// l'en-tête (image à pastille crayon, nom, poste · lieu, « Modifier »), Mon CV, Compétences trouvées, Ce que je
// cherche, puis « Mon parcours » en lignes qui ouvrent chacune leur page (?onglet=…). La pastille crayon ouvre
// « Ton image » : plus de bouton « Changer d'image ». « Modifier » ne change que le nom, le poste et le lieu.
type Identity = components["schemas"]["Identity"];

const image = useProfileImage();
const profiles = useProfiles();
const documents = ref<DocumentOut[]>([]);
const chunks = ref<Chunk[]>([]);
const identity = ref<Identity | null>(null);
const picking = ref(false);
const editing = ref(false);
const uploading = ref(false);
const message = ref("");

async function loadDocuments(): Promise<void> {
  const { data } = await api.GET("/api/documents");
  documents.value = data ?? [];
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
const cvLine = computed(() => {
  const doc = cv.value;
  if (!doc) return "";
  const state = doc.text_status !== "ok" ? "texte non lisible" : doc.chunk_count ? "analysé" : "pas encore analysé";
  return `Mis à jour ${dateInSentence(doc.uploaded_at)} · ${state}`;
});

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
    { key: "formations", label: "Formations", line: count("formation") ? plural(count("formation"), "formation", "formations") : "Aucune formation" },
    { key: "experiences", label: "Expériences", line: count("experience") ? plural(count("experience"), "expérience", "expériences") : "Aucune expérience" },
    { key: "documents", label: "Documents et certificats", line: docs || "Aucun document" },
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
            :size="72"
          />
          <span
            class="profile-head-pencil"
            aria-hidden="true"
          ><AppIcon name="pencil" /></span>
        </button>
        <div class="profile-head-text">
          <h1>{{ image.name.value || "Profil" }}</h1>
          <p
            v-if="subline"
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
        <div class="profile-card profile-cv">
          <AppIcon
            name="file"
            class="profile-cv-icon"
          />
          <div class="profile-cv-text">
            <strong data-test="profile-cv-name">{{ cv ? cv.filename : "Aucun CV déposé" }}</strong>
            <span>{{ cv ? cvLine : "PDF, DOCX, TXT ou MD · 10 Mo au plus" }}</span>
          </div>
          <a
            v-if="cv"
            class="button secondary action-2"
            :href="`/api/documents/${cv.id}/file`"
            target="_blank"
            rel="noopener"
            data-test="profile-cv-open"
          >Voir<span class="visually-hidden"> {{ cv.filename }} (nouvel onglet)</span></a>
          <label
            class="button secondary action-2 profile-cv-upload"
            :aria-busy="uploading ? 'true' : undefined"
            data-test="profile-cv-replace"
          >
            <input
              type="file"
              class="visually-hidden"
              accept=".pdf,.docx,.txt,.md"
              data-test="profile-cv-input"
              @change="onFile"
            >
            {{ uploading ? "Envoi…" : cv ? "Remplacer" : "Déposer mon CV" }}
          </label>
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
        <div class="profile-card profile-skills">
          <RouterLink
            v-for="skill in skills"
            :key="skill.id"
            class="profile-skill"
            :to="{ query: { onglet: 'competences', bloc: skill.id } }"
            :data-test="`profile-skill-${skill.id}`"
          >
            {{ skill.title }}
          </RouterLink>
          <RouterLink
            class="profile-skill-add"
            :to="{ query: { onglet: 'competences', nouveau: '1' } }"
            data-test="profile-skill-add"
          >
            + Ajouter
          </RouterLink>
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
            <RouterLink
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
            </RouterLink>
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
.profile-cv { display: flex; align-items: center; gap: var(--space-4); padding: var(--pd-pad-y) var(--pd-pad-x); }
.profile-cv-icon { flex: none; width: 28px; height: 28px; color: var(--primary-graphic); }
.profile-cv-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.profile-cv-text strong { font-size: var(--font-label); overflow-wrap: anywhere; }
.profile-cv-text span { font-size: var(--font-small); color: var(--text-secondary); }
.profile-cv .button { display: inline-flex; align-items: center; min-height: 44px; padding: 0 var(--space-5); box-sizing: border-box; border: 1.5px solid var(--primary); border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-semibold); text-decoration: none; white-space: nowrap; cursor: pointer; }
.profile-cv .button:hover { background: var(--primary-soft); }
.profile-cv-upload:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.profile-skills { display: flex; flex-wrap: wrap; gap: var(--space-2); padding: var(--pd-pad-y) var(--pd-pad-x); }
.profile-skill, .profile-skill-add { display: inline-flex; align-items: center; min-height: var(--pd-chip-h); padding: var(--pd-chip-y) var(--space-3); box-sizing: border-box; border-radius: var(--radius-pill); font-size: var(--font-small); font-weight: var(--weight-semibold); text-decoration: none; }
.profile-skill { background: var(--surface-muted); color: var(--text-secondary); }
.profile-skill:hover { color: var(--text); }
.profile-skill-add { border: 1.5px dashed var(--field-border); color: var(--primary-text); }
.profile-section .criteria-row { text-decoration: none; }
.profile-desktop .narrow-block, .profile-section .narrow-block { max-width: none; }
</style>
