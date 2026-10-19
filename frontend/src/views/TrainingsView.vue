<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type Training } from "../api/client";
import DisclosureRow from "../components/DisclosureRow.vue";
import DomainField from "../components/DomainField.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import PushTransition from "../components/PushTransition.vue";
import SidePanel from "../components/SidePanel.vue";
import TrainingCardBody from "../components/TrainingCardBody.vue";
import { usePhone } from "../composables/usePhone";
import { usePageReady } from "../composables/usePageTransition";
import { highlight, languageLabel } from "../newsLabels";
import { KINDS, ORP_LINKS, PRICES, STATUSES } from "../trainingLabels";
import { plural } from "../format";

import HoverNote from "../components/HoverNote.vue";
// Formations (docs/16 §5) : catalogue vérifié, suggestions de l'IA sur demande, suivi.
type Status = "interested" | "in_progress" | "done";

const route = useRoute();
const tab = computed<"catalog" | "mine">(() => (route.query.onglet === "miennes" ? "mine" : "catalog"));
const items = ref<Training[]>([]);
const keywords = ref<string[]>([]);
const languages = ref<string[]>([]);
const canSuggest = ref(false);
const loaded = ref(false);
usePageReady("trainings", () => loaded.value);
const domainOnly = ref(true);
const kind = ref("");
const price = ref("");
const language = ref("");
const suggesting = ref(false);
const message = ref("");

const hasDomain = computed(() => keywords.value.length > 0);
// « Mes formations » (docs/44 §3) : en cours d'abord, puis intéressé, puis terminées.
const MINE_ORDER: Record<string, number> = { in_progress: 0, interested: 1, done: 2 };
const shown = computed(() => {
  const found = items.value.filter(
    (t) =>
      (tab.value === "mine" ? t.mark !== null : true) &&
      (!kind.value || t.kind === kind.value) &&
      (!price.value || t.price === price.value) &&
      (!language.value || t.language === language.value),
  );
  if (tab.value !== "mine") return found;
  return [...found].sort((a, b) => (MINE_ORDER[a.mark!.status] ?? 9) - (MINE_ORDER[b.mark!.status] ?? 9));
});
// Deux groupes titrés, comme les sections des Actualités (docs/43 n° 21).
const sections = computed(() =>
  [
    { key: "certifications", label: "Certifications", items: shown.value.filter((t) => t.kind === "certification") },
    { key: "courses", label: "Cours et parcours", items: shown.value.filter((t) => t.kind !== "certification") },
  ].filter((section) => section.items.length),
);
const mineCount = computed(() => items.value.filter((t) => t.mark).length);

async function load(): Promise<void> {
  // Au premier chargement, les mots-clés ne sont pas encore connus : « Mon domaine » par défaut.
  const { data } = await api.GET("/api/trainings", {
    params: { query: { domain_only: domainOnly.value && (!loaded.value || hasDomain.value) } },
  });
  if (!data) return;
  items.value = data.items;
  keywords.value = data.domain_keywords;
  languages.value = data.languages;
  canSuggest.value = data.can_suggest;
  const first = !loaded.value;
  loaded.value = true;
  if (first && !data.domain_keywords.length && domainOnly.value) {
    // Sans domaine, le filtre ne garderait rien : tout le catalogue.
    domainOnly.value = false;
    await load();
  }
}

// Sans domaine, « Mon domaine » ouvre le champ sur place (docs/43 n° 4).
const domainFieldOpen = ref(false);

function setDomain(value: boolean): void {
  if (value && !hasDomain.value) {
    domainFieldOpen.value = !domainFieldOpen.value;
    return;
  }
  domainOnly.value = value;
  void load();
}

function onDomainSaved(): void {
  domainFieldOpen.value = false;
  domainOnly.value = true;
  void load();
}

function replace(training: Training): void {
  items.value = items.value.map((t) => (t.id === training.id ? training : t));
}

async function mark(
  training: Training,
  status: Status | null,
  extra: { progress?: string | null; done_at?: string | null; certified?: boolean | null } = {},
): Promise<void> {
  if (status === null) {
    await api.DELETE("/api/trainings/{training_id}/mark", { params: { path: { training_id: training.id } } });
    replace({ ...training, mark: null });
    return;
  }
  const { data } = await api.PUT("/api/trainings/{training_id}/mark", {
    params: { path: { training_id: training.id } },
    body: {
      status,
      progress: extra.progress ?? training.mark?.progress ?? null,
      done_at: extra.done_at ?? training.mark?.done_at ?? (status === "done" ? new Date().toISOString().slice(0, 10) : null),
      certified: extra.certified ?? training.mark?.certified ?? null,
    },
  });
  if (data) replace({ ...training, mark: data });
}

async function review(training: Training, keep: boolean): Promise<void> {
  await api.POST("/api/trainings/{training_id}/review", {
    params: { path: { training_id: training.id } },
    body: { keep },
  });
  if (keep) replace({ ...training, verified: true });
  else items.value = items.value.filter((t) => t.id !== training.id);
}

async function suggest(): Promise<void> {
  // Bouton toujours actif (docs/29 §3) : sans domaine, il dit quoi faire.
  if (!hasDomain.value) {
    message.value = "Définis d'abord ton domaine : bouton « Domaine ».";
    return;
  }
  suggesting.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/trainings/suggest");
    if (!data) {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Recherche impossible : ${detail}.` : "Recherche impossible.";
      return;
    }
    message.value = data.added
      ? `${plural(data.added, "formation proposée, marquée", "formations proposées, marquées")} « à vérifier » : garde-les ou écarte-les.`
      : "Rien de nouveau trouvé cette fois.";
    await load();
  } finally {
    suggesting.value = false;
  }
}

// Téléphone (docs/34 §2) : une liste fine, la fiche en plein écran, les filtres derrière
// « Filtrer », l'encadré ORP replié. Sur ordinateur, rien ne change.
const { phone } = usePhone();
const openId = ref<number | null>(null);
// Une formation ouverte depuis l'aperçu de la capsule (docs/92) : `?formation=ID`.
watch(
  () => route.query.formation,
  (id) => {
    if (typeof id === "string" && Number(id)) openId.value = Number(id);
  },
  { immediate: true },
);
const opened = computed(() => items.value.find((t) => t.id === openId.value) ?? null);
const filtersOpen = ref(false);
const activeFilters = computed(() => [kind.value, price.value, language.value].filter(Boolean).length);

onMounted(() => void load());
</script>

<template>
  <section class="band">
    <div class="container">
      <!-- Catalogue ou Suivies, dans l'onglet Formations de Progresser (docs/90). -->
      <nav
        class="sub-tabs"
        aria-label="Formations affichées"
      >
        <RouterLink
          :to="{ query: {} }"
          :class="{ active: tab === 'catalog' }"
          :aria-current="tab === 'catalog' ? 'true' : undefined"
          data-test="tab-catalog"
        >
          Catalogue
        </RouterLink>
        <RouterLink
          :to="{ query: { onglet: 'miennes' } }"
          :class="{ active: tab === 'mine' }"
          :aria-current="tab === 'mine' ? 'true' : undefined"
          data-test="tab-mine"
        >
          Suivies
          <span
            v-if="mineCount"
            class="tab-count"
          >{{ mineCount }}</span>
        </RouterLink>
      </nav>
      <component
        :is="phone ? DisclosureRow : 'aside'"
        :class="phone ? 'orp-note-row' : 'orp-note'"
        :title="phone ? 'Formation et chômage' : undefined"
        :value="phone ? 'accord de l\'ORP' : undefined"
        data-test="orp-note"
      >
        <strong><HoverNote text="L'assurance chômage peut financer certaines formations (« mesures relatives au marché du travail »). La plateforme ne dit pas si une formation sera acceptée : c'est la décision de l'ORP.">Formation et chômage</HoverNote> :</strong> financement possible <strong>sur demande à ton conseiller ORP et avec
          son accord préalable</strong>.
        <span class="orp-links">
          <a
            v-for="link in ORP_LINKS"
            :key="link.url"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
          >{{ link.label }}</a>
        </span>
      </component>

      <div
        v-if="loaded"
        class="news-filters"
      >
        <div
          class="segmented"
          role="radiogroup"
          aria-label="Formations affichées"
        >
          <button
            type="button"
            role="radio"
            :aria-checked="domainOnly && hasDomain"
            :aria-expanded="hasDomain ? undefined : domainFieldOpen"
            data-test="filter-domain"
            @click="setDomain(true)"
          >
            Domaine
          </button>
          <button
            type="button"
            role="radio"
            :aria-checked="!domainOnly || !hasDomain"
            data-test="filter-all"
            @click="setDomain(false)"
          >
            Tout
          </button>
        </div>
        <button
          v-if="phone"
          type="button"
          class="secondary small training-filter-toggle"
          :aria-expanded="filtersOpen"
          data-test="training-filter-toggle"
          @click="filtersOpen = !filtersOpen"
        >
          Filtrer{{ activeFilters ? ` · ${activeFilters}` : "" }}
        </button>
        <PushTransition :enabled="phone">
          <div
            v-show="!phone || filtersOpen"
            :class="phone ? 'training-filter-sheet' : 'training-filter-group'"
          >
            <select
              v-model="kind"
              aria-label="Type"
              data-test="filter-kind"
            >
              <option value="">
                Tous les types
              </option>
              <option
                v-for="(label, key) in KINDS"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
            <select
              v-model="price"
              aria-label="Prix"
              data-test="filter-price"
            >
              <option value="">
                Gratuit ou payant
              </option>
              <option
                v-for="(label, key) in PRICES"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
            <select
              v-if="languages.length > 1"
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
          </div>
        </PushTransition>
        <span
          v-if="canSuggest && tab === 'catalog'"
          class="news-status"
        >
          <button
            type="button"
            class="secondary small"
            :disabled="suggesting"
            data-test="suggest"
            @click="suggest"
          >
            <HoverNote :text="suggesting ? '' : 'Environ 0,02 à 0,05 $.'">
              {{ suggesting ? "Recherche en cours…" : "Chercher d'autres formations" }}
            </HoverNote>
          </button>
        </span>
      </div>
      <p
        v-if="message"
        class="hint"
        role="status"
      >
        {{ message }}
      </p>
      <PushTransition>
        <DomainField
          v-if="domainFieldOpen && !hasDomain"
          @saved="onDomainSaved"
        />
      </PushTransition>
      <LoadingBlocks
        v-if="!loaded"
        :columns="phone ? 1 : 3"
        :heights="['16rem', '16rem', '16rem']"
      />

      <p
        v-if="loaded && !shown.length"
        class="muted empty"
      >
        {{ tab === "mine" ? "Aucune formation suivie : marque une formation « Intéressé » dans le catalogue." : "Aucune formation avec ces filtres." }}
      </p>
      <template v-else>
        <section
          v-for="section in sections"
          :key="section.key"
          class="training-section"
          :data-test="`training-section-${section.key}`"
        >
          <h2 class="news-group-title">
            {{ section.label }}
          </h2>
          <ul
            v-if="phone"
            class="news-rows training-rows"
          >
            <li
              v-for="training in section.items"
              :key="training.id"
              data-test="training"
            >
              <button
                type="button"
                class="news-row training-row"
                :aria-expanded="openId === training.id"
                data-test="training-row"
                @click="openId = training.id"
              >
                <span class="news-row-main">
                  <span class="news-title"><template
                    v-for="(part, index) in highlight(training.title, training.matched)"
                    :key="index"
                  ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></span>
                  <span class="training-row-facts">{{ KINDS[training.kind] }} · {{ training.provider }} · {{ PRICES[training.price] }}</span>
                </span>
                <span
                  v-if="training.mark"
                  class="badge"
                >{{ STATUSES[training.mark.status] }}</span>
                <span
                  v-else-if="!training.verified"
                  class="badge warn"
                >à vérifier</span>
              </button>
            </li>
          </ul>
          <ul
            v-else
            class="training-grid"
          >
            <li
              v-for="training in section.items"
              :key="training.id"
              class="training-card"
              data-test="training"
            >
              <TrainingCardBody
                :training="training"
                @manage="openId = training.id"
                @review="(keep) => review(training, keep)"
              />
            </li>
          </ul>
        </section>
      </template>
    </div>
  </section>
  <!-- Le suivi dans le panneau latéral, sur ordinateur comme sur téléphone (docs/44 §2). -->
  <SidePanel
    v-if="opened"
    open
    :title="opened.title"
    @close="openId = null"
  >
    <div class="training-card training-sheet">
      <TrainingCardBody
        :training="opened"
        variant="panel"
        @mark="(status, extra) => mark(opened!, status, extra)"
        @review="(keep) => { review(opened!, keep); if (!keep) openId = null; }"
        @linked="(linked) => replace({ ...opened!, mark: linked })"
      />
    </div>
  </SidePanel>
</template>
