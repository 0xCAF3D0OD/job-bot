<script setup lang="ts">
import { computed, ref } from "vue";

import { api, type AlertsPage } from "../api/client";
import AppIcon from "./AppIcon.vue";

// Assistant des alertes (docs/21 §4) : un écran à la fois, tant qu'aucune alerte n'est en place.
const props = defineProps<{ page: AlertsPage }>();
const emit = defineEmits<{ updated: [page: AlertsPage]; done: [] }>();

const step = ref<1 | 2 | 3>(1);
const siteIndex = ref(0);
const form = ref({ terms: "", location: "" });
const busy = ref(false);

const searches = computed(() => props.page.searches.filter((s) => s.active));
// Sites avec une recherche à ouvrir (les sites ajoutés sans adresse sont laissés de côté).
const sites = computed(() =>
  props.page.sites.filter((site) => searches.value.some((s) => s.cells.find((c) => c.site === site.slug)?.url)),
);
const site = computed(() => sites.value[siteIndex.value] ?? null);

function cellUrl(searchId: number): string | null {
  const search = searches.value.find((s) => s.id === searchId);
  return search?.cells.find((c) => c.site === site.value?.slug)?.url ?? null;
}

async function add(): Promise<void> {
  if (!form.value.terms.trim()) return;
  const { data } = await api.POST("/api/alert-searches", {
    body: { terms: form.value.terms.trim(), location: form.value.location.trim() || null },
  });
  if (data) emit("updated", data);
  form.value = { terms: "", location: "" };
}

async function remove(id: number): Promise<void> {
  const { data } = await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: id } } });
  if (data) emit("updated", data);
}

// « C'est fait » : l'alerte est notée créée pour chaque recherche sur ce site.
async function siteDone(): Promise<void> {
  if (!site.value) return;
  busy.value = true;
  try {
    let latest: AlertsPage | undefined;
    for (const search of searches.value) {
      const { data } = await api.PUT("/api/alert-searches/{search_id}/sites/{site}", {
        params: { path: { search_id: search.id, site: site.value.slug } },
      });
      latest = data ?? latest;
    }
    if (latest) emit("updated", latest);
  } finally {
    busy.value = false;
  }
  nextSite();
}

function nextSite(): void {
  if (siteIndex.value + 1 < sites.value.length) siteIndex.value += 1;
  else step.value = 3;
}
</script>

<template>
  <section
    class="form-card wizard"
    data-test="alerts-wizard"
  >
    <p class="wizard-step">
      Étape {{ step }} sur 3
    </p>

    <template v-if="step === 1">
      <h2>Que veux-tu recevoir ?</h2>
      <p class="hint">
        Une recherche = des mots et un lieu. Garde celles qui te conviennent.
      </p>
      <ul class="keyword-chips">
        <li
          v-for="search in searches"
          :key="search.id"
          class="chip"
          data-test="wizard-search"
        >
          {{ search.terms }} · {{ search.location || "toute la Suisse" }}
          <button
            type="button"
            :aria-label="`Retirer ${search.terms}`"
            @click="remove(search.id)"
          >
            ×
          </button>
        </li>
      </ul>
      <form
        class="inline-form"
        data-test="wizard-add"
        @submit.prevent="add"
      >
        <input
          v-model="form.terms"
          type="text"
          maxlength="120"
          placeholder="Mots (DevOps)"
          aria-label="Mots"
          data-test="wizard-terms"
        >
        <input
          v-model="form.location"
          type="text"
          maxlength="80"
          placeholder="Lieu (Lausanne)"
          aria-label="Lieu"
        >
        <button
          type="submit"
          class="secondary small"
        >
          Ajouter
        </button>
      </form>
      <div class="form-actions">
        <button
          type="button"
          class="primary"
          :disabled="!searches.length"
          data-test="wizard-next"
          @click="step = 2"
        >
          Continuer <AppIcon name="chevron" />
        </button>
      </div>
    </template>

    <template v-else-if="step === 2 && site">
      <h2>Crée l'alerte sur {{ site.name }}</h2>
      <p class="hint">
        Ouvre la recherche, clique sur « Créer une alerte » (ou « Activer l'alerte ») et donne ton adresse e-mail.
        Site {{ siteIndex + 1 }} sur {{ sites.length }}.
      </p>
      <div class="wizard-links">
        <template
          v-for="search in searches"
          :key="search.id"
        >
          <a
            v-if="cellUrl(search.id)"
            :href="cellUrl(search.id)!"
            target="_blank"
            rel="noopener noreferrer"
            class="button-link primary-link"
            data-test="wizard-open"
          >Ouvrir {{ site.name }} : {{ search.terms }}{{ search.location ? ` · ${search.location}` : "" }}
            <AppIcon name="chevron" /></a>
        </template>
      </div>
      <div class="form-actions">
        <button
          type="button"
          class="primary"
          :disabled="busy"
          data-test="wizard-site-done"
          @click="siteDone"
        >
          C'est fait, site suivant <AppIcon name="chevron" />
        </button>
        <button
          type="button"
          class="link"
          data-test="wizard-skip"
          @click="nextSite"
        >
          Passer ce site
        </button>
      </div>
    </template>

    <template v-else>
      <h2>C'est prêt</h2>
      <p>
        Tes alertes arriveront dans ta boîte<template v-if="page.mailbox">
          (<strong>{{ page.mailbox }}</strong>)
        </template>, souvent dès le lendemain. Elles apparaîtront ici au premier
        envoi.
      </p>
      <div class="form-actions">
        <button
          type="button"
          class="primary"
          data-test="wizard-finish"
          @click="emit('done')"
        >
          Voir mes alertes
        </button>
      </div>
    </template>
  </section>
</template>
