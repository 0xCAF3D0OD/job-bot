<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import { api, type Offer, type RegistryCandidate } from "../api/client";
import { colorIndex, expiredText, formatDate, rateText, scoreLevel, sourceLabel } from "../format";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ offer: Offer; chunkTitles?: Record<number, string> }>();

function sources(ids: number[]): string {
  return ids
    .map((id) => props.chunkTitles?.[id])
    .filter(Boolean)
    .join(", ");
}
const emit = defineEmits<{
  close: [];
  status: [status: "to_review" | "later" | "ignored" | "preparing"];
  applied: [];
  expiry: [expired: boolean];
  address: [address: string];
  changed: [];
}>();

// Registre IDE (docs/12 §2.2) : propositions quand le nom ne suffit pas à trancher.
const searching = ref(false);
const proposals = ref<RegistryCandidate[]>([]);
const registryMessage = ref("");

async function searchRegistry(): Promise<void> {
  searching.value = true;
  registryMessage.value = "";
  proposals.value = [];
  try {
    const { data } = await api.GET("/api/offers/{offer_id}/address-candidates", {
      params: { path: { offer_id: props.offer.id } },
    });
    if (!data) {
      registryMessage.value = "Registre IDE injoignable, réessaie plus tard.";
    } else if (data.chosen_uid && props.offer.company_address_source !== "registry") {
      registryMessage.value = "Adresse trouvée dans le registre.";
      emit("changed");
    } else if (!data.candidates.length) {
      registryMessage.value = "Aucune entreprise active à ce nom dans le registre. Saisis l'adresse à la main.";
    } else {
      proposals.value = data.candidates;
      registryMessage.value = "Plusieurs entreprises possibles : choisis la bonne.";
    }
  } catch {
    registryMessage.value = "API injoignable.";
  } finally {
    searching.value = false;
  }
}

async function chooseRegistry(uid: string): Promise<void> {
  const { data } = await api.POST("/api/offers/{offer_id}/address-candidates/choose", {
    params: { path: { offer_id: props.offer.id } },
    body: { uid },
  });
  proposals.value = [];
  registryMessage.value = data ? "" : "Choix refusé.";
  if (data) emit("changed");
}

const STATUS_LABEL: Partial<Record<Offer["status"], string>> = {
  preparing: "En préparation",
  later: "Plus tard",
  ignored: "Ignorée",
  filtered_out: "Écartée par le filtre",
  applied: "Candidature envoyée",
};
const statusLabel = computed(() =>
  props.offer.expired_at && props.offer.status !== "applied" ? "Expirée" : (STATUS_LABEL[props.offer.status] ?? ""),
);
const ADDRESS_SOURCE: Record<string, string> = {
  page: "annonce",
  registry: "registre IDE",
  letter: "relevée dans l'annonce",
  manual: "saisie par toi",
};

// Menu « ⋯ » : les actions rares, hors de la vue principale (docs/12 §1).
const menuOpen = ref(false);
const menuRoot = ref<HTMLElement | null>(null);
function act(action: () => void): void {
  menuOpen.value = false;
  action();
}
function onDocumentClick(event: MouseEvent): void {
  if (menuOpen.value && menuRoot.value && !menuRoot.value.contains(event.target as Node)) menuOpen.value = false;
}
onMounted(() => document.addEventListener("click", onDocumentClick));
onUnmounted(() => document.removeEventListener("click", onDocumentClick));

const editingAddress = ref(false);
const addressDraft = ref("");
function startAddress(): void {
  addressDraft.value = props.offer.company_address ?? "";
  editingAddress.value = true;
}
function saveAddress(): void {
  editingAddress.value = false;
  emit("address", addressDraft.value);
}
watch(
  () => props.offer.id,
  () => {
    editingAddress.value = false;
    menuOpen.value = false;
    proposals.value = [];
    registryMessage.value = "";
  },
);

function initial(offer: Offer): string {
  return (offer.company ?? offer.title).trim().charAt(0).toUpperCase() || "?";
}
</script>

<template>
  <article
    class="detail-panel"
    data-test="offer-detail"
  >
    <div class="detail-top">
      <span
        :class="['logo', 'large', `c${colorIndex(offer.company ?? offer.title)}`]"
        aria-hidden="true"
      >{{ initial(offer) }}</span>
      <div class="detail-top-actions">
        <div
          v-if="offer.status !== 'applied'"
          ref="menuRoot"
          class="more-menu"
        >
          <button
            type="button"
            class="close"
            aria-label="Plus d'actions"
            :aria-expanded="menuOpen"
            data-test="more"
            @click="menuOpen = !menuOpen"
          >
            ⋯
          </button>
          <ul
            v-if="menuOpen"
            class="menu"
            role="menu"
          >
            <li v-if="offer.status === 'later' || offer.status === 'ignored' || offer.status === 'preparing'">
              <button
                type="button"
                role="menuitem"
                data-test="back-to-review"
                @click="act(() => emit('status', 'to_review'))"
              >
                Remettre à examiner
              </button>
            </li>
            <template v-else>
              <li>
                <button
                  type="button"
                  role="menuitem"
                  data-test="later"
                  @click="act(() => emit('status', 'later'))"
                >
                  Plus tard
                </button>
              </li>
              <li>
                <button
                  type="button"
                  role="menuitem"
                  data-test="ignore"
                  @click="act(() => emit('status', 'ignored'))"
                >
                  Ignorer
                </button>
              </li>
            </template>
            <li>
              <button
                v-if="offer.expired_at"
                type="button"
                role="menuitem"
                data-test="not-expired"
                @click="act(() => emit('expiry', false))"
              >
                Pas expirée
              </button>
              <button
                v-else
                type="button"
                role="menuitem"
                data-test="flag-expired"
                @click="act(() => emit('expiry', true))"
              >
                Signaler comme expirée
              </button>
            </li>
          </ul>
        </div>
        <button
          type="button"
          class="close"
          aria-label="Fermer le détail"
          data-test="close-detail"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>
    </div>
    <div>
      <h2>{{ offer.title }}</h2>
      <span class="detail">{{ offer.company ?? "Entreprise non indiquée" }}</span>
      <div class="status-line">
        <span
          v-if="statusLabel"
          :class="['badge', offer.status === 'applied' ? 'new' : '']"
          data-test="status-pill"
        >{{ statusLabel }}</span>
        <RouterLink
          v-if="offer.status === 'applied'"
          to="/candidatures"
          class="link"
        >
          Voir le suivi
        </RouterLink>
      </div>
    </div>
    <p
      v-if="offer.expired_at && offer.status !== 'applied'"
      class="notice expired-notice"
      data-test="expired"
    >
      {{ expiredText(offer) }}
    </p>

    <div
      class="address-line"
      data-test="address"
    >
      <template v-if="!editingAddress">
        <span class="muted">Adresse :</span>
        <span v-if="offer.company_address">
          {{ offer.company_address.split("\n").join(", ") }}
          <span class="hint">· {{ ADDRESS_SOURCE[offer.company_address_source ?? "manual"] }}</span>
        </span>
        <span
          v-else
          class="hint"
        >inconnue</span>
        <button
          type="button"
          class="link"
          data-test="edit-address"
          @click="startAddress"
        >
          {{ offer.company_address ? "Modifier" : "Ajouter" }}
        </button>
        <button
          v-if="offer.company && offer.company_address_source !== 'manual' && offer.company_address_source !== 'page'"
          type="button"
          class="link"
          :disabled="searching"
          data-test="search-registry"
          @click="searchRegistry"
        >
          {{ searching ? "Recherche…" : "Chercher dans le registre" }}
        </button>
      </template>
      <div
        v-if="registryMessage || proposals.length"
        class="registry-proposals"
        data-test="registry"
      >
        <p
          v-if="registryMessage"
          class="hint"
        >
          {{ registryMessage }}
        </p>
        <ul v-if="proposals.length">
          <li
            v-for="proposal in proposals"
            :key="proposal.uid"
          >
            <span>
              <strong>{{ proposal.name }}</strong><br>
              <span class="muted">{{ proposal.address.split("\n").join(", ") }}</span>
            </span>
            <button
              type="button"
              class="secondary small"
              data-test="choose-registry"
              @click="chooseRegistry(proposal.uid)"
            >
              Choisir
            </button>
          </li>
        </ul>
      </div>
      <form
        v-if="editingAddress"
        class="address-form"
        @submit.prevent="saveAddress"
      >
        <textarea
          v-model="addressDraft"
          rows="2"
          placeholder="Rue et numéro&#10;NPA localité"
          aria-label="Adresse de l'entreprise"
          data-test="address-input"
        />
        <div>
          <button
            type="submit"
            class="primary small"
            data-test="save-address"
          >
            Enregistrer
          </button>
          <button
            type="button"
            class="link"
            @click="editingAddress = false"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>

    <div
      v-if="offer.status !== 'applied'"
      class="triage"
      data-test="triage"
    >
      <RouterLink
        :to="`/offres/${offer.id}/preparer`"
        class="button-link primary-link"
        data-test="prepare"
      >
        {{ offer.status === "preparing" ? "Reprendre la lettre" : "Préparer ma candidature" }}
      </RouterLink>
      <button
        type="button"
        class="secondary small"
        data-test="mark-applied"
        @click="emit('applied')"
      >
        Marquer comme envoyée
      </button>
    </div>
    <div class="actions">
      <a
        v-if="offer.apply_url"
        :href="offer.apply_url"
        target="_blank"
        rel="noopener noreferrer"
        data-test="apply"
      >{{ offer.apply_kind === "external" ? "Postuler chez l'employeur" : "Postuler sur jobup" }}
        <AppIcon name="chevron" /></a>
      <a
        v-for="link in offer.links"
        :key="link.source"
        :class="{ secondary: offer.apply_url }"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
      >Voir sur {{ sourceLabel[link.source] }} <AppIcon name="chevron" /></a>
    </div>
    <section
      v-if="offer.summary_role"
      class="ai-block"
      data-test="ai"
    >
      <div class="ai-head">
        <span
          v-if="offer.score !== null && offer.score !== undefined"
          :class="['score', 'big', scoreLevel(offer.score)]"
        >{{ offer.score }}<small>/100</small></span>
        <span class="detail">
          Résumé et note par l'IA{{ offer.summary_partial ? ", sur l'extrait de l'alerte seulement" : "" }}.
          <template v-if="offer.score_stale">Ton profil a changé depuis : note à refaire.</template>
          <template v-if="offer.score === null">Pas de note : aucun bloc de profil actif.</template>
        </span>
      </div>
      <dl class="summary">
        <div><dt>Poste</dt><dd>{{ offer.summary_role }}</dd></div>
        <div><dt>Demande</dt><dd>{{ offer.summary_asks }}</dd></div>
        <div><dt>Offre</dt><dd>{{ offer.summary_offers }}</dd></div>
      </dl>
      <div
        v-if="offer.strengths?.length || offer.gaps?.length"
        class="points"
      >
        <div v-if="offer.strengths?.length">
          <h3>Points forts</h3>
          <ul data-test="strengths">
            <li
              v-for="point in offer.strengths"
              :key="point.text"
            >
              {{ point.text }}
              <span
                v-if="sources(point.chunk_ids)"
                class="detail"
              >Bloc : {{ sources(point.chunk_ids) }}</span>
            </li>
          </ul>
        </div>
        <div v-if="offer.gaps?.length">
          <h3>Manques</h3>
          <ul
            class="gaps"
            data-test="gaps"
          >
            <li
              v-for="point in offer.gaps"
              :key="point.text"
            >
              {{ point.text }}
            </li>
          </ul>
        </div>
      </div>
    </section>
    <p
      v-else-if="offer.score_error"
      class="badge reason"
    >
      Note impossible : {{ offer.score_error }}
    </p>
    <ul
      v-if="offer.filter_reasons?.length"
      class="reasons"
      data-test="reasons"
    >
      <li
        v-for="reason in offer.filter_reasons"
        :key="reason"
      >
        {{ reason }}
      </li>
    </ul>
    <p
      v-if="offer.enrich_status === 'expired'"
      class="badge reason"
    >
      L'annonce n'est plus en ligne sur jobup.
    </p>
    <ul class="checks">
      <li>
        <AppIcon name="check" /><strong>Lieu.</strong>
        <span>{{ offer.location ?? "non indiqué" }}</span>
      </li>
      <li>
        <AppIcon name="check" /><strong>Taux.</strong>
        <span>{{ rateText(offer.rate_min, offer.rate_max) || "non indiqué" }}</span>
      </li>
      <li v-if="offer.employment_type">
        <AppIcon name="check" /><strong>Type.</strong>
        <span>{{ offer.employment_type }}</span>
      </li>
      <li>
        <AppIcon name="check" /><strong>Vue.</strong>
        <span>{{ offer.seen_count }} fois, depuis le {{ formatDate(offer.first_seen_at) }}</span>
      </li>
    </ul>
    <div
      v-if="offer.description"
      class="full-text"
      data-test="description"
    >
      {{ offer.description }}
    </div>
    <p
      v-else-if="offer.snippet"
      class="detail-snippet"
    >
      {{ offer.snippet }}
    </p>
    <p
      v-else
      class="detail-snippet"
    >
      Pas d'extrait dans l'alerte : le texte complet de l'annonce est sur le site.
    </p>
  </article>
</template>
