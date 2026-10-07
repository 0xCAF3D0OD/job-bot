<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api, type Training } from "../api/client";
import PageHero from "../components/PageHero.vue";
import { highlight, languageLabel } from "../newsLabels";
import { FORMATS, KINDS, LEVELS, ORP_LINKS, PRICES, STATUSES } from "../trainingLabels";

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

const inputValue = (event: Event): string => (event.target as HTMLInputElement).value;

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

      <aside
        class="orp-note"
        data-test="orp-note"
      >
        <strong>Formation et chômage :</strong> l'assurance chômage peut financer certaines formations
        (« mesures relatives au marché du travail »), <strong>sur demande à ton conseiller ORP et avec son accord
          préalable</strong>. La plateforme ne dit pas si une formation sera acceptée : c'est la décision de l'ORP.
        <span class="orp-links">
          <a
            v-for="link in ORP_LINKS"
            :key="link.url"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
          >{{ link.label }}</a>
        </span>
      </aside>

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
            :title="hasDomain ? keywords.join(' · ') : 'Définis ton domaine dans Réglages → Actualités'"
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
        <span
          v-if="canSuggest && tab === 'catalog'"
          class="news-status"
        >
          <button
            type="button"
            class="secondary small"
            :disabled="suggesting || !hasDomain"
            :title="hasDomain ? 'Claude Haiku cherche sur Internet, environ 0,02 à 0,05 $' : 'Définis d\'abord ton domaine'"
            data-test="suggest"
            @click="suggest"
          >
            {{ suggesting ? "Recherche en cours…" : "Chercher d'autres formations" }}
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
        v-else
        class="training-grid"
      >
        <li
          v-for="training in shown"
          :key="training.id"
          class="training-card"
          data-test="training"
        >
          <div class="training-head">
            <span class="news-meta">{{ KINDS[training.kind] }} · {{ training.provider }}</span>
            <span
              v-if="!training.verified"
              class="badge warn"
              data-test="unverified"
            >à vérifier</span>
          </div>
          <a
            class="training-title"
            :href="training.url"
            target="_blank"
            rel="noopener noreferrer"
          ><template
            v-for="(part, index) in highlight(training.title, training.matched)"
            :key="index"
          ><mark v-if="part.hit">{{ part.text }}</mark><template v-else>{{ part.text }}</template></template></a>
          <p class="training-facts">
            {{ FORMATS[training.format] }} · {{ languageLabel(training.language) }} · {{ PRICES[training.price] }}
            <template v-if="training.level">
              · {{ LEVELS[training.level] }}
            </template>
            <template v-if="training.duration">
              · {{ training.duration }}
            </template>
          </p>
          <p
            v-if="training.description"
            class="training-text"
          >
            {{ training.description }}
          </p>
          <p
            v-if="training.prep"
            class="training-text"
          >
            <strong>Préparation conseillée :</strong> {{ training.prep }}
          </p>
          <p
            v-if="training.price === 'paid'"
            class="hint"
          >
            Financement possible seulement avec l'accord préalable de ton conseiller ORP.
          </p>
          <div
            v-if="!training.verified"
            class="training-actions"
          >
            <button
              type="button"
              class="secondary small"
              data-test="keep"
              @click="review(training, true)"
            >
              Garder
            </button>
            <button
              type="button"
              class="link danger"
              data-test="dismiss"
              @click="review(training, false)"
            >
              Écarter
            </button>
          </div>
          <div class="training-actions">
            <div
              class="segmented"
              role="radiogroup"
              aria-label="Suivi"
            >
              <button
                v-for="(label, key) in STATUSES"
                :key="key"
                type="button"
                role="radio"
                :aria-checked="training.mark?.status === key"
                :data-test="`mark-${key}`"
                @click="training.mark?.status === key ? mark(training, null) : mark(training, key as Status)"
              >
                {{ label }}
              </button>
            </div>
          </div>
          <label
            v-if="training.mark?.status === 'in_progress'"
            class="training-field"
          >Progression
            <input
              type="text"
              maxlength="80"
              placeholder="module 4/12"
              :value="training.mark.progress ?? ''"
              data-test="progress"
              @change="mark(training, 'in_progress', { progress: inputValue($event) })"
            >
          </label>
          <div
            v-if="training.mark?.status === 'done'"
            class="training-field"
          >
            <label>Terminée le
              <input
                type="date"
                :value="training.mark.done_at ?? ''"
                @change="mark(training, 'done', { done_at: inputValue($event) || null })"
              >
            </label>
            <label class="check">
              <input
                type="checkbox"
                :checked="training.mark.certified ?? false"
                data-test="certified"
                @change="mark(training, 'done', { certified: !(training.mark.certified ?? false) })"
              > certificat obtenu
            </label>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>
