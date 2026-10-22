<script setup lang="ts">
import { computed, ref } from "vue";

import DisclosureRow from "./DisclosureRow.vue";
import HoverNote from "./HoverNote.vue";
import IconButton from "./IconButton.vue";

// Les alertes existantes (docs/116 §1, mise en page 0.86.1 selon docs/interface.md) : la
// personne garde ses alertes sur jobup ou Indeed, sa messagerie les transfère à son adresse
// jobA1. Trois étapes, une ligne chacune séparée par un filet : un nom d'action, une ligne
// grise, au plus une action (copier). Le reste en description au survol.
const props = defineProps<{ address: string }>();

// Les expéditeurs des alertes (vus dans de vrais e-mails) : seulement eux, pas les messages
// des recruteurs ni les mots de passe oubliés.
const SENDERS = ["candidat@jobup.ch", "candidat@my.jobup.ch", "alert@indeed.com", "donotreply@jobalert.indeed.com"];
const MAILERS = [
  { key: "gmail", label: "Gmail" },
  { key: "outlook", label: "Outlook" },
  { key: "other", label: "Autre" },
] as const;
type Mailer = (typeof MAILERS)[number]["key"];
type Step = { title: string; hint: string; copy?: "address" | "senders" };

const mailer = ref<Mailer>("gmail");
const copied = ref<string | null>(null);
const senders = computed(() => (mailer.value === "gmail" ? `from:(${SENDERS.join(" OR ")})` : SENDERS.join("; ")));

const STEPS: Record<Mailer, Step[]> = {
  gmail: [
    { title: "Ajouter l'adresse de transfert", hint: "Paramètres, Transfert et POP/IMAP", copy: "address" },
    { title: "Recopier le code de Gmail", hint: "Il s'affiche dans « Les e-mails des sites »." },
    { title: "Créer le filtre", hint: "Les expéditeurs dans « De », puis « Transférer à ».", copy: "senders" },
  ],
  outlook: [
    { title: "Créer une règle", hint: "Paramètres, Courrier, Règles" },
    { title: "Coller les expéditeurs", hint: "Dans la condition « De ».", copy: "senders" },
    { title: "Transférer à l'adresse jobA1", hint: "Dans l'action « Transférer à ».", copy: "address" },
  ],
  other: [
    { title: "Créer une règle ou un filtre", hint: "Dans les réglages de ta messagerie." },
    { title: "Coller les expéditeurs", hint: "Les e-mails venant d'eux seulement.", copy: "senders" },
    { title: "Transférer à l'adresse jobA1", hint: "L'action « Transférer à ».", copy: "address" },
  ],
};

async function copy(what: "address" | "senders"): Promise<void> {
  try {
    await navigator.clipboard.writeText(what === "address" ? props.address : senders.value);
    copied.value = what;
    setTimeout(() => (copied.value = null), 2000);
  } catch {
    copied.value = null;
  }
}
</script>

<template>
  <DisclosureRow
    class="journal-toggle alerts-forward"
    title="Alertes existantes"
    value="à transférer"
    data-test="alerts-forward"
  >
    <div class="forward-body">
      <div class="forward-head">
        <p class="setting-desc">
          <HoverNote text="jobA1 ne demande jamais de mot de passe, et ne lit que les alertes.">
            Ta messagerie transfère tes alertes à jobA1.
          </HoverNote>
        </p>
        <div
          class="pill-row"
          role="radiogroup"
          aria-label="Messagerie"
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
      </div>

      <ol
        class="forward-steps"
        data-test="forward-steps"
      >
        <li
          v-for="(step, index) in STEPS[mailer]"
          :key="step.title"
        >
          <span
            class="step-number"
            aria-hidden="true"
          >{{ index + 1 }}</span>
          <span class="forward-step-text">
            <strong>{{ step.title }}</strong>
            <span class="hint">{{ step.hint }}</span>
          </span>
          <IconButton
            v-if="step.copy"
            icon="copy"
            :label="copied === step.copy ? 'Copié' : step.copy === 'address' ? `Copier l'adresse ${props.address}` : 'Copier les expéditeurs'"
            :data-test="`forward-copy-${step.copy}`"
            @click="copy(step.copy)"
          />
        </li>
      </ol>
    </div>
  </DisclosureRow>
</template>
