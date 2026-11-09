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
// La connexion Get'emAll est ouverte (docs/140) : ce qui lui part, si on la relie.
const getemall = ref(false);

onMounted(async () => {
  await load();
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
  guestMailbox.value = data?.guest_mailbox ?? false;
  billing.value = data?.billing ?? false;
  getemall.value = data?.getemall ?? false;
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
        <li>Ta recherche : critères, alertes, offres reçues avec leur note, candidatures, contacts notés, entretiens et leurs retours, justificatifs ORP.</li>
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
          L'exploitant voit seulement ton usage : dernière connexion, dépense de l'IA du mois, nombre d'offres reçues. Pendant un test de la plateforme, aussi la date de tes premières étapes (première alerte, première offre reçue, première candidature préparée, premiers justificatifs exportés), sans leur contenu, pour mesurer le temps de prise en main : elles sont effacées à la fin du test, ou avec ton compte.
        </li>
        <li>
          Il administre le serveur, mais ne voit jamais tes offres, candidatures, documents ou discussions. Il ne les lit qu'à ta demande ou par obligation légale.
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

      <h2 id="extension">
        L'extension du navigateur
      </h2>
      <ul data-test="privacy-extension">
        <li>Elle ne lit une page qu'au clic sur son icône, dans l'onglet ouvert.</li>
        <li>« Envoyer à jobA1 » : seulement l'annonce et son adresse. Jamais tes cookies, ton profil LinkedIn ni tes autres onglets.</li>
        <li>Ton nom est retiré du texte. Le journal garde l'offre touchée, jamais le texte.</li>
        <li>Sur jobup, jobs.ch et LinkedIn, elle met ton adresse jobA1 dans « Créer une alerte », sans rien valider.</li>
        <li>Transfert Gmail : seules les alertes des sites sont lues ; tout autre e-mail transféré est supprimé sans être lu.</li>
      </ul>

      <h2 id="ia">
        Ce qui part à l'IA (Anthropic)
      </h2>
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
      <p data-test="privacy-oauth">
        Si tu te connectes avec Apple, Google ou Microsoft, ce fournisseur sait que tu utilises jobA1 ; jobA1 garde
        seulement le numéro de ton compte chez lui et ton e-mail, tant que le lien existe (Réglages, Connexions).
      </p>

      <section
        v-if="getemall"
        class="privacy-partner"
        aria-labelledby="getemall"
        data-test="privacy-getemall"
      >
        <h2 id="getemall">
          Get'emAll, si tu le relies
        </h2>
        <p>
          Get'emAll est une app d'entraînement aux entretiens, du même exploitant, hébergée en Suisse. Elle ne reçoit
          <strong>rien</strong> tant que tu ne l'as pas autorisée.
        </p>
        <h3>Ce qui part</h3>
        <ul>
          <li>Tes premiers pas : combien sont faits sur 5, et le suivant.</li>
          <li>Tes candidatures : poste, entreprise, statut, date d'entretien.</li>
          <li>Le texte d'une offre quand tu t'entraînes pour elle, sans les contacts.</li>
          <li>Le nombre de recherches ORP du mois et l'objectif, <strong>seulement si tu l'as coché</strong>.</li>
        </ul>
        <h3>Ce qui ne part jamais</h3>
        <ul>
          <li>Ton nom, tes coordonnées, ton numéro AVS.</li>
          <li>Ton CV, tes lettres, tes documents, tes justificatifs ORP.</li>
          <li>Les contacts des offres et l'identifiant de ton compte jobA1.</li>
        </ul>
        <h3>Comment</h3>
        <ul>
          <li>Get'emAll lit ton suivi quand tu l'ouvres, sans en garder de copie. Seule l'offre choisie pour t'entraîner y est gardée.</li>
          <li>Il ne peut rien changer dans jobA1.</li>
          <li>jobA1 garde la date de la dernière lecture, visible dans Réglages.</li>
        </ul>
      </section>

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
        <li
          v-if="getemall"
          data-test="privacy-revoke"
        >
          <strong>Retirer l'accès</strong> d'une app reliée : Réglages › Connexions. Ce qu'elle a gardé s'efface depuis l'app.
        </li>
        <li>
          <strong>Fermer</strong> ton compte : tout est effacé, fichiers compris{{ getemall ? ", et l'accès des apps reliées est retiré" : "" }}. Aussi depuis le menu de ton compte.
        </li>
      </ul>
      <p v-if="loggedIn">
        <RouterLink
          :to="{ path: '/reglages', query: { rubrique: 'donnees' } }"
          class="link"
          data-test="privacy-settings"
        >
          Ouvrir Réglages, rubrique Compte
        </RouterLink>
      </p>
      <p v-if="loggedIn && getemall">
        <RouterLink
          :to="{ path: '/reglages', query: { rubrique: 'connexions' } }"
          class="link"
          data-test="privacy-connections"
        >
          Ouvrir Réglages › Connexions
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
          class="link"
          data-test="privacy-accessibility"
        >
          Voir ce qui est vérifié
        </RouterLink>
      </p>
    </div>
  </section>
</template>

<style>
/* Maquette ConfidentialiteGetemall (390 px) : la section Get'emAll dans une carte, après celle de l'IA. */
.privacy-partner { display: flex; flex-direction: column; gap: var(--space-3); margin: var(--space-6) 0; padding: var(--space-4); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); }
.privacy-page .privacy-partner h2 { margin: 0; }
.privacy-page .privacy-partner h3 { margin: var(--space-1) 0 0; font-size: var(--font-body); font-weight: var(--weight-bold); }
.privacy-partner p, .privacy-partner ul { margin: 0; }
.privacy-page .privacy-partner ul { display: flex; flex-direction: column; gap: var(--space-2); padding-left: var(--space-5); }
</style>
