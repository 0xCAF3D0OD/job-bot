<script setup lang="ts">
import Illustration from "./Illustration.vue";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type ChatAction, PROFILE_HEADER, storedProfile, UNAUTHORIZED_EVENT } from "../api/client";
import type { components } from "../api/schema";
import { blocks, readEvents } from "../assistantText";
import { focusBody, suggestionsFor, useAssistant } from "../composables/useAssistant";
import { announceDataChanged } from "../composables/useDataChanged";
import { usePhone } from "../composables/usePhone";
import CopyLabel from "./CopyLabel.vue";
import IconButton from "./IconButton.vue";
import AssistantMascot, { type MascotMood } from "./AssistantMascot.vue";
import EngagementMoment from "./EngagementMoment.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import PlanLimit from "./PlanLimit.vue";
import { usePlan } from "../composables/usePlan";

type Conversation = components["schemas"]["ConversationOut"];
// Propositions de l'assistant (docs/52) : affichées sous sa réponse, faites sur un clic.
type Line = { role: "user" | "assistant"; content: string; error?: boolean; actions?: ChatAction[] };

const route = useRoute();
const { available, open, focus, fresh, check, setFocus } = useAssistant();
const suggestions = computed(() => suggestionsFor(String(route.name ?? ""), focus.value));
const lines = ref<Line[]>([]);
const conversationId = ref<number | null>(null);
const recent = ref<Conversation[]>([]);
const draft = ref("");
const busy = ref(false);
const reading = ref<string | null>(null);
const copied = ref<number | null>(null);
const scroller = ref<HTMLElement | null>(null);
const input = ref<HTMLTextAreaElement | null>(null);
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
  if (event.key !== "Escape") return;
  // Ne ferme que le panneau, pas l'offre ouverte derrière.
  event.stopPropagation();
  open.value = false;
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

function startOver(): void {
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
          reading.value = null;
          reply.content += String(data.text ?? "");
          scrollDown();
        } else if (event === "tool") reading.value = String(data.label ?? "");
        else if (event === "action") {
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
    reading.value = null;
    controller = null;
    scrollDown();
  }
}

function onEnter(event: KeyboardEvent): void {
  if (event.shiftKey || event.isComposing) return;
  event.preventDefault();
  void send();
}

// Téléphone (retour du 2026-10-15) : pas de bouton « Envoyer », la touche Entrée du clavier
// envoie (étiquetée « Envoyer » grâce à enterkeyhint). Certains claviers Android ne
// signalent pas la touche : le retour à la ligne demandé est alors intercepté ici.
const { phone } = usePhone();

function onBeforeInput(event: InputEvent): void {
  if (!phone.value) return; // ordinateur : Maj+Entrée va à la ligne
  if (event.inputType !== "insertLineBreak" && event.inputType !== "insertParagraph") return;
  event.preventDefault();
  void send();
}

async function copy(text: string, index: number): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    copied.value = index;
    setTimeout(() => {
      if (copied.value === index) copied.value = null;
    }, 1500);
  } catch {
    copied.value = null;
  }
}

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

function day(value: string): string {
  return new Date(value).toLocaleDateString("fr-CH", { day: "numeric", month: "short" });
}

// « Nouvelle discussion » visible, l'effacement dans « ⋯ » (docs/74).
const headItems: MoreMenuItem[] = [
  { label: "Effacer la discussion", test: "assistant-erase", danger: true, run: () => void erase() },
];
</script>

<template>
  <template v-if="available">
    <button
      v-if="!open"
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
      v-else
      class="assistant-panel"
      role="dialog"
      aria-label="Assistant"
      data-test="assistant-panel"
      @keydown="onKey"
    >
      <header class="assistant-head">
        <strong class="assistant-title"><AssistantMascot
          :size="26"
          :mood="headMood"
        />Assistant</strong>
        <div class="assistant-head-actions">
          <button
            v-if="lines.length"
            type="button"
            class="link"
            data-test="assistant-new"
            @click="startOver"
          >
            Nouvelle discussion
          </button>
          <MoreMenu
            v-if="lines.length"
            :items="headItems"
            label="Actions sur la discussion"
            test-id="assistant-more"
          />
          <IconButton
            icon="close"
            label="Fermer l'assistant"
            data-test="assistant-close"
            @click="open = false"
          />
        </div>
      </header>

      <div
        ref="scroller"
        class="assistant-body"
        aria-live="polite"
      >
        <template v-if="!lines.length">
          <!-- Avant la première question (planche « Illustrations », règle §4). -->
          <Illustration
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
              <span class="muted">{{ day(conversation.updated_at) }}</span>
            </button>
          </div>
        </template>

        <div
          v-for="(line, index) in lines"
          :key="index"
          class="assistant-line"
          :class="[line.role, { error: line.error }]"
        >
          <!-- La mascotte devant chaque réponse (docs/97). -->
          <AssistantMascot
            v-if="line.role === 'assistant' && (line.content || line.actions?.length)"
            :size="24"
            :mood="lineMood(line)"
            class="assistant-line-mascot"
          />
          <p
            v-if="line.role === 'user' || line.error"
            class="assistant-plain"
          >
            {{ line.content }}
          </p>
          <template v-else>
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
                    >{{ part.text }}</a>
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
                    >{{ part.text }}</a>
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
                <button
                  type="button"
                  class="link"
                  data-test="assistant-copy"
                  @click="copy(block.text, index * 100 + b)"
                >
                  <CopyLabel :done="copied === index * 100 + b" />
                </button>
              </div>
            </template>
          </template>
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
        <p
          v-if="busy"
          class="muted assistant-status"
          data-test="assistant-status"
        >
          <AssistantMascot
            v-if="waiting"
            :size="24"
            mood="thinking"
          />
          {{ reading ? `Je consulte ${reading}…` : "…" }}
        </p>
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
      <form
        class="assistant-form"
        @submit.prevent="send()"
      >
        <textarea
          ref="input"
          v-model="draft"
          rows="2"
          maxlength="4000"
          :placeholder="phone ? 'Écris ou dicte ta question…' : 'Écris ta question…'"
          aria-label="Ta question"
          enterkeyhint="send"
          data-test="assistant-input"
          @keydown.enter="onEnter"
          @beforeinput="onBeforeInput"
        />
        <button
          type="submit"
          class="primary small assistant-send"
          :disabled="busy || reached('chat')"
          data-test="assistant-send"
        >
          Envoyer
        </button>
      </form>
    </div>
  </template>
</template>
