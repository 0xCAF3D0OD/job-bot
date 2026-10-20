<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { api, type AlertSearch, type AlertsPage } from "../api/client";
import AppIcon from "./AppIcon.vue";
import DisclosureRow from "./DisclosureRow.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import { offerUndo } from "../composables/useUndo";
import MailboxAddress from "./MailboxAddress.vue";

// Mes alertes (docs/20 §1) : une recherche par ligne, un site par colonne. La plateforme
// ouvre la recherche déjà remplie ; l'alerte se crée sur le site, avec l'adresse de son choix.
type Cell = AlertSearch["cells"][number];

const page = ref<AlertsPage | null>(null);
const form = ref({ terms: "", location: "" });
const adding = ref(false);
const dateFormat = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });

const active = computed(() => page.value?.searches.filter((s) => s.active) ?? []);
const paused = computed(() => page.value?.searches.filter((s) => !s.active) ?? []);
const siteName = (slug: string): string => page.value?.sites.find((s) => s.slug === slug)?.name ?? slug;

function apply(data: AlertsPage | undefined): void {
  if (data) page.value = data;
}

async function load(): Promise<void> {
  apply((await api.GET("/api/alert-searches")).data);
}

async function add(): Promise<void> {
  const { data } = await api.POST("/api/alert-searches", {
    body: { terms: form.value.terms.trim(), location: form.value.location.trim() || null },
  });
  if (!data) return;
  apply(data);
  form.value = { terms: "", location: "" };
  adding.value = false;
}

// Les actions d'une recherche dans son « ⋯ » (docs/74).
function searchItems(search: AlertSearch): MoreMenuItem[] {
  return [
    { label: "Modifier", test: "edit-alert", icon: "pencil", run: () => void edit(search) },
    { label: "Mettre de côté", test: "pause", icon: "clock", run: () => void setActive(search, false) },
    { label: "Supprimer", test: "remove-alert", danger: true, run: () => void remove(search) },
  ];
}

// Modifier sur place (docs/108, complément 0.77.1) : les mots et le lieu deviennent des champs,
// dans la ligne de la recherche.
const editing = ref<{ id: number; terms: string; location: string } | null>(null);
async function edit(search: AlertSearch): Promise<void> {
  editing.value = { id: search.id, terms: search.terms, location: search.location ?? "" };
  await nextTick();
  document.querySelector<HTMLInputElement>("[data-test=alert-edit-terms]")?.focus();
}
async function saveEdit(search: AlertSearch): Promise<void> {
  const value = editing.value;
  if (!value?.terms.trim()) return;
  editing.value = null;
  apply(
    (
      await api.PATCH("/api/alert-searches/{search_id}", {
        params: { path: { search_id: search.id } },
        body: { terms: value.terms.trim(), location: value.location.trim() },
      })
    ).data,
  );
}

async function setActive(search: AlertSearch, value: boolean): Promise<void> {
  apply(
    (
      await api.PATCH("/api/alert-searches/{search_id}", {
        params: { path: { search_id: search.id } },
        body: { active: value },
      })
    ).data,
  );
}

// Retirée tout de suite, « Annuler » pendant 6 s (docs/108 §1).
async function remove(search: AlertSearch): Promise<void> {
  const before = page.value;
  if (before) page.value = { ...before, searches: before.searches.filter((s) => s.id !== search.id) };
  await offerUndo({
    message: `Recherche « ${search.terms} » supprimée`,
    commit: async (keepalive) => {
      const { data } = await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: search.id } }, keepalive });
      if (!data) return false;
      apply(data);
    },
    restore: () => {
      page.value = before;
    },
  });
}

async function toggleCreated(search: AlertSearch, cell: Cell): Promise<void> {
  const params = { params: { path: { search_id: search.id, site: cell.site } } };
  apply(
    cell.created_at
      ? (await api.DELETE("/api/alert-searches/{search_id}/sites/{site}", params)).data
      : (await api.PUT("/api/alert-searches/{search_id}/sites/{site}", params)).data,
  );
}

function statusText(cell: Cell): string {
  if (cell.status === "received" && cell.received_at) return `reçue le ${dateFormat.format(new Date(cell.received_at))}`;
  if (cell.status === "created") return "créée, en attente";
  return "à créer";
}

onMounted(() => void load());
</script>

<template>
  <div
    v-if="page"
    class="alerts-panel"
    data-test="alerts-panel"
  >
    <h2 class="section-title first">
      Alertes
    </h2>
    <p
      class="notice"
      data-test="mailbox"
    >
      <template v-if="page.mailbox && page.personal_address">
        Ton adresse pour les alertes : <MailboxAddress
          :address="page.mailbox"
          personal
        />. Donne-la aux sites d'emploi : la plateforme
        reçoit pour toi.
      </template>
      <template v-else-if="page.mailbox">
        Boîte lue par la plateforme : <strong>{{ page.mailbox }}</strong>, dossier <strong>{{ page.folder }}</strong>.
        Les alertes doivent y arriver.
      </template>
      <template v-else>
        La lecture de ta boîte mail n'est pas encore branchée (réglage d'installation, voir le README).
      </template>
    </p>
    <DisclosureRow
      class="forwarding"
      title="Tu as donné une autre adresse sur le site ?"
    >
      <p class="hint">
        Fais-les suivre vers la boîte lue avec un filtre sur l'expéditeur :
      </p>
      <ul>
        <li
          v-for="site in page.sites"
          :key="site.slug"
        >
          <strong>{{ site.name }}</strong> : {{ site.senders.length ? site.senders.join(", ") : "à compléter dans Réglages › Sites suivis" }}
        </li>
      </ul>
    </DisclosureRow>

    <p
      v-if="!active.length"
      class="muted empty"
    >
      Aucune recherche suivie : ajoute-en une.
    </p>
    <div
      v-else
      class="table-scroll"
    >
      <table class="runs alerts-table">
        <thead>
          <tr>
            <th>Recherche</th>
            <th
              v-for="site in page.sites"
              :key="site.slug"
            >
              {{ site.name }}
            </th>
            <th><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="search in active"
            :key="search.id"
            data-test="alert-search"
          >
            <td>
              <form
                v-if="editing?.id === search.id"
                class="inline-edit stacked"
                data-test="alert-edit-form"
                @submit.prevent="saveEdit(search)"
                @keydown.esc="editing = null"
              >
                <input
                  v-model="editing.terms"
                  type="text"
                  maxlength="120"
                  required
                  aria-label="Mots de la recherche"
                  data-test="alert-edit-terms"
                >
                <input
                  v-model="editing.location"
                  type="text"
                  maxlength="80"
                  aria-label="Lieu"
                  placeholder="Toute la Suisse"
                  data-test="alert-edit-location"
                >
                <span class="inline-edit-actions">
                  <button
                    type="submit"
                    class="primary small"
                    data-test="alert-edit-save"
                  >
                    Enregistrer
                  </button>
                  <button
                    type="button"
                    class="secondary small"
                    @click="editing = null"
                  >
                    Annuler
                  </button>
                </span>
              </form>
              <template v-else>
                <strong>{{ search.terms }}</strong><br>
                <span class="muted">{{ search.location || "toute la Suisse" }}</span>
              </template>
            </td>
            <td
              v-for="cell in search.cells"
              :key="cell.site"
              :class="['alert-cell', cell.status]"
              :data-test="`cell-${cell.site}`"
            >
              <a
                v-if="cell.url && cell.status !== 'received'"
                :href="cell.url"
                :aria-label="`Ouvrir la recherche sur ${siteName(cell.site)}`"
                target="_blank"
                rel="noopener noreferrer"
                class="link"
              ><span class="with-icon"><AppIcon name="external" />Ouvrir</span></a>
              <a
                v-if="cell.remote_url && cell.status !== 'received'"
                :href="cell.remote_url"
                :aria-label="`La même recherche en télétravail sur ${siteName(cell.site)}`"
                target="_blank"
                rel="noopener noreferrer"
                class="link"
                data-test="cell-remote"
              >en télétravail</a>
              <span class="alert-status">{{ statusText(cell) }}</span>
              <label
                v-if="cell.status !== 'received'"
                class="check"
              >
                <input
                  type="checkbox"
                  :checked="Boolean(cell.created_at)"
                  :data-test="`created-${cell.site}`"
                  @change="toggleCreated(search, cell)"
                > J'ai créé l'alerte
              </label>
            </td>
            <td class="row-more">
              <MoreMenu
                :items="searchItems(search)"
                :label="`Actions sur la recherche ${search.terms}`"
                test-id="alert-more"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <form
      v-if="adding"
      class="form-card alert-form"
      data-test="add-alert-search"
      @submit.prevent="add"
    >
      <label>Mots
        <input
          v-model="form.terms"
          type="text"
          maxlength="120"
          required
          placeholder="DevOps"
          data-test="alert-terms"
        >
      </label>
      <label>Lieu (facultatif)
        <input
          v-model="form.location"
          type="text"
          maxlength="80"
          placeholder="Lausanne"
        >
      </label>
      <div class="form-actions">
        <button
          type="submit"
          class="primary small"
        >
          <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
        </button>
        <button
          type="button"
          class="link"
          @click="adding = false"
        >
          Annuler
        </button>
      </div>
    </form>
    <div
      v-else
      class="form-actions"
    >
      <button
        type="button"
        class="secondary small"
        data-test="add-alert"
        @click="adding = true"
      >
        <span class="with-icon"><AppIcon name="plus" />Ajouter une recherche</span>
      </button>
    </div>

    <DisclosureRow
      v-if="paused.length"
      class="forwarding"
      title="Recherches mises de côté"
      :value="String(paused.length)"
    >
      <ul>
        <li
          v-for="search in paused"
          :key="search.id"
        >
          {{ search.terms }} · {{ search.location || "toute la Suisse" }}
          <button
            type="button"
            class="link"
            @click="setActive(search, true)"
          >
            <span class="with-icon"><AppIcon name="play" />Reprendre</span>
          </button>
        </li>
      </ul>
    </DisclosureRow>
  </div>
</template>
