<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";

import { api } from "../api/client";
import { dateInList, timeOfDay } from "../dates";
import { sourceLabel } from "../format";
import IconButton from "./IconButton.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import SiteCodes from "./SiteCodes.vue";

// Les messages des sites (docs/112, docs/113 ; planche « 6. Alertes », 1.6.70) : une section, une
// carte. En tête, le code de vérification : le code lui-même quand il est là, sinon « J'attends un
// code » (la boîte relevée toutes les 15 secondes pendant 5 minutes) ; puis les trois derniers
// messages (gardés 30 jours), le site en titre, l'objet et l'heure en phrase, la date à droite.
type SiteCode = { search_id: number; site: string; code: string; received_at: string };
type SiteMessage = { id: number; site: string; subject?: string | null; received_at: string };
const props = defineProps<{ codes: SiteCode[]; guestMailbox: boolean }>();
const emit = defineEmits<{ refresh: [] }>();

const waiting = ref(false);
// Les trois derniers messages, tous avec « Tout voir » (1.6.70, divulgation progressive).
const LATEST = 3;
const all = ref(false);
const shown = computed(() => (all.value ? items.value : items.value.slice(0, LATEST)));
function siteName(item: SiteMessage): string {
  return item.site === "unknown" ? "Un site" : (sourceLabel[item.site] ?? item.site);
}
const message = ref("");
let timer: ReturnType<typeof setInterval> | undefined;
let stopAt = 0;
const WAIT_MS = 5 * 60_000;

const items = ref<SiteMessage[]>([]);
const openId = ref<number | null>(null);
const texts = reactive<Record<number, string>>({});

function stop(): void {
  clearInterval(timer);
  timer = undefined;
  waiting.value = false;
}

async function expect(): Promise<void> {
  message.value = "";
  const { data } = await api.POST("/api/alert-searches/expect-code");
  if (!data?.queued) {
    message.value = "Déjà six relevés rapides cette heure-ci : le code arrivera au prochain relevé.";
    return;
  }
  waiting.value = true;
  stopAt = Date.now() + WAIT_MS;
  // La page se met à jour seule : un code arrivé s'affiche en haut.
  timer = setInterval(() => {
    if (Date.now() > stopAt) stop();
    else emit("refresh");
  }, 10_000);
}

// Un nouveau code est là : on arrête d'attendre.
watch(
  () => props.codes.length,
  (now, before) => {
    if (waiting.value && now > (before ?? 0)) stop();
  },
);

// Un message ouvert à la fois ; le texte se charge la première fois.
async function toggle(item: SiteMessage): Promise<void> {
  openId.value = openId.value === item.id ? null : item.id;
  if (openId.value === null || item.id in texts) return;
  const { data } = await api.GET("/api/alert-searches/messages/{search_id}", { params: { path: { search_id: item.id } } });
  texts[item.id] = data?.text || "Ce message n'a pas de texte.";
}

onMounted(async () => {
  const { data } = await api.GET("/api/alert-searches/messages");
  if (Array.isArray(data)) items.value = data;
});
onUnmounted(stop);
</script>

<template>
  <section
    id="site-messages"
    class="alerts-section"
    data-test="site-mail"
  >
    <div class="alerts-section-head">
      <h2 class="section-title">
        Messages des sites
      </h2>
      <button
        v-if="items.length > LATEST"
        type="button"
        class="link"
        :aria-expanded="all"
        data-test="site-mail-all"
        @click="all = !all"
      >
        {{ all ? "Les trois derniers" : "Tout voir" }}
      </button>
    </div>
    <SettingCard class="site-mail-card">
      <!-- Le code arrivé prend la place de « J'attends un code » (0.84.2). -->
      <SettingRow
        title="Code de vérification"
        :description="codes.length ? 'Recopie-le sur le site qui te le demande.' : waiting ? 'J\'attends le code, pendant 5 minutes.' : guestMailbox ? 'Il s\'affiche ici dès qu\'il arrive dans la boîte de jobA1.' : 'Il s\'affiche ici dès qu\'il arrive.'"
        :stack="!!codes.length"
        data-test="site-code-row"
      >
        <SiteCodes
          v-if="codes.length"
          :codes="codes"
        />
        <button
          v-else
          type="button"
          class="secondary small"
          :disabled="waiting"
          data-test="site-code-expect"
          @click="expect"
        >
          {{ waiting ? "J'attends…" : "J'attends un code" }}
        </button>
      </SettingRow>
      <p
        v-if="message"
        class="setting-row-message muted"
        role="status"
      >
        {{ message }}
      </p>
      <template
        v-for="item in shown"
        :key="item.id"
      >
        <SettingRow
          :title="siteName(item)"
          :description="`${item.subject || 'Sans sujet'} · reçu à ${timeOfDay(item.received_at)}`"
          data-test="site-message"
        >
          <span class="muted alert-date">{{ dateInList(item.received_at) }}</span>
          <IconButton
            icon="chevron-down"
            :label="openId === item.id ? 'Refermer le message' : 'Lire le message'"
            :aria-expanded="openId === item.id"
            :data-test="`site-message-${item.id}`"
            @click="toggle(item)"
          />
        </SettingRow>
        <p
          v-if="openId === item.id"
          class="setting-row-message site-message-text"
          data-test="site-message-text"
        >
          {{ texts[item.id] ?? "…" }}
        </p>
      </template>
      <p
        v-if="!items.length"
        class="setting-row-message muted"
      >
        Aucun message pour l'instant.
      </p>
    </SettingCard>
  </section>
</template>
