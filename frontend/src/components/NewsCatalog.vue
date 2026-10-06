<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type NewsCatalog, type NewsSource } from "../api/client";
import { countryLabel, languageLabel } from "../newsLabels";

// Sources suggérées (docs/16 §4.1) : vérifiées, ajoutées en un clic.
const emit = defineEmits<{ added: [sources: NewsSource[]]; close: [] }>();
const data = ref<NewsCatalog | null>(null);
const domain = ref("");
const country = ref("");
const language = ref("");
const busy = ref("");

const countries = computed(() => [...new Set(data.value?.sources.map((s) => s.country))].sort());
const languages = computed(() =>
  [...new Set(data.value?.sources.map((s) => s.language).filter((l): l is string => Boolean(l)))].sort(),
);
const shown = computed(() =>
  (data.value?.sources ?? []).filter(
    (s) =>
      (!domain.value || s.domains.includes(domain.value)) &&
      (!country.value || s.country === country.value) &&
      (!language.value || s.language === language.value),
  ),
);

async function add(id: string): Promise<void> {
  busy.value = id;
  try {
    const { data: sources } = await api.POST("/api/news/catalog/{catalog_id}", {
      params: { path: { catalog_id: id } },
    });
    if (sources && data.value) {
      data.value = {
        ...data.value,
        sources: data.value.sources.map((s) => (s.id === id ? { ...s, added: true } : s)),
      };
      emit("added", sources);
    }
  } finally {
    busy.value = "";
  }
}

onMounted(async () => {
  data.value = (await api.GET("/api/news/catalog")).data ?? null;
});
</script>

<template>
  <div
    v-if="data"
    class="news-catalog"
    data-test="news-catalog"
  >
    <div class="catalog-filters">
      <select
        v-model="domain"
        aria-label="Domaine"
        data-test="catalog-domain"
      >
        <option value="">
          Tous les domaines
        </option>
        <option
          v-for="(label, key) in data.domains"
          :key="key"
          :value="key"
        >
          {{ label }}
        </option>
      </select>
      <select
        v-model="country"
        aria-label="Pays"
      >
        <option value="">
          Tous les pays
        </option>
        <option
          v-for="code in countries"
          :key="code"
          :value="code"
        >
          {{ countryLabel(code) }}
        </option>
      </select>
      <select
        v-model="language"
        aria-label="Langue"
      >
        <option value="">
          Toutes les langues
        </option>
        <option
          v-for="code in languages"
          :key="code"
          :value="code"
        >
          {{ languageLabel(code) }}
        </option>
      </select>
      <button
        type="button"
        class="link"
        @click="emit('close')"
      >
        Fermer
      </button>
    </div>
    <ul class="sites-list">
      <li
        v-for="source in shown"
        :key="source.id"
        data-test="catalog-source"
      >
        <span class="site-main">
          <strong>{{ source.name }}</strong>
          <span class="hint">{{ source.description }}</span>
          <span class="hint">
            {{ source.kind === "videos" ? "vidéos" : "articles" }} · {{ countryLabel(source.country) }}
            <template v-if="source.language"> · {{ languageLabel(source.language) }}</template>
            · {{ source.domains.map((d) => data!.domains[d] ?? d).join(", ") }}
          </span>
        </span>
        <span
          v-if="source.added"
          class="hint"
        >suivie ✓</span>
        <button
          v-else
          type="button"
          class="secondary small"
          :disabled="busy === source.id"
          data-test="catalog-add"
          @click="add(source.id)"
        >
          Ajouter
        </button>
      </li>
    </ul>
  </div>
</template>
