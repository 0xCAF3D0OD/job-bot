<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type OrpMonth } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import CalendarDate from "../components/CalendarDate.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import OrpBlocks from "../components/OrpBlocks.vue";
import OrpMonthBar from "../components/OrpMonth.vue";
import OrpSearchRows from "../components/OrpSearchRows.vue";
import OrpSheet from "../components/OrpSheet.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { formatMonth, orpPace, plural } from "../format";
import { dateText, meetingsToNote, pastTitle, timeAndPlace } from "../rendezVous";
import { isNetworkError } from "../network";

// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04). De haut en bas :
// l'objectif du mois (le cercle liquide), l'export, les trois dernières recherches, le lien vers le
// Suivi ORP du mois. Sans carte Rythme : A5 annulé le 2026-11-05 par Kevin (maquette Explorer).
// Ordinateur (maquette du 8 novembre, BilanOrdinateur) : la carte du mois à cheval sur la bande, l'export et
// « Ajouter une recherche », les quatre dernières recherches en lignes (icône calendrier de 36 px), puis les
// rendez-vous ORP (à noter, le prochain).
type MeetingPage = components["schemas"]["MeetingPage"];
const { phone } = usePhone();
const router = useRouter();
const meetings = ref<MeetingPage | null>(null);
const orp = ref<OrpMonth | null>(null);
const error = ref(false);
const offline = ref(false);
usePageReady("bilan-orp", () => !!orp.value || error.value);

const LAST_WIDE = 4;
const monthName = computed(() => (orp.value ? formatMonth(orp.value.month).split(" ")[0]!.replace(/^./, (c) => c.toUpperCase()) : ""));
const left = computed(() => Math.max(0, (orp.value?.target ?? 0) - (orp.value?.count ?? 0)));
const cardTitle = computed(() => {
  const o = orp.value;
  if (!o?.target) return monthName.value;
  return left.value ? `${monthName.value} · ${plural(left.value, "recherche", "recherches")} à faire` : `${monthName.value} · objectif atteint`;
});
const cardLine = computed(() => {
  const o = orp.value;
  if (!o) return "";
  if (!o.target) return "Indique l'objectif fixé avec ton ORP dans les Réglages";
  const [year, month] = o.month.split("-").map(Number);
  const deadline = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" }).format(new Date(year!, month!, 0));
  const pace = orpPace(o.count, o.target, o.month);
  return ["Objectif fixé avec ton ORP", `échéance le ${deadline}`, pace ? pace.word.replace(/\.$/, "").toLowerCase() : ""].filter(Boolean).join(" · ");
});
const cardLabel = computed(() => {
  const o = orp.value;
  if (!o) return "";
  return `${cardTitle.value}, ${o.target ? `${o.count} sur ${o.target}` : plural(o.count, "recherche", "recherches")}. Voir tout le mois`;
});
const toNote = computed(() => (meetings.value ? meetingsToNote(meetings.value) : []));
const nextMeeting = computed(() => {
  const m = meetings.value?.meeting;
  return m && new Date(m.starts_at).getTime() > Date.now() ? m : null;
});
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);
// Une recherche du mois : sa ligne dans le Suivi ORP du mois.
function openSearch(id: number): void {
  if (orp.value) void router.push({ path: "/bilan/orp", query: { mois: orp.value.month, candidature: id } });
}

async function load(): Promise<void> {
  error.value = false;
  offline.value = false;
  try {
    const [{ data }, rdv] = await Promise.all([
      api.GET("/api/orp"),
      phone.value ? Promise.resolve(null) : api.GET("/api/orp-meeting").catch(() => null),
    ]);
    if (!data) throw new Error();
    orp.value = data;
    meetings.value = rdv?.data ?? null;
  } catch (cause) {
    error.value = true;
    offline.value = isNetworkError(cause);
  }
}
onMounted(() => void load());
</script>

<template>
  <section :class="phone ? 'band blocks-page bilan-orp-blocks' : 'bilan-orp-page'">
    <div :class="phone ? 'container bilan-orp' : 'bilan-orp-wide'">
      <NetworkError
        v-if="error && offline"
        @retry="load()"
      />
      <p
        v-else-if="error"
        class="notice error"
        role="alert"
      >
        Le suivi ORP n'a pas pu être chargé.
      </p>
      <LoadingBlocks
        v-else-if="!orp"
        :heights="['10rem', '3.5rem', '14rem']"
      />
      <template v-else-if="!phone">
        <RouterLink
          :to="orp.target ? { path: '/bilan/orp', query: { mois: orp.month } } : { path: '/reglages', query: { rubrique: 'recherche' } }"
          class="today-orp-card bilan-orp-card"
          :aria-label="cardLabel"
          data-test="orp-goal"
        >
          <OrpMonthBar
            :title="cardTitle"
            :count="orp.count"
            :target="orp.target ?? null"
            :month="orp.month"
            :line="cardLine"
            band
          />
          <AppIcon
            name="chevron"
            class="today-orp-chevron"
          />
        </RouterLink>
        <div class="bilan-orp-actions">
          <button
            type="button"
            class="secondary"
            data-test="orp-export"
            @click="sheet?.printPdf()"
          >
            Exporter le formulaire (PDF)
          </button>
          <button
            type="button"
            class="secondary"
            data-test="orp-add"
            @click="router.push({ path: '/bilan/orp', query: { mois: orp.month, ajouter: '1' } })"
          >
            Ajouter une recherche
          </button>
        </div>
        <OrpSheet
          ref="sheet"
          :data="orp"
          @reload="load"
        />
        <section
          class="bilan-section"
          aria-labelledby="orp-last-title"
        >
          <div class="bilan-section-head">
            <h2 id="orp-last-title">
              Dernières recherches
            </h2>
            <span>{{ orp.count }} ce mois</span>
          </div>
          <p
            class="orp-proof-note"
            data-test="orp-proof-note"
          >
            L’ORP peut demander un justificatif pour chaque recherche : l’e-mail de confirmation ou une capture.
          </p>
          <OrpSearchRows
            :rows="orp.rows"
            :limit="LAST_WIDE"
            :link="orp.month"
          >
            <template #last>
              <li>
                <RouterLink
                  :to="{ path: '/bilan/orp', query: { mois: orp.month } }"
                  class="bilan-row-more"
                  data-test="orp-all"
                >
                  Voir tout le mois et les justificatifs<AppIcon name="chevron" />
                </RouterLink>
              </li>
            </template>
          </OrpSearchRows>
        </section>
        <section
          v-if="meetings"
          class="bilan-section"
          aria-labelledby="orp-rdv-title"
          data-test="bilan-rdv"
        >
          <div class="bilan-section-head">
            <h2 id="orp-rdv-title">
              Rendez-vous ORP
            </h2>
          </div>
          <ul class="orp-rows orp-rows-link">
            <li
              v-for="item in toNote"
              :key="item.id"
            >
              <RouterLink
                :to="{ path: '/candidatures/rendez-vous-orp' }"
                class="orp-row"
                :data-test="`bilan-rdv-note-${item.id}`"
              >
                <CalendarDate
                  v-bind="cal(item.starts_at)"
                  tone="orp"
                  :size="36"
                />
                <span class="orp-what"><strong>{{ pastTitle(item.starts_at).replace(" ORP", "") }}</strong><span class="orp-sub">{{ [item.place, `${dateText(item.starts_at).toLowerCase()}, ${timeAndPlace(item.starts_at, null)}`].filter(Boolean).join(" · ") }}</span></span>
                <span class="orp-row-state todo">À noter</span>
                <AppIcon
                  name="chevron"
                  class="orp-row-chevron"
                />
              </RouterLink>
            </li>
            <li>
              <RouterLink
                :to="{ path: '/candidatures/rendez-vous-orp' }"
                class="orp-row"
                data-test="bilan-rdv-next"
              >
                <span class="orp-what">Prochain rendez-vous</span>
                <span class="orp-row-state">{{ nextMeeting ? `${dateText(nextMeeting.starts_at)}, ${timeAndPlace(nextMeeting.starts_at, null)}` : "Pas encore fixé" }}</span>
                <AppIcon
                  name="chevron"
                  class="orp-row-chevron"
                />
              </RouterLink>
            </li>
          </ul>
        </section>
      </template>
      <template v-else>
        <!-- Téléphone (lot 18, §10.2 ; onglet ORP de la maquette Explorer) : les blocs du Suivi ORP. -->
        <OrpBlocks
          :data="orp"
          @open="openSearch"
          @export="sheet?.printPdf()"
        />
        <OrpSheet
          ref="sheet"
          :data="orp"
          @reload="load"
        />
      </template>
    </div>
  </section>
</template>
