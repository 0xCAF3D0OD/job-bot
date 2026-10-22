<script setup lang="ts">
import { nextTick, ref } from "vue";

import { api, type OrpMonth, type Source } from "../api/client";
import { printSheet } from "../composables/usePrint";
import { formatMonth, sourceLabel } from "../format";

// Les preuves ORP du mois (docs/09), en version imprimée, et ce qu'il faut savoir avant de les
// remettre. Le tableau à l'écran et la vue champ par champ sont partis en 0.67.4 (docs/85) :
// la liste « À déclarer » du Suivi et le panneau d'une candidature les remplacent.
const props = defineProps<{ data: OrpMonth }>();
const emit = defineEmits<{ reload: [] }>();

const withSearches = ref(false);
const today = new Intl.DateTimeFormat("fr-CH").format(new Date());

async function printPdf(journal = false): Promise<void> {
  withSearches.value = journal;
  await nextTick();
  const sheet = document.querySelector<HTMLElement>(".orp-sheet");
  if (sheet) printSheet(sheet, { title: `Preuves ORP - ${props.data.month}`, landscape: true });
  withSearches.value = false;
  await api.POST("/api/orp/{month}/exported", { params: { path: { month: props.data.month } } });
  emit("reload");
}

defineExpose({ printPdf });
</script>

<template>
  <div class="orp-sheet-tab">
    <p
      v-if="data.changed_after_submit"
      class="notice"
      data-test="changed"
    >
      Des candidatures ont changé après la remise : renvoie une version corrigée.
    </p>
    <p
      v-if="data.count && !data.holder.name"
      class="notice"
    >
      Ton nom n'est pas saisi : <RouterLink to="/profil?onglet=coordonnees">
        complète tes coordonnées
      </RouterLink> pour l'en-tête du PDF.
    </p>

    <!-- Version imprimée : A4 paysage, proche du formulaire officiel. -->
    <article
      class="orp-sheet print-sheet"
      aria-hidden="true"
    >
      <h2 class="orp-sheet-title">
        Preuves des recherches personnelles effectuées en vue de trouver un emploi
      </h2>
      <div class="orp-holder">
        <span>Nom et prénom : <strong>{{ data.holder.name }}</strong></span>
        <span>Adresse : {{ data.holder.address }}</span>
        <span>N° AVS : ______________________</span>
        <span>Période : <strong>{{ formatMonth(data.month) }}</strong></span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Entreprise, adresse</th>
            <th>Personne de contact, téléphone</th>
            <th>Poste</th>
            <th>Taux</th>
            <th>Mode</th>
            <th>Assignée ORP</th>
            <th>Résultat</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in data.rows"
            :key="row.application_id"
          >
            <td>{{ row.date }}</td>
            <td>{{ [row.company, row.address].filter(Boolean).join(", ") }}</td>
            <td>{{ [row.contact, row.phone].filter(Boolean).join(", ") }}</td>
            <td>
              {{ row.job_title }}
              <span
                v-if="row.url"
                class="orp-url"
              >{{ row.url }}</span>
            </td>
            <td>{{ row.rate }}</td>
            <td>{{ row.method }}</td>
            <td>{{ row.assigned }}</td>
            <td>{{ row.result }}</td>
          </tr>
        </tbody>
      </table>
      <div class="orp-sign">
        <span>Lieu et date : ______________________ (imprimé le {{ today }})</span>
        <span>Signature : ______________________</span>
      </div>
      <section
        v-if="withSearches && data.searches.length"
        class="orp-annex"
      >
        <h2>Annexe : journal des recherches ({{ formatMonth(data.month) }})</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Site</th>
              <th>Alerte</th>
              <th>Offres</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(search, index) in data.searches"
              :key="index"
            >
              <td>{{ new Date(search.received_at).toLocaleDateString("fr-CH") }}</td>
              <td>{{ sourceLabel[search.source as Source] ?? search.source }}</td>
              <td>{{ search.label }}</td>
              <td>{{ search.results_count }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </article>
  </div>
</template>
