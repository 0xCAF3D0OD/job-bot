<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type SiteOut } from "../api/client";
import AppIcon from "./AppIcon.vue";
import MoreInfo from "./MoreInfo.vue";
import { secureAddress, senders, useChecks } from "../validators";

// Sites dont les alertes sont suivies (docs/11 §2).
const sites = ref<SiteOut[]>([]);
// Sites d'offres en télétravail proposés en un clic (docs/26 §5).
type Suggestion = { name: string; senders: string[]; url: string; note: string };
const suggestions = ref<Suggestion[]>([]);
const loaded = ref(false);
const adding = ref(false);
const form = ref({ name: "", senders: "", url: "" });
const { errors, check, clearIfFixed, validate } = useChecks(
  { url: secureAddress, senders },
  (field) => form.value[field],
  "site",
);
const message = ref("");
const busy = ref(false);

const unrecognized = computed(() => sites.value.reduce((n, s) => n + s.unrecognized, 0));
const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

function detail(err: unknown, fallback: string): string {
  const value = (err as { detail?: unknown } | undefined)?.detail;
  if (typeof value === "string") return value.charAt(0).toUpperCase() + value.slice(1) + ".";
  if (Array.isArray(value)) {
    const first = value[0] as { msg?: string } | undefined;
    if (first?.msg) return first.msg.replace(/^Value error, /, "") + ".";
  }
  return fallback;
}

async function load(): Promise<void> {
  const { data } = await api.GET("/api/sites");
  sites.value = data ?? [];
  loaded.value = true;
  const proposed = await api.GET("/api/sites/suggestions");
  suggestions.value = proposed.data ?? [];
}

async function toggle(site: SiteOut): Promise<void> {
  const { data } = await api.PATCH("/api/sites/{site_id}", {
    params: { path: { site_id: site.id } },
    body: { active: !site.active },
  });
  if (data) sites.value = data;
}

async function remove(site: SiteOut): Promise<void> {
  if (!window.confirm(`Ne plus suivre ${site.name} ? Les offres déjà collectées restent.`)) return;
  const { data } = await api.DELETE("/api/sites/{site_id}", { params: { path: { site_id: site.id } } });
  if (data) sites.value = data;
}

async function add(): Promise<void> {
  message.value = "";
  if (!validate()) return;
  const senders = form.value.senders.split(/[\s,;]+/).filter(Boolean);
  const { data, error } = await api.POST("/api/sites", {
    body: { name: form.value.name.trim(), senders, url: form.value.url.trim() || null },
  });
  if (!data) {
    message.value = detail(error, "Ajout refusé : vérifie les champs.");
    return;
  }
  sites.value = data;
  adding.value = false;
  form.value = { name: "", senders: "", url: "" };
  message.value = "Site ajouté : ses prochaines alertes seront lues par l'IA.";
}

async function addSuggestion(suggestion: Suggestion): Promise<void> {
  message.value = "";
  const { data, error } = await api.POST("/api/sites", {
    body: { name: suggestion.name, senders: suggestion.senders, url: suggestion.url },
  });
  if (!data) {
    message.value = detail(error, "Ajout refusé.");
    return;
  }
  sites.value = data;
  suggestions.value = suggestions.value.filter((s) => s.name !== suggestion.name);
  message.value = `${suggestion.name} ajouté : crée ton alerte sur le site, ses e-mails seront lus par l'IA.`;
}

async function reread(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data } = await api.POST("/api/sites/reread");
    message.value = data
      ? `${data.updated} alerte(s) relue(s), ${data.new_offers} nouvelle(s) offre(s).`
      : "La relecture a échoué.";
    await load();
  } finally {
    busy.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div
    v-if="loaded"
    class="form-card sites-card"
    data-test="sites"
  >
    <fieldset>
      <legend>Sites suivis</legend>
      <p class="hint">
        Les sites dont la plateforme lit les e-mails d'alerte.
      </p>
      <MoreInfo>
        <p>
          jobup et Indeed ont un lecteur intégré ; les autres sont lus par l'IA (environ 0,01 $ par e-mail, tes
          coordonnées retirées).
        </p>
      </MoreInfo>
      <ul class="sites-list">
        <li
          v-for="site in sites"
          :key="site.id"
          :class="{ paused: !site.active }"
          data-test="site"
        >
          <span class="site-main">
            <strong>{{ site.name }}</strong>
            <span class="hint">
              {{ site.reader === "ai" ? "lu par l'IA" : "lecteur intégré" }} · {{ site.senders.join(", ") }}
            </span>
          </span>
          <span class="hint site-stats">
            {{ site.alerts }} alerte(s){{ site.last_alert_at ? ` · dernière le ${dateFormat.format(new Date(site.last_alert_at))}` : "" }}
          </span>
          <label class="check">
            <input
              type="checkbox"
              :checked="site.active"
              :data-test="`active-${site.slug}`"
              @change="toggle(site)"
            > suivi
          </label>
          <button
            v-if="!site.builtin"
            type="button"
            class="link danger"
            :data-test="`remove-${site.slug}`"
            @click="remove(site)"
          >
            Retirer
          </button>
        </li>
      </ul>

      <div
        v-if="suggestions.length"
        class="site-suggestions"
        data-test="site-suggestions"
      >
        <p class="hint">
          Offres en télétravail, avec les pays acceptés indiqués :
        </p>
        <ul>
          <li
            v-for="suggestion in suggestions"
            :key="suggestion.name"
          >
            <span>
              <a
                :href="suggestion.url"
                target="_blank"
                rel="noopener noreferrer"
              >{{ suggestion.name }}</a>
              <span class="muted"> · {{ suggestion.note }}</span>
            </span>
            <button
              type="button"
              class="link"
              :data-test="`suggest-${suggestion.name}`"
              @click="addSuggestion(suggestion)"
            >
              Ajouter
            </button>
          </li>
        </ul>
      </div>

      <form
        v-if="adding"
        class="form-grid"
        data-test="add-site-form"
        @submit.prevent="add"
      >
        <label>Nom
          <input
            v-model="form.name"
            type="text"
            placeholder="JobScout24"
            required
            data-test="site-name"
          >
        </label>
        <label>Adresse du site
          <input
            id="site-url"
            v-model="form.url"
            type="text"
            placeholder="https://www.jobscout24.ch"
            :aria-invalid="Boolean(errors.url)"
            :aria-describedby="errors.url ? 'site-url-error' : undefined"
            @blur="check('url')"
            @input="clearIfFixed('url')"
          >
          <span
            v-if="errors.url"
            id="site-url-error"
            class="field-error"
          >{{ errors.url }}</span>
        </label>
        <label class="wide">Adresse(s) d'expédition des alertes
          <input
            id="site-senders"
            v-model="form.senders"
            type="text"
            placeholder="alerts@jobscout24.ch ou jobscout24.ch"
            data-test="site-senders"
            :aria-invalid="Boolean(errors.senders)"
            :aria-describedby="errors.senders ? 'site-senders-error' : undefined"
            @blur="check('senders')"
            @input="clearIfFixed('senders')"
          >
          <span
            v-if="errors.senders"
            id="site-senders-error"
            class="field-error"
            data-test="error-senders"
          >{{ errors.senders }}</span>
        </label>
        <div class="form-actions wide">
          <button
            type="submit"
            class="secondary small"
            data-test="save-site"
          >
            Ajouter <AppIcon name="chevron" />
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
          data-test="add-site"
          @click="adding = true"
        >
          Ajouter un site
        </button>
        <button
          v-if="unrecognized"
          type="button"
          class="secondary small"
          :disabled="busy"
          data-test="reread"
          @click="reread"
        >
          {{ busy ? "Relecture…" : `Relire les alertes non reconnues (${unrecognized})` }}
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
