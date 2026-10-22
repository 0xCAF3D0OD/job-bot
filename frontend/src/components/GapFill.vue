<script setup lang="ts">
import { ref } from "vue";

import { api } from "../api/client";
import { gapSkill } from "../format";
import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";
import { usePlan } from "../composables/usePlan";

const { aiNote } = usePlan();

// « Je l'ai » sur un manque de la note (docs/121 §C.3) : une compétence que la personne a
// sans l'avoir écrite. Le bloc se relit sur place (le nom, une phrase qui le prouve), puis
// rejoint le profil ; l'offre est renotée aussitôt.
const props = defineProps<{ offerId: number; gap: string }>();
const emit = defineEmits<{ added: [] }>();

const open = ref(false);
const busy = ref(false);
const error = ref("");
const title = ref("");
const content = ref("");

function start(): void {
  title.value = (gapSkill(props.gap) ?? props.gap).slice(0, 200);
  content.value = "";
  error.value = "";
  open.value = true;
}

async function add(): Promise<void> {
  if (!title.value.trim() || !content.value.trim()) return;
  busy.value = true;
  error.value = "";
  try {
    const { data } = await api.POST("/api/offers/{offer_id}/gap-block", {
      params: { path: { offer_id: props.offerId } },
      body: { title: title.value.trim(), content: content.value.trim() },
    });
    if (!data) {
      error.value = "Le bloc n'a pas pu être ajouté. Réessaie.";
      return;
    }
    open.value = false;
    emit("added");
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <button
    v-if="!open"
    type="button"
    class="link gap-fill-open"
    data-test="gap-fill"
    @click="start"
  >
    Je l'ai
  </button>
  <form
    v-else
    class="gap-fill"
    data-test="gap-fill-form"
    @submit.prevent="add"
  >
    <label>Compétence
      <input
        v-model="title"
        type="text"
        maxlength="200"
        required
        data-test="gap-fill-title"
      >
    </label>
    <label>Où et comment, en une phrase
      <input
        v-model="content"
        type="text"
        maxlength="300"
        required
        placeholder="Trois ans d'infrastructure en Terraform chez…"
        data-test="gap-fill-content"
      >
    </label>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="pill-row">
      <button
        type="submit"
        class="primary"
        :disabled="busy || !title.trim() || !content.trim()"
        data-test="gap-fill-add"
      >
        <span class="with-icon"><AppIcon name="ai" /><HoverNote :text="aiNote('Environ 0,003 $.', undefined, 'L\'offre est renotée avec ce bloc.')">Ajouter au profil</HoverNote></span>
      </button>
      <button
        type="button"
        class="link"
        @click="open = false"
      >
        Annuler
      </button>
    </div>
  </form>
</template>
