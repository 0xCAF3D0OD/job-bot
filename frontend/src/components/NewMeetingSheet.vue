<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from "vue";

import { api, type Application } from "../api/client";
import type { components } from "../api/schema";
import { applicationBody } from "../applicationBody";
import { usePhone } from "../composables/usePhone";
import { dateText, timeAndPlace } from "../rendezVous";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import BusyButton from "./BusyButton.vue";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import FormField from "./FormField.vue";
import SegmentedControl from "./SegmentedControl.vue";

// « Nouveau rendez-vous » (paquet du 11 novembre, PR 41 ; maquettes CandidaturesOrdinateurB `ajrv` et RendezVous
// `addSheet`) : un seul panneau pour un entretien avec une entreprise et pour un rendez-vous ORP. Sur ordinateur, le
// panneau de droite (PR 37) ; sur téléphone, la fenêtre du bas. Date et heure toujours vides au départ.
// Entreprise : la candidature (liste des envoyées, avec recherche), le format, la date, l'heure, puis le lien, le numéro
// ou l'adresse selon le format ; la candidature passe en « Entretien ». ORP : date, heure, lieu ou lien.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];
type Kind = "entreprise" | "orp";
type Format = "telephone" | "visio" | "sur_place";

const props = defineProps<{
  open: boolean;
  applications: Application[];
  // Ouvert depuis une candidature : elle est déjà choisie.
  applicationId?: number | null;
  kind?: Kind;
  // Le rendez-vous ORP déjà prévu : un nouveau le remplace (un seul à venir).
  planned?: Meeting | null;
}>();
const emit = defineEmits<{ close: []; orp: [page: Page]; interview: [application: Application] }>();

const { phone } = usePhone();
const KINDS = [
  { value: "entreprise", label: "Une entreprise", test: "meeting-kind-entreprise" },
  { value: "orp", label: "L’ORP", test: "meeting-kind-orp" },
];
const FORMATS = [
  { value: "telephone", label: "Téléphone", test: "meeting-format-telephone" },
  { value: "visio", label: "Visio", test: "meeting-format-visio" },
  { value: "sur_place", label: "Sur place", test: "meeting-format-sur_place" },
];
const WHERE: Record<Format, { label: string; type: string; mode: "url" | "tel" | "text" }> = {
  telephone: { label: "Numéro", type: "tel", mode: "tel" },
  visio: { label: "Lien de la visio", type: "text", mode: "url" },
  sur_place: { label: "Adresse", type: "text", mode: "text" },
};

const kind = ref<string>(props.kind ?? "entreprise");
const format = ref<string>("visio");
const chosen = ref<number | null>(props.applicationId ?? null);
const day = ref("");
const time = ref("");
const place = ref("");
const picking = ref<"" | "date" | "time">("");
const errors = ref({ application: "", when: "" });
const message = ref("");
const busy = ref(false);
const body = ref<HTMLElement | null>(null);

// La liste : les candidatures envoyées qui peuvent encore donner un entretien, les plus récentes d'abord.
const candidates = computed(() =>
  props.applications
    .filter((a) => a.status !== "refus" && a.status !== "engagement")
    .slice()
    .sort((a, b) => (b.sent_at ?? "").localeCompare(a.sent_at ?? "")),
);
function nameOf(a: Application): string {
  return [a.job_title || "Poste non indiqué", a.company].filter(Boolean).join(" · ");
}
const picked = computed(() => candidates.value.find((a) => a.id === chosen.value) ?? null);

// Le champ « Candidature » : une liste déroulante avec recherche (combobox). Le texte long est coupé par « … ».
const listId = useId();
const search = ref(picked.value ? nameOf(picked.value) : "");
const listOpen = ref(false);
const active = ref(0);
function fold(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}
const matches = computed(() => {
  const words = picked.value && search.value === nameOf(picked.value) ? [] : fold(search.value).split(/\s+/).filter(Boolean);
  return candidates.value.filter((a) => words.every((w) => fold(nameOf(a)).includes(w)));
});
function openList(): void {
  listOpen.value = true;
  active.value = Math.max(0, matches.value.findIndex((a) => a.id === chosen.value));
}
function typed(): void {
  chosen.value = null;
  listOpen.value = true;
  active.value = 0;
}
function choose(a: Application): void {
  chosen.value = a.id;
  search.value = nameOf(a);
  listOpen.value = false;
  errors.value.application = "";
}
function leaveList(): void {
  listOpen.value = false;
  // Un texte tapé sans choix : on revient à la candidature choisie, ou au champ vide.
  search.value = picked.value ? nameOf(picked.value) : "";
}
function onKey(event: KeyboardEvent): void {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (!listOpen.value) return openList();
    const n = matches.value.length;
    if (n) active.value = (active.value + (event.key === "ArrowDown" ? 1 : n - 1)) % n;
  } else if (event.key === "Enter" && listOpen.value) {
    event.preventDefault();
    const a = matches.value[active.value];
    if (a) choose(a);
  } else if (event.key === "Escape" && listOpen.value) {
    event.preventDefault();
    event.stopPropagation();
    leaveList();
  }
}

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    kind.value = props.kind ?? "entreprise";
    chosen.value = props.applicationId ?? null;
    search.value = picked.value ? nameOf(picked.value) : "";
    format.value = "visio";
    day.value = "";
    time.value = "";
    place.value = "";
    picking.value = "";
    errors.value = { application: "", when: "" };
    message.value = "";
  },
);
watch(kind, () => {
  place.value = "";
  errors.value = { application: "", when: "" };
  message.value = "";
});

function pickedWhen(value: { date: string; time: string }): void {
  day.value = value.date;
  time.value = value.time;
  const which = picking.value;
  picking.value = "";
  if (day.value && time.value) errors.value.when = "";
  void nextTick(() => body.value?.querySelector<HTMLElement>(`[data-test=dt-${which || "date"}]`)?.focus());
}
function cancelPick(): void {
  const which = picking.value;
  picking.value = "";
  void nextTick(() => body.value?.querySelector<HTMLElement>(`[data-test=dt-${which || "date"}]`)?.focus());
}

const where = computed(() => WHERE[format.value as Format]);
const plannedLine = computed(() =>
  props.planned ? `${dateText(props.planned.starts_at)}, ${timeAndPlace(props.planned.starts_at, props.planned.place)}` : "",
);

const FAILED = "Le rendez-vous n’est pas enregistré. Ta saisie est gardée, réessaie dans un instant.";
// Le message du serveur quand il en donne un lisible (une phrase), sinon le nôtre.
function refusal(error: unknown): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  return typeof detail === "string" && detail ? detail : FAILED;
}

async function save(): Promise<void> {
  message.value = "";
  errors.value.application = kind.value === "entreprise" && !picked.value ? "Choisis la candidature." : "";
  errors.value.when = !day.value ? "Indique la date du rendez-vous." : !time.value ? "Indique l’heure." : "";
  if (errors.value.application || errors.value.when) {
    await nextTick();
    const target = errors.value.application ? "[data-test=meeting-application]" : !day.value ? "[data-test=dt-date]" : "[data-test=dt-time]";
    body.value?.querySelector<HTMLElement>(target)?.focus();
    return;
  }
  const at = new Date(`${day.value}T${time.value}`).toISOString();
  busy.value = true;
  try {
    if (kind.value === "orp") {
      const { data, error } = await api.PUT("/api/orp-meeting", { body: { starts_at: at, place: place.value, advisor: props.planned?.advisor ?? "" } });
      if (data) emit("orp", data);
      else message.value = refusal(error);
      return;
    }
    const application = picked.value!;
    const { data } = await api.PUT("/api/applications/{application_id}", {
      params: { path: { application_id: application.id } },
      body: {
        ...applicationBody(application),
        status: "entretien",
        status_reason: application.status_reason ?? null,
        status_at: application.status === "entretien" ? (application.status_at ?? null) : null,
        interview_at: at,
        interview_place: place.value.trim() || null,
        interview_format: format.value as Format,
      },
    });
    if (data) emit("interview", data);
    else message.value = FAILED;
  } catch {
    // Le serveur ne répond pas, ou la connexion est coupée : jamais d'échec silencieux (défaut du 13 novembre). Le
    // panneau reste ouvert et la saisie est gardée.
    message.value = "Connexion perdue : le rendez-vous n’est pas enregistré. Ta saisie est gardée, réessaie dans un instant.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Nouveau rendez-vous"
    :subtitle="phone ? '' : 'jobA1 prépare ta fiche la veille'"
    :icon="phone ? '' : 'calendar'"
    class="new-meeting"
    data-test="new-meeting"
    @close="emit('close')"
  >
    <div
      ref="body"
      class="new-meeting-body"
    >
      <DateTimePanel
        v-if="picking"
        :date="day"
        :time="time"
        title="Nouveau rendez-vous"
        @confirm="pickedWhen"
        @cancel="cancelPick"
      />
      <form
        v-else
        id="new-meeting-form"
        class="new-meeting-form"
        data-test="new-meeting-form"
        novalidate
        @submit.prevent="save"
      >
        <SegmentedControl
          v-model="kind"
          :options="KINDS"
          label="Avec qui ?"
          full
        />
        <template v-if="kind === 'entreprise'">
          <div class="new-meeting-combo">
            <FormField
              v-slot="{ id, describedby, invalid }"
              label="Candidature"
              :error="errors.application"
            >
              <input
                :id="id"
                v-model="search"
                type="text"
                role="combobox"
                autocomplete="off"
                aria-autocomplete="list"
                :aria-expanded="listOpen"
                :aria-controls="listId"
                :aria-activedescendant="listOpen && matches[active] ? `${listId}-${matches[active]!.id}` : undefined"
                :aria-describedby="describedby"
                :aria-invalid="invalid"
                data-test="meeting-application"
                @focus="openList"
                @click="openList"
                @input="typed"
                @keydown="onKey"
                @blur="leaveList"
              >
            </FormField>
            <AppIcon
              name="chevron-down"
              class="new-meeting-chevron"
            />
            <ul
              v-show="listOpen"
              :id="listId"
              role="listbox"
              aria-label="Candidatures envoyées"
              class="new-meeting-list"
              data-test="meeting-applications"
            >
              <li
                v-for="(a, index) in matches"
                :id="`${listId}-${a.id}`"
                :key="a.id"
                role="option"
                :aria-selected="a.id === chosen"
                :class="{ active: index === active }"
                :data-test="`meeting-application-${a.id}`"
                @mousedown.prevent="choose(a)"
              >
                {{ nameOf(a) }}
              </li>
              <li
                v-if="!matches.length"
                class="none"
                role="presentation"
              >
                Aucune candidature ne correspond
              </li>
            </ul>
          </div>
          <SegmentedControl
            v-model="format"
            :options="FORMATS"
            label="Format"
            full
          />
        </template>
        <p
          v-else-if="planned"
          class="new-meeting-note"
          data-test="meeting-replaces"
        >
          Ton rendez-vous ORP du {{ plannedLine.charAt(0).toLowerCase() + plannedLine.slice(1) }} est remplacé par celui-ci.
        </p>
        <div class="new-meeting-when">
          <DateTimeField
            :date="day"
            :time="time"
            :open="picking"
            compact
            outlined
            :aria-invalid="errors.when ? 'true' : undefined"
            @open="picking = $event"
          />
          <p
            v-if="errors.when"
            class="field-error"
            role="alert"
            data-test="meeting-when-error"
          >
            {{ errors.when }}
          </p>
        </div>
        <FormField
          v-if="kind === 'entreprise'"
          :key="format"
          v-slot="{ id, describedby, invalid }"
          :label="where.label"
        >
          <input
            :id="id"
            v-model="place"
            :type="where.type"
            :inputmode="where.mode"
            maxlength="1000"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="meeting-where"
          >
        </FormField>
        <FormField
          v-else
          v-slot="{ id, describedby, invalid }"
          label="Lieu ou lien"
          optional
        >
          <input
            :id="id"
            v-model="place"
            type="text"
            maxlength="200"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="meeting-where"
          >
        </FormField>
        <p
          v-if="kind === 'entreprise'"
          class="new-meeting-note"
          data-test="meeting-note"
        >
          La candidature passe en « Entretien ». Tu pourras t’entraîner la veille.
        </p>
        <p
          v-if="message"
          role="alert"
          class="notice error"
        >
          {{ message }}
        </p>
      </form>
    </div>
    <template
      v-if="!picking"
      #actions
    >
      <BusyButton
        type="submit"
        form="new-meeting-form"
        class="primary action-1"
        :busy="busy"
        busy-label="Ajout…"
        data-test="meeting-save"
      >
        Ajouter le rendez-vous
      </BusyButton>
    </template>
  </BottomSheet>
</template>

<style>
/* Maquette : 20 px entre les blocs (16 sur téléphone), champs de 56 px aux coins de 12, date et heure en 1,4 fr et
   1 fr, la phrase en 14/20, le bouton plein de 52 px sur toute la largeur. */
.new-meeting { --nm-52: 52px; --nm-20: 20px; --nm-14: 14px; --nm-lh: 20px; --nm-list: 264px; --nm-12: 12px; }
.new-meeting-form { display: flex; flex-direction: column; gap: var(--nm-20); }
.new-meeting-form .form-field { margin: 0; min-width: 0; }
.new-meeting-form input { width: 100%; min-width: 0; }
.new-meeting-when { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-2); }
.new-meeting-note { margin: 0; font-size: var(--nm-14); line-height: var(--nm-lh); color: var(--text-secondary); }
.new-meeting-combo { position: relative; }
.new-meeting-form .new-meeting-combo input { padding-right: calc(var(--space-8) + var(--space-3)); text-overflow: ellipsis; }
.new-meeting-chevron { position: absolute; z-index: 1; right: var(--space-4); top: var(--nm-20); width: var(--space-4); height: var(--space-4); color: var(--text-secondary); pointer-events: none; }
.new-meeting-list {
  position: absolute; z-index: 2; left: 0; right: 0; top: calc(100% + var(--space-1)); max-height: var(--nm-list); overflow-y: auto; margin: 0; padding: var(--space-1);
  list-style: none; background: var(--surface); border: 1px solid var(--line); border-radius: var(--nm-12); box-shadow: var(--shadow-menu);
}
.new-meeting-list li { display: flex; align-items: center; min-height: var(--target-min); padding: var(--space-1) var(--space-3); border-radius: var(--space-2); font-size: var(--font-label); cursor: pointer; overflow-wrap: anywhere; }
.new-meeting-list li.active { background: var(--primary-soft); }
.new-meeting-list li[aria-selected="true"] { font-weight: var(--weight-bold); }
.new-meeting-list li.none { color: var(--text-secondary); cursor: default; }
.new-meeting :is(.sheet-actions) > .primary { width: 100%; min-height: var(--nm-52); justify-content: center; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
@media (max-width: 820px) {
  .new-meeting-form { gap: var(--space-4); }
}
</style>
