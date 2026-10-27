<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import { usePlan } from "../composables/usePlan";
import InlineConfirm from "./InlineConfirm.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// La formule (docs/125 §4 et §6), dans Réglages › Compte (1.6.67, planche « 5. Réglages ») : une
// carte avec une ligne d'en-tête (son nom, ce qu'elle limite, quand les compteurs repartent) puis
// une ligne par usage (« 37 sur 150 ») avec sa jauge ; une carte pour Plus (ce qu'il ajoute, ou
// la date de fin et « Résilier »), les conditions acceptées sous « Passer à Plus » ; une carte
// des paiements reçus. L'exploitant n'a pas de formule : les cartes ne s'affichent pas.
const { plan, refresh } = usePlan();
const route = useRoute();
const router = useRouter();

const MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
function day(iso: string | null | undefined, year = false): string {
  if (!iso) return "";
  const [y, month, date] = iso.split("-").map(Number);
  return `${date === 1 ? "1er" : date} ${MONTHS[month! - 1]}${year ? ` ${y}` : ""}`;
}
function money(cents: number, currency: string): string {
  return `${(cents / 100).toFixed(2).replace(".", ",")} ${currency}`;
}

const resets = computed(() => day(plan.value?.resets_on));
// La phrase de l'en-tête : ce que la formule limite, et quand les compteurs repartent.
const planLine = computed(() => {
  if (plan.value?.plan !== "plus") return `Gratuite : seule l'IA a des limites, remises à zéro le ${resets.value}.`;
  const who = offered.value ? "Offerte par l'équipe jobA1" : "Payée chaque mois";
  return `${who} : l'IA va plus loin, compteurs remis à zéro le ${resets.value}.`;
});
const plusLimits = computed(() => plan.value?.limits.plus ?? {});
const paid = computed(() => plan.value?.plan === "plus" && !!plan.value.plan_until);
const offered = computed(() => plan.value?.plan === "plus" && !plan.value.plan_until);
const canBuy = computed(() => !!plan.value?.billing_available && plan.value.plan !== "plus");

const accepted = ref(false);
const busy = ref(false);
const confirming = ref(false);
// Une ligne à la fois : le retour du paiement, une erreur, la résiliation faite.
const message = ref<{ text: string; kind: "ok" | "hint" | "error" } | null>(null);

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function detail(error: unknown, fallback: string): string {
  const text = (error as { detail?: unknown } | undefined)?.detail;
  return typeof text === "string" ? `${capitalized(text)}.` : fallback;
}

async function buy(): Promise<void> {
  busy.value = true;
  message.value = null;
  try {
    const { data, error } = await api.POST("/api/billing/checkout", { body: { accept_terms: accepted.value } });
    if (!data) {
      message.value = { text: detail(error, "La page de paiement ne s'ouvre pas. Réessaie plus tard."), kind: "error" };
      return;
    }
    // La page de paiement est celle de Payrexx : jobA1 ne voit jamais la carte.
    window.location.assign(data.link);
  } finally {
    busy.value = false;
  }
}

async function cancel(): Promise<void> {
  busy.value = true;
  try {
    const { data, error } = await api.POST("/api/billing/cancel");
    if (!data) {
      message.value = { text: detail(error, "La résiliation n'a pas abouti. Réessaie plus tard."), kind: "error" };
      return;
    }
    confirming.value = false;
    await refresh();
    message.value = { text: `Résilié : Plus reste actif jusqu'au ${day(data.plan_until)}, sans nouveau paiement.`, kind: "ok" };
  } finally {
    busy.value = false;
  }
}

// Le retour de la page de paiement (`?paiement=ok|annule|echec`) : on vérifie auprès du serveur,
// qui demande à Payrexx, puis l'adresse redevient propre.
onMounted(async () => {
  const back = route.query.paiement;
  if (typeof back !== "string") return;
  if (back === "ok") {
    const { data } = await api.POST("/api/billing/sync");
    await refresh();
    message.value = data?.confirmed
      ? { text: `Merci : Plus est actif jusqu'au ${day(data.plan_until)}.`, kind: "ok" }
      : { text: "Le paiement est en cours de confirmation : Plus s'active dans quelques minutes.", kind: "hint" };
  } else if (back === "annule") {
    message.value = { text: "Paiement annulé : rien n'a été débité.", kind: "hint" };
  } else {
    message.value = { text: "Le paiement n'a pas abouti : rien n'a été débité. Réessaie.", kind: "error" };
  }
  const query = { ...route.query };
  delete query.paiement;
  void router.replace({ query });
});
</script>

<template>
  <template v-if="plan && !plan.unlimited">
    <SettingCard data-test="plan-panel">
      <SettingRow
        :title="`Formule ${plan.plan === 'plus' ? 'Plus' : 'Essentiel'}`"
        :description="planLine"
        data-test="plan-name"
      />
      <p
        v-if="message"
        :class="['setting-row-message', message.kind === 'error' ? 'notice error' : 'hint']"
        :role="message.kind === 'error' ? 'alert' : 'status'"
        data-test="plan-message"
      >
        {{ message.text }}
      </p>
      <!-- Une ligne par usage, le compteur à droite ; la jauge redit le compteur, sans rien de plus
           (WCAG 1.4.1) : elle est cachée aux lecteurs d'écran. -->
      <SettingRow
        v-for="usage in plan.usage"
        :key="usage.key"
        :title="capitalized(usage.label)"
        :data-test="`plan-${usage.key}`"
      >
        <span class="plan-usage-count">{{ usage.used }} sur {{ usage.limit }}</span>
        <span
          class="plan-usage-gauge"
          :style="{ '--p': Math.min(100, Math.round((usage.used / (usage.limit || 1)) * 100)) }"
          aria-hidden="true"
        />
      </SettingRow>
    </SettingCard>

    <!-- Plus payé : la date de fin, et résilier (confirmé sous la ligne). -->
    <SettingCard v-if="paid">
      <SettingRow
        :title="`Plus jusqu'au ${day(plan.plan_until)}`"
        :description="plan.cancelled ? 'Puis Essentiel. Pas de nouveau paiement.' : 'Renouvelé chaque mois, sans engagement.'"
        data-test="plan-paid"
      >
        <button
          v-if="!plan.cancelled && !confirming"
          type="button"
          class="secondary small"
          data-test="plan-cancel"
          @click="confirming = true"
        >
          Résilier
        </button>
      </SettingRow>
      <div
        v-if="confirming"
        class="setting-row-form"
      >
        <InlineConfirm
          :message="`Résilier Plus ? Il reste actif jusqu'au ${day(plan.plan_until)}, sans nouveau paiement.`"
          confirm-label="Résilier"
          :busy="busy"
          @confirm="cancel"
          @cancel="confirming = false"
        />
      </div>
    </SettingCard>

    <!-- Essentiel : ce que Plus ajoute ; une fois le paiement ouvert, « Passer à Plus », les
         conditions acceptées d'abord, juste dessous. -->
    <SettingCard v-else-if="plan.plan !== 'plus'">
      <SettingRow
        v-slot="c"
        :title="`Plus · ${plan.plus_price_chf} CHF par mois`"
        :description="`${plusLimits.letter} lettres et CV, ${plusLimits.practice} entraînements, ${plusLimits.score} offres notées. ${canBuy ? 'Sans engagement.' : 'Le paiement arrive bientôt.'}`"
        data-test="plan-plus"
      >
        <button
          v-if="canBuy"
          type="button"
          class="primary small"
          :disabled="!accepted || busy"
          :aria-describedby="`${c.describedby ?? ''} plan-terms`.trim()"
          data-test="plan-buy"
          @click="buy"
        >
          Passer à Plus
        </button>
      </SettingRow>
      <div
        v-if="canBuy"
        class="setting-row-form"
      >
        <label
          id="plan-terms"
          class="checkbox plan-terms"
        >
          <input
            v-model="accepted"
            type="checkbox"
            data-test="plan-accept"
          >
          <span>J'accepte les <RouterLink to="/conditions">conditions d'utilisation</RouterLink></span>
        </label>
      </div>
    </SettingCard>

    <SettingCard
      v-if="plan.payments.length"
      data-test="plan-payments"
    >
      <SettingRow
        title="Paiements"
        description="Les paiements reçus pour Plus."
      />
      <SettingRow
        v-for="(payment, index) in plan.payments"
        :key="index"
        :title="day(payment.paid_on, true)"
      >
        <span class="plan-usage-count">{{ money(payment.amount_cents, payment.currency) }}</span>
      </SettingRow>
    </SettingCard>
  </template>
</template>
