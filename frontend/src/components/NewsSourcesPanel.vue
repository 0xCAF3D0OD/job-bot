<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type NewsPreferences, type NewsSource } from "../api/client";
import { COUNTRIES, LANGUAGES } from "../newsLabels";
import NewsCatalog from "./NewsCatalog.vue";
import SidePanel from "./SidePanel.vue";

import HoverNote from "./HoverNote.vue";
// Réglages des Actualités (docs/15 §2, docs/16) : « Mon domaine » et sources.
const sources = ref<NewsSource[]>([]);
const preferences = ref<NewsPreferences | null>(null);
const keyword = ref("");
const loaded = ref(false);
// Un seul formulaire ouvert à la fois : adresse, suggestions ou veille.
const adding = ref<"" | "url" | "catalog" | "search">("");
const search = ref({ query: "", country: "CH", language: "fr" });
const form = ref({ url: "", name: "", match: "", country: "", language: "", labour_market: false });
const message = ref("");
const busy = ref(false);

async function load(): Promise<void> {
  const [list, prefs] = await Promise.all([api.GET("/api/news/sources"), api.GET("/api/news/preferences")]);
  sources.value = Array.isArray(list.data) ? list.data : [];
  preferences.value = Array.isArray(prefs.data?.domain_keywords) ? prefs.data : null;
  loaded.value = true;
}

async function saveKeywords(keywords: string[]): Promise<void> {
  if (!preferences.value) return;
  const { data } = await api.PUT("/api/news/preferences", {
    body: { ...preferences.value, domain_keywords: keywords },
  });
  if (data) preferences.value = data;
}

// Bouton toujours actif (docs/29 §3) : sans mot-clé, il le dit et rend la main au champ.
const keywordHint = ref("");

function addKeywords(): void {
  const current = preferences.value?.domain_keywords ?? [];
  // « DevOps, Kubernetes » : plusieurs mots-clés d'un coup, séparés par des virgules.
  const added = keyword.value.split(",").map((k) => k.trim()).filter(Boolean);
  if (!added.length) {
    keywordHint.value = "Écris un mot-clé, par exemple DevOps.";
    document.querySelector<HTMLInputElement>("[data-test=domain-input]")?.focus();
    return;
  }
  keywordHint.value = "";
  keyword.value = "";
  void saveKeywords([...current, ...added]);
}

function removeKeyword(value: string): void {
  void saveKeywords((preferences.value?.domain_keywords ?? []).filter((k) => k !== value));
}

async function update(
  source: NewsSource,
  change: { active?: boolean; country?: string; language?: string; labour_market?: boolean },
): Promise<void> {
  const { data } = await api.PATCH("/api/news/sources/{source_id}", {
    params: { path: { source_id: source.id } },
    body: change,
  });
  if (data) sources.value = data;
}

async function remove(source: NewsSource): Promise<void> {
  if (!window.confirm(`Ne plus suivre ${source.name} ?`)) return;
  const { data } = await api.DELETE("/api/news/sources/{source_id}", {
    params: { path: { source_id: source.id } },
  });
  if (data) {
    sources.value = data;
    openId.value = null;
  }
}

// Lignes calmes (docs/48 §3) : le nom, une ligne courte, l'interrupteur ; le reste dans le panneau.
const openId = ref<number | null>(null);
const opened = computed(() => sources.value.find((s) => s.id === openId.value) ?? null);
function origin(source: NewsSource): string {
  if (source.query) return `veille Google Actualités : « ${source.query} »`;
  return `${source.kind === "videos" ? "vidéos" : "articles"}${source.match ? ` · filtre : ${source.match}` : ""}`;
}
function line(source: NewsSource): string {
  return [
    source.query ? `veille « ${source.query} »` : source.kind === "videos" ? "vidéos" : "articles",
    source.country ? COUNTRIES[source.country as keyof typeof COUNTRIES] : "",
    source.language ? LANGUAGES[source.language as keyof typeof LANGUAGES] : "langues mêlées",
    source.labour_market ? "marché de l'emploi" : "",
  ]
    .filter(Boolean)
    .join(" · ");
}

async function add(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/news/sources", {
      body: {
        url: form.value.url.trim(),
        name: form.value.name.trim() || null,
        match: form.value.match.trim() || null,
        country: form.value.country || null,
        language: form.value.language || null,
        labour_market: form.value.labour_market,
      },
    });
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Ajout refusé : ${detail}.` : "Ajout refusé : vérifie l'adresse.";
      return;
    }
    sources.value = data;
    adding.value = "";
    form.value = { url: "", name: "", match: "", country: "", language: "", labour_market: false };
    message.value = "Source ajoutée : ses contenus arrivent dans quelques secondes.";
  } finally {
    busy.value = false;
  }
}

async function addSearch(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data, response } = await api.POST("/api/news/searches", {
      body: { ...search.value, query: search.value.query.trim() },
    });
    if (!data) {
      message.value = response.status === 409 ? "Cette veille existe déjà." : "Veille refusée : vérifie les mots-clés.";
      return;
    }
    sources.value = data;
    adding.value = "";
    search.value = { ...search.value, query: "" };
    message.value = "Veille ajoutée : ses articles arrivent dans quelques secondes.";
  } finally {
    busy.value = false;
  }
}

function catalogAdded(list: NewsSource[]): void {
  sources.value = list;
  message.value = "Source ajoutée : ses contenus arrivent dans quelques secondes.";
}

const value = (event: Event): string => (event.target as HTMLSelectElement).value;

onMounted(() => void load());
</script>

<template>
  <div
    v-if="loaded"
    class="form-card sites-card"
    data-test="news-sources"
  >
    <fieldset v-if="preferences">
      <legend>
        Mon domaine
      </legend>
      <ul
        class="keyword-chips"
        data-test="domain-keywords"
      >
        <li
          v-for="item in preferences.domain_keywords"
          :key="item"
          class="chip"
        >
          {{ item }}
          <button
            type="button"
            :aria-label="`Retirer ${item}`"
            @click="removeKeyword(item)"
          >
            ×
          </button>
        </li>
        <li
          v-if="!preferences.domain_keywords.length"
          class="hint"
        >
          Aucun mot-clé pour l'instant.
        </li>
      </ul>
      <form
        class="inline-form"
        @submit.prevent="addKeywords"
      >
        <input
          v-model="keyword"
          type="text"
          maxlength="200"
          placeholder="DevOps, Kubernetes, CKA…"
          aria-label="Mots-clés à ajouter"
          data-test="domain-input"
        >
        <button
          type="submit"
          class="secondary small"
        >
          Ajouter
        </button>
      </form>
      <span
        v-if="keywordHint"
        class="field-error"
        role="status"
      >{{ keywordHint }}</span>
    </fieldset>

    <fieldset>
      <legend>
        Sources des Actualités
      </legend>
      <ul class="calm-list">
        <li
          v-for="source in sources"
          :key="source.id"
          :class="{ paused: !source.active }"
          data-test="news-source"
        >
          <button
            type="button"
            class="calm-row"
            :data-test="`open-source-${source.id}`"
            @click="openId = source.id"
          >
            <strong>{{ source.name }}</strong>
            <span class="hint">
              {{ line(source) }}<template v-if="source.error"> · <span class="danger">dernier relevé en échec</span></template>
            </span>
          </button>
          <label class="filter-switch calm-switch">
            <span class="visually-hidden">{{ source.name }} suivie</span>
            <input
              type="checkbox"
              role="switch"
              :checked="source.active"
              data-test="source-active"
              @change="update(source, { active: !source.active })"
            >
          </label>
        </li>
      </ul>
      <SidePanel
        v-if="opened"
        open
        :title="opened.name"
        @close="openId = null"
      >
        <div
          class="calm-panel"
          data-test="source-panel"
        >
          <p class="hint">
            {{ origin(opened) }}<template v-if="opened.error">
              · <span class="danger">dernier relevé en échec</span>
            </template>
          </p>
          <label class="filter-switch calm-panel-switch">
            <span>Suivie</span>
            <input
              type="checkbox"
              role="switch"
              :checked="opened.active"
              @change="update(opened, { active: !opened.active })"
            >
          </label>
          <label>Pays
            <select
              :value="opened.country ?? ''"
              data-test="source-country"
              @change="update(opened, { country: value($event) })"
            >
              <option value="">pays ?</option>
              <option
                v-for="(label, code) in COUNTRIES"
                :key="code"
                :value="code"
              >{{ label }}</option>
            </select>
          </label>
          <label>Langue
            <select
              :value="opened.language ?? ''"
              @change="update(opened, { language: value($event) })"
            >
              <option value="">langues mêlées</option>
              <option
                v-for="(label, code) in LANGUAGES"
                :key="code"
                :value="code"
              >{{ label }}</option>
            </select>
          </label>
          <label class="check">
            <input
              type="checkbox"
              :checked="opened.labour_market"
              data-test="source-labour"
              @change="update(opened, { labour_market: !opened.labour_market })"
            >
            <HoverNote text="Avec « Mon domaine », une source « marché de l'emploi » garde ses articles sur l'emploi (chômage, salaires, embauches).">
              Marché de l'emploi
            </HoverNote>
          </label>
          <p class="calm-panel-foot">
            <button
              type="button"
              class="link danger"
              data-test="remove-source"
              @click="remove(opened)"
            >
              Retirer cette source
            </button>
          </p>
        </div>
      </SidePanel>
      <NewsCatalog
        v-if="adding === 'catalog'"
        @added="catalogAdded"
        @close="adding = ''"
      />
      <form
        v-else-if="adding === 'search'"
        class="form-grid"
        data-test="add-news-search"
        @submit.prevent="addSearch"
      >
        <label class="wide">
          <span>Mots-clés
          </span>
          <input
            v-model="search.query"
            type="text"
            minlength="2"
            maxlength="100"
            placeholder="Kubernetes emploi"
            required
            data-test="search-query"
          >
        </label>
        <label>Pays
          <select v-model="search.country">
            <option
              v-for="(label, code) in COUNTRIES"
              :key="code"
              :value="code"
            >{{ label }}</option>
          </select>
        </label>
        <label>Langue
          <select v-model="search.language">
            <option
              v-for="(label, code) in LANGUAGES"
              :key="code"
              :value="code"
            >{{ label }}</option>
          </select>
        </label>
        <div class="form-actions wide">
          <button
            type="submit"
            class="secondary small"
            :disabled="busy"
            data-test="save-news-search"
          >
            Créer la veille
          </button>
          <button
            type="button"
            class="link"
            @click="adding = ''"
          >
            Annuler
          </button>
        </div>
      </form>
      <form
        v-else-if="adding === 'url'"
        class="form-grid"
        data-test="add-news-source"
        @submit.prevent="add"
      >
        <label class="wide">
          <HoverNote text="Pour YouTube, l'ID se trouve sur la chaîne : « … plus », puis « Partager la chaîne », puis « Copier l'ID de la chaîne ».">
            Adresse du site, du flux RSS, ou ID de chaîne YouTube
          </HoverNote>
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
        <label>Pays
          <select v-model="form.country">
            <option value="">d'après l'adresse</option>
            <option
              v-for="(label, code) in COUNTRIES"
              :key="code"
              :value="code"
            >{{ label }}</option>
          </select>
        </label>
        <label>Langue
          <select v-model="form.language">
            <option value="">d'après le flux</option>
            <option
              v-for="(label, code) in LANGUAGES"
              :key="code"
              :value="code"
            >{{ label }}</option>
          </select>
        </label>
        <label class="check wide">
          <input
            v-model="form.labour_market"
            type="checkbox"
          > Marché de l'emploi
        </label>
        <div class="form-actions wide">
          <button
            type="submit"
            class="secondary small"
            :disabled="busy"
            data-test="save-news-source"
          >
            {{ busy ? "Vérification…" : "Ajouter" }}
          </button>
          <button
            type="button"
            class="link"
            @click="adding = ''"
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
          data-test="browse-catalog"
          @click="adding = 'catalog'"
        >
          Parcourir les suggestions
        </button>
        <button
          type="button"
          class="secondary small"
          data-test="add-search"
          @click="adding = 'search'"
        >
          Nouvelle veille
        </button>
        <button
          type="button"
          class="link"
          data-test="add-news"
          @click="adding = 'url'"
        >
          Ajouter par adresse
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
