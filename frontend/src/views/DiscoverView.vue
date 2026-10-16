<script setup lang="ts">
import Illustration, { type IllustrationName } from "../components/Illustration.vue";
import { useAuth } from "../composables/useAuth";

// La plateforme, pour qui n'est pas connecté (docs/67, complément) : à quoi sert jobA1, comment
// on s'en sert, ce qu'il advient des données. L'accès se fait sur invitation (docs/65).
const { loggedIn } = useAuth();

const STEPS: { art: IllustrationName; title: string; text: string }[] = [
  {
    art: "alertes-carte",
    title: "Tes alertes, une fois pour toutes",
    text: "Tu crées tes alertes sur les sites d'emploi ; les offres arrivent ici, au même endroit, sans doublons.",
  },
  {
    art: "offres-profils",
    title: "Les offres qui te correspondent d'abord",
    text: "Chaque offre est comparée à ce que tu cherches et à ton profil : les meilleures en tête, les autres de côté.",
  },
  {
    art: "suivi-envoi",
    title: "Ta candidature préparée",
    text: "Une lettre et un CV adaptés à l'offre, que tu relis, corriges et envoies toi-même.",
  },
  {
    art: "tableau-de-bord",
    title: "Le suivi, sans rien oublier",
    text: "Réponses, entretiens, relances : tout est daté, et la plateforme te rappelle ce qui attend.",
  },
  {
    art: "preuves-orp",
    title: "Tes preuves ORP prêtes",
    text: "Chaque mois, la liste de tes recherches est prête à remettre à l'ORP, avant la date limite.",
  },
  {
    art: "formations",
    title: "Ton métier, et ce qui bouge",
    text: "Les actualités et les formations de ton domaine, triées pour toi.",
  },
];
</script>

<template>
  <article
    class="discover"
    data-test="discover"
  >
    <header class="discover-hero">
      <Illustration
        name="porte-ouverte"
        class="discover-hero-art"
      />
      <h1>Less searching. More living.</h1>
      <p class="discover-lead">
        jobA1 t'aide à chercher un emploi en Suisse et à prouver tes recherches à l'ORP, sans y passer tes journées.
      </p>
      <RouterLink
        v-if="!loggedIn"
        to="/connexion"
        class="button-link primary-link"
        data-test="discover-login"
      >
        Se connecter
      </RouterLink>
      <p
        v-if="!loggedIn"
        class="hint"
      >
        L'accès se fait sur invitation.
      </p>
    </header>

    <h2 class="discover-title">
      Comment ça marche
    </h2>
    <ol class="discover-steps">
      <li
        v-for="(item, i) in STEPS"
        :key="item.art"
        class="discover-step"
      >
        <Illustration
          :name="item.art"
          class="discover-art"
        />
        <div>
          <span class="discover-number">{{ i + 1 }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
        </div>
      </li>
    </ol>

    <section class="discover-data">
      <h2>Tes données restent à toi</h2>
      <p>
        Ton compte est séparé de ceux des autres. Tu peux tout exporter, ou supprimer ton compte. Tes coordonnées et les noms
        de tes contacts ne partent jamais à l'IA.
      </p>
      <RouterLink to="/tes-donnees">
        Ce qui est gardé, et ce qui part à l'IA
      </RouterLink>
    </section>
  </article>
</template>
