<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api, type Training } from "../api/client";
import DisclosureRow from "../components/DisclosureRow.vue";
import HelpTip from "../components/HelpTip.vue";
import PageHero from "../components/PageHero.vue";
import PushTransition from "../components/PushTransition.vue";
import SidePanel from "../components/SidePanel.vue";
import TrainingCardBody from "../components/TrainingCardBody.vue";
import { usePhone } from "../composables/usePhone";
import { highlight, languageLabel } from "../newsLabels";
import { KINDS, ORP_LINKS, PRICES, STATUSES } from "../trainingLabels";

// Formations (docs/16 §5) : catalogue vérifié, suggestions de l'IA sur demande, suivi.
type Status = "interested" | "in_progress" | "done";

const route = useRoute();
const tab = computed<"catalog" | "mine">(() => (route.query.onglet === "miennes" ? "mine" : "catalog"));
const items = ref<Training[]>([]);
const keywords = ref<string[]>([]);
const languages = ref<string[]>([]);
const canSuggest = ref(false);
const loaded = ref(false);
const domainOnly = ref(true);
const kind = ref("");
const price = ref("");
const language = ref("");
const suggesting = ref(false);
const message = ref("");

const hasDomain = computed(() => keywords.value.length > 0);
const shown = computed(() =>
  items.value.filter(
    (t) =>
      (tab.value === "mine" ? t.mark !== null : true) &&
      (!kind.value || t.kind === kind.value) &&
      (!price.value || t.price === price.value) &&
      (!language.value || t.language === language.value),
  ),
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

function setDomain(value: boolean): void {
  domainOnly.value = value;
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
    message.value = "Définis d'abord ton domaine dans Réglages › Actualités.";
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
      ? `${data.added} formation(s) proposée(s), marquées « à vérifier » : garde-les ou écarte-les.`
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
const opened = computed(() => items.value.find((t) => t.id === openId.value) ?? null);
const filtersOpen = ref(false);
const activeFilters = computed(() => [kind.value, price.value, language.value].filter(Boolean).length);

onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Formations"
    title="Se former dans son domaine"
    subtitle="Certifications et cours en ligne pour ton domaine."
  />
  <section class="band">
    <div class="container">
      <nav
        class="prep-tabs"
        aria-label="Formations"
      >
        <RouterLink
          :to="{ query: {} }"
          :class="{ active: tab === 'catalog' }"
          data-test="tab-catalog"
        >
          Catalogue
        </RouterLink>
        <RouterLink
          :to="{ query: { onglet: 'miennes' } }"
          :class="{ active: tab === 'mine' }"
          data-test="tab-mine"
        >
          Mes formations
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
        <strong>Formation et chômage :</strong> financement possible <strong>sur demande à ton conseiller ORP et avec
          son accord préalable</strong>.
        <HelpTip
          label="Aide : financement"
          text="L'assurance chômage peut financer certaines formations (« mesures relatives au marché du travail »). La plateforme ne dit pas si une formation sera acceptée : c'est la décision de l'ORP."
        />
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
            :disabled="!hasDomain"
            data-test="filter-domain"
            @click="setDomain(true)"
          >
            Mon domaine
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
        <HelpTip
          v-if="hasDomain"
          :text="`Mon domaine : ${keywords.join(', ')}. À modifier dans Réglages › Actualités.`"
          label="Mots de Mon domaine"
        />
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
            {{ suggesting ? "Recherche en cours…" : "Chercher d'autres formations" }}
            <span
              v-if="!suggesting"
              class="cost"
            >· 0,02 à 0,05 $</span>
          </button>
          <HelpTip
            label="Aide : suggestions de l'IA"
            text="L'IA cherche d'autres formations sur Internet. Elles arrivent marquées « à vérifier » : garde-les ou écarte-les."
          />
        </span>
      </div>
      <p
        v-if="message"
        class="hint"
        role="status"
      >
        {{ message }}
      </p>
      <p
        v-if="loaded && !hasDomain"
        class="hint"
      >
        Pour filtrer selon ton domaine (DevOps, Kubernetes…), indique tes mots-clés dans
        <RouterLink to="/reglages#actualites">
          Réglages → Actualités
        </RouterLink>.
      </p>

      <p
        v-if="loaded && !shown.length"
        class="muted empty"
      >
        {{ tab === "mine" ? "Aucune formation suivie : marque une formation « Intéressé » dans le catalogue." : "Aucune formation avec ces filtres." }}
      </p>
      <ul
        v-else-if="phone"
        class="news-rows training-rows"
      >
        <li
          v-for="training in shown"
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
          v-for="training in shown"
          :key="training.id"
          class="training-card"
          data-test="training"
        >
          <TrainingCardBody
            :training="training"
            @mark="(status, extra) => mark(training, status, extra)"
            @review="(keep) => review(training, keep)"
            @linked="(linked) => replace({ ...training, mark: linked })"
          />
        </li>
      </ul>
    </div>
  </section>
  <SidePanel
    v-if="phone && opened"
    open
    :title="opened.title"
    @close="openId = null"
  >
    <div class="training-card training-sheet">
      <TrainingCardBody
        :training="opened"
        @mark="(status, extra) => mark(opened!, status, extra)"
        @review="(keep) => { review(opened!, keep); if (!keep) openId = null; }"
        @linked="(linked) => replace({ ...opened!, mark: linked })"
      />
    </div>
  </SidePanel>
</template>
