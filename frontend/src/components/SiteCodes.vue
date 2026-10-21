<script setup lang="ts">
import { computed, ref } from "vue";

import { sourceLabel } from "../format";

// Les codes des sites (docs/112) : le code de vérification qu'un site envoie à l'adresse
// jobA1 de la personne, 30 minutes, dans la carte « Les e-mails des sites » (SiteMail), à la
// place de « J'attends un code » (0.84.2).
type SiteCode = { search_id: number; site: string; code: string; received_at: string };
const props = defineProps<{ codes: SiteCode[] }>();

const copied = ref<number | null>(null);
const time = new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Zurich" });
const shown = computed(() =>
  props.codes.map((c) => ({
    ...c,
    name: c.site === "unknown" ? "Un site" : sourceLabel[c.site],
    spaced: c.code.length === 6 ? `${c.code.slice(0, 3)} ${c.code.slice(3)}` : c.code,
  })),
);

async function copy(code: SiteCode): Promise<void> {
  try {
    await navigator.clipboard.writeText(code.code);
    copied.value = code.search_id;
    setTimeout(() => (copied.value = null), 2000);
  } catch {
    copied.value = null;
  }
}
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
        <span class="site-code-label">Code {{ item.name }} · reçu à {{ time.format(new Date(item.received_at)) }}</span>
        <strong
          class="site-code-value"
          data-test="site-code-value"
        >{{ item.spaced }}</strong>
      </span>
      <button
        type="button"
        class="pill"
        data-test="site-code-copy"
        @click="copy(item)"
      >
        {{ copied === item.search_id ? "Copié" : "Copier le code" }}
      </button>
    </li>
  </ul>
</template>
