<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, PROFILE_HEADER, storedProfile, UNAUTHORIZED_EVENT } from "../api/client";
import type { components } from "../api/schema";
import { blocks, readEvents } from "../assistantText";

type Conversation = components["schemas"]["ConversationOut"];
type Line = { role: "user" | "assistant"; content: string; error?: boolean };

// Suggestions de départ ; celles propres à chaque page viendront avec la PR b (docs/24 §6).
const SUGGESTIONS = ["Que faire aujourd'hui ?", "Où en suis-je pour l'ORP ce mois-ci ?", "Comment créer mes alertes ?"];

const route = useRoute();
const available = ref(false);
const open = ref(false);
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

onMounted(async () => {
  const { data } = await api.GET("/api/assistant/status");
  available.value = Boolean(data?.available);
});

async function loadRecent(): Promise<void> {
  const { data } = await api.GET("/api/assistant/conversations");
  recent.value = data ?? [];
}

async function toggle(): Promise<void> {
  open.value = !open.value;
  if (!open.value) return;
  if (!conversationId.value) await loadRecent();
  await nextTick();
  input.value?.focus();
}

function scrollDown(): void {
  void nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight;
  });
}
watch(() => lines.value.length, scrollDown);

function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") open.value = false;
}

async function resume(conversation: Conversation): Promise<void> {
  const { data } = await api.GET("/api/assistant/conversations/{conversation_id}", {
    params: { path: { conversation_id: conversation.id } },
  });
  if (!data) return;
  conversationId.value = data.id;
  lines.value = data.messages.map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content }));
  scrollDown();
}

function startOver(): void {
  controller?.abort();
  conversationId.value = null;
  lines.value = [];
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

async function send(text: string = draft.value): Promise<void> {
  const question = text.trim();
  if (!question || busy.value) return;
  draft.value = "";
  busy.value = true;
  lines.value.push({ role: "user", content: question });
  lines.value.push({ role: "assistant", content: "" });
  const reply = lines.value[lines.value.length - 1] as Line;
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
      body: JSON.stringify({ conversation_id: conversationId.value, text: question, page: route.fullPath }),
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
    if (!reply.content) lines.value.splice(lines.value.indexOf(reply), 1);
    busy.value = false;
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

function day(value: string): string {
  return new Date(value).toLocaleDateString("fr-CH", { day: "numeric", month: "short" });
}
</script>

<template>
  <template v-if="available">
    <button
      v-if="!open"
      type="button"
      class="assistant-fab"
      aria-label="Ouvrir l'assistant"
      data-test="assistant-open"
      @click="toggle"
    >
      <span
        class="assistant-fab-dot"
        aria-hidden="true"
      />
      Assistant
    </button>
    <aside
      v-else
      class="assistant-panel"
      role="dialog"
      aria-label="Assistant"
      data-test="assistant-panel"
      @keydown="onKey"
    >
      <header class="assistant-head">
        <strong>Assistant</strong>
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
          <button
            v-if="lines.length"
            type="button"
            class="link danger"
            data-test="assistant-erase"
            @click="erase"
          >
            Effacer
          </button>
          <button
            type="button"
            class="assistant-close"
            aria-label="Fermer l'assistant"
            data-test="assistant-close"
            @click="open = false"
          >
            ×
          </button>
        </div>
      </header>

      <div
        ref="scroller"
        class="assistant-body"
        aria-live="polite"
      >
        <template v-if="!lines.length">
          <p class="muted assistant-intro">
            Pose une question sur la plateforme ou sur tes données : offres, candidatures, preuves ORP, entretiens.
            L'assistant lit et conseille, il ne modifie rien.
          </p>
          <div class="assistant-suggestions">
            <button
              v-for="suggestion in SUGGESTIONS"
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
                    <strong v-if="part.bold">{{ part.text }}</strong>
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
                    <strong v-if="part.bold">{{ part.text }}</strong>
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
                  {{ copied === index * 100 + b ? "Copié" : "Copier" }}
                </button>
              </div>
            </template>
          </template>
        </div>
        <p
          v-if="busy"
          class="muted assistant-status"
          data-test="assistant-status"
        >
          {{ reading ? `Je consulte ${reading}…` : "…" }}
        </p>
      </div>

      <form
        class="assistant-form"
        @submit.prevent="send()"
      >
        <textarea
          ref="input"
          v-model="draft"
          rows="2"
          maxlength="4000"
          placeholder="Écris ta question…"
          aria-label="Ta question"
          data-test="assistant-input"
          @keydown.enter="onEnter"
        />
        <button
          type="submit"
          class="primary small"
          :disabled="busy || !draft.trim()"
          data-test="assistant-send"
        >
          Envoyer
        </button>
      </form>
    </aside>
  </template>
</template>
