<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, QUIET, type Chunk, type ChunkKind, type ChunkProposal } from "../api/client";
import { plural } from "../format";
import BusyButton from "./BusyButton.vue";
import FormField from "./FormField.vue";

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
// « Tes coordonnées » (B, décision de Kevin du 16.11) : en tête, les coordonnées trouvées en haut du CV (sur le
// serveur, sans IA), seulement pour les champs encore vides du profil ; modifiables, enregistrées avec « Ajouter N
// éléments » et jamais avant. Un champ déjà rempli n'est pas proposé, donc jamais écrasé.
const CONTACT_FIELDS = [
  { key: "name", label: "Prénom et nom", autocomplete: "name", type: "text" },
  { key: "street", label: "Rue", autocomplete: "street-address", type: "text" },
  { key: "postcode", label: "NPA", autocomplete: "postal-code", type: "text" },
  { key: "city", label: "Localité", autocomplete: "address-level2", type: "text" },
  { key: "phone", label: "Téléphone", autocomplete: "tel", type: "tel" },
  { key: "email", label: "E-mail", autocomplete: "email", type: "email" },
] as const;
type ContactKey = (typeof CONTACT_FIELDS)[number]["key"];
const contact = ref<{ selected: boolean; values: Partial<Record<ContactKey, string>> } | null>(null);
const contactFields = computed(() => CONTACT_FIELDS.filter((f) => contact.value && f.key in contact.value.values));
onMounted(async () => {
  try {
    const [mine, found] = await Promise.all([
      api.GET("/api/identity", QUIET),
      api.GET("/api/identity/from-document/{document_id}", { params: { path: { document_id: props.documentId } }, ...QUIET }),
    ]);
    if (!mine.data || !found.data) return;
    const values: Partial<Record<ContactKey, string>> = {};
    for (const { key } of CONTACT_FIELDS) {
      const proposed = found.data[key]?.trim();
      if (proposed && !mine.data[key]?.trim()) values[key] = proposed;
    }
    if (Object.keys(values).length) contact.value = { selected: true, values };
  } catch {
    // Sans coordonnées trouvées, la relecture reste celle des éléments.
  }
});

// Au moment d'ajouter, les coordonnées sont relues : un champ rempli entre-temps n'est pas envoyé.
async function saveContact(): Promise<boolean> {
  const values = contact.value?.values ?? {};
  const mine = await api.GET("/api/identity");
  if (!mine.data) return false;
  const body: Partial<Record<ContactKey, string>> = {};
  for (const [key, value] of Object.entries(values) as [ContactKey, string][]) {
    if (value.trim() && !mine.data[key]?.trim()) body[key] = value.trim();
  }
  if (!Object.keys(body).length) return true;
  const { data } = await api.PUT("/api/identity", { body });
  return !!data;
}

const selectedCount = computed(() => items.value.filter((i) => i.selected).length + (contact.value?.selected ? 1 : 0));

function duplicateTitle(id: number | null): string | null {
  if (id === null) return null;
  return props.existing.find((c) => c.id === id)?.title ?? null;
}

async function save(): Promise<void> {
  if (saving.value) return;
  // Bouton toujours actif (docs/29 §3) : sans bloc coché, il le dit.
  if (!selectedCount.value) {
    error.value = "Coche au moins un élément à ajouter.";
    return;
  }
  saving.value = true;
  error.value = "";
  let created = 0;
  if (contact.value?.selected) {
    let ok = false;
    try {
      ok = await saveContact();
    } catch {
      ok = false;
    }
    if (!ok) {
      error.value = "Coordonnées refusées : vérifie le NPA (quatre chiffres) et l’e-mail.";
      saving.value = false;
      return;
    }
    created += 1;
  }
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
    error.value = `${plural(created, "élément ajouté", "éléments ajoutés")}, puis un refus : vérifie titres et contenus.`;
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
      <h3>
        Repris de « {{ documentName }} »
      </h3>
      <ul class="proposal-list">
        <li
          v-if="contact"
          :class="['proposal', { off: !contact.selected }]"
          data-test="proposal-contact"
        >
          <label class="check proposal-check">
            <input
              v-model="contact.selected"
              type="checkbox"
              aria-label="Ajouter tes coordonnées"
            >
            <span class="badge">Tes coordonnées</span>
          </label>
          <FormField
            v-for="field in contactFields"
            :key="field.key"
            v-slot="{ id, describedby, invalid }"
            :label="field.label"
          >
            <input
              :id="id"
              v-model="contact.values[field.key]"
              :type="field.type"
              :autocomplete="field.autocomplete"
              maxlength="200"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              :data-test="`contact-${field.key}`"
            >
          </FormField>
        </li>
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
            :aria-label="`Titre de l’élément ${index + 1}`"
            required
          >
          <textarea
            v-model="item.content"
            rows="3"
            :aria-label="`Contenu de l’élément ${index + 1}`"
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
        <BusyButton
          type="submit"
          class="primary"
          :busy="saving"
          busy-label="Ajout…"
          data-test="add-proposals"
        >
          Ajouter {{ plural(selectedCount, "élément", "éléments") }}
        </BusyButton>
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
