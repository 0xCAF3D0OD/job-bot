<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { knownProviders, oauthMessage, PROVIDER_LABEL, type Provider, startHref } from "../oauthText";
import InlineConfirm from "./InlineConfirm.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Compte › Connexions (docs/65, complément du 2026-11-05) : les comptes Apple, Google ou Microsoft liés, en lier
// un, en retirer un. Le dernier moyen de se connecter (pas de mot de passe, un seul lien) ne se retire pas : le
// serveur le refuse, la ligne le dit. Mêmes cartes et lignes que la rubrique Mes données (SettingCard, SettingRow).
type Connections = components["schemas"]["Connections"];

const route = useRoute();
const data = ref<Connections | null>(null);
const problem = ref("");
const confirming = ref<number | null>(null);

// Les fournisseurs configurés qui ne sont pas encore liés à ce compte.
const providers = computed<Provider[]>(() =>
  knownProviders(data.value?.providers).filter((name) => !data.value?.links.some((link) => link.provider === name)),
);
// Le retour du fournisseur : lié (?lie=google) ou refusé (?erreur=deja-lie&fournisseur=google).
const notice = computed(() => {
  if (typeof route.query.erreur === "string") return oauthMessage(route.query.erreur, route.query.fournisseur);
  return "";
});
const linked = computed(() =>
  typeof route.query.lie === "string" && route.query.lie in PROVIDER_LABEL
    ? `Ton compte ${PROVIDER_LABEL[route.query.lie as Provider]} est lié.`
    : "",
);
const onlyWay = computed(() => Boolean(data.value && !data.value.has_password && data.value.links.length === 1));

function label(provider: string): string {
  return PROVIDER_LABEL[provider as Provider] ?? provider;
}

async function load(): Promise<void> {
  const { data: found } = await api.GET("/api/account/connexions");
  data.value = found ?? null;
}

async function remove(id: number): Promise<void> {
  confirming.value = null;
  problem.value = "";
  const { error, response } = await api.DELETE("/api/account/connexions/{connection_id}", {
    params: { path: { connection_id: id } },
  });
  if (!response.ok) {
    const detail = (error as { detail?: unknown } | undefined)?.detail;
    problem.value = typeof detail === "string" ? detail.charAt(0).toUpperCase() + detail.slice(1) + "." : "Le lien n’a pas pu être retiré.";
    return;
  }
  await load();
}

onMounted(load);
</script>

<template>
  <SettingCard data-test="connections-panel">
    <p
      v-if="notice"
      class="notice"
      role="alert"
      data-test="connections-error"
    >
      {{ notice }}
    </p>
    <p
      v-else-if="linked"
      class="hint"
      role="status"
      data-test="connections-linked"
    >
      {{ linked }}
    </p>
    <template v-if="data">
      <SettingRow
        v-for="link in data.links"
        :key="link.id"
        :title="label(link.provider)"
        :description="link.email ?? 'Compte lié'"
        :data-test="`connection-${link.provider}`"
      >
        <button
          v-if="confirming !== link.id"
          type="button"
          class="secondary small"
          :disabled="onlyWay"
          :aria-describedby="onlyWay ? 'connections-only-way' : undefined"
          :data-test="`connection-remove-${link.provider}`"
          @click="confirming = link.id"
        >
          Retirer
        </button>
      </SettingRow>
      <div
        v-if="confirming !== null"
        class="setting-row-form"
      >
        <InlineConfirm
          message="Retirer ce compte ? Tu ne pourras plus t’en servir pour te connecter."
          confirm-label="Retirer"
          @confirm="remove(confirming)"
          @cancel="confirming = null"
        />
      </div>
      <p
        v-if="onlyWay"
        id="connections-only-way"
        class="hint"
        data-test="connections-only-way"
      >
        C’est ton seul moyen de te connecter : lie d’abord un autre compte pour pouvoir le retirer.
      </p>
      <p
        v-if="problem"
        class="notice"
        role="alert"
      >
        {{ problem }}
      </p>
      <SettingRow
        v-if="!data.links.length"
        title="Aucun compte lié"
        :description="data.has_password ? 'Tu te connectes avec ton identifiant et ton mot de passe.' : ''"
      />
      <SettingRow
        v-for="provider in providers"
        :key="`lier-${provider}`"
        :title="`Lier un compte ${PROVIDER_LABEL[provider]}`"
        :description="`Pour te connecter avec « Continuer avec ${PROVIDER_LABEL[provider]} ».`"
      >
        <a
          class="button-link"
          :href="startHref(provider, { link: true })"
          :data-test="`connection-link-${provider}`"
        >Lier</a>
      </SettingRow>
    </template>
  </SettingCard>
</template>
