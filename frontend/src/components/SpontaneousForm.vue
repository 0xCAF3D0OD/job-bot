<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import HelpTip from "./HelpTip.vue";

// Candidature spontanée (docs/39 §1) : entreprise, poste visé, « Pourquoi elle » ; puis, au
// choix, l'adresse au registre du commerce ; enfin la préparation habituelle (lettre, CV).
const router = useRouter();
// L'offre existe dès « Continuer » : la liste des offres se recharge pour la montrer, même si
// le panneau est fermé sans passer par « Préparer ».
const emit = defineEmits<{ created: [id: number] }>();
const form = reactive({ company: "", title: "", website: "", reason: "" });
const saving = ref(false);
const error = ref("");
const offerId = ref<number | null>(null);

type Candidate = { uid: string; name: string; address: string; canton: string | null };
const searching = ref(false);
const candidates = ref<Candidate[]>([]);
const webAddress = ref<string | null>(null);
const searchMessage = ref("");
const chosen = ref<string | null>(null);

async function create(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const { data } = await api.POST("/api/offers/spontaneous", {
      body: { company: form.company, title: form.title, reason: form.reason, website: form.website || null },
    });
    if (!data) {
      error.value = "Création impossible : vérifie l'entreprise, le poste et « Pourquoi elle ».";
      return;
    }
    offerId.value = data.id;
    emit("created", data.id);
  } finally {
    saving.value = false;
  }
}

async function searchAddress(): Promise<void> {
  if (offerId.value === null) return;
  searching.value = true;
  searchMessage.value = "";
  try {
    const { data } = await api.GET("/api/offers/{offer_id}/address-candidates", {
      params: { path: { offer_id: offerId.value } },
    });
    if (!data) {
      searchMessage.value = "Registre injoignable pour l'instant : tu pourras compléter l'adresse à l'envoi.";
      return;
    }
    candidates.value = data.candidates;
    webAddress.value = data.web_address ?? null;
    if (!data.candidates.length && !data.web_address) searchMessage.value = "Aucune entreprise trouvée à ce nom.";
  } finally {
    searching.value = false;
  }
}

async function choose(uid: string): Promise<void> {
  if (offerId.value === null) return;
  const { data } = await api.POST("/api/offers/{offer_id}/address-candidates/choose", {
    params: { path: { offer_id: offerId.value } },
    body: { uid },
  });
  if (data) chosen.value = data.company_address;
}

function prepare(): void {
  if (offerId.value !== null) void router.push(`/candidatures/offres/${offerId.value}/preparer`);
}
</script>

<template>
  <form
    v-if="offerId === null"
    class="spontaneous-form"
    data-test="spontaneous-form"
    @submit.prevent="create"
  >
    <label>Entreprise
      <input
        v-model="form.company"
        maxlength="200"
        required
        autocomplete="organization"
        data-test="spontaneous-company"
      >
    </label>
    <label>Poste visé
      <input
        v-model="form.title"
        maxlength="200"
        required
        placeholder="Ingénieur DevOps"
        data-test="spontaneous-title"
      >
    </label>
    <label>Site de l'entreprise (facultatif)
      <input
        v-model="form.website"
        maxlength="300"
        inputmode="url"
        placeholder="exemple.ch"
        data-test="spontaneous-website"
      >
    </label>
    <label>
      <span>Pourquoi elle
        <HelpTip
          label="Aide : pourquoi elle"
          text="Deux ou trois lignes avec tes mots : ce que fait l'entreprise, ce qui t'attire, une personne rencontrée. La lettre s'en sert pour son ouverture."
        />
      </span>
      <textarea
        v-model="form.reason"
        rows="4"
        maxlength="1500"
        required
        data-test="spontaneous-reason"
      />
    </label>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <button
      type="submit"
      class="primary small"
      :disabled="saving"
      data-test="spontaneous-create"
    >
      Continuer
    </button>
  </form>

  <div
    v-else
    class="spontaneous-form"
    data-test="spontaneous-address"
  >
    <p class="muted">
      L'adresse de {{ form.company }} servira au formulaire ORP. Tu peux aussi la compléter à l'envoi.
    </p>
    <p
      v-if="chosen"
      data-test="spontaneous-chosen"
    >
      <strong>Adresse :</strong> {{ chosen.split("\n").join(", ") }}
    </p>
    <template v-else>
      <span class="spontaneous-search">
        <button
          type="button"
          class="secondary small"
          :disabled="searching"
          data-test="spontaneous-search"
          @click="searchAddress"
        >
          {{ searching ? "Recherche…" : "Chercher l'adresse au registre" }}
        </button>
        <HelpTip
          label="Aide : registre du commerce"
          text="Le registre du commerce (IDE) est consulté gratuitement. S'il ne trouve rien, l'IA cherche l'adresse sur Internet (environ 0,02 $)."
        />
      </span>
      <ul
        v-if="candidates.length"
        class="spontaneous-candidates"
      >
        <li
          v-for="candidate in candidates"
          :key="candidate.uid"
        >
          <span>
            <strong>{{ candidate.name }}</strong><br>
            <span class="muted">{{ candidate.address.split("\n").join(", ") }}</span>
          </span>
          <button
            type="button"
            class="secondary small"
            data-test="spontaneous-choose"
            @click="choose(candidate.uid)"
          >
            Choisir
          </button>
        </li>
      </ul>
      <p v-else-if="webAddress">
        <strong>Trouvée sur Internet :</strong> {{ webAddress.split("\n").join(", ") }}
      </p>
      <p
        v-if="searchMessage"
        class="hint"
      >
        {{ searchMessage }}
      </p>
    </template>
    <button
      type="button"
      class="primary small"
      data-test="spontaneous-prepare"
      @click="prepare"
    >
      Préparer la candidature
    </button>
  </div>
</template>
