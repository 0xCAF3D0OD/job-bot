<script setup lang="ts">
import { computed, nextTick, ref } from "vue";

import { api, type AlertsPage } from "../api/client";
import AlertSiteSteps from "./AlertSiteSteps.vue";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import HoverNote from "./HoverNote.vue";
import MailboxAddress from "./MailboxAddress.vue";
import SidePanel from "./SidePanel.vue";

// Assistant des alertes (docs/21 §4) : un écran à la fois, tant qu'aucune alerte n'est en place.
// `focus` (1.6.70) : « Créer » ou « Vérifier l'alerte » sur une ligne de la page Alertes ouvre le pas à
// pas directement sur ce site, pour cette recherche ; à la fin, retour à la page.
// `desk` (planche AlertesOrdinateurSite, paquet du 13 novembre) : sur ordinateur, l'étape 2 passe dans le panneau de
// droite « Alerte <site> » (440 px, DECISIONS du 13.11) : « Site N sur M », 5 traits, le rappel de la recherche,
// 3 étapes numérotées, pied « Plus tard » et « J'ai créé l'alerte ». Avec `focus` (une carte « À créer »), seul le
// panneau s'affiche, au-dessus de la liste ; il passe ensuite aux autres sites encore à créer pour cette recherche.
const props = defineProps<{ page: AlertsPage; focus?: { site: string; terms: string } | null; desk?: boolean }>();
const emit = defineEmits<{ updated: [page: AlertsPage]; done: [] }>();

const step = ref<1 | 2 | 3>(props.focus ? 2 : 1);
// Pas d'illustration : l'assistant est une tâche (décision de Kevin du 27.10).
const siteIndex = ref(0);
const form = ref({ terms: "", location: "" });
const busy = ref(false);

const searches = computed(() =>
  props.page.searches.filter(
    (s) => s.active && (!props.focus || s.terms.trim().toLowerCase() === props.focus.terms.trim().toLowerCase()),
  ),
);
// Les exemples des champs suivent ta recherche (le métier choisi à l'accueil), pas un métier
// au hasard (docs/104 §5).
const termsExample = computed(() => props.page.searches[0]?.terms ?? "ton métier");
const placeExample = computed(() => props.page.searches.find((s) => s.location)?.location ?? "Lausanne");
// Sites avec une recherche à ouvrir (les sites ajoutés sans adresse sont laissés de côté). Dans le panneau ouvert
// depuis une carte, seulement les sites encore à créer (et celui de la carte).
const sites = computed(() =>
  props.page.sites.filter(
    (site) =>
      searches.value.some((s) => s.cells.find((c) => c.site === site.slug)?.url) &&
      (!props.desk ||
        !props.focus ||
        site.slug === props.focus.site ||
        searches.value.some((s) => s.cells.find((c) => c.site === site.slug)?.status === "todo")),
  ),
);
const site = computed(() => sites.value[siteIndex.value] ?? null);
if (props.focus) siteIndex.value = Math.max(0, sites.value.findIndex((s) => s.slug === props.focus!.site));

// Même recherche en télétravail (docs/26 §5) : une fois par mots, le lieu ne compte pas.
const remoteLinks = computed(() => {
  const seen = new Map<string, string>();
  for (const search of searches.value) {
    const url = search.cells.find((c) => c.site === site.value?.slug)?.remote_url;
    if (url && !seen.has(search.terms)) seen.set(search.terms, url);
  }
  return [...seen.entries()].map(([terms, url]) => ({ terms, url }));
});

function cellUrl(searchId: number): string | null {
  const search = searches.value.find((s) => s.id === searchId);
  return search?.cells.find((c) => c.site === site.value?.slug)?.url ?? null;
}

async function add(): Promise<boolean> {
  if (!form.value.terms.trim()) return false;
  const { data } = await api.POST("/api/alert-searches", {
    body: { terms: form.value.terms.trim(), location: form.value.location.trim() || null },
  });
  if (!data) return false;
  emit("updated", data);
  form.value = { terms: "", location: "" };
  return true;
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

// Bouton toujours actif (docs/29 §3) : sans recherche, il explique.
const searchHint = ref("");
// « Continuer » ajoute aussi la recherche tapée et pas encore ajoutée avec le « + » (2026-11-05, Kevin) :
// le gros bouton bleu juste en dessous est celui qu'on presse.
async function continueToSites(): Promise<void> {
  if (form.value.terms.trim()) {
    if (!(await add())) return;
    await nextTick();
  }
  if (!searches.value.length) {
    searchHint.value = "Ajoute au moins une recherche pour continuer.";
    return;
  }
  searchHint.value = "";
  step.value = 2;
}

function nextSite(): void {
  copiedOnOpen.value = false;
  if (props.desk && props.focus && siteIndex.value + 1 < sites.value.length) siteIndex.value += 1;
  else if (props.focus) emit("done");
  else if (siteIndex.value + 1 < sites.value.length) siteIndex.value += 1;
  else {
    step.value = 3;
    if (props.desk) void nextTick(() => document.querySelector<HTMLElement>("[data-test=wizard-finish]")?.focus());
  }
}

// Fermer le panneau (croix, Échap, clic à côté) : retour à la liste, ou à l'étape 1 de l'assistant.
function closePanel(): void {
  copiedOnOpen.value = false;
  if (props.focus) emit("done");
  else step.value = 1;
}
const panelSearch = computed(() =>
  searches.value
    .filter((s) => cellUrl(s.id))
    .map((s) => `${s.terms} · ${s.location || "Toute la Suisse"}`)
    .join(", "),
);
// Sur ordinateur, l'étape 1 reste affichée derrière le panneau de l'étape 2.
const shownStep = computed(() => (props.desk && step.value === 2 ? 1 : step.value));
const panelLinks = computed(() => searches.value.filter((s) => cellUrl(s.id)));
// Les liens du panneau pour AlertSiteSteps : un par recherche, puis ceux du télétravail.
const panelSiteLinks = computed(() => {
  const name = site.value?.name ?? "";
  const many = panelLinks.value.length > 1;
  return [
    ...panelLinks.value.map((search) => ({ key: `search-${search.id}`, url: cellUrl(search.id)!, label: `Ouvrir ${name}${many ? ` : ${search.terms}` : ""}` })),
    ...remoteLinks.value.map((link) => ({ key: `remote-${link.terms}`, url: link.url, label: `Ouvrir ${name} en télétravail${many ? ` : ${link.terms}` : ""}` })),
  ];
});

// Ouvrir un site copie l'adresse d'avance (docs/121 §B.2) : il ne reste qu'à la coller.
const copiedOnOpen = ref(false);
function copyOnOpen(): void {
  const address = props.page.mailbox;
  if (!address) return;
  void navigator.clipboard
    ?.writeText(address)
    .then(() => (copiedOnOpen.value = true))
    .catch(() => undefined);
}
</script>

<template>
  <section
    v-if="!(desk && focus)"
    class="form-card wizard"
    data-test="alerts-wizard"
  >
    <ol
      class="wizard-progress"
      aria-hidden="true"
    >
      <li
        v-for="n in 3"
        :key="n"
        :class="{ done: n < shownStep, current: n === shownStep }"
      />
    </ol>
    <p class="wizard-step">
      Étape {{ shownStep }} sur 3<span
        v-if="shownStep === 2 && site"
        data-test="wizard-site-count"
      > · site {{ siteIndex + 1 }} sur {{ sites.length }}</span>
    </p>

    <template v-if="shownStep === 1">
      <h2>Offres à recevoir</h2>
      <ul class="keyword-chips">
        <li
          v-for="search in searches"
          :key="search.id"
          class="chip"
          data-test="wizard-search"
        >
          {{ search.terms }} · {{ search.location || "toute la Suisse" }}
          <IconButton
            icon="close"
            :label="`Retirer ${search.terms}`"
            data-test="wizard-remove"
            @click="remove(search.id)"
          />
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
          :placeholder="`Mots (${termsExample})`"
          aria-label="Mots"
          data-test="wizard-terms"
        >
        <input
          v-model="form.location"
          type="text"
          maxlength="80"
          :placeholder="`Lieu (${placeExample})`"
          aria-label="Lieu"
        >
        <IconButton
          icon="plus"
          label="Ajouter la recherche"
          type="submit"
          data-test="wizard-add-submit"
        />
      </form>
      <div class="form-actions">
        <button
          type="button"
          class="primary"
          data-test="wizard-next"
          @click="continueToSites"
        >
          Continuer
        </button>
        <span
          v-if="searchHint"
          class="field-error"
          role="status"
        >{{ searchHint }}</span>
      </div>
    </template>

    <template v-else-if="shownStep === 2 && site">
      <h2>Crée l’alerte sur {{ site.name }}</h2>
      <!-- Une ligne (docs/121 §B.2) : l'adresse est copiée en ouvrant le site, il reste à la
             coller dans « Créer une alerte » ; le détail au survol. -->
      <p class="hint">
        <template v-if="page.mailbox">
          <HoverNote text="Sur le site, « Créer une alerte » ou « Activer l’alerte », puis colle l’adresse.">
            {{ copiedOnOpen ? "Adresse copiée :" : "En ouvrant le site, l’adresse est copiée :" }}
          </HoverNote>{{ " " }}<MailboxAddress
            :address="page.mailbox"
            :personal="page.personal_address"
            data-test="wizard-address"
          />
        </template>
        <template v-else>
          Ouvre la recherche, clique sur « Créer une alerte » et donne ton adresse e-mail.
        </template>
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
            class="button-link"
            data-test="wizard-open"
            @click="copyOnOpen"
          ><span class="with-icon">Ouvrir {{ site.name }} : {{ search.terms }}{{ search.location ? ` · ${search.location}` : "" }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
        </template>
        <a
          v-for="link in remoteLinks"
          :key="link.terms"
          :href="link.url"
          target="_blank"
          rel="noopener noreferrer"
          class="button-link"
          data-test="wizard-open-remote"
          @click="copyOnOpen"
        ><span class="with-icon">Ouvrir {{ site.name }} en télétravail : {{ link.terms }}<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></span></a>
      </div>
      <!-- Deux boutons égaux, côte à côte (docs/104 §4). -->
      <div class="form-actions wizard-site-actions">
        <button
          type="button"
          class="primary"
          :disabled="busy"
          data-test="wizard-site-done"
          @click="siteDone"
        >
          J’ai créé l’alerte
        </button>
        <button
          type="button"
          class="secondary"
          data-test="wizard-skip"
          @click="nextSite"
        >
          Plus tard
        </button>
      </div>
    </template>

    <template v-else>
      <h2>C’est prêt</h2>
      <p>
        Tes alertes arriveront<template v-if="page.mailbox">
          à <MailboxAddress
            :address="page.mailbox"
            :personal="page.personal_address"
          />
        </template><template v-else>
          dans ta boîte
        </template>, souvent dès le lendemain, avec le lien de confirmation si besoin.
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
  <SidePanel
    v-if="desk && step === 2 && site"
    open
    :title="`Alerte ${site.name}`"
    :eyebrow="`Site ${siteIndex + 1} sur ${sites.length}`"
    panel-class="alert-site-panel"
    @close="closePanel"
  >
    <template #top>
      <ol
        class="alert-site-progress"
        aria-hidden="true"
      >
        <li
          v-for="(s, n) in sites"
          :key="s.slug"
          :class="{ done: n <= siteIndex }"
        />
      </ol>
    </template>
    <AlertSiteSteps
      :key="site.slug"
      :site-name="site.name"
      :search-label="panelSearch"
      :links="panelSiteLinks"
      :mailbox="page.mailbox"
    />
    <template #footer>
      <button
        type="button"
        class="alert-site-later"
        data-test="wizard-skip"
        @click="nextSite"
      >
        Plus tard
      </button>
      <button
        type="button"
        class="action-1 alert-site-done"
        :disabled="busy"
        data-test="wizard-site-done"
        @click="siteDone"
      >
        J’ai créé l’alerte
      </button>
    </template>
  </SidePanel>
</template>

<style>
/* Panneau « Alerte <site> » (planche AlertesOrdinateurSite) : valeurs du HTML de la planche, couleurs en jetons. */
.alert-site-progress { flex: none; display: flex; gap: var(--space-1); margin: 0; padding: 0 var(--space-6) var(--space-4); list-style: none; }
.alert-site-progress li { flex: 1; height: 4px; border-radius: var(--radius-pill); background: var(--line-strong); }
.alert-site-progress li.done { background: var(--primary-graphic); }
/* Interligne de 22 px et décalage du titre d'étape (5 px, centré sur le rond de 32 px) : valeurs de la planche. */
.alert-site-panel .side-panel-body { display: block; padding-top: var(--space-1); }
/* La croix de la planche : 24 px, trait 2,2, couleur du texte. */
.alert-site-panel .side-panel-close { color: var(--text); }
.alert-site-panel .side-panel-close .icon { width: 24px; height: 24px; stroke-width: 2.2; }
.alert-site-later { flex: none; min-height: var(--target-min); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); }
.alert-site-done { flex: 1; justify-content: center; text-align: center; height: var(--btn-secondary); border-radius: var(--radius-pill); font-size: var(--font-body); }
</style>
