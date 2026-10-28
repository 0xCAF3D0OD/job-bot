<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";

import { api, type Profile, type ProfileList } from "../api/client";
import { useProfiles } from "../composables/useProfiles";
import { COUNTRIES, LANGUAGES } from "../newsLabels";
import { plural } from "../format";
import BusyButton from "./BusyButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";
import { offerUndo } from "../composables/useUndo";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Profils d'essai (docs/17 §2) : des chercheurs d'emploi fictifs, pour juger si les
// Actualités et les Formations leur conviennent. Une carte (1.6.67, planche « 5. Réglages ») :
// une ligne d'en-tête, une ligne par profil avec « Utiliser » et « ⋯ » à droite, puis « Créer ».
const { list, current, load, set, choose } = useProfiles();
const adding = ref(false);
const busy = ref(false);
const message = ref("");
const empty = () => ({ name: "", occupation: "", keywords: "", languages: ["fr"] as string[], countries: ["CH"] as string[] });
const form = ref(empty());
const canPropose = ref(false);
const proposing = ref(false);

// Mots-clés proposés par l'IA à partir du métier (docs/17 §2), environ 0,001 $.
async function propose(): Promise<void> {
  // Bouton toujours actif (docs/29 §3) : sans métier, il le dit.
  if (form.value.occupation.trim().length < 2) {
    message.value = "Indique d'abord le métier (deux lettres au moins).";
    return;
  }
  proposing.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/profiles/keywords", {
      body: { occupation: form.value.occupation.trim() },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Proposition impossible : ${detail}.` : "Proposition impossible.";
      return;
    }
    if (!data.keywords.length) {
      message.value = "Aucun mot-clé proposé : précise le métier.";
      return;
    }
    form.value.keywords = data.keywords.join(", ");
  } finally {
    proposing.value = false;
  }
}

function apply(data: ProfileList | undefined): void {
  if (data) set(data);
}

async function create(): Promise<void> {
  if (busy.value) return;
  busy.value = true;
  message.value = "";
  try {
    const { data } = await api.POST("/api/profiles", {
      body: {
        name: form.value.name.trim(),
        occupation: form.value.occupation.trim() || null,
        domain_keywords: form.value.keywords.split(",").map((k) => k.trim()).filter(Boolean),
        languages: form.value.languages,
        countries: form.value.countries,
      },
    });
    if (!data) {
      message.value = "Création refusée : vérifie le nom.";
      return;
    }
    apply(data);
    adding.value = false;
    form.value = empty();
    message.value = "Profil créé : choisis-le dans le menu en haut pour voir ses Formations.";
  } finally {
    busy.value = false;
  }
}

// La phrase d'un profil : « infirmière · soins, EMS · 3 sources ».
function line(profile: Profile): string {
  return [
    profile.occupation,
    profile.domain_keywords.length ? profile.domain_keywords.join(", ") : "domaine non renseigné",
    plural(profile.sources, "source", "sources"),
  ]
    .filter(Boolean)
    .join(" · ");
}

// « Utiliser » visible, le reste dans « ⋯ » (docs/74).
function profileItems(profile: Profile): MoreMenuItem[] {
  return [
    { label: "Dupliquer", test: "profile-duplicate", icon: "copy", run: () => void duplicate(profile) },
    { label: "Renommer", test: "profile-rename", icon: "pencil", run: () => void rename(profile) },
    ...(profile.is_main ? [] : [{ label: "Supprimer", test: "profile-delete", icon: "trash" as const, danger: true, run: () => void remove(profile) }]),
  ];
}

async function duplicate(profile: Profile): Promise<void> {
  apply((await api.POST("/api/profiles/{profile_id}/duplicate", { params: { path: { profile_id: profile.id } } })).data);
}

// Renommer sur place (docs/108, complément 0.77.1) : le nom devient un champ, à sa place.
// Pas de bouton « Enregistrer » (1.6.67) : Entrée ou quitter le champ enregistre, Échap annule.
const renaming = ref<{ id: number; name: string } | null>(null);
async function rename(profile: Profile): Promise<void> {
  renaming.value = { id: profile.id, name: profile.name };
  await nextTick();
  document.querySelector<HTMLInputElement>("[data-test=profile-rename-input]")?.select();
}
async function saveRename(profile: Profile): Promise<void> {
  const name = renaming.value?.name.trim();
  renaming.value = null;
  if (!name || name === profile.name) return;
  apply(
    (await api.PATCH("/api/profiles/{profile_id}", { params: { path: { profile_id: profile.id } }, body: { name } }))
      .data,
  );
}

// Retiré tout de suite, « Annuler » pendant 6 s (docs/108 §1).
async function remove(profile: Profile): Promise<void> {
  const before = list.value;
  if (before) list.value = { ...before, items: before.items.filter((p) => p.id !== profile.id) };
  if (current.value?.id === profile.id) choose(before?.items.find((p) => p.is_main)?.id ?? 0);
  await offerUndo({
    message: `Profil « ${profile.name} » supprimé`,
    commit: async (keepalive) => {
      const { data } = await api.DELETE("/api/profiles/{profile_id}", { params: { path: { profile_id: profile.id } }, keepalive });
      if (!data) return false;
      apply(data);
    },
    restore: () => {
      list.value = before;
    },
  });
}

function toggle(field: "languages" | "countries", value: string): void {
  const values = form.value[field];
  form.value[field] = values.includes(value) ? values.filter((v) => v !== value) : [...values, value];
}

onMounted(async () => {
  await load();
  canPropose.value = Boolean((await api.GET("/api/profiles/keywords")).data?.available);
});
</script>

<template>
  <SettingCard
    v-if="list"
    class="sites-card"
    data-test="profiles-panel"
  >
    <SettingRow
      title="Profils d'essai"
      description="Des chercheurs d'emploi fictifs, pour juger les Actualités et les Formations."
    />
    <template
      v-for="profile in list.items"
      :key="profile.id"
    >
      <form
        v-if="renaming?.id === profile.id"
        class="inline-edit setting-row-form"
        data-test="profile-rename-form"
        @submit.prevent="saveRename(profile)"
        @keydown.esc="renaming = null"
      >
        <input
          v-model="renaming.name"
          type="text"
          maxlength="60"
          required
          aria-label="Nom du profil"
          data-test="profile-rename-input"
          @blur="saveRename(profile)"
        >
      </form>
      <SettingRow
        v-else
        :title="profile.is_main ? `${profile.name} (principal)` : profile.name"
        :description="line(profile)"
        data-test="profile"
      >
        <span
          v-if="current?.id === profile.id"
          class="hint with-icon"
        ><AppIcon name="done" />Utilisé</span>
        <button
          v-else
          type="button"
          class="secondary small"
          data-test="profile-use"
          @click="choose(profile.id)"
        >
          Utiliser
        </button>
        <MoreMenu
          :items="profileItems(profile)"
          :label="`Plus d'actions sur le profil ${profile.name}`"
          test-id="profile-more"
        />
      </SettingRow>
    </template>
    <form
      v-if="adding"
      class="form-grid setting-row-form"
      data-test="add-profile"
      @submit.prevent="create"
    >
      <label>Nom
        <input
          v-model="form.name"
          type="text"
          maxlength="60"
          required
          placeholder="Infirmière à Lausanne"
          data-test="profile-name"
        >
      </label>
      <label>Métier (facultatif)
        <input
          v-model="form.occupation"
          type="text"
          maxlength="120"
          placeholder="infirmière en soins généraux"
          data-test="profile-occupation"
        >
      </label>
      <label class="wide">« Domaine » : mots-clés séparés par des virgules
        <input
          v-model="form.keywords"
          type="text"
          maxlength="600"
          placeholder="soins, infirmière, hôpital, EMS"
          data-test="profile-keywords"
        >
      </label>
      <div
        v-if="canPropose"
        class="wide"
      >
        <BusyButton
          class="secondary small"
          :busy="proposing"
          busy-label="Proposition…"
          data-test="propose-keywords"
          @click="propose"
        >
          <HoverNote :text="proposing ? '' : 'Environ 0,001 $.'">
            <span class="with-icon"><AppIcon name="ai" />Proposer des mots-clés</span>
          </HoverNote>
        </BusyButton>
      </div>
      <div class="wide chip-group">
        <span class="chip-label">Langues</span>
        <button
          v-for="(label, code) in LANGUAGES"
          :key="code"
          type="button"
          :class="['chip', { on: form.languages.includes(code) }]"
          :aria-pressed="form.languages.includes(code)"
          @click="toggle('languages', code)"
        >
          {{ label }}
        </button>
      </div>
      <div class="wide chip-group">
        <span class="chip-label">Pays</span>
        <button
          v-for="(label, code) in COUNTRIES"
          :key="code"
          type="button"
          :class="['chip', { on: form.countries.includes(code) }]"
          :aria-pressed="form.countries.includes(code)"
          @click="toggle('countries', code)"
        >
          {{ label }}
        </button>
      </div>
      <div class="form-actions wide">
        <BusyButton
          type="submit"
          class="secondary small"
          :busy="busy"
          busy-label="Création…"
          data-test="save-profile"
        >
          Créer le profil
        </BusyButton>
        <button
          type="button"
          class="link"
          @click="adding = false"
        >
          Annuler
        </button>
      </div>
    </form>
    <SettingRow
      v-else
      title="Un autre profil"
      description="Un métier, ses mots-clés, ses langues et ses pays."
    >
      <button
        type="button"
        class="secondary small"
        data-test="add-profile-open"
        @click="adding = true"
      >
        <span class="with-icon"><AppIcon name="plus" />Créer un profil</span>
      </button>
    </SettingRow>
    <p
      v-if="message"
      class="muted setting-row-message"
      role="status"
    >
      {{ message }}
    </p>
  </SettingCard>
</template>
