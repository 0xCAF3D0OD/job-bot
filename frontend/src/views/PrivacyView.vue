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

onMounted(async () => {
  await load();
  const { data } = await api.GET("/api/privacy");
  contact.value = data?.contact ?? null;
});
</script>

<template>
  <PageHero
    title="Tes données"
    subtitle="Ce que jobA1 garde sur toi, et ce que tu peux en faire."
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
      <p>
        Sur le serveur de la plateforme : une base de données et un dossier de fichiers, chacun séparé par compte.
        Tout reste jusqu'à ce que tu supprimes ton compte, sauf les discussions avec l'assistant (effacées après 30 jours)
        et les notifications (90 jours).
      </p>

      <h2>Qui y a accès</h2>
      <p>
        Toi seul, par ta connexion. Aucun autre compte ne voit tes données. L'exploitant de la plateforme voit seulement
        ton usage (dernière connexion, dépense de l'IA du mois, nombre d'offres reçues) ; il administre le serveur, mais
        la plateforme ne lui montre jamais tes offres, candidatures, documents ou discussions.
      </p>

      <h2>Ce qui part à l'IA</h2>
      <p>
        Pour noter les offres, rédiger les lettres et répondre à l'assistant, la plateforme envoie à l'IA (Anthropic) le
        texte des offres, tes blocs de profil et ce que tu lui demandes ; le texte de ton CV quand tu demandes des
        propositions de blocs ; le contenu des alertes des sites que l'IA lit. <strong>Jamais tes coordonnées</strong> (nom,
        adresse, téléphone, e-mail), ni les noms de tes contacts : la plateforme les ajoute elle-même aux lettres.
      </p>
      <p>
        Les notifications sur ton téléphone passent par le service ntfy seulement si tu les as activées.
      </p>

      <h2>Ce que tu peux faire</h2>
      <p>
        Dans Réglages, rubrique Compte :
        <strong>exporter</strong> toutes tes données (une archive avec tes données, tes documents et tes e-mails d'alerte),
        ou <strong>supprimer</strong> ton compte : tout est effacé, fichiers compris.
      </p>
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
    </div>
  </section>
</template>
