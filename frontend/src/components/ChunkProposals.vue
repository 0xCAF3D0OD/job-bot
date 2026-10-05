<script setup lang="ts">
import { computed, ref } from "vue";

import { api, type Chunk, type ChunkKind, type ChunkProposal } from "../api/client";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{
  documentId: number;
  documentName: string;
  proposals: ChunkProposal[];
  existing: Chunk[];
}>();
const emit = defineEmits<{ close: []; saved: [count: number] }>();

const KIND_LABELS: Record<ChunkKind, string> = {
  experience: "Expérience",
  competence: "Compétence",
  formation: "Formation",
  preference: "Préférence",
  redhibitoire: "Rédhibitoire",
  ton: "Ton",
};

// Copie modifiable ; les doublons sont décochés par défaut.
const items = ref(
  props.proposals.map((p) => ({ ...p, tags: [...p.tags], selected: p.duplicate_of === null })),
);
const saving = ref(false);
const error = ref("");
const selectedCount = computed(() => items.value.filter((i) => i.selected).length);

function duplicateTitle(id: number | null): string | null {
  if (id === null) return null;
  return props.existing.find((c) => c.id === id)?.title ?? null;
}

async function save(): Promise<void> {
  saving.value = true;
  error.value = "";
  let created = 0;
  try {
    for (const item of items.value.filter((i) => i.selected)) {
      const { data } = await api.POST("/api/profile-chunks", {
        body: {
          kind: item.kind,
          title: item.title,
          content: item.content,
          tags: item.tags,
          active: true,
          document_id: props.documentId,
        },
      });
      if (!data) throw new Error("refusé");
      created += 1;
    }
    emit("saved", created);
  } catch {
    error.value = `${created} bloc(s) ajouté(s), puis un refus : vérifie titres et contenus.`;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div
    class="overlay"
    @click.self="emit('close')"
  >
    <form
      class="form-card editor proposals"
      data-test="proposals"
      @submit.prevent="save"
    >
      <h3>Blocs proposés pour « {{ documentName }} »</h3>
      <p class="hint">
        Relis et corrige chaque bloc, puis coche ceux à ajouter. Les blocs qui ressemblent à un bloc existant sont
        décochés.
      </p>
      <ul class="proposal-list">
        <li
          v-for="(item, index) in items"
          :key="index"
          :class="['proposal', { off: !item.selected }]"
          data-test="proposal"
        >
          <label class="check proposal-check">
            <input
              v-model="item.selected"
              type="checkbox"
              :aria-label="`Ajouter « ${item.title} »`"
            >
            <span class="badge">{{ KIND_LABELS[item.kind] }}</span>
            <span
              v-if="duplicateTitle(item.duplicate_of)"
              class="badge reason"
            >ressemble à : {{ duplicateTitle(item.duplicate_of) }}</span>
          </label>
          <input
            v-model="item.title"
            type="text"
            maxlength="200"
            :aria-label="`Titre du bloc ${index + 1}`"
            required
          >
          <textarea
            v-model="item.content"
            rows="3"
            :aria-label="`Contenu du bloc ${index + 1}`"
            required
          />
          <span
            v-if="item.tags.length"
            class="detail"
          >{{ item.tags.map((t) => `#${t}`).join(" ") }}</span>
        </li>
      </ul>
      <p
        v-if="error"
        class="notice error"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          :disabled="saving || !selectedCount"
          data-test="add-proposals"
        >
          Ajouter {{ selectedCount }} bloc(s) <AppIcon name="chevron" />
        </button>
        <button
          type="button"
          class="secondary"
          @click="emit('close')"
        >
          Annuler
        </button>
      </div>
    </form>
  </div>
</template>
