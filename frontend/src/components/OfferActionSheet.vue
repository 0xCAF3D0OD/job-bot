<script setup lang="ts">
import type { Offer } from "../api/client";
import type { MoreMenuItem } from "./MoreMenu.vue";
import BottomSheet from "./BottomSheet.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";
import { companyPlace } from "../format";

// La feuille d'actions d'une offre (maquette ActionsOffre, docs/139 étape 5d, C6) : ouverte par le « ⋯ » de
// sa carte, jamais par un appui long seul (clavier, lecteurs d'écran). « Écarter l'offre » en rouge garde
// « Annuler » 6 s dans le message (docs/108) ; « Marquer comme envoyée » ouvre le formulaire de la
// candidature. Le titre de la feuille est le poste, l'entreprise et le lieu dessous. `extra` : les actions propres
// à la fiche, après les deux de la liste (étape 6, O9).
// `sentTitle` : « J'ai déjà postulé » dans la fiche (lot 15.2), « Marquer comme envoyée » dans la liste.
withDefaults(defineProps<{ offer: Offer | null; extra?: MoreMenuItem[]; sentTitle?: string }>(), {
  extra: () => [],
  sentTitle: "Marquer comme envoyée",
});
const emit = defineEmits<{ close: []; discard: [offer: Offer]; sent: [offer: Offer] }>();
</script>

<template>
  <BottomSheet
    :open="offer !== null"
    :title="offer?.title ?? ''"
    data-test="offer-actions"
    @close="emit('close')"
  >
    <template v-if="offer">
      <p class="offer-actions-where">
        {{ companyPlace(offer.company, offer.location) }}
      </p>
      <GroupedList :level="3">
        <GroupedRow
          v-if="offer.status !== 'ignored'"
          title="Écarter l’offre"
          icon="close"
          button
          :chevron="false"
          class="offer-actions-discard"
          data-test="offer-action-discard"
          @click="emit('discard', offer)"
        />
        <GroupedRow
          v-if="offer.status !== 'applied'"
          :title="sentTitle"
          icon="send"
          button
          :chevron="false"
          data-test="offer-action-sent"
          @click="emit('sent', offer)"
        />
        <GroupedRow
          v-for="item in extra"
          :key="item.test"
          :title="item.label"
          :icon="item.icon"
          button
          :chevron="false"
          :data-test="`offer-action-${item.test}`"
          @click="emit('close'); item.run?.()"
        />
      </GroupedList>
    </template>
  </BottomSheet>
</template>
