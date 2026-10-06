<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type NewsSource } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Sources des Actualités (docs/15 §2) : site, flux RSS ou chaîne YouTube.
const sources = ref<NewsSource[]>([]);
const loaded = ref(false);
const adding = ref(false);
const form = ref({ url: "", name: "", match: "" });
const message = ref("");
const busy = ref(false);

async function load(): Promise<void> {
  const { data } = await api.GET("/api/news/sources");
  sources.value = data ?? [];
  loaded.value = true;
}

async function toggle(source: NewsSource): Promise<void> {
  const { data } = await api.PATCH("/api/news/sources/{source_id}", {
    params: { path: { source_id: source.id } },
    body: { active: !source.active },
  });
  if (data) sources.value = data;
}

async function remove(source: NewsSource): Promise<void> {
  if (!window.confirm(`Ne plus suivre ${source.name} ?`)) return;
  const { data } = await api.DELETE("/api/news/sources/{source_id}", {
    params: { path: { source_id: source.id } },
  });
  if (data) sources.value = data;
}

async function add(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/news/sources", {
      body: { url: form.value.url.trim(), name: form.value.name.trim() || null, match: form.value.match.trim() || null },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Ajout refusé : ${detail}.` : "Ajout refusé : vérifie l'adresse.";
      return;
    }
    sources.value = data;
    adding.value = false;
    form.value = { url: "", name: "", match: "" };
    message.value = "Source ajoutée : ses nouveautés arriveront au prochain relevé (toutes les 6 heures).";
  } finally {
    busy.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div
    v-if="loaded"
    id="actualites"
    class="form-card sites-card"
    data-test="news-sources"
  >
    <fieldset>
      <legend>Sources des Actualités</legend>
      <p class="hint">
        Flux publics, relevés toutes les 6 heures, sans coût. Colle l'adresse d'un site ou d'un flux RSS ; pour
        YouTube, l'ID de la chaîne (sur la chaîne : « … plus » → « Partager la chaîne » → « Copier l'ID de la chaîne »).
      </p>
      <ul class="sites-list">
        <li
          v-for="source in sources"
          :key="source.id"
          :class="{ paused: !source.active }"
          data-test="news-source"
        >
          <span class="site-main">
            <strong>{{ source.name }}</strong>
            <span class="hint">
              {{ source.kind === "videos" ? "vidéos" : "articles" }}{{ source.match ? ` · filtre : ${source.match}` : "" }}
              <template v-if="source.error"> · <span class="danger">dernier relevé en échec</span></template>
            </span>
          </span>
          <label class="check">
            <input
              type="checkbox"
              :checked="source.active"
              @change="toggle(source)"
            > suivie
          </label>
          <button
            type="button"
            class="link danger"
            @click="remove(source)"
          >
            Retirer
          </button>
        </li>
      </ul>
      <form
        v-if="adding"
        class="form-grid"
        data-test="add-news-source"
        @submit.prevent="add"
      >
        <label class="wide">Adresse du site, du flux RSS, ou ID de chaîne YouTube
          <input
            v-model="form.url"
            type="text"
            placeholder="https://… ou ID de chaîne YouTube (UC…)"
            required
            data-test="news-url"
          >
        </label>
        <label>Nom (facultatif)
          <input
            v-model="form.name"
            type="text"
          >
        </label>
        <label>Ne garder que ce qui contient (facultatif)
          <input
            v-model="form.match"
            type="text"
            placeholder="emploi"
          >
        </label>
        <div class="form-actions wide">
          <button
            type="submit"
            class="primary small"
            :disabled="busy"
            data-test="save-news-source"
          >
            {{ busy ? "Vérification…" : "Ajouter" }} <AppIcon name="chevron" />
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
          data-test="add-news"
          @click="adding = true"
        >
          Ajouter une source
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
