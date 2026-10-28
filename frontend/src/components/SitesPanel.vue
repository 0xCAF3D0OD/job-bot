<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type SiteOut } from "../api/client";
import AppIcon from "./AppIcon.vue";
import BusyButton from "./BusyButton.vue";
import IconButton from "./IconButton.vue";
import SidePanel from "./SidePanel.vue";
import { secureAddress, senders, useChecks } from "../validators";
import { onDay, plural } from "../format";

import { useAuth } from "../composables/useAuth";
import { offerUndo } from "../composables/useUndo";
import { usePlan } from "../composables/usePlan";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

const { plan } = usePlan();
// Mettre un site en pause vaut pour son compte ; ajouter ou retirer un site change la liste
// commune à tous les comptes : réservé à l'exploitant (docs/65).
const { me } = useAuth();
const owner = computed(() => Boolean(me.value?.is_owner));
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

async function setActive(site: SiteOut, active: boolean, keepalive = false): Promise<boolean> {
  const { data } = await api.PATCH("/api/sites/{site_id}", {
    params: { path: { site_id: site.id } },
    body: { active },
    keepalive,
  });
  if (data) sites.value = data;
  return Boolean(data);
}

// Suivre un site s'applique tout de suite ; ne plus le suivre aussi, avec « Annuler » pendant 6 s
// (1.6.66, §4, comme Garder et Écarter) : le serveur ne le reçoit qu'à la fin.
async function toggle(site: SiteOut): Promise<void> {
  if (!site.active) {
    await setActive(site, true);
    return;
  }
  const before = sites.value;
  sites.value = before.map((s) => (s.id === site.id ? { ...s, active: false } : s));
  await offerUndo({
    message: `${site.name} n'est plus suivi.`,
    commit: (keepalive) => setActive(site, false, keepalive),
    restore: () => {
      sites.value = before;
    },
  });
}

// Retiré tout de suite, « Annuler » pendant 6 s (docs/108 §1) ; les offres déjà collectées restent.
async function remove(site: SiteOut): Promise<void> {
  const before = sites.value;
  sites.value = before.filter((s) => s.id !== site.id);
  openId.value = null;
  await offerUndo({
    message: `${site.name} n'est plus suivi`,
    commit: async (keepalive) => {
      const { data } = await api.DELETE("/api/sites/{site_id}", { params: { path: { site_id: site.id } }, keepalive });
      if (!data) return false;
      sites.value = data;
    },
    restore: () => {
      sites.value = before;
    },
  });
}

// Lignes calmes (docs/48 §3) : le détail et « Retirer » dans le panneau.
const openId = ref<number | null>(null);
const opened = computed(() => sites.value.find((s) => s.id === openId.value) ?? null);
// « Lu directement · 83 alertes · dernière le 22 oct. » (planche « 5. Réglages »).
function line(site: SiteOut): string {
  return `${site.reader === "ai" ? "Lu par l'IA" : "Lu directement"} · ${stats(site)}`;
}
function stats(site: SiteOut): string {
  const last = site.last_alert_at ? ` · dernière ${onDay(site.last_alert_at)}` : "";
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
  if (busy.value) return;
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
  <!-- Les sites suivis (1.6.66, planche « 5. Réglages ») : une ligne d'en-tête, puis une ligne par site
       avec son interrupteur, dans la même carte (loi de proximité). -->
  <SettingCard
    v-if="loaded"
    class="sites-card"
    data-test="sites"
  >
    <SettingRow
      title="Sites suivis"
      description="La plateforme lit leurs e-mails d'alerte."
    />
    <SettingRow
      v-for="site in sites"
      :key="site.id"
      v-slot="c"
      :title="site.name"
      :description="line(site)"
      :class="{ paused: !site.active }"
      data-test="site"
    >
      <IconButton
        v-if="owner"
        icon="more"
        :label="`Détails de ${site.name}`"
        :data-test="`open-${site.slug}`"
        @click="openId = site.id"
      />
      <input
        type="checkbox"
        role="switch"
        :checked="site.active"
        :aria-labelledby="c.labelledby"
        :aria-describedby="c.describedby"
        :data-test="`active-${site.slug}`"
        @change="toggle(site)"
      >
    </SettingRow>
    <SettingRow
      v-for="suggestion in owner ? suggestions : []"
      :key="suggestion.name"
      :title="suggestion.name"
      :description="`Site de télétravail à ajouter · ${suggestion.note}`"
      data-test="site-suggestions"
    >
      <IconButton
        icon="plus"
        :label="`Ajouter ${suggestion.name}`"
        :data-test="`suggest-${suggestion.name}`"
        @click="addSuggestion(suggestion)"
      />
    </SettingRow>
    <SettingRow
      v-if="unrecognized"
      title="Alertes non reconnues"
      :description="`${plural(unrecognized, 'alerte', 'alertes')} à relire par l'IA.`"
    >
      <BusyButton
        class="secondary small"
        :busy="busy"
        busy-label="Relecture…"
        data-test="reread"
        @click="reread"
      >
        Relire
      </BusyButton>
    </SettingRow>
    <SettingRow
      v-if="owner && !adding"
      title="Un autre site"
      description="Ses e-mails d'alerte seront lus par l'IA."
    >
      <button
        type="button"
        class="secondary small"
        data-test="add-site"
        @click="adding = true"
      >
        <span class="with-icon"><AppIcon name="plus" />Ajouter un site</span>
      </button>
    </SettingRow>
    <form
      v-if="owner && adding"
      class="form-grid setting-row-form"
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
          <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
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
    <p
      v-if="message"
      class="muted setting-row-message"
      role="status"
    >
      {{ message }}
    </p>
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
            <dd>{{ opened.reader === "ai" ? plan?.unlimited ? "par l'IA (environ 0,01 $ par e-mail)" : "par l'IA" : "directement" }}</dd>
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
        <p
          v-if="!opened.builtin"
          class="calm-panel-foot"
        >
          <IconButton
            icon="trash"
            label="Retirer ce site"
            danger
            :data-test="`remove-${opened.slug}`"
            @click="remove(opened)"
          />
        </p>
      </div>
    </SidePanel>
  </SettingCard>
</template>
