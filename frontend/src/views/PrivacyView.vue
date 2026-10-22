<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import PageHero from "../components/PageHero.vue";
import { useAuth } from "../composables/useAuth";

// Tes données (docs/65 §6) : ce qui est gardé, où, combien de temps, qui y a accès, ce qui
// part à l'IA. Publique : elle se lit avant d'accepter une invitation. Les mentions
// (responsable, contact, hébergeur) sont écrites par l'exploitant, dans la Plateforme.
const { loggedIn, load } = useAuth();
const contact = ref<string | null>(null);
// La boîte des invités en place (docs/113) : les e-mails des sites ne passent plus par
// l'exploitant.
const guestMailbox = ref(false);
// Le paiement de Plus est ouvert (docs/125 §6).
const billing = ref(false);

onMounted(async () => {
  await load();
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
  guestMailbox.value = data?.guest_mailbox ?? false;
  billing.value = data?.billing ?? false;
});
</script>

<template>
  <PageHero
    title="Données personnelles"
  />
  <section class="band">
    <div class="container narrow privacy-page">
      <h2>Ce qui est gardé</h2>
      <ul>
        <li>Ton profil : coordonnées, CV et documents déposés, blocs de profil (expériences, compétences…).</li>
        <li>Ta recherche : critères, alertes, offres reçues avec leur note, candidatures, contacts notés, entretiens et leurs retours, preuves ORP.</li>
        <li>Les e-mails d'alerte reçus pour toi, tels quels, pour les relire si un site change de format.</li>
        <li>Tes réglages, tes formations suivies, tes discussions avec l'assistant.</li>
      </ul>

      <h2>Où, et combien de temps</h2>
      <ul>
        <li>Sur le serveur de la plateforme : une base de données et un dossier de fichiers, séparés par compte.</li>
        <li>Jusqu'à ce que tu supprimes ton compte. Sauf les discussions avec l'assistant (30 jours), les notifications et les copies des e-mails d'alerte (90 jours).</li>
        <li>
          Une sauvegarde chiffrée chaque nuit, que seul l'exploitant peut ouvrir, gardée <strong>6 mois au plus</strong>.
          Un compte supprimé y reste jusqu'à 6 mois ; il ne revient que si toute la plateforme est restaurée.
        </li>
      </ul>

      <h2>Qui y a accès</h2>
      <ul>
        <li><strong>Toi seul</strong>, par ta connexion. Aucun autre compte ne voit tes données.</li>
        <li>
          L'exploitant voit seulement ton usage : dernière connexion, dépense de l'IA du mois, nombre d'offres reçues.
        </li>
        <li>
          Il administre le serveur, mais la plateforme ne lui montre jamais tes offres, candidatures, documents ou
          discussions. Il s'engage à ne pas les lire, sauf à ta demande ou par obligation légale.
        </li>
      </ul>

      <h2>Les e-mails des sites d'emploi</h2>
      <ul data-test="privacy-mailbox">
        <template v-if="guestMailbox">
          <li>
            Les sites t'écrivent à ton adresse jobA1. Ces e-mails arrivent dans <strong>la boîte de jobA1</strong>,
            hébergée en Suisse chez Infomaniak, séparée de celle de l'exploitant.
          </li>
          <li>jobA1 les range dans ton compte, puis <strong>les efface de cette boîte</strong> ; personne ne la lit à la main.</li>
        </template>
        <li v-else>
          Les sites t'écrivent à ton adresse jobA1. Ces e-mails passent par la boîte e-mail de la plateforme, que
          l'exploitant administre.
        </li>
        <li>Un code de vérification d'un site est effacé de jobA1 <strong>30 minutes</strong> après son arrivée, avec la copie de son e-mail. Il ne part jamais dans la notification du téléphone.</li>
        <li>Les autres messages des sites (bienvenue, alerte modifiée…) sont gardés 30 jours.</li>
      </ul>

      <h2>Ce qui part à l'IA (Anthropic)</h2>
      <ul>
        <li>Le texte des offres, tes blocs de profil et ce que tu demandes : pour noter, rédiger et répondre.</li>
        <li>Le texte de ton CV, sans tes coordonnées ni ta date de naissance, pour proposer tes blocs de profil.</li>
        <li>Le contenu des alertes des sites que l'IA lit.</li>
        <li>
          <strong>Jamais tes coordonnées</strong> (nom, adresse, téléphone, e-mail) ni les noms de tes contacts : la
          plateforme les ajoute elle-même aux lettres.
        </li>
      </ul>
      <p>
        Les notifications sur ton téléphone passent par le service ntfy, seulement si tu les as activées.
      </p>

      <template v-if="billing">
        <h2>Le paiement de Plus (Payrexx)</h2>
        <ul data-test="privacy-billing">
          <li>Payrexx, un prestataire suisse, reçoit ton nom, ton e-mail et ton moyen de paiement ; jobA1 ne voit jamais ta carte.</li>
          <li>jobA1 garde ta formule, la date de fin de Plus et tes paiements (date, montant), tant que ton compte existe.</li>
          <li>Les justificatifs de paiement sont gardés 10 ans par Payrexx et l'exploitant : c'est une obligation comptable.</li>
          <li>
            Les règles du paiement et de la résiliation : <RouterLink to="/conditions">Conditions d'utilisation</RouterLink>.
          </li>
        </ul>
      </template>

      <h2>Ce qui est possible</h2>
      <p>Dans Réglages, rubrique Compte :</p>
      <ul>
        <li><strong>Exporter</strong> tout : une archive avec tes données, tes documents et tes e-mails d'alerte des 90 derniers jours.</li>
        <li><strong>Fermer</strong> ton compte : tout est effacé, fichiers compris. Aussi depuis le menu de ton compte.</li>
      </ul>
      <p v-if="loggedIn">
        <RouterLink
          :to="{ path: '/reglages', query: { rubrique: 'compte' } }"
          data-test="privacy-settings"
        >
          Ouvrir Réglages, rubrique Compte
        </RouterLink>
      </p>

      <h2>Responsable</h2>
      <p
        v-if="contact"
        class="privacy-contact"
        data-test="privacy-contact"
      >
        {{ contact }}
      </p>
      <p
        v-else
        class="hint"
        data-test="privacy-missing"
      >
        L'exploitant de la plateforme n'a pas encore indiqué ses coordonnées.
      </p>

      <h2>Accessibilité</h2>
      <p>
        <RouterLink
          to="/accessibilite"
          data-test="privacy-accessibility"
        >
          Voir ce qui est vérifié
        </RouterLink>
      </p>
    </div>
  </section>
</template>
