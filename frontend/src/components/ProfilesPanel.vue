<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type Profile, type ProfileList } from "../api/client";
import { useProfiles } from "../composables/useProfiles";
import { COUNTRIES, LANGUAGES } from "../newsLabels";
import AppIcon from "./AppIcon.vue";

// Profils d'essai (docs/17 §2) : des chercheurs d'emploi fictifs, pour juger si les
// Actualités et les Formations leur conviennent.
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
    message.value = "Profil créé : choisis-le dans le menu en haut pour voir ses Actualités et ses Formations.";
  } finally {
    busy.value = false;
  }
}

async function duplicate(profile: Profile): Promise<void> {
  apply((await api.POST("/api/profiles/{profile_id}/duplicate", { params: { path: { profile_id: profile.id } } })).data);
}

async function rename(profile: Profile): Promise<void> {
  const name = window.prompt("Nouveau nom du profil", profile.name)?.trim();
  if (!name || name === profile.name) return;
  apply(
    (await api.PATCH("/api/profiles/{profile_id}", { params: { path: { profile_id: profile.id } }, body: { name } }))
      .data,
  );
}

async function remove(profile: Profile): Promise<void> {
  if (!window.confirm(`Supprimer le profil « ${profile.name} » ?`)) return;
  apply((await api.DELETE("/api/profiles/{profile_id}", { params: { path: { profile_id: profile.id } } })).data);
  if (current.value?.id === profile.id) choose(list.value?.items.find((p) => p.is_main)?.id ?? 0);
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
  <div
    v-if="list"
    class="form-card sites-card"
    data-test="profiles-panel"
  >
    <fieldset>
      <legend>Tes profils</legend>
      <p class="hint">
        Des chercheurs d'emploi fictifs, pour voir si les Actualités et les Formations leur conviennent. Un profil d'essai
        a son propre « Mon domaine », ses filtres et ses sources ; tes offres, candidatures et preuves ORP ne changent
        pas. Aucune donnée personnelle n'est demandée.
      </p>
      <ul class="sites-list">
        <li
          v-for="profile in list.items"
          :key="profile.id"
          data-test="profile"
        >
          <span class="site-main">
            <strong>{{ profile.name }}<template v-if="profile.is_main"> (principal)</template></strong>
            <span class="hint">
              <template v-if="profile.occupation">{{ profile.occupation }} · </template>
              {{ profile.domain_keywords.length ? profile.domain_keywords.join(", ") : "domaine non renseigné" }}
              · {{ profile.sources }} source(s)
            </span>
          </span>
          <span
            v-if="current?.id === profile.id"
            class="hint"
          >utilisé ✓</span>
          <button
            v-else
            type="button"
            class="secondary small"
            data-test="profile-use"
            @click="choose(profile.id)"
          >
            Utiliser
          </button>
          <button
            type="button"
            class="link"
            data-test="profile-duplicate"
            @click="duplicate(profile)"
          >
            Dupliquer
          </button>
          <button
            type="button"
            class="link"
            @click="rename(profile)"
          >
            Renommer
          </button>
          <button
            v-if="!profile.is_main"
            type="button"
            class="link danger"
            data-test="profile-delete"
            @click="remove(profile)"
          >
            Supprimer
          </button>
        </li>
      </ul>
      <form
        v-if="adding"
        class="form-grid"
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
        <label class="wide">« Mon domaine » : mots-clés séparés par des virgules
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
          <button
            type="button"
            class="secondary small"
            :disabled="proposing || form.occupation.trim().length < 2"
            title="Claude Haiku reçoit seulement le métier ; environ 0,001 $"
            data-test="propose-keywords"
            @click="propose"
          >
            {{ proposing ? "Proposition…" : "Proposer des mots-clés à partir du métier" }}
          </button>
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
          <button
            type="submit"
            class="primary small"
            :disabled="busy"
            data-test="save-profile"
          >
            Créer le profil <AppIcon name="chevron" />
          </button>
          <button
            type="button"
            class="link"
            @click="adding = false"
          >
            Annuler
          </button>
        </div>
      </form>
      <div
        v-else
        class="form-actions"
      >
        <button
          type="button"
          class="secondary small"
          data-test="add-profile-open"
          @click="adding = true"
        >
          Créer un profil d'essai
        </button>
      </div>
      <p
        v-if="message"
        class="hint"
        role="status"
      >
        {{ message }}
      </p>
    </fieldset>
  </div>
</template>
