<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type OrpMonth, type OrpRow } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import BottomSheet from "../components/BottomSheet.vue";
import CalendarDate from "../components/CalendarDate.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import NetworkError from "../components/NetworkError.vue";
import OrpMonthBar from "../components/OrpMonth.vue";
import OrpProofCard from "../components/OrpProofCard.vue";
import OrpSearchRows from "../components/OrpSearchRows.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import OrpFiche from "../components/OrpFiche.vue";
import OrpSheet from "../components/OrpSheet.vue";
import SidePanel from "../components/SidePanel.vue";
import TaskCheck from "../components/TaskCheck.vue";
import { usePageReady } from "../composables/usePageTransition";
import { usePhone } from "../composables/usePhone";
import { formatMonth, ofMonth, orpChannel, orpLeftLine, plural, shiftMonth } from "../format";
import { dateText, meetingsToNote, pastTitle, timeAndPlace } from "../rendezVous";
import { isNetworkError } from "../network";

// Bilan › ORP (docs/139 étape 8a, maquette Explorer ; B3 à B6, Kevin, 2026-11-04). De haut en bas :
// l'objectif du mois (le cercle liquide), l'export, les trois dernières recherches, le lien vers le
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
    // Le mois dont les justificatifs restent à remettre porte « À remettre » (planche BilanOrdinateurMoisPrecedents).
    const note = previous.value?.month === month && previous.value.state === "a_remettre" ? "À remettre" : undefined;
    if (month !== viewMonth.value) items.push({ label: capitalMonth(month), test: `orp-month-${month}`, icon: "calendar", run: go(month), note });
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
// Planche BilanOrdinateurMois : le mois déplié se replie (« Replier le mois », la carte du mois), sans ?tout=1.
const foldTo = computed(() => ({ path: "/bilan", query: viewingPast.value ? { orp: viewMonth.value } : {} }));
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
  const month = shownMonth.value?.month;
  if (month) void router.push({ path: "/bilan/orp", query: { mois: month, candidature: id } });
}

// Téléphone (§37 du 16.11, planches OrpMois, OrpMoisPrecedents, OrpExports) : la carte « Mois ORP · novembre » avec sa
// barre et son chevron ; replié, les trois premières à déclarer ; déplié, toutes, puis les recherches du mois et
// « Replier le mois » ; en bas, « Mois précédents » et « Autres exports », chacun dans sa feuille du bas.
const PHONE_DECLARE = 3;
const phoneTitle = computed(() => (shownMonth.value ? `Mois ORP · ${formatMonth(shownMonth.value.month).split(" ")[0]!.toLowerCase()}` : ""));
const phoneLine = computed(() => {
  const o = shownMonth.value;
  if (!o) return "";
  return o.target ? orpLeftLine(o.count, o.target, o.month, o.due_date) : "Indique l’objectif fixé avec ton ORP dans les Réglages";
});
// « À déclarer à l'ORP » sur téléphone (§61 du 17.11, planche Orp) : un cercle à cocher par ligne. Cochée, la ligne
// reste en place avec la coche verte et « Déclarée · 17 nov. », et le compteur du titre baisse ; « Annuler » est le
// cercle lui-même. Même marque que la fiche « Pour l'ORP » (PUT / DELETE …/job-room).
const checked = ref(new Map<number, string>());
const busyRows = ref(new Set<number>());
const phoneRows = computed<Pending[]>(() =>
  [previous.value, current.value]
    .filter((m, index, list): m is OrpMonth => !!m && m.state !== "remis" && list.findIndex((x) => x?.month === m.month) === index)
    .flatMap((m) => m.rows.filter((row) => !row.declared_at || checked.value.has(row.application_id)).map((row) => ({ ...row, month: m.month }))),
);
const phonePending = computed(() => (expanded.value ? phoneRows.value : phoneRows.value.slice(0, PHONE_DECLARE)));
async function declare(row: Pending, on: boolean): Promise<void> {
  const id = row.application_id;
  if (busyRows.value.has(id)) return;
  busyRows.value = new Set([...busyRows.value, id]);
  try {
    const params = { params: { path: { application_id: id } } };
    const { error } = on ? await api.PUT("/api/applications/{application_id}/job-room", params) : await api.DELETE("/api/applications/{application_id}/job-room", params);
    if (error !== undefined) return;
    const today = new Date().toISOString().slice(0, 10);
    for (const month of [previous.value, current.value]) {
      const found = month?.rows.find((r) => r.application_id === id);
      if (found) found.declared_at = on ? today : null;
    }
    const next = new Map(checked.value);
    if (on) next.set(id, SHORT_DAY.format(new Date()));
    else next.delete(id);
    checked.value = next;
  } finally {
    const left = new Set(busyRows.value);
    left.delete(id);
    busyRows.value = left;
  }
}
const SHORT_DAY = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });
function shortDay(row: OrpRow): string {
  const [d, m, y] = row.date.split(".").map(Number);
  return d && m && y ? SHORT_DAY.format(new Date(y, m - 1, d)) : row.date;
}
const ficheTo = (row: Pending) => ({ path: `/bilan/orp/candidature/${row.application_id}`, query: { mois: row.month } });
const monthsOpen = ref(false);
const exportsOpen = ref(false);
// « Exporter le formulaire (PDF) » passe dans « Autres exports » sur téléphone (Kevin, 16.11, 14 h 06).
const phoneExportItems = computed<MoreMenuItem[]>(() => [
  { label: "Exporter le formulaire (PDF)", test: "orp-export", icon: "download", run: () => void sheet.value?.printPdf() },
  ...exportItems.value,
]);
function runItem(item: MoreMenuItem): void {
  monthsOpen.value = false;
  exportsOpen.value = false;
  item.run?.();
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
    await loadMonths(data);
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
        <OrpProofCard
          wide
          @changed="load()"
        />
        <RouterLink
          :to="expanded ? foldTo : shownMonth.target ? allTo : { path: '/reglages', query: { rubrique: 'recherche' } }"
          class="today-orp-card bilan-orp-card"
          :aria-label="expanded ? cardLabel.replace('Voir tout le mois', 'Replier le mois') : cardLabel"
          :aria-expanded="expanded || undefined"
          data-test="orp-goal"
        >
          <OrpMonthBar
            :title="monthName"
            :count="shownMonth.count"
            :target="shownMonth.target ?? null"
            :month="shownMonth.month"
            :due="shownMonth.due_date"
            :line="cardLine"
            band
          />
          <AppIcon
            :name="expanded ? 'chevron-up' : 'chevron'"
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
            <div class="bilan-section-head">
              <h2 id="orp-declare-title">
                À déclarer à l’ORP · {{ pending.length }}
              </h2>
            </div>
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
            <template #last>
              <li>
                <RouterLink
                  v-if="expanded"
                  :to="foldTo"
                  class="bilan-card-more"
                  aria-expanded="true"
                  data-test="orp-fold"
                >
                  Replier le mois<AppIcon name="chevron-up" />
                </RouterLink>
                <RouterLink
                  v-else
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
            v-if="!declared.length && expanded"
            :to="foldTo"
            class="bilan-card-more"
            aria-expanded="true"
            data-test="orp-fold"
          >
            Replier le mois<AppIcon name="chevron-up" />
          </RouterLink>
          <RouterLink
            v-else-if="!declared.length"
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
                <!-- Maquette du 13.11 (BilanOrdinateur) : pas encore fixé, le calendrier vide en pointillés ; fixé (non dessiné), la date à venir en bleu. -->
                <CalendarDate
                  v-if="nextMeeting"
                  v-bind="cal(nextMeeting.starts_at)"
                  tone="blue"
                  :size="36"
                />
                <svg
                  v-else
                  class="bilan-cal-empty"
                  width="36"
                  height="39"
                  viewBox="0 0 48 52"
                  aria-hidden="true"
                  data-test="bilan-rdv-empty"
                >
                  <rect
                    x="3"
                    y="7"
                    width="42"
                    height="42"
                    rx="10"
                    fill="none"
                    stroke-width="2.5"
                    stroke-dasharray="5 4"
                  />
                  <path
                    d="M14 2.5 V9 M34 2.5 V9"
                    fill="none"
                    stroke-width="3"
                    stroke-linecap="round"
                  />
                </svg>
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
            chevron
            test-id="orp-months"
          />
          <MoreMenu
            :items="exportItems"
            :inline="false"
            trigger="Autres exports"
            trigger-icon="download"
            chevron
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
          <template #head-actions>
            <a
              href="https://www.job-room.ch"
              target="_blank"
              rel="noopener"
              class="orp-fiche-job-room"
              data-test="orp-fiche-job-room"
            >Ouvrir Job-Room<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
          </template>
          <OrpFiche
            v-if="fiche"
            :application-id="fiche.application_id"
            :month="fiche.month"
            wide
            @declared="onDeclared"
          />
        </SidePanel>
      </template>
      <template v-else-if="shownMonth">
        <!-- Téléphone, refait d'après les planches OrpMois, OrpMoisPrecedents et OrpExports (§37 du 16.11). -->
        <div
          class="orp-phone"
          data-test="orp-phone"
        >
          <!-- Les justificatifs du mois passé, en tâche à cocher (§58 du 17.11, planche Orp). -->
          <OrpProofCard @changed="load()" />
          <RouterLink
            :to="expanded ? foldTo : shownMonth.target ? allTo : { path: '/reglages', query: { rubrique: 'recherche' } }"
            class="today-orp-card bilan-orp-card"
            :aria-label="expanded ? cardLabel.replace('Voir tout le mois', 'Replier le mois') : cardLabel"
            :aria-expanded="shownMonth.target ? expanded : undefined"
            data-test="orp-goal"
          >
            <OrpMonthBar
              :title="phoneTitle"
              :count="shownMonth.count"
              :target="shownMonth.target ?? null"
              :month="shownMonth.month"
              :due="shownMonth.due_date"
              :line="phoneLine"
              band
            />
            <AppIcon
              :name="expanded ? 'chevron-up' : 'chevron-down'"
              class="today-orp-chevron"
            />
          </RouterLink>

          <section
            v-if="pending.length"
            class="bilan-section"
            aria-labelledby="orp-declare-title"
            data-test="orp-to-declare"
          >
            <div class="bilan-section-head">
              <h2 id="orp-declare-title">
                À déclarer à l’ORP · {{ pending.length }}
              </h2>
            </div>
            <div
              v-for="row in phonePending"
              :key="row.application_id"
              class="bilan-card orp-declare-row"
            >
              <TaskCheck
                :checked="checked.has(row.application_id)"
                :label="checked.has(row.application_id) ? `Annuler : ${row.company} pas encore déclarée` : `Marquer ${row.company} comme déclarée`"
                :busy="busyRows.has(row.application_id)"
                :data-test="`orp-declare-check-${row.application_id}`"
                @toggle="(on) => declare(row, on)"
              />
              <RouterLink
                :to="ficheTo(row)"
                class="orp-declare-link"
                :data-test="`orp-declare-${row.application_id}`"
              >
                <span class="bilan-card-what">
                  <strong class="orp-phone-top"><span>{{ row.company }}</span><span
                    v-if="row.missing.length && !checked.has(row.application_id)"
                    class="orp-phone-chip todo"
                  >Infos à compléter</span></strong>
                  <span>{{ checked.has(row.application_id) ? `Déclarée · ${checked.get(row.application_id)}` : `${row.job_title} · ${shortDay(row)}` }}</span>
                </span>
                <span
                  class="arrow-circle small"
                  aria-hidden="true"
                ><AppIcon name="arrow-right" /></span>
              </RouterLink>
            </div>
          </section>

          <section
            v-if="expanded"
            class="bilan-section"
            aria-labelledby="orp-month-title"
            data-test="orp-searches"
          >
            <div class="bilan-section-head">
              <h2 id="orp-month-title">
                Recherches {{ ofMonth(shownMonth.month) }}
              </h2>
              <span>{{ shownMonth.count }} ce mois</span>
            </div>
            <button
              v-for="row in declared"
              :key="row.application_id"
              type="button"
              class="bilan-card"
              :data-test="`orp-row-${row.application_id}`"
              @click="openSearch(row.application_id)"
            >
              <span class="bilan-card-what">
                <strong class="orp-phone-top"><span>{{ row.company }}</span><span :class="['orp-phone-chip', row.missing.length ? 'todo' : 'ok']">{{ row.missing.length ? "Justificatif à joindre" : "Justificatif joint" }}</span></strong>
                <span>{{ row.job_title }} · {{ shortDay(row) }}</span>
              </span>
              <span
                class="arrow-circle small"
                aria-hidden="true"
              ><AppIcon name="arrow-right" /></span>
            </button>
            <RouterLink
              :to="foldTo"
              class="bilan-card-more"
              aria-expanded="true"
              data-test="orp-fold"
            >
              Replier le mois<AppIcon name="chevron-up" />
            </RouterLink>
          </section>

          <div
            class="orp-phone-more"
            data-test="orp-more-row"
          >
            <button
              type="button"
              class="secondary"
              aria-haspopup="dialog"
              data-test="orp-months"
              @click="monthsOpen = true"
            >
              <AppIcon name="calendar" />Mois précédents
            </button>
            <button
              type="button"
              class="secondary"
              aria-haspopup="dialog"
              data-test="orp-exports"
              @click="exportsOpen = true"
            >
              <AppIcon name="download" />Autres exports
            </button>
          </div>
        </div>
        <BottomSheet
          :open="monthsOpen"
          title="Mois précédents"
          data-test="orp-months-sheet"
          @close="monthsOpen = false"
        >
          <ul class="orp-phone-sheet-list">
            <li
              v-for="item in monthItems"
              :key="item.test"
            >
              <button
                type="button"
                :data-test="item.test"
                @click="runItem(item)"
              >
                <AppIcon name="calendar" /><span>{{ item.label }}</span><span
                  v-if="item.note"
                  class="orp-phone-chip todo"
                >{{ item.note }}</span>
              </button>
            </li>
          </ul>
        </BottomSheet>
        <BottomSheet
          :open="exportsOpen"
          title="Autres exports"
          data-test="orp-exports-sheet"
          @close="exportsOpen = false"
        >
          <ul class="orp-phone-sheet-list">
            <li
              v-for="item in phoneExportItems"
              :key="item.test"
            >
              <a
                v-if="item.href"
                :href="item.href"
                :download="item.download || undefined"
                :data-test="item.test"
                @click="exportsOpen = false"
              ><AppIcon name="download" /><span>{{ item.label }}</span></a>
              <button
                v-else
                type="button"
                :data-test="item.test"
                @click="runItem(item)"
              >
                <AppIcon name="download" /><span>{{ item.label }}</span>
              </button>
            </li>
          </ul>
        </BottomSheet>
        <OrpSheet
          ref="sheet"
          :data="shownMonth"
          @reload="load"
        />
      </template>
    </div>
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (prefers-reduced-motion: reduce) {
.face-mouth-enter-active, .face-mouth-leave-active, .face-tile { transition: none; }
}
.bilan-orp-more { --bom-6: 6px; --bom-10: 10px; --bom-13: 0.8125rem; --bom-16: 16px; --bom-20: 20px; --bom-500: 500; }
/* Bilan › ORP sur téléphone (§37 du 16.11 ; HTML d'OrpMois) : les cartes de l'ordinateur à 68 px, 12/16, titre 16 ;
   pastille 12/700 de rayon 6 après l'entreprise ; deux pilules de 44 px à parts égales ; feuilles en lignes de 52. */
.orp-phone { --bilan-card-h: 68px; --bilan-pad-y: 12px; --bilan-pad: 16px; --bilan-17: 16px; --bilan-bar: 8px; --bilan-lh-21: 21px; --orp-h2: 17px; --orp-chip-r: 6px; display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-6); }
.orp-phone .today-orp-card { gap: var(--space-3); margin: 0; padding: var(--space-4); border: 1.5px solid var(--card-line); box-shadow: none; }
.orp-phone .orp-month-band, .orp-phone .bilan-section { gap: var(--space-2); }
.orp-phone .bilan-card { gap: var(--space-3); }
.orp-phone .bilan-card-what > span { margin-top: var(--space-1); }
.orp-phone .bilan-section-head h2 { font-size: var(--orp-h2); }
.orp-phone .bilan-card-what { font-size: var(--font-body); }
.orp-phone-top { display: flex; gap: var(--space-2); align-items: center; }
.orp-phone-top > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
/* « À déclarer à l'ORP » (§61 du 17.11, planche Orp) : le cercle à cocher (zone de 44 px) à gauche, dans la marge de la
   carte ; le reste de la ligne ouvre la fiche. Cercle à 40 px du bord (42 sur la planche), texte à 74 (76). */
.orp-phone .orp-declare-row { cursor: default; }
.orp-declare-link { flex: 1; min-width: 0; display: flex; align-items: center; gap: var(--space-3); align-self: stretch; color: inherit; text-decoration: none; }
.orp-phone-chip { flex: none; padding: var(--space-1) var(--space-2); border-radius: var(--orp-chip-r); font-size: var(--font-caption); white-space: nowrap; }
.orp-phone-chip.todo { background: var(--peach-soft); color: var(--peach-text); }
.orp-phone-chip.ok { background: var(--success-soft); color: var(--success); }
.orp-phone-more { display: flex; gap: var(--space-2); }
.orp-phone-more > button { flex: 1; min-width: 0; gap: var(--space-2); height: var(--target-min); padding: 0 var(--space-2); border: 1.5px solid var(--primary-graphic); border-radius: var(--radius-pill); background: var(--surface); color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-bold); }
/* À 320 px, les deux pilules gardent leur texte entier : l’icône part. */
@media (max-width: 359px) { .orp-phone-more > button > .icon { display: none; } }
.orp-phone-sheet-list { --orp-medium: 500; margin: 0; padding: 0; list-style: none; }
.orp-phone-sheet-list :is(button, a) { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: 52px; padding: 0 var(--space-1); border: 0; border-top: 1px solid var(--line); border-radius: 0; background: none; color: var(--text); font: inherit; font-weight: var(--orp-medium); text-decoration: none; }
.orp-phone-sheet-list :is(button, a) > span:first-of-type { flex: 1; text-align: left; }
.orp-phone-sheet-list .icon { width: 20px; height: 20px; color: var(--text-secondary); }
</style>
