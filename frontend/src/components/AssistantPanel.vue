<script setup lang="ts">
import SceneIllustration from "./SceneIllustration.vue";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type ChatAction, PROFILE_HEADER, storedProfile, UNAUTHORIZED_EVENT } from "../api/client";
import { dateInList } from "../dates";
import type { components } from "../api/schema";
import { blocks, readEvents } from "../assistantText";
import { focusBody, greetingText, suggestionsFor, useAssistant } from "../composables/useAssistant";
import { useDailyDose } from "../composables/useDailyDose";
import { announceDataChanged } from "../composables/useDataChanged";
import { pickerOpen, useDismissLayer, openLayerKind } from "../composables/useDismissLayer";
import { usePhone } from "../composables/usePhone";
import AppIcon from "./AppIcon.vue";
import BrandMark from "./BrandMark.vue";
import Composer from "./Composer.vue";
import CopyButton from "./CopyButton.vue";
import IconButton from "./IconButton.vue";
import InlineConfirm from "./InlineConfirm.vue";
import AssistantMascot, { type MascotMood } from "./AssistantMascot.vue";
import EngagementMoment from "./EngagementMoment.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import PlanLimit from "./PlanLimit.vue";
import { usePlan } from "../composables/usePlan";

type Conversation = components["schemas"]["ConversationOut"];
// Propositions de l'assistant (docs/52) : affichées sous sa réponse, faites sur un clic.
type Line = { role: "user" | "assistant"; content: string; error?: boolean; actions?: ChatAction[] };

const route = useRoute();
const router = useRouter();
const { available, open, focus, fresh, pending, check, setFocus } = useAssistant();
const suggestions = computed(() => suggestionsFor(String(route.name ?? ""), focus.value));
const lines = ref<Line[]>([]);
const conversationId = ref<number | null>(null);
const recent = ref<Conversation[]>([]);
const draft = ref("");
const busy = ref(false);
const scroller = ref<HTMLElement | null>(null);
const input = ref<{ focus: () => void } | null>(null);
const fab = ref<HTMLButtonElement | null>(null);
let controller: AbortController | null = null;

// Les visages de la mascotte (docs/99) : elle réfléchit pendant la réponse, puis « a trouvé »
// sur la réponse qui vient d'arriver (2 s dans l'en-tête, jusqu'à la question suivante en ligne).
const replying = ref<Line | null>(null);
const found = ref<Line | null>(null);
const headFound = ref(false);
let headTimer: ReturnType<typeof setTimeout> | undefined;
const headMood = computed<MascotMood>(() => (busy.value ? "thinking" : headFound.value ? "found" : "listening"));
const waiting = computed(() => busy.value && !replying.value?.content && !replying.value?.actions?.length);
function lineMood(line: Line): MascotMood {
  if (line.error) return "listening";
  if (busy.value && line === replying.value) return "thinking";
  return line === found.value ? "found" : "listening";
}
function showFound(reply: Line): void {
  found.value = reply;
  headFound.value = true;
  clearTimeout(headTimer);
  headTimer = setTimeout(() => (headFound.value = false), 2000);
}

// Ordinateur (maquette du 8 novembre, docs/143, D24) : le panneau latéral non modal de 480 px passe par la couche
// commune : un seul panneau à la fois, clic à l'extérieur et Échap le ferment, le focus revient au bouton flottant.
// Le bouton flottant se cache quand un autre panneau, les filtres ou le sélecteur de date sont ouverts.
const layer = useDismissLayer("assistant", () => (open.value = false));
watch(open, (value) => {
  if (value && !phone.value) layer.show(fab.value);
  else if (!value) layer.hide(false);
});
const fabHidden = computed(() => (openLayerKind.value !== null && openLayerKind.value !== "assistant") || pickerOpen.value > 0);
// Sous l'en-tête : le haut du panneau suit le bas de l'en-tête.
const panelTop = ref(0);
watch(open, (value) => {
  if (!value) return;
  panelTop.value = Math.max(0, document.querySelector<HTMLElement>("[data-test=app-header]")?.getBoundingClientRect().bottom ?? 0);
});

onMounted(() => void check());
onBeforeUnmount(() => clearTimeout(headTimer));

async function loadRecent(): Promise<void> {
  const { data } = await api.GET("/api/assistant/conversations");
  recent.value = data ?? [];
}

watch(open, async (value) => {
  if (!value) return;
  if (!conversationId.value) await loadRecent();
  await nextTick();
  input.value?.focus();
});
// Raccourci « Demander à l'assistant » : nouvelle discussion sur l'élément choisi.
watch(fresh, () => {
  if (lines.value.length && !busy.value) startOver();
});

function followLink(): void {
  // Sur téléphone, le panneau couvre la page : on le ferme pour la montrer.
  if (globalThis.matchMedia?.("(max-width: 640px)").matches) open.value = false;
}

function scrollDown(): void {
  void nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight;
  });
}
watch(() => lines.value.length, scrollDown);

function onKey(event: KeyboardEvent): void {
  if (event.key !== "Escape" || page.value) return;
  // Ne ferme que le panneau, pas l'offre ouverte derrière ; le focus revient au bouton flottant.
  event.stopPropagation();
  layer.hide(true);
}

async function resume(conversation: Conversation): Promise<void> {
  const { data } = await api.GET("/api/assistant/conversations/{conversation_id}", {
    params: { path: { conversation_id: conversation.id } },
  });
  if (!data) return;
  conversationId.value = data.id;
  const rows: Line[] = data.messages.map((m) => ({
    role: m.role === "user" ? "user" : "assistant",
    content: m.content,
  }));
  // Chaque proposition va sous la réponse qui l'a faite : la première écrite après elle.
  for (const action of data.actions) {
    const index = data.messages.findIndex((m) => m.role === "assistant" && m.created_at >= action.created_at);
    const line = rows[index >= 0 ? index : rows.length - 1];
    if (line) (line.actions ??= []).push(action);
  }
  lines.value = rows;
  scrollDown();
}

// Effacer ne se rattrape pas : la confirmation s'ouvre sur place, sous la tête (règles §4, Menu « ⋯ »).
const confirmingErase = ref(false);

function startOver(): void {
  confirmingErase.value = false;
  controller?.abort();
  conversationId.value = null;
  lines.value = [];
  found.value = null;
  void loadRecent();
  input.value?.focus();
}

async function erase(): Promise<void> {
  if (conversationId.value) {
    await api.DELETE("/api/assistant/conversations/{conversation_id}", {
      params: { path: { conversation_id: conversationId.value } },
    });
  }
  startOver();
}

// « Envoyer » reste actif (docs/29 §3) : sans question, il rend la main au champ.
const emptyHint = ref(false);

// Les messages du mois (docs/125) : le compteur suit chaque réponse.
const { reached, refresh: refreshPlan } = usePlan();

async function send(text: string = draft.value): Promise<void> {
  const question = text.trim();
  if (busy.value) return;
  if (!question) {
    emptyHint.value = true;
    input.value?.focus();
    return;
  }
  emptyHint.value = false;
  draft.value = "";
  busy.value = true;
  lines.value.push({ role: "user", content: question });
  lines.value.push({ role: "assistant", content: "" });
  const reply = lines.value[lines.value.length - 1] as Line;
  replying.value = reply;
  found.value = null;
  headFound.value = false;
  controller = new AbortController();
  const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "text/event-stream" };
  const profile = storedProfile();
  if (profile) headers[PROFILE_HEADER] = profile;
  try {
    const response = await fetch("/api/assistant/messages", {
      method: "POST",
      headers,
      credentials: "same-origin",
      signal: controller.signal,
      body: JSON.stringify({
        conversation_id: conversationId.value,
        text: question,
        page: route.path,
        focus: focusBody(focus.value),
      }),
    });
    if (response.status === 401) globalThis.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    if (!response.ok || !response.body) {
      const detail = (await response.json().catch(() => null)) as { detail?: unknown } | null;
      reply.content = typeof detail?.detail === "string" ? detail.detail : "L'assistant ne répond pas, réessaie.";
      reply.error = true;
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { events, rest } = readEvents(buffer);
      buffer = rest;
      for (const { event, data } of events) {
        if (event === "conversation") conversationId.value = Number(data.id);
        else if (event === "text") {
          reply.content += String(data.text ?? "");
          scrollDown();
        } else if (event === "action") {
          (reply.actions ??= []).push(data as unknown as ChatAction);
          scrollDown();
        }
        else if (event === "error") {
          lines.value.push({ role: "assistant", content: String(data.message ?? ""), error: true });
        }
      }
    }
  } catch (error) {
    if ((error as Error).name !== "AbortError" && !reply.content) {
      reply.content = "La connexion a été coupée, réessaie.";
      reply.error = true;
    }
  } finally {
    if (!reply.content && !reply.actions?.length) lines.value.splice(lines.value.indexOf(reply), 1);
    else if (!reply.error && lines.value[lines.value.length - 1] === reply) showFound(reply);
    busy.value = false;
    void refreshPlan();
    replying.value = null;
    controller = null;
    scrollDown();
  }
}

// Entrée envoie, Maj + Entrée passe à la ligne : le Composer s'en charge.
const { phone } = usePhone();

// La page Assistant du téléphone (docs/139 Q4, étape 11a) : le même panneau, sur toute la page, au-dessus de la
// barre du bas ; la discussion reste quand on change d'onglet. Un raccourci « Demander à l'assistant » y mène.
const page = computed(() => phone.value && route.name === "assistant");
// Les Réglages et les Notifications du téléphone (maquettes, Kevin, 6.11) : pages sans barre ni bouton flottant.
// Préparer (maquette du 8 novembre) : la lettre se retouche dans sa propre zone de saisie, le bouton reste masqué.
const quiet = computed(() => (phone.value && ["settings", "notifications"].includes(String(route.name))) || route.name === "preparation");
watch(open, (value) => {
  if (!value || !phone.value) return;
  open.value = false;
  void router.push({ name: "assistant" });
});

// Le premier message de la page (décision de Kevin du 2026-11-05, AS3) : écrit par l'app, sans IA, avec les
// chiffres de l'Accueil et le prénom des Coordonnées ; puis des réponses selon la situation. « Préparer la
// lettre » ouvre Ma candidature (AS4) ; les autres posent la question à l'Assistant.
type Reply = { label: string; to?: string };
const greeting = ref("");
const replies = ref<Reply[]>([]);
const dailyDose = useDailyDose();
const fallbackReplies = (): Reply[] => suggestionsFor("today", null).map((label) => ({ label }));
async function loadGreeting(): Promise<void> {
  try {
    const [, current, who] = await Promise.all([
      dailyDose.load(),
      api.GET("/api/offers", { params: { query: { view: "in_progress", sort: "activity", limit: 100 } } }),
      api.GET("/api/identity").catch(() => null),
    ]);
    const today = dailyDose.today.value;
    const name = who?.data?.name?.trim().split(/\s+/)[0] ?? "";
    const offers = dailyDose.triagePending.value ? dailyDose.dose.value.length : 0;
    greeting.value = greetingText(name, offers, today?.to_follow_up ?? 0);
    const list: Reply[] = [];
    const letter = (current.data?.items ?? []).find((offer) => offer.status === "preparing");
    if (letter) list.push({ label: `Préparer la lettre pour ${letter.company}`, to: `/candidatures/offres/${letter.id}/preparer` });
    if (today?.to_follow_up) list.push({ label: "Préparer les relances" });
    if (today?.orp_meeting_at) list.push({ label: "Préparer mon rendez-vous ORP" });
    replies.value = list.length ? list : fallbackReplies();
  } catch {
    greeting.value = greetingText("", 0, 0);
    replies.value = fallbackReplies();
  }
}
watch(
  page,
  (value) => {
    if (!value) return;
    if (!lines.value.length) void loadGreeting();
    if (!conversationId.value) void loadRecent();
  },
  { immediate: true },
);

// Une question posée d'ailleurs : envoyée dès que le panneau ou la page Assistant s'affiche.
watch(
  [pending, open, page],
  () => {
    const question = pending.value;
    if (!question || busy.value || !(open.value || page.value)) return;
    pending.value = null;
    void send(question);
  },
  { immediate: true },
);

// « Confirmer », « Non merci », « Annuler » : seul un clic change quelque chose (docs/52).
const deciding = ref<number | null>(null);
const celebrated = ref<number | null>(null);
const DECISIONS = {
  confirm: "/api/assistant/actions/{action_id}/confirm",
  decline: "/api/assistant/actions/{action_id}/decline",
  undo: "/api/assistant/actions/{action_id}/undo",
} as const;

async function decide(action: ChatAction, decision: keyof typeof DECISIONS): Promise<void> {
  deciding.value = action.id;
  try {
    const { data } = await api.POST(DECISIONS[decision], { params: { path: { action_id: action.id } } });
    if (!data) {
      action.note = "Impossible pour l'instant, réessaie.";
      return;
    }
    Object.assign(action, data);
    if (!data.note && decision !== "decline") announceDataChanged();
    // Une candidature confirmée en « Poste obtenu » (statut engagement) : le moment de fête (docs/60 §2.1).
    if (decision === "confirm" && data.state === "done" && data.kind === "application_status" && data.label.endsWith("« Poste obtenu »")) {
      celebrated.value = action.id;
    }
  } finally {
    deciding.value = null;
  }
}

const DONE_TEXT: Record<string, string> = {
  done: "Fait.",
  undone: "Annulé : remis comme avant.",
  declined: "Laissé tel quel.",
  stale: "Plus à faire : rien n'a été changé.",
};

// « Nouvelle discussion » visible, l'effacement dans « ⋯ » (docs/74), confirmé sur place.
const headItems: MoreMenuItem[] = [
  { label: "Effacer la discussion", test: "assistant-erase", icon: "trash", danger: true, run: () => (confirmingErase.value = true) },
];
</script>

<template>
  <template v-if="available">
    <button
      v-if="!open && !page && !quiet && !fabHidden"
      ref="fab"
      type="button"
      class="assistant-fab"
      aria-label="Ouvrir l'assistant"
      data-test="assistant-open"
      @click="open = true"
    >
      <AssistantMascot :size="28" />
      <span class="assistant-fab-label">Assistant</span>
    </button>
    <div
      v-if="open || page"
      :class="['assistant-panel', page ? 'assistant-page' : 'side-panel-modeless side-panel-480']"
      :role="page ? 'region' : 'complementary'"
      :aria-label="page ? 'Assistant' : undefined"
      :aria-labelledby="page ? undefined : 'assistant-title'"
      :style="page ? undefined : { top: `${panelTop}px` }"
      data-test="assistant-panel"
      @keydown="onKey"
    >
      <header class="assistant-head">
        <!-- La page : le logo et le titre, comme une page d'onglet (D11) ; le crayon ouvre une nouvelle discussion. -->
        <h1
          v-if="page"
          class="assistant-page-title"
        >
          <BrandMark :size="28" />Assistant
        </h1>
        <h2
          v-else
          id="assistant-title"
          class="assistant-title"
        >
          <AssistantMascot
            :size="32"
            :mood="headMood"
          />Assistant
        </h2>
        <div class="assistant-head-actions">
          <IconButton
            v-if="page"
            icon="pencil"
            label="Nouvelle discussion"
            data-test="assistant-new"
            @click="startOver"
          />
          <button
            v-else-if="lines.length"
            type="button"
            class="link side-panel-action"
            aria-label="Nouvelle discussion"
            data-test="assistant-new"
            @click="startOver"
          >
            Nouvelle
          </button>
          <MoreMenu
            v-if="lines.length"
            :items="headItems"
            label="Plus d'actions sur la discussion"
            test-id="assistant-more"
          />
          <IconButton
            v-if="!page"
            icon="close"
            label="Fermer l'assistant"
            data-test="assistant-close"
            @click="layer.hide(true)"
          />
        </div>
      </header>
      <InlineConfirm
        v-if="confirmingErase && lines.length"
        message="Effacer la discussion ? Elle ne pourra pas être retrouvée."
        confirm-label="Effacer"
        @confirm="erase"
        @cancel="confirmingErase = false"
        @keydown.esc.stop
      />

      <div
        ref="scroller"
        class="assistant-body"
        aria-live="polite"
      >
        <template v-if="!lines.length && page">
          <div
            v-if="greeting"
            class="assistant-line assistant"
            data-test="assistant-greeting"
          >
            <AssistantMascot
              :size="28"
              class="assistant-line-mascot"
            />
            <div class="assistant-bubble">
              <p>{{ greeting }}</p>
            </div>
          </div>
          <div
            v-if="greeting"
            class="assistant-replies"
          >
            <template
              v-for="reply in replies"
              :key="reply.label"
            >
              <RouterLink
                v-if="reply.to"
                :to="reply.to"
                class="assistant-reply"
                data-test="assistant-reply"
              >
                <span class="with-icon">{{ reply.label }}<AppIcon name="arrow-right" /></span>
              </RouterLink>
              <button
                v-else
                type="button"
                class="assistant-reply"
                data-test="assistant-reply"
                @click="send(reply.label)"
              >
                {{ reply.label }}
              </button>
            </template>
          </div>
        </template>
        <template v-else-if="!lines.length">
          <!-- Avant la première question (planche « Illustrations », règle §4). -->
          <SceneIllustration
            name="assistant-vide"
            class="spot assistant-spot"
            sizes="(max-width: 820px) 260px, 424px"
          />
          <p class="muted assistant-intro">
            Pose une question sur tes offres, candidatures ou preuves ORP. Il propose, tu confirmes.
          </p>
          <div class="assistant-suggestions">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              type="button"
              class="chip"
              data-test="assistant-suggestion"
              @click="send(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </template>
        <template v-if="!lines.length">
          <div
            v-if="recent.length"
            class="assistant-recent"
          >
            <p class="assistant-label">
              Discussions récentes
            </p>
            <button
              v-for="conversation in recent.slice(0, 6)"
              :key="conversation.id"
              type="button"
              class="assistant-recent-item"
              data-test="assistant-recent"
              @click="resume(conversation)"
            >
              <span>{{ conversation.title }}</span>
              <span class="muted">{{ dateInList(conversation.updated_at) }}</span>
            </button>
          </div>
        </template>

        <template
          v-for="(line, index) in lines"
          :key="index"
        >
          <!-- Pas de bulle vide (lot 11.3) : une réponse n'apparaît qu'avec son premier texte ou sa première action. -->
          <div
            v-if="line.role === 'user' || line.error || line.content || line.actions?.length"
            class="assistant-line"
            :class="[line.role, { error: line.error }]"
          >
            <!-- La mascotte devant chaque réponse (docs/97), sans cercle, 28 px (LISEZMOI du 8 novembre). -->
            <AssistantMascot
              v-if="line.role === 'assistant' && (line.content || line.actions?.length)"
              :size="28"
              :mood="lineMood(line)"
              class="assistant-line-mascot"
            />
            <p
              v-if="line.role === 'user' || line.error"
              class="assistant-plain"
            >
              {{ line.content }}
            </p>
            <div
              v-else
              class="assistant-bubble"
            >
              <template
                v-for="(block, b) in blocks(line.content)"
                :key="b"
              >
                <p v-if="block.kind === 'p'">
                  <template
                    v-for="(row, r) in block.lines"
                    :key="r"
                  >
                    <br v-if="r > 0">
                    <template
                      v-for="(part, p) in row"
                      :key="p"
                    >
                      <RouterLink
                        v-if="part.href && !part.external"
                        :to="part.href"
                        data-test="assistant-link"
                        @click="followLink"
                      >
                        {{ part.text }}
                      </RouterLink>
                      <a
                        v-else-if="part.href"
                        :href="part.href"
                        target="_blank"
                        rel="noopener noreferrer"
                      >{{ part.text }}<span class="visually-hidden"> (nouvel onglet)</span></a>
                      <strong v-else-if="part.bold">{{ part.text }}</strong>
                      <template v-else>
                        {{ part.text }}
                      </template>
                    </template>
                  </template>
                </p>
                <component
                  :is="block.ordered ? 'ol' : 'ul'"
                  v-else-if="block.kind === 'list'"
                >
                  <li
                    v-for="(item, i) in block.items"
                    :key="i"
                  >
                    <template
                      v-for="(part, p) in item"
                      :key="p"
                    >
                      <RouterLink
                        v-if="part.href && !part.external"
                        :to="part.href"
                        data-test="assistant-link"
                        @click="followLink"
                      >
                        {{ part.text }}
                      </RouterLink>
                      <a
                        v-else-if="part.href"
                        :href="part.href"
                        target="_blank"
                        rel="noopener noreferrer"
                      >{{ part.text }}<span class="visually-hidden"> (nouvel onglet)</span></a>
                      <strong v-else-if="part.bold">{{ part.text }}</strong>
                      <template v-else>
                        {{ part.text }}
                      </template>
                    </template>
                  </li>
                </component>
                <div
                  v-else
                  class="assistant-copy"
                >
                  <pre>{{ block.text }}</pre>
                  <CopyButton
                    :value="block.text"
                    test-id="assistant-copy"
                  />
                </div>
              </template>
            </div>
            <div
              v-for="action in line.actions ?? []"
              :key="action.id"
              :class="['assistant-action', action.state]"
              data-test="assistant-action"
            >
              <EngagementMoment
                v-if="celebrated === action.id && action.state === 'done'"
                @close="celebrated = null"
              />
              <p class="assistant-action-label">
                {{ action.label }}
              </p>
              <div
                v-if="action.state === 'proposed'"
                class="assistant-action-buttons"
              >
                <button
                  type="button"
                  class="secondary small"
                  :disabled="deciding === action.id"
                  data-test="assistant-action-decline"
                  @click="decide(action, 'decline')"
                >
                  Non merci
                </button>
                <button
                  type="button"
                  class="primary small"
                  :disabled="deciding === action.id"
                  data-test="assistant-action-confirm"
                  @click="decide(action, 'confirm')"
                >
                  Confirmer
                </button>
              </div>
              <p
                v-if="action.state === 'proposed' && action.note"
                class="hint"
                role="status"
              >
                {{ action.note }}
              </p>
              <p
                v-else-if="action.state !== 'proposed'"
                class="assistant-action-state"
                role="status"
              >
                <span>{{ action.note ?? DONE_TEXT[action.state] }}</span>
                <button
                  v-if="action.state === 'done'"
                  type="button"
                  class="link"
                  :disabled="deciding === action.id"
                  data-test="assistant-action-undo"
                  @click="decide(action, 'undo')"
                >
                  Annuler
                </button>
              </p>
            </div>
          </div>
        </template>
        <!-- L'Assistant écrit (maquette du 8 novembre, lot 11.3) : le logo sans cercle et trois points dans une bulle de
             la forme d'une réponse, jusqu'au premier texte ; la bulle de la réponse prend alors sa place. -->
        <div
          v-if="waiting"
          class="assistant-line assistant assistant-waiting"
          role="status"
          aria-live="polite"
          data-test="assistant-waiting"
        >
          <AssistantMascot
            :size="28"
            mood="thinking"
            class="assistant-line-mascot"
          />
          <span
            class="assistant-bubble assistant-dots"
            aria-hidden="true"
          ><span /><span /><span /></span>
          <span class="visually-hidden">L'Assistant écrit…</span>
        </div>
      </div>

      <p
        v-if="focus?.label"
        class="assistant-focus"
        data-test="assistant-focus"
      >
        <span>À propos de : {{ focus.label }}</span>
        <IconButton
          icon="close"
          class="chip-remove"
          label="Ne plus parler de cet élément"
          data-test="assistant-focus-clear"
          @click="setFocus(null)"
        />
      </p>
      <p
        v-if="emptyHint && !draft.trim()"
        class="field-error assistant-empty"
        role="status"
      >
        Écris ta question.
      </p>
      <PlanLimit usage="chat" />
      <!-- La zone de saisie commune (Composer, D25) : une ligne, sans « + » (pas de pièce jointe à l'IA sans règle,
           I-1 et E-5) ni micro (dictée masquée, O-4). -->
      <div class="assistant-form">
        <Composer
          ref="input"
          v-model="draft"
          :placeholder="page ? 'Demande quelque chose…' : 'Demander à l\'Assistant'"
          send-label="Envoyer"
          :busy="busy || reached('chat')"
          data-test="assistant-input"
          @send="send"
        />
      </div>
      <!-- AS7 : sous le champ, sur la page comme dans le panneau. -->
      <p
        class="assistant-disclaimer"
        data-test="assistant-disclaimer"
      >
        L'Assistant peut se tromper. Relis toujours avant d'envoyer.
      </p>
    </div>
  </template>
</template>
