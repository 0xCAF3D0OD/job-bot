<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId } from "vue";

import AppIcon from "./AppIcon.vue";
import { useDismissLayer } from "../composables/useDismissLayer";
import { DICTATION_ALLOWED, type ComposerAttachment, type ComposerItem } from "../composer";

// La zone de saisie unique (maquette du 8 novembre, docs/143, D25) : pour tout message libre envoyé tel quel
// (Assistant, retouche de la lettre, ajout d'une offre, texte d'une annonce). Une ligne : une pilule avec +, le
// champ, le micro et Envoyer. Plusieurs lignes : le texte en haut, + et Envoyer sur la barre du bas. Entrée envoie,
// Maj + Entrée passe à la ligne ; le champ grandit jusqu'à 6 lignes (field-sizing, ou useAutoGrow), puis défile.
// Les champs de formulaire restent des champs de formulaire (FormField).

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder: string;
    rows?: number;
    mic?: boolean;
    sendLabel?: string;
    plusItems?: ComposerItem[];
    plusDirection?: "up" | "down";
    minChars?: number;
    attachments?: ComposerAttachment[];
    // Les fichiers acceptés au glisser-déposer (« application/pdf,image/png ») ; vide : aucun.
    accept?: string;
    busy?: boolean;
    // La suite du compteur (« la flèche enregistre et refait la note », maquette OffreProvisoire).
    counterHint?: string;
    // La boîte de l'Assistant (prompt du 10 novembre, PR 19 ; maquettes Assistant et AssistantOrdinateur, comme la
    // zone de saisie de Claude) : le texte en haut, dès une ligne ; + à gauche, micro et Envoyer à droite en dessous.
    // Envoyer reste visible, gris et `aria-disabled` tant qu'il n'y a rien à envoyer.
    stacked?: boolean;
  }>(),
  { rows: 1, mic: false, sendLabel: "Envoyer", plusItems: () => [], plusDirection: "up", minChars: 0, attachments: () => [], accept: "", busy: false, counterHint: "", stacked: false },
);
const emit = defineEmits<{
  "update:modelValue": [value: string];
  send: [text: string];
  attach: [item: string | File];
  remove: [id: string];
}>();

const area = ref<HTMLTextAreaElement | null>(null);
const plusButton = ref<HTMLButtonElement | null>(null);
const menuId = useId();
const counterId = useId();
const menu = useDismissLayer("composer");
const dragging = ref(false);
const multi = computed(() => props.rows > 1 && !props.stacked);
const length = computed(() => props.modelValue.trim().length);
const canSend = computed(() => {
  if (props.busy) return false;
  if (props.minChars > 0) return length.value >= props.minChars;
  return length.value > 0 || props.attachments.length > 0;
});
const showMic = computed(() => props.mic && DICTATION_ALLOWED && speech() !== null);

function speech(): (new () => { lang: string; onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null; start: () => void }) | null {
  const w = globalThis as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as ReturnType<typeof speech>;
}

function dictate(): void {
  const Recognition = speech();
  if (!Recognition) return;
  const recognition = new Recognition();
  recognition.lang = "fr-CH";
  recognition.onresult = (event) => {
    const text = Array.from(event.results).map((result) => result[0]?.transcript ?? "").join(" ");
    emit("update:modelValue", `${props.modelValue}${props.modelValue ? " " : ""}${text}`.trim());
  };
  recognition.start();
}

function send(): void {
  if (!canSend.value) return;
  emit("send", props.modelValue.trim());
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  send();
}

function pick(item: ComposerItem): void {
  menu.hide(true);
  emit("attach", item.id);
}

async function toggleMenu(): Promise<void> {
  menu.toggle(plusButton.value);
  if (menu.open.value) {
    await nextTick();
    document.getElementById(menuId)?.querySelector<HTMLElement>("[role=menuitem]")?.focus();
  }
}

// Flèches entre les entrées du menu (règles « Panneaux et menus »).
function onMenuKeydown(event: KeyboardEvent): void {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  event.preventDefault();
  const items = [...(document.getElementById(menuId)?.querySelectorAll<HTMLElement>("[role=menuitem]") ?? [])];
  const at = items.indexOf(document.activeElement as HTMLElement);
  const next = (at + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
  items[next]?.focus();
}

function accepts(file: File): boolean {
  if (!props.accept) return false;
  return props.accept.split(",").some((type) => {
    const wanted = type.trim();
    return wanted.endsWith("/*") ? file.type.startsWith(wanted.slice(0, -1)) : file.type === wanted;
  });
}
function onDragOver(event: DragEvent): void {
  if (!props.accept || !event.dataTransfer?.types.includes("Files")) return;
  event.preventDefault();
  dragging.value = true;
}
function onDrop(event: DragEvent): void {
  dragging.value = false;
  if (!props.accept) return;
  event.preventDefault();
  for (const file of Array.from(event.dataTransfer?.files ?? [])) if (accepts(file)) emit("attach", file);
}

// Un clic dans la fenêtre hors du menu le ferme (la couche commune est sous les fenêtres modales).
function onDocumentClick(event: MouseEvent): void {
  if (!menu.open.value) return;
  const target = event.target as Node;
  if (document.getElementById(menuId)?.contains(target) || plusButton.value?.contains(target)) return;
  menu.hide(false);
}
onMounted(() => document.addEventListener("click", onDocumentClick, true));
onBeforeUnmount(() => document.removeEventListener("click", onDocumentClick, true));

defineExpose({ focus: () => area.value?.focus() });
</script>

<template>
  <div
    :class="['composer', stacked ? 'composer-stacked' : multi ? 'composer-multi' : 'composer-pill', { 'composer-drag': dragging }]"
    data-test="composer"
    @dragover="onDragOver"
    @dragleave="dragging = false"
    @drop="onDrop"
  >
    <div
      v-if="menu.open.value"
      :id="menuId"
      role="menu"
      :aria-label="plusItems.length ? 'Joindre' : undefined"
      :class="['composer-menu', `composer-menu-${plusDirection}`]"
      data-test="composer-menu"
      @keydown="onMenuKeydown"
    >
      <button
        v-for="item in plusItems"
        :key="item.id"
        type="button"
        role="menuitem"
        class="composer-menu-item"
        :data-test="`composer-item-${item.id}`"
        @click="pick(item)"
      >
        <AppIcon :name="item.icon" />
        <span>
          <span class="composer-menu-label">{{ item.label }}</span>
          <span
            v-if="item.hint"
            class="composer-menu-hint"
          >{{ item.hint }}</span>
        </span>
      </button>
    </div>
    <ul
      v-if="attachments.length"
      class="composer-files"
      aria-label="Pièces jointes"
    >
      <li
        v-for="file in attachments"
        :key="file.id"
        class="composer-file"
      >
        <AppIcon name="file" />
        <span>{{ file.label }}</span>
        <button
          type="button"
          class="composer-file-remove"
          :aria-label="`Retirer ${file.label}`"
          :data-test="`composer-remove-${file.id}`"
          @click="emit('remove', file.id)"
        >
          <AppIcon name="close" />
        </button>
      </li>
    </ul>
    <div class="composer-row">
      <button
        v-if="plusItems.length && !multi && !stacked"
        ref="plusButton"
        type="button"
        class="composer-icon"
        aria-label="Joindre un fichier"
        aria-haspopup="menu"
        :aria-expanded="menu.open.value"
        :aria-controls="menu.open.value ? menuId : undefined"
        data-test="composer-plus"
        @click="toggleMenu"
      >
        <AppIcon name="plus" />
      </button>
      <textarea
        ref="area"
        class="composer-input"
        :rows="rows"
        :value="modelValue"
        :placeholder="placeholder"
        :aria-label="placeholder"
        :aria-describedby="minChars > 0 ? counterId : undefined"
        data-test="composer-input"
        @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
        @keydown="onKeydown"
      />
      <template v-if="!multi && !stacked">
        <button
          v-if="showMic"
          type="button"
          class="composer-icon"
          aria-label="Dicter"
          data-test="composer-mic"
          @click="dictate"
        >
          <AppIcon name="mic" />
        </button>
        <button
          type="button"
          class="composer-send"
          :aria-label="sendLabel"
          :disabled="!canSend"
          data-test="composer-send"
          @click="send"
        >
          <AppIcon name="arrow-up" />
        </button>
      </template>
    </div>
    <div
      v-if="multi"
      class="composer-bar"
    >
      <button
        v-if="plusItems.length"
        ref="plusButton"
        type="button"
        class="composer-icon"
        aria-label="Joindre un fichier"
        aria-haspopup="menu"
        :aria-expanded="menu.open.value"
        :aria-controls="menu.open.value ? menuId : undefined"
        data-test="composer-plus"
        @click="toggleMenu"
      >
        <AppIcon name="plus" />
      </button>
      <span class="composer-spacer" />
      <button
        type="button"
        class="composer-send"
        :aria-label="sendLabel"
        :disabled="!canSend"
        data-test="composer-send"
        @click="send"
      >
        <AppIcon name="arrow-up" />
      </button>
    </div>
    <div
      v-if="stacked"
      class="composer-bar composer-stacked-bar"
    >
      <button
        v-if="plusItems.length"
        ref="plusButton"
        type="button"
        class="composer-icon"
        aria-label="Joindre un fichier"
        aria-haspopup="menu"
        :aria-expanded="menu.open.value"
        :aria-controls="menu.open.value ? menuId : undefined"
        data-test="composer-plus"
        @click="toggleMenu"
      >
        <AppIcon name="plus" />
      </button>
      <span class="composer-spacer" />
      <button
        v-if="showMic"
        type="button"
        class="composer-icon"
        aria-label="Dicter"
        data-test="composer-mic"
        @click="dictate"
      >
        <AppIcon name="mic" />
      </button>
      <button
        type="button"
        class="composer-send composer-send-round"
        :aria-label="sendLabel"
        :aria-disabled="canSend ? undefined : 'true'"
        data-test="composer-send"
        @click="send"
      >
        <span class="composer-send-dot"><AppIcon name="arrow-up" /></span>
      </button>
    </div>
    <p
      v-if="minChars > 0"
      :id="counterId"
      class="composer-counter"
      aria-live="polite"
      data-test="composer-counter"
    >
      {{ length < minChars ? `${length} caractères, ${minChars} au moins` : `${length} caractères` }}{{ counterHint ? ` · ${counterHint}` : "" }}
    </p>
  </div>
</template>
