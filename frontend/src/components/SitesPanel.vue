<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type SiteOut } from "../api/client";
import HelpTip from "./HelpTip.vue";
import SidePanel from "./SidePanel.vue";
import { secureAddress, senders, useChecks } from "../validators";
import { plural } from "../format";

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
  if (data) {
    sites.value = data;
    openId.value = null;
  }
}

// Lignes calmes (docs/48 §3) : le détail et « Retirer » dans le panneau.
const openId = ref<number | null>(null);
const opened = computed(() => sites.value.find((s) => s.id === openId.value) ?? null);
function stats(site: SiteOut): string {
  const last = site.last_alert_at ? ` · dernière le ${dateFormat.format(new Date(site.last_alert_at))}` : "";
  return `${plural(site.alerts, "alerte", "alertes", "aucune alerte")}${last}`;
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
      ? `${plural(data.updated, "alerte relue", "alertes relues")}, ${plural(data.new_offers, "nouvelle offre", "nouvelles offres", "aucune nouvelle offre")}.`
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
      <legend>
        Sites suivis
        <HelpTip
          text="La plateforme lit leurs e-mails d'alerte. jobup et Indeed ont un lecteur intégré ; les autres sont lus par l'IA (environ 0,01 $ par e-mail, tes coordonnées retirées)."
          label="Aide : sites suivis"
        />
      </legend>
      <ul class="calm-list">
        <li
          v-for="site in sites"
          :key="site.id"
          :class="{ paused: !site.active }"
          data-test="site"
        >
          <button
            type="button"
            class="calm-row"
            :data-test="`open-${site.slug}`"
            @click="openId = site.id"
          >
            <strong>{{ site.name }}</strong>
            <span class="hint">
              {{ site.reader === "ai" ? "lu par l'IA" : "lecteur intégré" }} · {{ stats(site) }}
            </span>
          </button>
          <label class="filter-switch calm-switch">
            <span class="visually-hidden">{{ site.name }} suivi</span>
            <input
              type="checkbox"
              role="switch"
              :checked="site.active"
              :data-test="`active-${site.slug}`"
              @change="toggle(site)"
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
          data-test="site-panel"
        >
          <dl class="summary-rows">
            <div>
              <dt>Lecture</dt>
              <dd>{{ opened.reader === "ai" ? "par l'IA (environ 0,01 $ par e-mail)" : "lecteur intégré" }}</dd>
            </div>
            <div>
              <dt>E-mails de</dt>
              <dd>{{ opened.senders.join(", ") }}</dd>
            </div>
            <div>
              <dt>Alertes reçues</dt>
              <dd>{{ stats(opened) }}</dd>
            </div>
            <div v-if="opened.unrecognized">
              <dt>Non reconnues</dt>
              <dd>{{ opened.unrecognized }}</dd>
            </div>
          </dl>
          <label class="filter-switch calm-panel-switch">
            <span>Suivi</span>
            <input
              type="checkbox"
              role="switch"
              :checked="opened.active"
              @change="toggle(opened)"
            >
          </label>
          <p
            v-if="!opened.builtin"
            class="calm-panel-foot"
          >
            <button
              type="button"
              class="link danger"
              :data-test="`remove-${opened.slug}`"
              @click="remove(opened)"
            >
              Retirer ce site
            </button>
          </p>
        </div>
      </SidePanel>

      <div
        v-if="suggestions.length"
        class="site-suggestions"
        data-test="site-suggestions"
      >
        <p class="hint">
          Sites de télétravail à ajouter :
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
        <label class="wide">Adresses d'expédition des alertes
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
            Ajouter
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
