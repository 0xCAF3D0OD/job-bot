<script setup lang="ts">
import { computed } from "vue";

import CopyButton from "./CopyButton.vue";

// L'adresse où un compte reçoit ses alertes (docs/65 §3, docs/104). Pour un invité, tant
// qu'elle passe par la boîte de l'exploitant (« boite+code@… »), le nom de la boîte est abrégé
// (« k…+code@… ») ; le bouton Copier, juste à côté, copie l'adresse entière, à donner aux sites. Avec le
// domaine des alertes (« nom-code@alertes… », ou « alertes+nom-code@… » sans « catch-all »),
// rien n'est à cacher.
const props = defineProps<{ address: string; personal?: boolean }>();

const shown = computed(() => {
  const [local = "", domain = ""] = props.address.split("@");
  if (!props.personal || !local.includes("+")) return props.address;
  const [box = "", code = ""] = local.split("+");
  // « alertes+nom-code@domaine » (0.82.3) : la boîte du domaine des alertes, pas celle de
  // l'exploitant ; rien à cacher.
  if (code.includes("-")) return props.address;
  return `${box.charAt(0)}…+${code}@${domain}`;
});
</script>

<template>
  <span class="mailbox-address">
    <strong data-test="mailbox-address">{{ shown }}</strong>
    <CopyButton
      :value="address"
      label="Copier l'adresse"
      test-id="mailbox-copy"
    />
  </span>
</template>
