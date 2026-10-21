<script setup lang="ts">
import { computed, ref } from "vue";

import DisclosureRow from "./DisclosureRow.vue";
import MailboxAddress from "./MailboxAddress.vue";

// Lier ses alertes existantes (docs/116 §1) : la personne garde ses alertes sur jobup ou
// Indeed, et sa messagerie les transfère à son adresse jobA1. Jamais un mot de passe d'un
// site. Seulement les expéditeurs des alertes : pas les mots de passe oubliés, pas les
// messages des recruteurs. Gmail confirme l'adresse par un code, que jobA1 affiche dans
// « Les e-mails des sites ».
const props = defineProps<{ address: string }>();

// Les expéditeurs des alertes (vus dans de vrais e-mails, sauf mention).
const SENDERS = ["candidat@jobup.ch", "candidat@my.jobup.ch", "alert@indeed.com", "donotreply@jobalert.indeed.com"];
const MAILERS = [
  { key: "gmail", label: "Gmail" },
  { key: "outlook", label: "Outlook" },
  { key: "other", label: "Autre" },
] as const;
type Mailer = (typeof MAILERS)[number]["key"];

const mailer = ref<Mailer>("gmail");
const copied = ref(false);
const filter = computed(() =>
  mailer.value === "gmail" ? `from:(${SENDERS.join(" OR ")})` : SENDERS.join("; "),
);

async function copyFilter(): Promise<void> {
  try {
    await navigator.clipboard.writeText(filter.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    copied.value = false;
  }
}
</script>

<template>
  <DisclosureRow
    class="journal-toggle alerts-forward"
    title="J'ai déjà des alertes"
    value="les transférer"
    data-test="alerts-forward"
  >
    <div class="forward-body">
      <p class="setting-desc">
        Garde tes alertes jobup ou Indeed : ta messagerie les transfère à ton adresse jobA1. jobA1 ne te demande
        jamais le mot de passe d'un site.
      </p>
      <div
        class="pill-row"
        role="radiogroup"
        aria-label="Ta messagerie"
      >
        <button
          v-for="item in MAILERS"
          :key="item.key"
          type="button"
          role="radio"
          :aria-checked="mailer === item.key"
          :class="['pill', { selected: mailer === item.key }]"
          :data-test="`forward-${item.key}`"
          @click="mailer = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <ol
        class="forward-steps"
        data-test="forward-steps"
      >
        <template v-if="mailer === 'gmail'">
          <li>
            Dans Gmail : Paramètres, « Voir tous les paramètres », « Transfert et POP/IMAP », « Ajouter une adresse de
            transfert » :
            <MailboxAddress
              :address="props.address"
              personal
            />
          </li>
          <li>
            Gmail envoie un code à cette adresse : il s'affiche sur cette page, dans « Les e-mails des sites ». Recopie-le
            dans Gmail.
          </li>
          <li>
            Laisse « Désactiver le transfert » coché, pour ne pas tout envoyer. Puis « Filtres et adresses bloquées »,
            « Créer un filtre » ; dans « De », colle les expéditeurs ci-dessous ; « Créer un filtre », « Transférer à »
            ton adresse jobA1.
          </li>
        </template>
        <template v-else-if="mailer === 'outlook'">
          <li>Dans Outlook : Paramètres, « Courrier », « Règles », « Ajouter une nouvelle règle ».</li>
          <li>Condition « De » : colle les expéditeurs ci-dessous.</li>
          <li>
            Action « Transférer à » :
            <MailboxAddress
              :address="props.address"
              personal
            />
          </li>
        </template>
        <template v-else>
          <li>Cherche « règle » ou « filtre » dans les réglages de ta messagerie.</li>
          <li>Pour les e-mails venant des expéditeurs ci-dessous : « Transférer à » ton adresse jobA1.</li>
          <li>
            Ton adresse jobA1 :
            <MailboxAddress
              :address="props.address"
              personal
            />
          </li>
        </template>
      </ol>

      <div class="forward-filter">
        <code data-test="forward-filter">{{ filter }}</code>
        <button
          type="button"
          class="pill"
          data-test="forward-copy"
          @click="copyFilter"
        >
          {{ copied ? "Copié" : "Copier les expéditeurs" }}
        </button>
      </div>
      <p class="hint">
        Seulement les alertes : ne transfère pas tout, ni les messages des recruteurs.
      </p>
    </div>
  </DisclosureRow>
</template>
