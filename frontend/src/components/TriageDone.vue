<script setup lang="ts">
import { computed, ref } from "vue";

import type { Offer } from "../api/client";
import { usePhone } from "../composables/usePhone";
import { companyPlace, plural } from "../format";
import CompanyLogo from "./CompanyLogo.vue";
import MomentScreen from "./MomentScreen.vue";

// La fin du tri (lot du 11 novembre au soir, PR 45 ; maquettes FinDuTri et FinDuTriOrdinateur), sur le modèle de
// « C’est fait ! » et « Candidature envoyée » : l'illustration, « C’est trié ! », le compte des offres gardées et
// écartées, puis une ligne par offre gardée avec « Préparer ». Sans offre gardée : pas de carte, un seul bouton.
const props = defineProps<{ kept: Offer[]; dismissed: number }>();
const { phone } = usePhone();

const line = computed(() => {
  if (!props.kept.length) return "Aucune offre gardée cette fois.";
  const parts = [plural(props.kept.length, "offre gardée", "offres gardées")];
  if (props.dismissed) parts.push(plural(props.dismissed, "écartée", "écartées"));
  return `${parts.join(", ")}.`;
});
const prepare = (offer: Offer) => ({ name: "preparation", params: { id: offer.id } });

// Le focus arrive ici quand la dernière offre est triée.
const root = ref<HTMLElement | null>(null);
defineExpose({ focus: () => root.value?.focus() });
</script>

<template>
  <div
    ref="root"
    class="tri-done"
    tabindex="-1"
    data-test="triage-done"
  >
    <MomentScreen
      image="/tri/fin-du-tri.webp"
      title="C’est"
      hand="trié !"
      hand-phone
    >
      <p data-test="triage-summary">
        {{ line }}<template v-if="!phone && kept.length">
          Tu peux préparer les lettres et CV maintenant, ou plus tard depuis Candidatures.
        </template>
      </p>
      <ul
        v-if="kept.length"
        class="tri-done-list"
        data-test="triage-kept"
      >
        <li
          v-for="offer in kept"
          :key="offer.id"
        >
          <CompanyLogo
            :offer="offer"
            pair
            class="tri-done-logo"
          />
          <span class="tri-done-names">
            <b>{{ offer.title }}</b>
            <span>{{ companyPlace(offer.company || "Entreprise non indiquée", offer.location) }}</span>
          </span>
          <RouterLink
            :to="prepare(offer)"
            class="tri-done-prepare"
            :aria-label="`Préparer : ${offer.title}`"
          >
            Préparer
          </RouterLink>
        </li>
      </ul>
      <template #actions>
        <RouterLink
          v-if="kept.length"
          :to="prepare(kept[0]!)"
          class="button-link primary-link tri-done-main"
          data-test="triage-prepare-first"
        >
          {{ phone ? "Préparer la première candidature" : "Préparer la première" }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'today' }"
          :class="['tri-done-home', { 'tri-done-home-alone': !kept.length }]"
          data-test="triage-home"
        >
          Retour à l’accueil
        </RouterLink>
      </template>
    </MomentScreen>
  </div>
</template>

<style scoped>
.tri-done { --td-logo: 44px; --td-row: 68px; --td-card: 480px; --td-16: 1rem; --td-21: 1.3125rem; --td-14: 0.875rem; --td-15: 0.9375rem; --td-17: 1.0625rem; --td-48: 48px; --td-10: 10px; outline: none; }
/* Sur ordinateur, la fin du tri reste dans la page, sous l'en-tête (maquette FinDuTriOrdinateur) : la règle
   globale « .sent-screen » (écran poussé du téléphone) ne s'applique pas. */
@media (min-width: 821px) { .tri-done :deep(.sent-screen) { position: static; overflow: visible; background: none; } }
@media (min-width: 1024px) { .tri-done :deep(.sent-screen-actions) { gap: var(--space-3); } }
.tri-done-list { width: 100%; box-sizing: border-box; margin: var(--space-2) 0 0; padding: 0; list-style: none; border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface); text-align: left; }
.tri-done-list li { display: flex; align-items: center; gap: var(--space-3); min-height: var(--td-row); padding: 0 var(--space-2) 0 var(--space-4); }
.tri-done-list li + li { border-top: 1px solid var(--tri-rule); }
.tri-done-logo { flex: none; width: var(--td-logo); height: var(--td-logo); }
.tri-done-names { flex: 1; min-width: 0; display: grid; }
.tri-done-names b { font-size: var(--td-16); line-height: var(--td-21); font-weight: var(--weight-bold); color: var(--text); }
.tri-done-names span { font-size: var(--td-14); color: var(--text-secondary); }
.tri-done-prepare { display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-2); font-size: var(--td-15); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
.tri-done-main { justify-content: center; width: 100%; box-sizing: border-box; min-height: var(--btn-primary); border-radius: var(--radius-pill); font-size: var(--td-17); font-weight: var(--weight-bold); }
.tri-done-home { display: flex; align-items: center; justify-content: center; min-height: var(--td-48); font-size: var(--td-16); font-weight: var(--weight-bold); color: var(--primary-text); text-decoration: none; }
@media (min-width: 1024px) {
  .tri-done-list { width: var(--td-card); margin-top: var(--space-5); }
  .tri-done-main { order: 2; width: auto; min-height: var(--target-min); padding: 0 var(--space-5); font-size: var(--td-15); }
  .tri-done-home { order: 1; min-height: var(--target-min); padding: 0 var(--space-4); border: 1.5px solid var(--tri-outline); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--td-15); font-weight: var(--weight-semibold); }
}
</style>
