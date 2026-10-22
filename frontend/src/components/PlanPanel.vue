<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import { usePlan } from "../composables/usePlan";
import InlineConfirm from "./InlineConfirm.vue";

// La formule (docs/125 §4 et §6), dans Réglages › Compte : son nom, ce qu'elle limite, une ligne
// par usage (« 37 sur 150 ») avec sa jauge, quand les compteurs repartent, ce que Plus ajoute ;
// une fois le paiement ouvert, « Passer à Plus » (les conditions acceptées d'abord), la date de
// fin, « Résilier » et les paiements reçus. L'exploitant n'a pas de formule : la carte ne
// s'affiche pas.
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
  <div
    v-if="plan && !plan.unlimited"
    class="form-card plan-card"
    data-test="plan-panel"
  >
    <fieldset>
      <legend>Formule</legend>
      <p
        class="setting-desc"
        data-test="plan-name"
      >
        <template v-if="plan.plan === 'plus'">
          <strong>Plus</strong>{{ offered ? ", offerte par l'équipe jobA1" : "" }} : l'IA va plus loin chaque mois ; le reste n'a pas de limite.
        </template>
        <template v-else>
          <strong>Essentiel</strong>, gratuite : l'IA a des limites chaque mois ; le reste n'en a pas.
        </template>
      </p>
      <p
        v-if="message"
        :class="message.kind === 'error' ? 'notice error' : 'hint plan-message'"
        :role="message.kind === 'error' ? 'alert' : 'status'"
        data-test="plan-message"
      >
        {{ message.text }}
      </p>
      <ul
        class="plan-usage"
        data-test="plan-usage"
      >
        <li
          v-for="usage in plan.usage"
          :key="usage.key"
          :data-test="`plan-${usage.key}`"
        >
          <span class="plan-usage-name">{{ capitalized(usage.label) }}</span>
          <span class="plan-usage-count">{{ usage.used }} sur {{ usage.limit }}</span>
          <span
            class="plan-usage-gauge"
            :style="{ '--p': Math.min(100, Math.round((usage.used / (usage.limit || 1)) * 100)) }"
            aria-hidden="true"
          />
        </li>
      </ul>
      <p
        class="hint plan-resets"
        data-test="plan-resets"
      >
        Les compteurs repartent le {{ resets }}.
      </p>

      <!-- Plus payé : la date de fin, et résilier. -->
      <template v-if="paid">
        <p
          class="setting-info plan-plus"
          data-test="plan-paid"
        >
          <strong>Plus jusqu'au {{ day(plan.plan_until) }}</strong>{{ plan.cancelled ? ", puis Essentiel. Pas de nouveau paiement." : ", renouvelé chaque mois." }}
        </p>
        <div
          v-if="!plan.cancelled && !confirming"
          class="form-actions setting-pills"
        >
          <button
            type="button"
            class="pill"
            data-test="plan-cancel"
            @click="confirming = true"
          >
            Résilier
          </button>
        </div>
        <InlineConfirm
          v-if="confirming"
          :message="`Résilier Plus ? Il reste actif jusqu'au ${day(plan.plan_until)}, sans nouveau paiement.`"
          confirm-label="Résilier"
          :busy="busy"
          @confirm="cancel"
          @cancel="confirming = false"
        />
      </template>

      <!-- Essentiel : ce que Plus ajoute, et l'acheter une fois le paiement ouvert. -->
      <template v-else-if="plan.plan !== 'plus'">
        <p
          class="setting-info plan-plus"
          data-test="plan-plus"
        >
          <strong>Plus · {{ plan.plus_price_chf }} CHF par mois</strong> :
          {{ plusLimits.letter }} lettres, {{ plusLimits.cv }} CV, {{ plusLimits.practice }} entraînements, {{ plusLimits.score }} offres notées. {{ canBuy ? "Sans engagement." : "Le paiement arrive bientôt." }}
        </p>
        <template v-if="canBuy">
          <label class="checkbox plan-terms">
            <input
              v-model="accepted"
              type="checkbox"
              data-test="plan-accept"
            >
            <span>J'accepte les <RouterLink to="/conditions">conditions d'utilisation</RouterLink></span>
          </label>
          <div class="form-actions">
            <button
              type="button"
              class="primary"
              :disabled="!accepted || busy"
              data-test="plan-buy"
              @click="buy"
            >
              Passer à Plus
            </button>
          </div>
        </template>
      </template>

      <template v-if="plan.payments.length">
        <p class="plan-payments-title">
          Paiements
        </p>
        <ul
          class="plan-usage plan-payments"
          data-test="plan-payments"
        >
          <li
            v-for="(payment, index) in plan.payments"
            :key="index"
          >
            <span>{{ day(payment.paid_on, true) }}</span>
            <span class="plan-usage-count">{{ money(payment.amount_cents, payment.currency) }}</span>
          </li>
        </ul>
      </template>
    </fieldset>
  </div>
</template>
