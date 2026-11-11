<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type OrpMonth, type OrpRow } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import CalendarDate from "../components/CalendarDate.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import OrpBlocks from "../components/OrpBlocks.vue";
import OrpBar from "../components/OrpBar.vue";
import OrpProofCard from "../components/OrpProofCard.vue";
import OrpSearchRows from "../components/OrpSearchRows.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import OrpFiche from "../components/OrpFiche.vue";
import OrpSheet from "../components/OrpSheet.vue";
import SidePanel from "../components/SidePanel.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { formatMonth, ofMonth, orpChannel, plural, shiftMonth } from "../format";
import { dateText, meetingsToNote, pastTitle, timeAndPlace } from "../rendezVous";
import { isNetworkError } from "../network";

// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04). De haut en bas :
// l'objectif du mois (la barre ORP), l'export, les trois dernières recherches, le lien vers le
// Suivi ORP du mois. Sans carte Rythme : A5 annulé le 2026-11-05 par Kevin (maquette Explorer).
// Ordinateur (maquette du 8 novembre, BilanOrdinateur) : la carte du mois à cheval sur la bande, l'export et
// « Ajouter une recherche », les quatre dernières recherches en lignes (icône calendrier de 36 px), puis les
// rendez-vous ORP (à noter, le prochain).
// Maquette du 9 novembre (BilanOrdinateur, BilanOrdinateurFiche ; §2.5, §10.3, §11) : la carte du mois en cours
// (« Novembre », « 4 sur 13 », « Encore 9 d’ici le 5 décembre · dans les temps ») ; « À déclarer à l’ORP », les
// candidatures du mois passé et du mois en cours pas encore déclarées, en cartes, chacune ouvrant le panneau « Pour
// l’ORP » ; « Recherches de novembre », celles déjà déclarées ; les rendez-vous ORP en cartes.
type MeetingPage = components["schemas"]["MeetingPage"];
const { phone } = usePhone();
const router = useRouter();
const route = useRoute();
// Récapitulatif du 11 novembre, PR 33 (Kevin, 11.11) : sur ordinateur, plus de page « Suivi ORP » à part. Le mois
// affiché vient de l'adresse (?orp=2026-09, le mois en cours sinon) ; « Voir tout le mois » déplie toutes les
// recherches sur place (?tout=1) ; « Mois précédents », en bas, garde l'accès aux anciens mois et à leurs exports.
const viewMonth = computed(() => {
  const asked = route.query.orp;
  return typeof asked === "string" && /^\d{4}-\d{2}$/.test(asked) && asked <= thisMonth() ? asked : thisMonth();
});
const viewingPast = computed(() => viewMonth.value !== thisMonth());
const expanded = computed(() => route.query.tout === "1");
const PAST_MONTHS = 6;
const monthItems = computed<MoreMenuItem[]>(() => {
  const go = (month: string) => () => void router.push({ path: "/bilan", query: month === thisMonth() ? {} : { orp: month } });
  const items: MoreMenuItem[] = [];
  if (viewingPast.value) items.push({ label: `Revenir à ${formatMonth(thisMonth()).toLowerCase()}`, test: "orp-month-current", icon: "calendar", run: go(thisMonth()) });
  for (let i = 1; i <= PAST_MONTHS; i += 1) {
    const month = shiftMonth(thisMonth(), -i);
    if (month !== viewMonth.value) items.push({ label: capitalMonth(month), test: `orp-month-${month}`, icon: "calendar", run: go(month) });
  }
  return items;
});
const exportItems = computed<MoreMenuItem[]>(() => {
  const o = shownMonth.value;
  if (!o) return [];
  return [
    { label: "Télécharger en CSV (Excel)", test: "orp-csv", icon: "download", href: `/api/orp/${o.month}/csv`, download: true },
    ...(o.searches.length ? [{ label: "PDF avec le journal des recherches", test: "orp-pdf-journal", icon: "download" as const, run: () => void sheet.value?.printPdf(true) }] : []),
  ];
});
const meetings = ref<MeetingPage | null>(null);
const orp = ref<OrpMonth | null>(null);
const error = ref(false);
const offline = ref(false);
usePageReady("bilan-orp", () => !!orp.value || error.value);

const LAST_WIDE = 4;
const DECLARE_SHOWN = 3;
// Sur ordinateur, le mois en cours et le mois passé (le serveur donne par défaut le mois à remettre).
const current = ref<OrpMonth | null>(null);
const previous = ref<OrpMonth | null>(null);
const shownMonth = computed(() => current.value ?? orp.value);
function capitalMonth(month: string): string {
  return formatMonth(month).replace(/^./, (c) => c.toUpperCase());
}
const capital = (month: string) => formatMonth(month).split(" ")[0]!.replace(/^./, (c) => c.toUpperCase());
const monthName = computed(() => (shownMonth.value ? capital(shownMonth.value.month) : ""));
const cardLabel = computed(() => {
  const o = shownMonth.value;
  if (!o) return "";
  return `${monthName.value} : ${o.target ? `${o.count} recherches sur ${o.target}` : plural(o.count, "recherche", "recherches")}. Voir tout le mois`;
});
const cardLine = computed(() => (shownMonth.value?.target ? undefined : "Indique l’objectif fixé avec ton ORP dans les Réglages"));
// « À déclarer à l'ORP » : les envoyées pas encore sur la feuille de recherches, le mois passé d'abord.
type Pending = OrpRow & { month: string };
const pending = computed<Pending[]>(() =>
  [previous.value, current.value]
    .filter((m, index, list): m is OrpMonth => !!m && m.state !== "remis" && list.findIndex((x) => x?.month === m.month) === index)
    .flatMap((m) => m.rows.filter((row) => !row.declared_at).map((row) => ({ ...row, month: m.month }))),
);
const pendingMonths = computed(() => {
  const names = [...new Set(pending.value.map((row) => formatMonth(row.month).split(" ")[0]!.toLowerCase()))];
  return names.join(" et ");
});
const declareAll = ref(false);
const pendingShown = computed(() => (declareAll.value || expanded.value ? pending.value : pending.value.slice(0, DECLARE_SHOWN)));
// « Voir tout le mois et les justificatifs » et le chevron de la carte : le mois déplié, sur place.
const allTo = computed(() => ({ path: "/bilan", query: { ...(viewingPast.value ? { orp: viewMonth.value } : {}), tout: "1" } }));
const declared = computed(() => (shownMonth.value?.rows ?? []).filter((row) => row.declared_at));
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
// « 22.10.2026 » du formulaire.
function rowDay(row: OrpRow): { day: number; month: number } {
  const [day, month] = row.date.split(".").map(Number);
  return { day: day ?? 1, month: month ?? 1 };
}
// Le panneau « Pour l'ORP » (maquette BilanOrdinateurFiche) : la fiche à recopier dans Job-Room.
const fiche = ref<Pending | null>(null);
function onDeclared(): void {
  fiche.value = null;
  void load();
}
const toNote = computed(() => (meetings.value ? meetingsToNote(meetings.value) : []));
const nextMeeting = computed(() => {
  const m = meetings.value?.meeting;
  return m && new Date(m.starts_at).getTime() > Date.now() ? m : null;
});
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);
// Une recherche du mois : sa ligne dans le Suivi ORP du mois.
function openSearch(id: number): void {
  if (orp.value) void router.push({ path: "/bilan/orp", query: { mois: orp.value.month, candidature: id } });
}

function thisMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}
async function monthData(month: string, known: OrpMonth): Promise<OrpMonth | null> {
  if (known.month === month) return known;
  const { data } = await api.GET("/api/orp", { params: { query: { month } } }).catch(() => ({ data: undefined }));
  return data ?? null;
}
async function loadMonths(known: OrpMonth): Promise<void> {
  // Un mois passé se regarde seul ; le mois en cours garde, dans « À déclarer », les oubliées du mois d'avant.
  const month = viewMonth.value;
  const [cur, prev] = await Promise.all([monthData(month, known), viewingPast.value ? Promise.resolve(null) : monthData(shiftMonth(month, -1), known)]);
  current.value = cur;
  previous.value = prev;
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
    if (!phone.value) await loadMonths(data);
    orp.value = data;
    meetings.value = rdv?.data ?? null;
  } catch (cause) {
    error.value = true;
    offline.value = isNetworkError(cause);
  }
}
onMounted(() => void load());
watch(viewMonth, () => void load());
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
        Le suivi ORP n’a pas pu être chargé.
      </p>
      <LoadingBlocks
        v-else-if="!orp"
        :heights="['10rem', '3.5rem', '14rem']"
      />
      <template v-else-if="!phone && shownMonth">
        <!-- Le mois précédent à remettre, ou remis (récapitulatif du 11 novembre, PR 29). -->
        <OrpProofCard @changed="load()" />
        <RouterLink
          :to="shownMonth.target ? allTo : { path: '/reglages', query: { rubrique: 'recherche' } }"
          class="today-orp-card bilan-orp-card"
          :aria-label="cardLabel"
          data-test="orp-goal"
        >
          <OrpBar
            :month="shownMonth.month"
            :count="shownMonth.count"
            :target="shownMonth.target ?? null"
            :due="shownMonth.due_date"
            :note="cardLine"
            pace
            card
          />
          <AppIcon
            name="chevron"
            class="today-orp-chevron"
          />
        </RouterLink>
        <div class="bilan-orp-actions">
          <button
            type="button"
            class="secondary action-2"
            data-test="orp-export"
            @click="sheet?.printPdf()"
          >
            Exporter le formulaire (PDF)
          </button>
          <button
            type="button"
            class="secondary action-2"
            data-test="orp-add"
            @click="router.push({ path: '/candidatures/suivi', query: { ajouter: '1' } })"
          >
            Ajouter une recherche
          </button>
        </div>
        <OrpSheet
          ref="sheet"
          :data="shownMonth"
          @reload="load"
        />
        <section
          v-if="pending.length"
          class="bilan-section bilan-declare"
          aria-labelledby="orp-declare-title"
          data-test="orp-to-declare"
        >
          <div class="bilan-section-head">
            <h2 id="orp-declare-title">
              À déclarer à l’ORP · {{ pending.length }}
            </h2>
          </div>
          <p class="bilan-section-sub">
            Envoyées en {{ pendingMonths }}, pas encore sur ta feuille de recherches.
          </p>
          <button
            v-for="row in pendingShown"
            :key="row.application_id"
            type="button"
            class="bilan-card"
            aria-haspopup="dialog"
            :data-test="`orp-declare-${row.application_id}`"
            @click="fiche = row"
          >
            <CalendarDate
              v-bind="rowDay(row)"
              tone="past"
              :size="36"
            />
            <span class="bilan-card-what"><strong>{{ row.company }}</strong><span>{{ row.job_title }} · {{ orpChannel(row.method) }}</span></span>
            <span :class="['bilan-card-state', row.missing.length ? 'todo' : 'ok']">{{ row.missing.length ? "Infos à compléter" : "Prête" }}</span>
            <span
              class="arrow-circle small"
              aria-hidden="true"
            ><AppIcon name="arrow-right" /></span>
          </button>
          <button
            v-if="!declareAll && !expanded && pending.length > DECLARE_SHOWN"
            type="button"
            class="bilan-card-more"
            data-test="orp-declare-more"
            @click="declareAll = true"
          >
            Voir {{ pending.length - DECLARE_SHOWN === 1 ? "l’autre" : `les ${pending.length - DECLARE_SHOWN} autres` }}<AppIcon name="chevron" />
          </button>
        </section>
        <section
          class="bilan-section"
          aria-labelledby="orp-last-title"
          data-test="orp-searches"
        >
          <div class="bilan-section-head">
            <h2 id="orp-last-title">
              Recherches {{ ofMonth(shownMonth.month) }}
            </h2>
            <span>{{ shownMonth.count }} ce mois</span>
          </div>
          <p
            class="bilan-section-sub"
            data-test="orp-proof-note"
          >
            Déjà déclarées. L’ORP peut demander un justificatif pour chaque recherche : l’e-mail de confirmation ou une capture de la candidature.
          </p>
          <OrpSearchRows
            :rows="declared"
            :limit="expanded ? undefined : LAST_WIDE"
            :link="shownMonth.month"
          >
            <template
              v-if="!expanded"
              #last
            >
              <li>
                <RouterLink
                  :to="allTo"
                  class="bilan-card-more"
                  data-test="orp-all"
                >
                  Voir tout le mois et les justificatifs<AppIcon name="chevron" />
                </RouterLink>
              </li>
            </template>
          </OrpSearchRows>
          <RouterLink
            v-if="!declared.length && !expanded"
            :to="allTo"
            class="bilan-card-more"
            data-test="orp-all"
          >
            Voir tout le mois et les justificatifs<AppIcon name="chevron" />
          </RouterLink>
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
          <ul class="bilan-cards">
            <li
              v-for="item in toNote"
              :key="item.id"
            >
              <RouterLink
                :to="{ path: '/candidatures/rendez-vous-orp' }"
                class="bilan-card"
                :data-test="`bilan-rdv-note-${item.id}`"
              >
                <CalendarDate
                  v-bind="cal(item.starts_at)"
                  tone="orp"
                  :size="36"
                />
                <span class="bilan-card-what"><strong>{{ pastTitle(item.starts_at).replace(" ORP", "") }}</strong><span>{{ [item.place, `${dateText(item.starts_at).toLowerCase()}, ${timeAndPlace(item.starts_at, null)}`].filter(Boolean).join(" · ") }}</span></span>
                <span class="bilan-card-state todo">À noter</span>
                <span
                  class="arrow-circle small"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span>
              </RouterLink>
            </li>
            <li>
              <RouterLink
                :to="{ path: '/candidatures/rendez-vous-orp' }"
                class="bilan-card"
                data-test="bilan-rdv-next"
              >
                <span class="bilan-card-what"><strong>Prochain rendez-vous</strong></span>
                <span class="bilan-card-state">{{ nextMeeting ? `${dateText(nextMeeting.starts_at)}, ${timeAndPlace(nextMeeting.starts_at, null)}` : "Pas encore fixé" }}</span>
                <span
                  class="arrow-circle small"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span>
              </RouterLink>
            </li>
          </ul>
        </section>
        <!-- Hors maquette, décidé avec Kevin le 11.11 : les anciens mois et les autres exports, en bas. -->
        <div
          class="bilan-orp-more"
          data-test="orp-more-row"
        >
          <MoreMenu
            :items="monthItems"
            :inline="false"
            trigger="Mois précédents"
            trigger-icon="calendar"
            test-id="orp-months"
          />
          <MoreMenu
            :items="exportItems"
            :inline="false"
            trigger="Autres exports"
            trigger-icon="download"
            test-id="orp-exports"
          />
        </div>
        <SidePanel
          :open="!!fiche"
          title="Pour l’ORP"
          :width="480"
          data-test="orp-fiche-panel"
          @close="fiche = null"
        >
          <OrpFiche
            v-if="fiche"
            :application-id="fiche.application_id"
            :month="fiche.month"
            @declared="onDeclared"
          />
        </SidePanel>
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
