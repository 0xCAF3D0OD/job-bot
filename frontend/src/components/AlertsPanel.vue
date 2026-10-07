<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type AlertSearch, type AlertsPage } from "../api/client";
import AppIcon from "./AppIcon.vue";
import MoreInfo from "./MoreInfo.vue";

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

async function edit(search: AlertSearch): Promise<void> {
  const terms = window.prompt("Mots de la recherche", search.terms)?.trim();
  if (terms === undefined || !terms) return;
  const location = window.prompt("Lieu (vide : toute la Suisse)", search.location ?? "");
  if (location === null) return;
  apply(
    (
      await api.PATCH("/api/alert-searches/{search_id}", {
        params: { path: { search_id: search.id } },
        body: { terms, location: location.trim() },
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

async function remove(search: AlertSearch): Promise<void> {
  if (!window.confirm(`Supprimer la recherche « ${search.terms} » ?`)) return;
  apply(
    (await api.DELETE("/api/alert-searches/{search_id}", { params: { path: { search_id: search.id } } })).data,
  );
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
      Mes alertes
    </h2>
    <p class="hint">
      « Ouvrir » affiche la recherche sur le site : crée l'alerte là-bas, puis coche « J'ai créé l'alerte ».
    </p>
    <MoreInfo>
      <p>
        Sur le site, le bouton s'appelle souvent « Créer une alerte » ou « Activer l'alerte » ; donne l'adresse e-mail
        de ton choix. La plateforme ne peut pas créer l'alerte à ta place : il faudrait se connecter à tes comptes sur
        ces sites.
      </p>
    </MoreInfo>
    <p
      class="notice"
      data-test="mailbox"
    >
      <template v-if="page.mailbox">
        Boîte lue par la plateforme : <strong>{{ page.mailbox }}</strong>, dossier <strong>{{ page.folder }}</strong>.
        Les alertes doivent y arriver.
      </template>
      <template v-else>
        La lecture de ta boîte mail n'est pas encore branchée (réglage d'installation, voir le README).
      </template>
    </p>
    <details class="forwarding">
      <summary>Tu as donné une autre adresse sur le site ?</summary>
      <p class="hint">
        Fais-les suivre vers la boîte lue avec un filtre sur l'expéditeur :
      </p>
      <ul>
        <li
          v-for="site in page.sites"
          :key="site.slug"
        >
          <strong>{{ site.name }}</strong> : {{ site.senders.length ? site.senders.join(", ") : "à compléter dans Réglages → Sites suivis" }}
        </li>
      </ul>
    </details>

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
              <strong>{{ search.terms }}</strong><br>
              <span class="muted">{{ search.location || "toute la Suisse" }}</span>
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
                target="_blank"
                rel="noopener noreferrer"
                class="link"
                :title="`Ouvrir la recherche sur ${siteName(cell.site)}`"
              >Ouvrir <AppIcon name="chevron" /></a>
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
            <td class="row-actions">
              <button
                type="button"
                class="link"
                @click="edit(search)"
              >
                Modifier
              </button>
              <button
                type="button"
                class="link"
                data-test="pause"
                @click="setActive(search, false)"
              >
                Mettre de côté
              </button>
              <button
                type="button"
                class="link danger"
                @click="remove(search)"
              >
                Supprimer
              </button>
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
          Ajouter
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
        Ajouter une recherche
      </button>
    </div>

    <details
      v-if="paused.length"
      class="forwarding"
    >
      <summary>Recherches mises de côté ({{ paused.length }})</summary>
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
            Reprendre
          </button>
        </li>
      </ul>
    </details>
  </div>
</template>
