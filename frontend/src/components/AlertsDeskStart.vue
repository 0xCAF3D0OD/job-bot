<script setup lang="ts">
import { computed } from "vue";

import type { AlertsPage } from "../api/client";
import { searchSummary, START_SITES } from "../alertsState";
import AppIcon from "./AppIcon.vue";
import BlockRow from "./BlockRow.vue";
import "../blocks.css";

// Mes alertes e-mail sur ordinateur, rien en place (planche AlertesOrdinateurVide du 17.11, option A de Kevin) : la
// carte « Ta recherche » (postes · lieux, « Modifier »), puis « À créer » avec une ligne par site, qui ouvre le volet
// du site (AlertesOrdinateurSite). Les familles et les lignes reprennent les styles de la liste des alertes.
const props = defineProps<{ page: AlertsPage }>();
const emit = defineEmits<{ edit: []; open: [site: string] }>();

const summary = computed(() => searchSummary(props.page.searches));
const lineOf = (slug: string): string[] => (START_SITES[slug] ? [START_SITES[slug].line] : []);
// Les sites où une recherche active a une adresse, dans l'ordre de la planche.
const sites = computed(() =>
  props.page.sites
    .filter((site) => props.page.searches.some((s) => s.active && s.cells.find((c) => c.site === site.slug)?.url))
    .sort((a, b) => (START_SITES[a.slug]?.order ?? 9) - (START_SITES[b.slug]?.order ?? 9)),
);
</script>

<template>
  <div
    class="blocks-page alerts-families desk"
    data-test="alerts-start"
  >
    <section
      class="alerts-search-card"
      aria-labelledby="alerts-search-title"
      data-test="alerts-search-card"
    >
      <h2
        id="alerts-search-title"
        class="alerts-family-title"
      >
        Ta recherche
      </h2>
      <div class="alerts-search-row">
        <span class="block-row-text">
          <b class="block-row-title">
            <span
              :aria-hidden="summary.text !== summary.full ? 'true' : undefined"
              data-test="alerts-search-summary"
            >{{ summary.text }}</span><span
              v-if="summary.text !== summary.full"
              class="visually-hidden"
            >{{ summary.full }}</span>
          </b>
          <span class="block-row-line">Reprise de tes critères.</span>
        </span>
        <button
          type="button"
          class="alerts-search-edit"
          aria-haspopup="dialog"
          data-test="alerts-search-edit"
          @click="emit('edit')"
        >
          Modifier<span
            class="list-chevron"
            aria-hidden="true"
          ><AppIcon name="chevron" /></span>
        </button>
      </div>
    </section>
    <section
      class="alerts-family"
      aria-labelledby="alerts-start-sites"
    >
      <h2
        id="alerts-start-sites"
        class="alerts-family-title"
      >
        À créer · {{ sites.length }} {{ sites.length > 1 ? "sites" : "site" }}
      </h2>
      <p class="alerts-family-help">
        Environ 2 minutes par site. Tu peux en faire un seul maintenant et les autres plus tard.
      </p>
      <BlockRow
        v-for="site in sites"
        :key="site.slug"
        :title="site.name"
        :lines="lineOf(site.slug)"
        :aside="{ text: 'À créer', tone: 'muted' }"
        aria-haspopup="dialog"
        :data-test="`alerts-start-${site.slug}`"
        @click="emit('open', site.slug)"
      />
    </section>
  </div>
</template>

<style>
/* La carte « Ta recherche » (AlertesOrdinateurVide) : bordée comme les lignes, 18,5 px de marge, 24 px dessous ;
   « Modifier » et le cercle bleu de 36 px à droite, comme l'action des lignes (LISEZMOI du 17.11, §6). */
.alerts-search-card { padding: var(--alerts-pad-x); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.alerts-families.desk .alerts-search-card .alerts-family-title { margin: 0; }
.alerts-search-row { display: flex; align-items: center; gap: var(--space-4); margin-top: var(--space-2); }
.alerts-search-edit { flex: none; display: flex; align-items: center; gap: var(--space-3); min-height: var(--target-min); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); cursor: pointer; }
</style>
