<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";

import { api } from "../api/client";
import { sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";
import DisclosureRow from "./DisclosureRow.vue";
import HoverNote from "./HoverNote.vue";
import SiteCodes from "./SiteCodes.vue";

// Les e-mails des sites (docs/112, docs/113, mise en page 0.84.2) : une rubrique, une carte.
// En tête, le code de vérification : le code lui-même quand il est là, sinon « J'attends un
// code » (la boîte relevée toutes les 15 secondes pendant 5 minutes) ; puis, sous un filet,
// les messages des sites gardés 30 jours. Où passent ces e-mails : au survol du titre.
type SiteCode = { search_id: number; site: string; code: string; received_at: string };
type SiteMessage = { id: number; site: string; subject?: string | null; received_at: string };
const props = defineProps<{ codes: SiteCode[]; guestMailbox: boolean }>();
const emit = defineEmits<{ refresh: [] }>();

const waiting = ref(false);
// Rien à montrer : ni code, ni attente, ni message des sites.
const quiet = computed(() => !props.codes.length && !waiting.value && !items.value.length);
const message = ref("");
let timer: ReturnType<typeof setInterval> | undefined;
let stopAt = 0;
const WAIT_MS = 5 * 60_000;

const items = ref<SiteMessage[]>([]);
const openId = ref<number | null>(null);
const texts = reactive<Record<number, string>>({});
const day = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short", timeZone: "Europe/Zurich" });

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
    class="site-mail"
    data-test="site-mail"
  >
    <!-- Ni code ni message (docs/131 §B.11) : une ligne repliable, « J'attends un code » dedans ;
         la carte revient dès qu'un code ou un message arrive. -->
    <DisclosureRow
      v-if="quiet"
      title="Les e-mails des sites"
      value="aucun code en attente"
      data-test="site-mail-quiet"
    >
      <p
        v-if="guestMailbox"
        class="setting-desc"
      >
        <HoverNote
          text="Reçus en Suisse chez Infomaniak, effacés de la boîte une fois rangés."
          data-test="guest-mailbox-note"
        >
          Les e-mails des sites passent par la boîte de jobA1.
        </HoverNote>
      </p>
      <div class="site-mail-row">
        <div class="site-mail-text">
          <strong>Code de vérification</strong>
          <p class="setting-desc">
            {{ waiting ? "J'attends le code, pendant 5 minutes." : "Il s'affiche ici dès qu'il arrive." }}
          </p>
          <p
            v-if="message"
            class="hint"
            role="status"
          >
            {{ message }}
          </p>
        </div>
        <button
          type="button"
          class="pill"
          :disabled="waiting"
          data-test="site-code-expect"
          @click="expect"
        >
          {{ waiting ? "J'attends…" : "J'attends un code" }}
        </button>
      </div>
    </DisclosureRow>
    <template v-else>
      <!-- Où passent ces e-mails : en description au survol du titre (docs/interface.md,
         titres et textes 5), plus en pied de carte (0.86.1). -->
      <h2 class="section-title first">
        <HoverNote
          :text="guestMailbox ? 'Reçus en Suisse chez Infomaniak, effacés de la boîte une fois rangés.' : ''"
          data-test="guest-mailbox-note"
        >
          Les e-mails des sites
        </HoverNote>
      </h2>
      <div class="settings-card site-mail-card">
        <!-- Le code arrivé prend la place de « J'attends un code » (0.84.2). -->
        <div class="site-mail-row">
          <SiteCodes
            v-if="codes.length"
            :codes="codes"
          />
          <template v-else>
            <div class="site-mail-text">
              <strong>Code de vérification</strong>
              <p class="setting-desc">
                {{ waiting ? "J'attends le code, pendant 5 minutes." : "Il s'affiche ici dès qu'il arrive." }}
              </p>
              <p
                v-if="message"
                class="hint"
                role="status"
              >
                {{ message }}
              </p>
            </div>
            <button
              type="button"
              class="pill"
              :disabled="waiting"
              data-test="site-code-expect"
              @click="expect"
            >
              {{ waiting ? "J'attends…" : "J'attends un code" }}
            </button>
          </template>
        </div>
        <div
          v-if="items.length"
          class="site-mail-messages"
          data-test="site-messages"
        >
          <strong>Messages des sites</strong>
          <p class="setting-desc">
            Hors alertes, gardés 30 jours.
          </p>
          <ul class="site-message-list">
            <li
              v-for="item in items"
              :key="item.id"
              data-test="site-message"
            >
              <button
                type="button"
                class="site-message-row"
                :aria-expanded="openId === item.id"
                @click="toggle(item)"
              >
                <span class="site-message-head">
                  <span class="site-message-subject">{{ item.subject || "Sans sujet" }}</span>
                  <span class="site-message-meta">{{ item.site === "unknown" ? "un site" : sourceLabel[item.site] }} · {{ day.format(new Date(item.received_at)) }}</span>
                </span>
                <AppIcon
                  name="chevron"
                  class="site-message-chevron"
                />
              </button>
              <p
                v-if="openId === item.id"
                class="site-message-text"
              >
                {{ texts[item.id] ?? "…" }}
              </p>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </section>
</template>
