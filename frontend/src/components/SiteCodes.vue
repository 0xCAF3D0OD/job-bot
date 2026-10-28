<script setup lang="ts">
import { computed } from "vue";

import { timeOfDay } from "../dates";
import { sourceLabel } from "../format";
import CopyButton from "./CopyButton.vue";

// Les codes des sites (docs/112) : le code de vérification qu'un site envoie à l'adresse
// jobA1 de la personne, 30 minutes, dans la carte « Les e-mails des sites » (SiteMail), à la
// place de « J'attends un code » (0.84.2).
type SiteCode = { search_id: number; site: string; code: string; received_at: string };
const props = defineProps<{ codes: SiteCode[] }>();

const shown = computed(() =>
  props.codes.map((c) => ({
    ...c,
    name: c.site === "unknown" ? "Un site" : sourceLabel[c.site],
    spaced: c.code.length === 6 ? `${c.code.slice(0, 3)} ${c.code.slice(3)}` : c.code,
  })),
);
</script>

<template>
  <ul
    v-if="shown.length"
    class="site-code-list"
    data-test="site-codes"
  >
    <li
      v-for="item in shown"
      :key="item.search_id"
      class="site-code"
      data-test="site-code"
    >
      <span class="site-code-text">
        <span class="site-code-label">Code {{ item.name }} · reçu à {{ timeOfDay(item.received_at) }}</span>
        <span class="with-icon">
          <strong
            class="site-code-value"
            data-test="site-code-value"
          >{{ item.spaced }}</strong>
          <CopyButton
            :value="item.code"
            label="Copier le code"
            test-id="site-code-copy"
          />
        </span>
      </span>
    </li>
  </ul>
</template>
