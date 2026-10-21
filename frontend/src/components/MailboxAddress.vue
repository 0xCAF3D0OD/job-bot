<script setup lang="ts">
import { computed, ref } from "vue";

// L'adresse où un compte reçoit ses alertes (docs/65 §3, docs/104). Pour un invité, tant
// qu'elle passe par la boîte de l'exploitant (« boite+code@… »), le nom de la boîte est abrégé
// (« k…+code@… ») ; « Copier l'adresse » copie l'adresse entière, à donner aux sites. Avec le
// domaine des alertes (« nom-code@alertes… », ou « alertes+nom-code@… » sans « catch-all »),
// rien n'est à cacher.
const props = defineProps<{ address: string; personal?: boolean }>();
const copied = ref(false);

const shown = computed(() => {
  const [local = "", domain = ""] = props.address.split("@");
  if (!props.personal || !local.includes("+")) return props.address;
  const [box = "", code = ""] = local.split("+");
  // « alertes+nom-code@domaine » (0.82.3) : la boîte du domaine des alertes, pas celle de
  // l'exploitant ; rien à cacher.
  if (code.includes("-")) return props.address;
  return `${box.charAt(0)}…+${code}@${domain}`;
});

async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.address);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    copied.value = false;
  }
}
</script>

<template>
  <span class="mailbox-address">
    <strong data-test="mailbox-address">{{ shown }}</strong>
    <button
      type="button"
      class="link"
      data-test="mailbox-copy"
      @click="copy"
    >
      {{ copied ? "Adresse copiée" : "Copier l'adresse" }}
    </button>
  </span>
</template>
