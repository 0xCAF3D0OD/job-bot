<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import PageHero from "../components/PageHero.vue";

// Conditions d'utilisation (docs/125 §7) : publiques, comme Données personnelles et
// Accessibilité. Un projet à faire relire par un juriste avant d'encaisser : le paiement reste
// fermé (`JOBBOT_BILLING_ENABLED`) tant que ce n'est pas fait.
const contact = ref<string | null>(null);

onMounted(async () => {
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
});
</script>

<template>
  <PageHero title="Conditions d'utilisation" />
  <section class="band">
    <div
      class="container narrow privacy-page"
      data-test="terms"
    >
      <h2>Le service</h2>
      <ul>
        <li>jobA1 aide à chercher un emploi en Suisse : il reçoit les offres de tes alertes, les note, prépare tes lettres et tes CV, suit tes candidatures et tes preuves pour l'ORP.</li>
        <li>jobA1 n'envoie jamais une candidature à ta place et ne se connecte pas à tes comptes sur les sites d'emploi.</li>
        <li>La note d'une offre et les textes de l'IA sont des aides : relis-les avant de t'en servir.</li>
      </ul>

      <h2>Les formules</h2>
      <ul>
        <li><strong>Essentiel</strong> est gratuite. Tout ce qui n'appelle pas l'IA est illimité, y compris le suivi et les preuves ORP ; l'IA a des limites chaque mois, écrites dans Réglages › Compte.</li>
        <li><strong>Plus</strong> coûte 7 CHF par mois, sans TVA (l'exploitant n'y est pas assujetti). Elle relève les limites de l'IA.</li>
        <li>Les compteurs repartent le premier de chaque mois. Une limite atteinte ne bloque rien d'autre.</li>
      </ul>

      <h2>Le paiement</h2>
      <ul>
        <li>Le paiement passe par Payrexx, un prestataire suisse ; jobA1 ne voit jamais ta carte.</li>
        <li>Plus se renouvelle chaque mois, au même jour, jusqu'à ce que tu le résilies.</li>
        <li>Tu résilies quand tu veux, dans Réglages › Compte : Plus reste actif jusqu'à la fin du mois payé, sans nouveau paiement. Un mois commencé n'est pas remboursé.</li>
        <li>En arrêtant Plus, tu ne perds rien : tes lettres, tes CV, tes notes et ton suivi restent.</li>
      </ul>

      <h2>Données personnelles</h2>
      <p>
        Ce que jobA1 garde, pourquoi et combien de temps : <RouterLink to="/tes-donnees">
          Données personnelles
        </RouterLink>. Tu peux tout exporter et supprimer ton compte à tout moment.
      </p>

      <h2>Responsabilité</h2>
      <ul>
        <li>jobA1 fait de son mieux pour que le service fonctionne, sans garantir qu'il soit toujours disponible ni qu'une offre reçue soit encore ouverte.</li>
        <li>Tu restes responsable de ce que tu envoies aux employeurs et à l'ORP.</li>
      </ul>

      <h2>Droit applicable</h2>
      <p>Le droit suisse s'applique.</p>

      <h2>L'exploitant</h2>
      <p
        v-if="contact"
        class="privacy-contact"
        data-test="terms-contact"
      >
        {{ contact }}
      </p>
      <p
        v-else
        class="hint"
      >
        L'exploitant de la plateforme n'a pas encore indiqué ses coordonnées.
      </p>
    </div>
  </section>
</template>
